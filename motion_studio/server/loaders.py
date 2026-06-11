"""Resolve a clip/bundle name to a :class:`Motion` and an editor scene.

These helpers centralize how the server finds the motion behind a request:
either a saved ``.motion`` bundle in the workspace, or a raw ``.pkl`` under the
optional ``pkl_dir``. They are used by ``/load``, ``/bundle/load``,
``/mesh_*``, ``/correct_motion``, etc.
"""

from __future__ import annotations

import os

from motion_studio.bundle import Bundle, load_bundle
from motion_studio.core.types import Motion
from motion_studio.smpl import convert
from motion_studio.smpl import io as smpl_io

from . import video_cache
from .state import ServerState

# Source video extensions matched next to a raw clip's motion .pkl.
_VIDEO_EXTS = (".mp4", ".mov", ".webm", ".mkv")


def load_raw_motion(st: ServerState, clip: str) -> Motion | None:
    """Load a raw ``pkl_dir/<clip>.pkl`` as a Motion, or None."""
    pkl = st.raw_pkl_path(clip)
    if not pkl or not os.path.isfile(pkl):
        return None
    return smpl_io.load_motion_pkl(pkl)


def load_bundle_for(st: ServerState, name: str) -> Bundle | None:
    """Load the ``.motion`` bundle named ``name``, or None if it is absent."""
    path = st.bundle_path(name)
    if not os.path.isfile(path):
        return None
    return load_bundle(path)


def resolve_motion(
    st: ServerState, clip: str, prefer_edited: bool = False
) -> tuple[Motion | None, str]:
    """Find the motion behind ``clip``: bundle first, then raw pkl.

    Args:
      st: The server state.
      clip: Clip / bundle name.
      prefer_edited: If a bundle has an edited motion, return it instead of the
        original.

    Returns:
      ``(motion, where)`` where ``where`` is ``"bundle"``, ``"raw"`` or ``""``
      (not found, motion is None).
    """
    bundle = load_bundle_for(st, clip)
    if bundle is not None:
        if prefer_edited and bundle.edited is not None:
            return bundle.edited, "bundle"
        return bundle.original, "bundle"
    raw = load_raw_motion(st, clip)
    if raw is not None:
        return raw, "raw"
    return None, ""


def scene_from_motion(
    st: ServerState, motion: Motion, *, source: str = "original"
) -> dict:
    """Build a scene dict for ``motion`` (joints via SMPL FK)."""
    return convert.build_scene(motion, st.config.smpl_dir, source=source)


def raw_video_path(st: ServerState, clip: str) -> str | None:
    """Return the raw background video for ``clip``, if any.

    The video is the pre-cut per-clip video named by the exact clip name
    (``videos_dir/<clip>.<ext>``); None when no ``videos_dir`` is configured or
    no matching file exists.
    """
    if not st.config.videos_dir:
        return None
    for ext in _VIDEO_EXTS:
        candidate = os.path.join(st.config.videos_dir, clip + ext)
        if os.path.isfile(candidate):
            return candidate
    return None


def bundle_video_file(st: ServerState, name: str, bundle: Bundle) -> str | None:
    """Materialize a bundle's video bytes to the cache; return its path or None.

    Cheap file I/O (no GPU/ffmpeg), safe to call outside ``heavy_lock``.
    """
    if bundle.video is None:
        return None
    return video_cache.bundle_video_path(st.config, name, bundle.video)


def attach_floor(
    st: ServerState, scene: dict, name: str, motion: Motion
) -> dict:
    """Estimate and attach a single ground plane to ``scene``.

    Sets ``scene['floor']`` to ``[a, b, c]`` (plus ``floors``/``floor_meta``)
    so the Sol tab shows a plane on load. The plane comes from the configured
    floor plugin (see ``config.floor_spec``). Run under ``heavy_lock``.

    Args:
      st: The server state.
      scene: A scene dict to mutate.
      name: Clip / bundle name (floor cache key).
      motion: The motion to estimate the floor for.

    Returns:
      The same ``scene`` dict, mutated in place.
    """
    entry = video_cache.estimate_floor(st, name, motion)
    if entry is None:
        return scene
    plane = entry["plane"]
    scene["floor"] = plane
    scene["floors"] = {"raw": plane, "corrected": plane}
    scene["floor_meta"] = {
        "tilt_deg": entry.get("tilt_deg"),
        "n_contacts": entry.get("n_contacts"),
        "source": "ransac",
    }
    return scene


def attach_frames(
    st: ServerState,
    scene: dict,
    name: str,
    motion: Motion,
    video_path: str | None,
    offset_s: float = 0.0,
) -> dict:
    """Extract (once) and attach background video frames to ``scene``.

    Populates ``frames`` (relative URLs served under ``/cache/<name>/``),
    ``frame_w/frame_h``, ``video_duration``, ``clip_duration`` and ``bg_offset``
    on the scene; also sets ``_clip_dir`` (the frontend's frame base URL) and
    ``has_video``. A no-op (frames stay empty) when there is no video. Must run
    under ``heavy_lock``.

    Args:
      st: The server state.
      scene: A scene dict to mutate.
      name: Clip / bundle name (cache key + URL base).
      motion: The clip motion (frame count, fps).
      video_path: Path to a readable source video, or None.
      offset_s: Start offset into the video, in seconds.

    Returns:
      The same ``scene`` dict, mutated in place.
    """
    scene["_clip_dir"] = f"/cache/{name}"
    if not video_path or not os.path.isfile(video_path):
        return scene
    meta = video_cache.ensure_frames(
        st.config, name, video_path, motion, offset_s=offset_s
    )
    if meta is None:
        return scene
    scene.update(meta)
    scene["has_video"] = True
    return scene


def attach_bundle_media(st: ServerState, scene: dict, bundle: Bundle) -> dict:
    """Augment a scene with a bundle's edited state, params, comments, metrics.

    Args:
      st: The server state (for SMPL FK of any edited motion).
      scene: A scene dict from :func:`scene_from_motion`.
      bundle: The loaded bundle to read metadata from.

    Returns:
      The same ``scene`` dict, mutated in place.
    """
    scene["video_params"] = dict(bundle.video_params)
    scene["comments"] = list(bundle.comments)
    scene["metrics"] = dict(bundle.metrics)
    scene["has_music"] = bundle.music is not None
    scene["has_video"] = bundle.video is not None
    scene["source_clip"] = bundle.manifest.get("source_clip", "")
    if bundle.edited is not None:
        joints, _fps, _v, _f = convert.fk_joints(
            bundle.edited, st.config.smpl_dir, want_mesh=False
        )
        n, t, j, _ = joints.shape
        import numpy as np

        scene["edited"] = True
        scene["joints_edited"] = np.round(joints, 5).reshape(-1).tolist()
    else:
        scene["edited"] = False
    return scene
