"""Per-clip background-frame cache and floor estimation for the editor.

The frontend draws the source video behind the dancers as a billboard of PNG
frames sampled at the motion's fps. This module materializes those frames once
under ``config.workspace/cache/<name>/frames/`` and reports the metadata the
frontend reads off ``/load`` (``frames``, ``frame_w/frame_h``,
``video_duration``, ``clip_duration``, ``bg_offset``). It also estimates a
single ground plane for the clip via the configured floor plugin and caches it
under ``cache/<name>/floor.json`` so the Sol tab shows a plane on load.

A bundle stores its video as raw bytes; :func:`bundle_video_path` writes those
bytes to ``cache/<name>/video.mp4`` once so ffmpeg can read them. All ffmpeg /
SMPL work here must run under the server's ``heavy_lock``.
"""

from __future__ import annotations

import json
import os

from motion_studio.core.types import Motion
from motion_studio.smpl import convert

# Width the legacy tool extracted background frames at (height auto, keeps
# aspect). Keeps the billboard textures small and the segmentation fast.
_FRAME_WIDTH = 640
_FRAMES_SUBDIR = "frames"
_NOBG_SUBDIR = "nobg"
_VIDEO_NAME = "video.mp4"
_FLOOR_NAME = "floor.json"


def cache_dir(config, name: str) -> str:
    """Return (and create) the cache directory for clip ``name``."""
    path = os.path.join(config.workspace, "cache", name)
    os.makedirs(path, exist_ok=True)
    return path


def frames_dir(config, name: str) -> str:
    """Return the per-clip extracted-frames directory."""
    return os.path.join(cache_dir(config, name), _FRAMES_SUBDIR)


def nobg_dir(config, name: str) -> str:
    """Return the per-clip background-removed (DeepLab) cache directory."""
    return os.path.join(cache_dir(config, name), _NOBG_SUBDIR)


def bundle_video_path(config, name: str, video: bytes) -> str:
    """Write a bundle's raw video bytes to the cache once; return the path.

    Args:
      config: The server configuration (for the workspace cache root).
      name: Clip / bundle name.
      video: Raw ``video.mp4`` bytes from the bundle.

    Returns:
      The path of the materialized ``cache/<name>/video.mp4``.
    """
    path = os.path.join(cache_dir(config, name), _VIDEO_NAME)
    if not os.path.isfile(path) or os.path.getsize(path) != len(video):
        tmp = path + ".tmp"
        with open(tmp, "wb") as f:
            f.write(video)
        os.replace(tmp, path)
    return path


def _list_frame_urls(name: str, fdir: str) -> list[str]:
    """Return sorted ``frames/NNNN.png`` relative URLs present in ``fdir``."""
    if not os.path.isdir(fdir):
        return []
    pngs = sorted(f for f in os.listdir(fdir) if f.endswith(".png"))
    return [f"{_FRAMES_SUBDIR}/{f}" for f in pngs]


def _frame_dims(fdir: str, frames: list[str]) -> tuple[int, int]:
    """Return ``(w, h)`` of the first frame, or a 640x360 fallback."""
    if not frames:
        return _FRAME_WIDTH, 360
    try:
        from PIL import Image

        with Image.open(os.path.join(os.path.dirname(fdir), frames[0])) as im:
            return int(im.size[0]), int(im.size[1])
    except Exception:  # noqa: BLE001
        return _FRAME_WIDTH, 360


def ensure_frames(
    config,
    name: str,
    video_path: str,
    motion: Motion,
    offset_s: float = 0.0,
    force: bool = False,
) -> dict | None:
    """Extract the clip's background frames once; return frame metadata.

    Frames are sampled at the motion's fps from ``offset_s`` into the video, to
    line the billboard up with the choreography. Existing frames are reused
    unless ``force`` is set (used by ``/set_bg_offset`` to re-extract).

    Args:
      config: The server configuration.
      name: Clip / bundle name.
      video_path: Path to a readable source video.
      motion: The clip motion (for frame count and fps).
      offset_s: Start offset into the video, in seconds.
      force: Re-extract even if a cached set of frames exists.

    Returns:
      A dict with ``frames`` (relative URLs), ``frame_w``, ``frame_h``,
      ``video_duration``, ``clip_duration``, ``bg_offset``, or None if no frame
      could be extracted. Must be called under ``heavy_lock``.
    """
    fdir = frames_dir(config, name)
    n_frames = int(motion.n_frames)
    fps = float(motion.fps or convert.DEFAULT_FPS)
    existing = _list_frame_urls(name, fdir)
    if existing and not force:
        frames = existing
    else:
        res = convert.extract_frames(
            video_path, float(offset_s), n_frames, fps, fdir, width=_FRAME_WIDTH
        )
        frames = _list_frame_urls(name, fdir) if res else []
    if not frames:
        return None
    w, h = _frame_dims(fdir, frames)
    vid_dur = convert.video_duration(video_path)
    return {
        "frames": frames,
        "frame_w": w,
        "frame_h": h,
        "video_duration": round(vid_dur, 3) if vid_dur is not None else None,
        "clip_duration": round(n_frames / fps, 3),
        "bg_offset": round(float(offset_s), 3),
    }


def _floor_cache_path(config, name: str) -> str:
    """Return the per-clip cached-floor JSON path."""
    return os.path.join(cache_dir(config, name), _FLOOR_NAME)


def load_cached_floor(config, name: str) -> dict | None:
    """Return a previously cached floor for ``name``, or None."""
    path = _floor_cache_path(config, name)
    if not os.path.isfile(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
        return data if isinstance(data, dict) and data.get("plane") else None
    except Exception:  # noqa: BLE001
        return None


def _save_cached_floor(config, name: str, entry: dict) -> None:
    """Atomically write the per-clip floor cache (best-effort)."""
    path = _floor_cache_path(config, name)
    tmp = path + ".tmp"
    try:
        with open(tmp, "w") as f:
            json.dump(entry, f, indent=2)
        os.replace(tmp, path)
    except Exception:  # noqa: BLE001
        pass


def estimate_floor(st, name: str, motion: Motion) -> dict | None:
    """Estimate one ground plane for ``motion`` via the configured plugin.

    Delegates to the floor plugin named by ``config.floor_spec`` (the built-in
    default fits a generic RANSAC plane to the lowest foot points), then caches
    the resulting plane per clip under ``cache/<name>/floor.json``.

    Args:
      st: The server state (SMPL dir, floor plugin spec, heavy lock).
      name: Clip / bundle name (cache key).
      motion: The motion to estimate the floor for.

    Returns:
      ``{"plane": [a, b, c], "tilt_deg": float, "n_contacts": int}`` or None on
      failure. Must be called under ``heavy_lock``.
    """
    cached = load_cached_floor(st.config, name)
    if cached is not None:
        return cached
    import math

    from motion_studio.core.plugins import load_floor

    try:
        floor = load_floor(
            st.config.floor_spec, smpl_dir=st.config.smpl_dir
        ).estimate(motion)
        plane = floor.plane
    except Exception:  # noqa: BLE001
        return None
    a, b, c = float(plane[0]), float(plane[1]), float(plane[2])
    entry = {
        "plane": [a, b, c],
        "tilt_deg": round(math.degrees(math.atan(math.hypot(a, b))), 4),
        "n_contacts": 0,
    }
    _save_cached_floor(st.config, name, entry)
    return entry
