"""Discover SMPL motions in a folder and import them into the workspace.

Clips are organized as three independent, flat directories chosen by the user:

    pkl_dir/      <clip>.pkl          (required: the SMPL motions)
    videos_dir/   <clip>.mp4|mov      (optional: per-clip background videos)
    audio_dir/    <clip>.wav|mp3      (optional: per-clip music)

Each motion clip is matched to its music and video by file stem (the exact clip
name), then converted into a self-contained ``.motion`` bundle in the workspace.

Background videos are matched by the exact clip name (``<clip>.mp4``). They are
expected to be already cut to the clip's segment and aligned to the music (done
offline by ``scripts/precut_videos.py``); this module embeds them as-is and
never trims at import time.
"""

from __future__ import annotations

import dataclasses
import glob
import os

from . import bundle
from .smpl import io as smpl_io

_VIDEO_EXTS = (".mp4", ".mov", ".webm", ".mkv")
_MUSIC_EXTS = (".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac")


@dataclasses.dataclass
class DatasetEntry:
    """One clip discovered in a dataset folder.

    Attributes:
      name: Clip name (the motion file stem).
      motion_path: Path to the SMPL .pkl motion file.
      music_path: Path to the matched music file, or None.
      video_path: Path to the matched video file, or None.
    """

    name: str
    motion_path: str
    music_path: str | None = None
    video_path: str | None = None


def _match_by_stem(stem: str, folder: str, exts) -> str | None:
    """Return first file in ``folder`` named ``stem`` with one of ``exts``."""
    if not os.path.isdir(folder):
        return None
    for ext in exts:
        candidate = os.path.join(folder, stem + ext)
        if os.path.isfile(candidate):
            return candidate
    return None


def clip_ytid(name: str) -> str:
    """Return the 11-char youtube id a clip name starts with.

    AIOZ-GDANCE clips are named ``<ytid>_<take>_<start>_<len>`` where ``ytid``
    is the 11-character youtube id of the source video the clip was cut from
    (e.g. ``-4yoUMiBwXg_01_0_960`` -> ``-4yoUMiBwXg``).

    Args:
      name: The clip / motion file stem.

    Returns:
      The first 11 characters of ``name``.
    """
    return name[:11]


def entry_for_clip(
    pkl_dir: str,
    name: str,
    videos_dir: str | None = None,
    audio_dir: str | None = None,
) -> DatasetEntry | None:
    """Return the :class:`DatasetEntry` for a single clip, or None if absent.

    Args:
      pkl_dir: Folder of ``<clip>.pkl`` SMPL motions.
      name: The clip name (motion file stem) to resolve.
      videos_dir: Optional folder of per-clip videos matched by exact name.
      audio_dir: Optional folder of per-clip music matched by exact name.

    Returns:
      The entry, or None if ``pkl_dir/<name>.pkl`` does not exist.
    """
    motion_path = os.path.join(pkl_dir, name + ".pkl")
    if not os.path.isfile(motion_path):
        return None
    return DatasetEntry(
        name=name,
        motion_path=motion_path,
        music_path=(
            _match_by_stem(name, audio_dir, _MUSIC_EXTS) if audio_dir else None
        ),
        video_path=(
            _match_by_stem(name, videos_dir, _VIDEO_EXTS)
            if videos_dir
            else None
        ),
    )


def scan_dataset(
    pkl_dir: str,
    videos_dir: str | None = None,
    audio_dir: str | None = None,
) -> list[DatasetEntry]:
    """Scan ``pkl_dir`` and return one entry per motion clip.

    Args:
      pkl_dir: Folder of ``<clip>.pkl`` SMPL motions (one file per clip).
      videos_dir: Optional folder of pre-cut per-clip videos named by the
        exact clip name (``<clip>.mp4``); a clip's video is matched from here.
      audio_dir: Optional folder of per-clip music named by the exact clip name
        (``<clip>.wav|mp3|...``); a clip's music is matched from here.

    Returns:
      Entries sorted by clip name. Empty if no motions are found.

    Raises:
      FileNotFoundError: If ``pkl_dir`` is not a directory.
    """
    if not os.path.isdir(pkl_dir):
        raise FileNotFoundError(f"no such pkl directory: {pkl_dir!r}")

    entries: list[DatasetEntry] = []
    for path in sorted(glob.glob(os.path.join(pkl_dir, "*.pkl"))):
        stem = os.path.splitext(os.path.basename(path))[0]
        entries.append(
            DatasetEntry(
                name=stem,
                motion_path=path,
                music_path=(
                    _match_by_stem(stem, audio_dir, _MUSIC_EXTS)
                    if audio_dir
                    else None
                ),
                video_path=(
                    _match_by_stem(stem, videos_dir, _VIDEO_EXTS)
                    if videos_dir
                    else None
                ),
            )
        )
    return entries


def bundle_path_for(workspace: str, name: str) -> str:
    """Return the .motion path for clip ``name`` inside ``workspace``."""
    return os.path.join(workspace, "bundles", name + bundle.MOTION_EXT)


def import_entry(entry: DatasetEntry, workspace: str) -> str:
    """Convert one dataset entry into a ``.motion`` bundle in the workspace.

    The original motion is loaded once; the bundle stores it as both the
    original and (initially) un-edited session, together with the matched music
    when present.

    Video handling: ``entry.video_path`` is a per-clip video matched by the
    exact clip name (``<clip>.mp4``). It is expected to be already cut to the
    clip's segment and aligned to the music offline (by
    ``scripts/precut_videos.py``), so it is embedded as-is with no trimming and
    no offset (``video_params["bg_offset"]`` is ``0.0``).

    Args:
      entry: The clip to import (its matched video/music paths are already
        resolved on the entry).
      workspace: Workspace root; the bundle is written under ``bundles/``.

    Returns:
      The path of the written ``.motion`` bundle.
    """
    motion = smpl_io.load_motion_pkl(entry.motion_path)
    out_path = bundle_path_for(workspace, entry.name)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    music_ext = "wav"
    if entry.music_path:
        music_ext = os.path.splitext(entry.music_path)[1].lstrip(".") or "wav"

    video_arg = entry.video_path
    video_params = None
    if entry.video_path and os.path.isfile(entry.video_path):
        # Pre-cut per-clip video; embed as-is, already aligned to the motion.
        video_params = {"bg_offset": 0.0}

    bundle.save_bundle(
        out_path,
        original=motion,
        edited=None,
        video=video_arg,
        music=entry.music_path,
        music_ext=music_ext,
        video_params=video_params,
        source_clip=entry.name,
    )
    return out_path


def import_dataset(
    pkl_dir: str,
    workspace: str,
    videos_dir: str | None = None,
    audio_dir: str | None = None,
) -> list[str]:
    """Import every clip found in ``pkl_dir`` into the workspace.

    Args:
      pkl_dir: Folder of ``<clip>.pkl`` SMPL motions.
      workspace: Workspace root for the written bundles.
      videos_dir: Optional folder of per-clip videos matched by exact name.
      audio_dir: Optional folder of per-clip music matched by exact name.

    Returns:
      The list of written ``.motion`` bundle paths.
    """
    return [
        import_entry(e, workspace)
        for e in scan_dataset(
            pkl_dir, videos_dir=videos_dir, audio_dir=audio_dir
        )
    ]
