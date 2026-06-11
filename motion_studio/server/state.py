"""Shared server state: config, the global heavy lock, and lazy helpers.

The Flask app keeps one :class:`ServerState` on ``app.config["MS_STATE"]``. It
holds the resolved :class:`~motion_studio.config.Config`, a single global lock
serializing all GPU/SMPL/ffmpeg work, and small lazily-built caches (SMPL faces,
foot-vertex masks, per-clip mesh state). Torch and SMPL are imported only when a
heavy request actually needs them, so ``--help`` and startup stay light.
"""

from __future__ import annotations

import collections
import contextlib
import os
import threading
import time
from collections.abc import Iterator

from motion_studio.config import Config
from motion_studio.core.types import Motion

# Bound on the per-clip mesh-state LRU cache. Each entry pins one batch_size=1
# SMPL model (GPU-resident); the cap keeps total VRAM bounded across clips.
_MESH_CACHE_CAP = 6

# How long a heavy request waits for the global lock before giving up with a
# 503 instead of blocking a worker thread forever behind a stuck GPU/ffmpeg job.
_HEAVY_LOCK_TIMEOUT_S = 120.0

# A background (warm-up) job only runs once the editor has been idle for this
# long. A single warm-up compute holds the GPU lock for seconds, so yielding
# per-acquire is not enough: during playback the gaps between frame requests
# would let a multi-second compute slip in and stall the next frame. Requiring a
# real idle gap keeps the GPU fully available while the user plays/scrubs.
_IDLE_GAP_S = 1.5


class HeavyBusyError(RuntimeError):
    """Raised when the global heavy lock cannot be acquired in time.

    Handlers map this to an HTTP 503 (server busy) rather than blocking the
    request thread indefinitely behind another GPU / ffmpeg / segmentation job.
    """


def _is_safe_name(name: str) -> bool:
    """Return True if ``name`` is a plain clip/bundle name (no traversal)."""
    if not name:
        return False
    return not ("/" in name or ".." in name or name.startswith("."))


class ServerState:
    """Mutable, shared state for one running Motion Studio server.

    Attributes:
      config: The resolved server configuration.
      heavy_lock: A lock serializing all GPU / SMPL / ffmpeg operations.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.heavy_lock = threading.Lock()
        # Count of interactive requests currently in (or waiting for) the heavy
        # path. Background warm-up jobs check this and yield so the editor stays
        # responsive while they run (see :meth:`heavy` / :meth:`heavy_idle`).
        self._interactive = 0
        self._interactive_lock = threading.Lock()
        # Monotonic timestamp of the most recent interactive heavy activity;
        # background jobs wait for a quiet gap after it (see ``heavy_idle``).
        self._last_interactive = 0.0
        self._mesh_states: collections.OrderedDict[
            tuple[str, float, str], object
        ] = collections.OrderedDict()
        self._mesh_lock = threading.Lock()
        self._foot_masks: dict[str, list] | None = None
        self._foot_lock = threading.Lock()
        self._seg = None  # (model, weights, device) for /bg_nobg, lazy.
        self._seg_lock = threading.Lock()
        self.comments_store = os.path.join(config.workspace, "comments.json")

    # -- heavy lock --------------------------------------------------------

    @contextlib.contextmanager
    def heavy(self, timeout: float = _HEAVY_LOCK_TIMEOUT_S) -> Iterator[None]:
        """Acquire the global heavy lock with a timeout (context manager).

        Drop-in for ``with st.heavy_lock:`` that refuses to block a worker
        thread forever: if another GPU / ffmpeg / segmentation job holds the
        lock past ``timeout`` seconds, it raises :class:`HeavyBusyError` (which
        handlers turn into an HTTP 503) instead of hanging.

        Args:
          timeout: Seconds to wait for the lock before giving up.

        Yields:
          None, with the lock held.

        Raises:
          HeavyBusyError: If the lock cannot be acquired within ``timeout``.
        """
        with self._interactive_lock:
            self._interactive += 1
            self._last_interactive = time.monotonic()
        try:
            if not self.heavy_lock.acquire(timeout=timeout):
                raise HeavyBusyError(
                    f"server busy: heavy lock held longer than {timeout:.0f}s"
                )
            try:
                yield
            finally:
                self.heavy_lock.release()
        finally:
            with self._interactive_lock:
                self._interactive -= 1
                self._last_interactive = time.monotonic()

    def interactive_pending(self) -> int:
        """Return how many interactive requests are in the heavy path."""
        with self._interactive_lock:
            return self._interactive

    @contextlib.contextmanager
    def heavy_idle(self, poll: float = 0.15) -> Iterator[None]:
        """Acquire the heavy lock at *background* priority.

        Unlike :meth:`heavy`, this never makes an interactive request wait: it
        only takes the lock while no interactive heavy request is in flight, and
        backs off (releasing immediately) the moment one appears. Warm-up jobs
        (metrics, prewarm) use it so a full-library pass cannot starve the
        editor of the single GPU lock. Blocks until it can run; intended for
        background daemon threads only.

        Args:
          poll: Seconds between readiness checks while yielding.

        Yields:
          None, with the lock held and no interactive request waiting.
        """
        while True:
            # Wait for a genuine idle gap: no interactive request in flight AND
            # none in the last _IDLE_GAP_S seconds. This is what keeps a
            # multi-second warm-up compute from slipping into the gaps between
            # playback frame requests and stalling the next frame.
            while (
                self.interactive_pending() > 0
                or (time.monotonic() - self._last_interactive) < _IDLE_GAP_S
            ):
                time.sleep(poll)
            if not self.heavy_lock.acquire(timeout=0.5):
                continue
            # An interactive request may have arrived while we were acquiring;
            # if so, yield the lock back to it rather than blocking it.
            if self.interactive_pending() > 0:
                self.heavy_lock.release()
                time.sleep(poll)
                continue
            break
        try:
            yield
        finally:
            self.heavy_lock.release()

    # -- paths -------------------------------------------------------------

    def bundle_path(self, name: str) -> str:
        """Return the ``.motion`` bundle path for ``name`` in the workspace."""
        from motion_studio import library

        return library.bundle_path_for(self.config.workspace, name)

    def raw_pkl_path(self, clip: str) -> str | None:
        """Return the raw ``pkl_dir/<clip>.pkl`` path, if a pkl dir is set."""
        if not self.config.pkl_dir:
            return None
        return os.path.join(self.config.pkl_dir, clip + ".pkl")

    def clip_mtime(self, clip: str) -> float:
        """Return the source-file mtime backing ``clip`` (cache-key salt).

        Resolves the same way as the loaders (bundle first, then raw pkl) and
        returns the modification time of whichever file exists, so a cache keyed
        by ``(clip, mtime, ...)`` is invalidated automatically when the bundle
        is re-saved or the raw pkl changes. Returns ``0.0`` if neither exists.
        """
        bundle = self.bundle_path(clip)
        if os.path.isfile(bundle):
            try:
                return os.path.getmtime(bundle)
            except OSError:
                return 0.0
        pkl = self.raw_pkl_path(clip)
        if pkl and os.path.isfile(pkl):
            try:
                return os.path.getmtime(pkl)
            except OSError:
                return 0.0
        return 0.0

    # -- lazy heavy helpers ------------------------------------------------

    def _free_mesh_state(self, state) -> None:
        """Free a mesh state's GPU model on eviction (best-effort)."""
        smpl = getattr(state, "smpl", None)
        if smpl is None:
            return
        from motion_studio.smpl import refit

        refit._free_smpl(smpl)

    def mesh_state_if_present(self, clip: str, mtime: float, source: str = ""):
        """Return the cached :class:`MeshState` for the key, or None on a miss.

        The fast path for playback: a hit means the caller never has to resolve
        (re-read + unzip) the motion behind ``clip`` at all. The cache is keyed
        by ``(clip, mtime, source)`` so a re-saved bundle / edited motion is not
        served stale.

        Args:
          clip: Clip / bundle name.
          mtime: Source-file mtime (see :meth:`clip_mtime`).
          source: Which motion variant ("" / "original" / "corrected").

        Returns:
          The cached mesh state, or None if absent (caller must resolve the
          motion and call :meth:`mesh_state`).
        """
        cache_key = (clip, float(mtime), source)
        with self._mesh_lock:
            state = self._mesh_states.get(cache_key)
            if state is not None:
                self._mesh_states.move_to_end(cache_key)
            return state

    def mesh_state(
        self, clip: str, mtime: float, motion: Motion, source: str = ""
    ):
        """Return a cached per-clip :class:`MeshState`, building it once.

        Args:
          clip: Clip / bundle name.
          mtime: Source-file mtime (see :meth:`clip_mtime`); part of the key so
            the cache self-invalidates when the source file changes.
          motion: The motion to build the mesh state from on a cache miss.
          source: Which motion variant ("" / "original" / "corrected").

        Returns:
          The cached or freshly built mesh state. Must be called under
          ``heavy_lock`` on the building path (SMPL load). The cache is
          LRU-bounded (:data:`_MESH_CACHE_CAP`); the evicted state's GPU model
          is freed.
        """
        from motion_studio.smpl import convert

        cache_key = (clip, float(mtime), source)
        with self._mesh_lock:
            state = self._mesh_states.get(cache_key)
            if state is not None:
                self._mesh_states.move_to_end(cache_key)
                return state
            state = convert.MeshState(motion, self.config.smpl_dir)
            self._mesh_states[cache_key] = state
            while len(self._mesh_states) > _MESH_CACHE_CAP:
                _ek, evicted = self._mesh_states.popitem(last=False)
                self._free_mesh_state(evicted)
            return state

    def invalidate_mesh(self, clip: str) -> None:
        """Drop every cached mesh state for ``clip`` (e.g. after an edit)."""
        with self._mesh_lock:
            stale = [k for k in self._mesh_states if k[0] == clip]
            for k in stale:
                self._free_mesh_state(self._mesh_states.pop(k))

    def reset_dataset_caches(self) -> None:
        """Drop SMPL-derived caches after a data-source change.

        E.g. a new ``smpl_dir`` set from the UI, so they rebuild against the
        new config.
        """
        with self._mesh_lock:
            for k in list(self._mesh_states):
                self._free_mesh_state(self._mesh_states.pop(k))
        with self._foot_lock:
            self._foot_masks = None

    def seg_model(self):
        """Return ``(model, weights, device)`` for person segmentation.

        Lazily loads torchvision DeepLabV3-ResNet101 (COCO/VOC, "person" class)
        once and caches it. Must be reachable under ``heavy_lock`` (GPU).
        """
        if self._seg is not None:
            return self._seg
        with self._seg_lock:
            if self._seg is not None:
                return self._seg
            import torch
            import torchvision.models.segmentation as tvseg
            from torchvision.models.segmentation import (
                DeepLabV3_ResNet101_Weights,
            )

            weights = DeepLabV3_ResNet101_Weights.DEFAULT
            model = tvseg.deeplabv3_resnet101(weights=weights).eval()
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(device)
            self._seg = (model, weights, device)
            return self._seg

    def foot_masks(self) -> dict[str, list]:
        """Return SMPL foot-vertex masks ``{"left": [...], "right": [...]}``.

        Builds an SMPL model once to read the LBS-derived sole vertices, then
        caches the result. Must be reachable under ``heavy_lock``.
        """
        if self._foot_masks is not None:
            return self._foot_masks
        with self._foot_lock:
            if self._foot_masks is not None:
                return self._foot_masks
            import numpy as np
            import torch

            from motion_studio.plugins_builtin.utils.floor_utils import (
                foot_vertex_masks,
            )
            from motion_studio.smpl import refit

            device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu"
            )
            smpl = refit.get_smpl(self.config.smpl_dir, device, batch_size=1)
            left, right = foot_vertex_masks(smpl)
            self._foot_masks = {
                "left": [int(i) for i in np.asarray(left).ravel().tolist()],
                "right": [int(i) for i in np.asarray(right).ravel().tolist()],
            }
            return self._foot_masks
