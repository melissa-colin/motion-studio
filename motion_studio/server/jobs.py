"""Background jobs: folder import, metrics warm-up, background-crop prewarm.

These let long, batch operations run off the request thread so the UI stays
responsive and can poll progress:

  * the **import** job converts a ``pkl_dir`` (matched against ``videos_dir`` /
    ``audio_dir``) into ``.motion`` bundles;
  * the **metrics** job computes each bundle's reference metrics once and caches
    them in the bundle manifest so the library list is sortable by metric;
  * the **prewarm** registry runs the (slow, GPU) background-crop segmentation
    for a whole clip ahead of playback so scrubbing never freezes waiting on a
    per-frame mask.

Progress is exposed as plain dicts (see the ``*_status`` helpers) that the API
serializes to JSON. There is one process per server, so module-level singletons
guarded by a lock are sufficient.
"""

from __future__ import annotations

import os
import threading

from motion_studio import bundle as bundle_mod
from motion_studio import library

# -- shared progress state ------------------------------------------------

_lock = threading.Lock()

_import = {
    "running": False,
    "total": 0,
    "done": 0,
    "failed": 0,
    "current": "",
    "imported_names": [],
}

_metrics = {
    "running": False,
    "total": 0,
    "done": 0,
    "failed": 0,
    "current": "",
}

# Per-(clip, source) background-crop prewarm progress.
_prewarm: dict[tuple[str, str], dict] = {}


def import_status() -> dict:
    """Return a snapshot of the import job's progress."""
    with _lock:
        return dict(_import)


def metrics_status() -> dict:
    """Return a snapshot of the metrics job's progress."""
    with _lock:
        return dict(_metrics)


def prewarm_status(clip: str, source: str) -> dict:
    """Return a snapshot of a clip's background-crop prewarm progress."""
    with _lock:
        st = _prewarm.get((clip, source))
        return dict(st) if st else {"running": False, "total": 0, "done": 0}


# -- folder import --------------------------------------------------------


def start_import(
    st,
    pkl_dir: str,
    videos_dir: str | None,
    audio_dir: str | None,
) -> bool:
    """Start (or refuse, if already running) a background folder import.

    Args:
      st: The server state.
      pkl_dir: Folder of ``<clip>.pkl`` motions to import.
      videos_dir: Optional folder of per-clip videos matched by name.
      audio_dir: Optional folder of per-clip music matched by name.

    Returns:
      True if a job was started, False if one is already running.
    """
    with _lock:
        if _import["running"]:
            return False
        _import.update(
            running=True,
            total=0,
            done=0,
            failed=0,
            current="",
            imported_names=[],
        )

    def _run():
        try:
            entries = library.scan_dataset(
                pkl_dir, videos_dir=videos_dir, audio_dir=audio_dir
            )
        except Exception:  # noqa: BLE001 - surfaced via failed count
            with _lock:
                _import.update(running=False, failed=1)
            return
        with _lock:
            _import["total"] = len(entries)
        for entry in entries:
            with _lock:
                _import["current"] = entry.name
            try:
                # Pure file I/O (load pkl, write bundle) -- no GPU, so we do not
                # take the heavy lock and never block interactive requests.
                library.import_entry(entry, st.config.workspace)
                with _lock:
                    _import["done"] += 1
                    _import["imported_names"].append(entry.name)
            except Exception:  # noqa: BLE001 - keep going, count the failure
                with _lock:
                    _import["failed"] += 1
        with _lock:
            _import.update(running=False, current="")
        # A fresh batch of bundles has no cached metrics yet -- warm them.
        start_metrics(st)

    threading.Thread(target=_run, name="ms-import", daemon=True).start()
    return True


# -- metrics warm-up ------------------------------------------------------


def _bundle_has_metrics(path: str) -> bool:
    """Return True if a bundle already has non-empty reference metrics."""
    try:
        meta = bundle_mod.load_bundle_meta(path)
    except Exception:  # noqa: BLE001
        return False
    ref = (meta.metrics or {}).get("ref")
    return bool(ref)


def _compute_ref_metrics(st, clip, motion) -> dict:
    """Score ``motion`` with the configured metrics plugin against its floor.

    The reference metrics are computed against the clip's actual floor (the
    saved manual plane if any, else the estimated one), so they match the floor
    the editor displays and the metrics plugin actually uses.
    """
    from motion_studio.core.plugins import load_metrics
    from motion_studio.core.types import Floor

    from . import loaders

    plane = loaders.active_floor_plane(st, clip, motion)
    floor = Floor(plane=plane if plane else (0.0, 0.0, 0.0))
    plugin = load_metrics(st.config.metrics_spec, smpl_dir=st.config.smpl_dir)
    raw = plugin.compute(motion, floor)
    import numpy as np

    out: dict[str, float] = {}
    for key, value in dict(raw).items():
        if value is None:
            continue
        try:
            fval = float(value)
        except (TypeError, ValueError):
            continue
        if np.isfinite(fval):
            out[str(key)] = fval
    return out


def compute_and_cache_ref(st, clip: str, motion) -> dict:
    """Compute a bundle's reference metrics once (foreground) and cache them.

    Used on clip open so the editor shows the starting ("départ") metrics
    immediately without the user asking. Foreground priority (``heavy``): the
    user is already waiting on the open. Caches into the bundle manifest so the
    library list becomes sortable by these values too.

    Args:
      st: The server state.
      clip: Bundle name.
      motion: The bundle's original motion to score.

    Returns:
      The ``{metric: value}`` scores, or ``{}`` if there is no bundle, no real
      metrics plugin, or on failure (e.g. a metrics plugin that errors).
    """
    from motion_studio.config import DEFAULT_METRICS

    # Only auto-compute for a real (non-default) metrics plugin -- matches the
    # boot warm-up gate (app.py) and the UI's metric-column visibility.
    if not st.config.metrics_spec or st.config.metrics_spec == DEFAULT_METRICS:
        return {}
    path = st.bundle_path(clip)
    if not os.path.isfile(path):
        return {}
    try:
        with st.heavy():
            scores = _compute_ref_metrics(st, clip, motion)
        bundle_mod.update_manifest_metrics(path, scores)
        return scores
    except Exception:  # noqa: BLE001 - metrics are best-effort on open
        return {}


def start_metrics(st, force: bool = False) -> bool:
    """Start a background pass computing each bundle's reference metrics.

    Args:
      st: The server state.
      force: Recompute every bundle even if metrics are already cached.

    Returns:
      True if a job was started, False if one is already running.
    """
    with _lock:
        if _metrics["running"]:
            return False
        _metrics.update(running=True, total=0, done=0, failed=0, current="")

    def _run():
        root = os.path.join(st.config.workspace, "bundles")
        try:
            names = (
                sorted(
                    f
                    for f in os.listdir(root)
                    if f.endswith(bundle_mod.MOTION_EXT)
                )
                if os.path.isdir(root)
                else []
            )
        except OSError:
            names = []
        with _lock:
            _metrics["total"] = len(names)
        for fn in names:
            path = os.path.join(root, fn)
            name = fn[: -len(bundle_mod.MOTION_EXT)]
            with _lock:
                _metrics["current"] = name
            if not force and _bundle_has_metrics(path):
                with _lock:
                    _metrics["done"] += 1
                continue
            try:
                b = bundle_mod.load_bundle(path)
                motion = b.original
                # Background priority: never starve the interactive editor of
                # the single GPU lock while warming the whole library.
                with st.heavy_idle():
                    scores = _compute_ref_metrics(st, name, motion)
                bundle_mod.update_manifest_metrics(path, scores)
                with _lock:
                    _metrics["done"] += 1
            except Exception:  # noqa: BLE001 - keep going, count the failure
                with _lock:
                    _metrics["failed"] += 1
        with _lock:
            _metrics.update(running=False, current="")

    threading.Thread(target=_run, name="ms-metrics", daemon=True).start()
    return True


# -- background-crop prewarm ----------------------------------------------


def start_prewarm(st, clip: str, source: str, frames: list[int]) -> bool:
    """Pre-segment a clip's background crop for ``frames`` into the cache.

    Runs the slow per-frame DeepLab segmentation ahead of playback so the
    per-frame ``/bg_nobg`` requests just hit the cache. Idempotent: a frame
    already cached is skipped. One worker per (clip, source) at a time.

    Args:
      st: The server state.
      clip: Clip / bundle name.
      source: Motion variant ("original" / "corrected" / "").
      frames: Frame indices to warm.

    Returns:
      True if a job was started, False if one is already running for the key.
    """
    key = (clip, source)
    with _lock:
        cur = _prewarm.get(key)
        if cur and cur.get("running"):
            return False
        _prewarm[key] = {
            "running": True,
            "total": len(frames),
            "done": 0,
        }

    def _run():
        # Imported lazily so a server without the segmentation stack still
        # starts; the worker simply no-ops if the helper is unavailable.
        try:
            from . import api_video
        except Exception:  # noqa: BLE001
            with _lock:
                _prewarm[key].update(running=False)
            return
        warm = getattr(api_video, "prewarm_frame", None)
        for t in frames:
            if warm is not None:
                try:
                    warm(st, clip, source, int(t))
                except Exception:  # noqa: BLE001 - best-effort warming
                    pass
            with _lock:
                _prewarm[key]["done"] += 1
        with _lock:
            _prewarm[key]["running"] = False

    threading.Thread(
        target=_run, name=f"ms-prewarm-{clip}", daemon=True
    ).start()
    return True
