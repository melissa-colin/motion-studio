"""The ``.motion`` save-file format for a Motion Studio editing session.

A ``.motion`` file is a single ZIP archive that bundles everything about one
editing session: the original SMPL motion, the edited motion (if any), the
source video and music, plus all the side metadata the editor needs to reopen
the session exactly where the user left off (camera/video placement, comments,
metrics, ...). Reopening a bundle restores the full session; a caller that only
wants the SMPL can read ``original``/``edited`` and ignore the rest.

The archive layout is::

    manifest.json        session metadata (see save_bundle for the schema)
    motion_original.npz   poses, trans, betas (+ scalar fields) of the original
    motion_edited.npz     same, for the edited motion (absent if no edits)
    video.mp4             source video bytes (optional)
    music.<ext>           music bytes, original extension (optional)
    thumbnail.png         preview image (optional)
"""

from __future__ import annotations

import dataclasses
import datetime
import io
import json
import os
import tempfile
import threading
import zipfile
from typing import Any

import numpy as np

from motion_studio.core.types import Motion

MOTION_EXT = ".motion"

# Per-bundle write lock. ``save_bundle`` and ``update_manifest_metrics`` both
# replace a bundle on disk; the background metrics warm-up can target the same
# file a user is saving. Serializing each bundle's writers (keyed by real path)
# behind one lock makes the read-modify-write of ``update_manifest_metrics``
# and the replace of ``save_bundle`` mutually exclusive, so a save is never
# clobbered by a concurrent metric write and no reader sees a half-written zip.
_path_locks: dict[str, threading.Lock] = {}
_path_locks_guard = threading.Lock()


def _lock_for(path: str) -> threading.Lock:
    """Return the process-wide write lock for the bundle at ``path``."""
    key = os.path.realpath(path)
    with _path_locks_guard:
        lock = _path_locks.get(key)
        if lock is None:
            lock = threading.Lock()
            _path_locks[key] = lock
        return lock


_FORMAT = "motion-studio"
_VERSION = 1
_MANIFEST_NAME = "manifest.json"
_ORIGINAL_NAME = "motion_original.npz"
_EDITED_NAME = "motion_edited.npz"
_VIDEO_NAME = "video.mp4"
_THUMBNAIL_NAME = "thumbnail.png"
_MUSIC_STEM = "music"


@dataclasses.dataclass
class Bundle:
    """A loaded ``.motion`` editing session.

    Attributes:
      original: The original (unedited) motion.
      edited: The edited motion, or None if the session had no edits.
      video: Raw source video bytes, or None.
      music: Raw music bytes, or None.
      music_ext: Extension of the music file, without the leading dot.
      video_params: Video placement params (posX, posY, scale, ...).
      comments: List of user comments attached to the session.
      metrics: Mapping {"ref": {...}, "cur": {...}} of metric values.
      manifest: The full manifest dict, as stored in the archive.
    """

    original: Motion
    edited: Motion | None
    video: bytes | None
    music: bytes | None
    music_ext: str
    video_params: dict[str, Any]
    comments: list[Any]
    metrics: dict[str, Any]
    manifest: dict[str, Any]


@dataclasses.dataclass
class BundleMeta:
    """A cheaply loaded ``.motion`` session: motions + metadata, lazy media.

    Reading a bundle's ``video.mp4`` / music bytes can be tens of megabytes;
    the hot playback path (``/mesh_frame``, ``/mesh_faces``, ``resolve_motion``)
    only needs the SMPL motions and the manifest. :func:`load_bundle_meta`
    decodes just the manifest and the small ``.npz`` motion members and leaves
    the heavy video/music bytes behind lazy accessors, so a playback request no
    longer re-reads the whole archive.

    Attributes:
      original: The original (unedited) motion.
      edited: The edited motion, or None if the session had no edits.
      music_ext: Extension of the music file, without the leading dot.
      video_params: Video placement params (posX, posY, scale, ...).
      comments: List of user comments attached to the session.
      metrics: Mapping {"ref": {...}, "cur": {...}} of metric values.
      manifest: The full manifest dict, as stored in the archive.
      has_video: Whether the archive carries a ``video.mp4`` member.
      has_music: Whether the archive carries a music member.
    """

    original: Motion
    edited: Motion | None
    music_ext: str
    video_params: dict[str, Any]
    comments: list[Any]
    metrics: dict[str, Any]
    manifest: dict[str, Any]
    has_video: bool
    has_music: bool
    _path: str

    def video_bytes(self) -> bytes | None:
        """Read and return the archive's ``video.mp4`` bytes, or None."""
        if not self.has_video:
            return None
        with zipfile.ZipFile(self._path, "r") as zf:
            if _VIDEO_NAME not in set(zf.namelist()):
                return None
            return zf.read(_VIDEO_NAME)

    def music_bytes(self) -> bytes | None:
        """Read and return the archive's music bytes, or None."""
        if not self.has_music:
            return None
        music_name = f"{_MUSIC_STEM}.{self.music_ext}"
        with zipfile.ZipFile(self._path, "r") as zf:
            if music_name not in set(zf.namelist()):
                return None
            return zf.read(music_name)


def motion_to_npz_dict(m: Motion) -> dict[str, np.ndarray]:
    """Serialize a Motion to a flat dict of arrays for ``np.savez``.

    Scalar fields (gender, fps, name) are stored as 0-d arrays so they survive
    the round-trip through an ``.npz`` archive. ``betas`` is stored only when
    present; its absence is recorded by a ``has_betas`` flag.

    Args:
      m: The motion to serialize.

    Returns:
      A mapping of archive member name to numpy array.
    """
    out: dict[str, np.ndarray] = {
        "poses": np.asarray(m.poses),
        "trans": np.asarray(m.trans),
        "gender": np.asarray(m.gender),
        "fps": np.asarray(float(m.fps)),
        "name": np.asarray(m.name),
        "has_betas": np.asarray(m.betas is not None),
    }
    if m.betas is not None:
        out["betas"] = np.asarray(m.betas)
    return out


def motion_from_npz(npz: np.lib.npyio.NpzFile) -> Motion:
    """Rebuild a Motion from an opened ``.npz`` produced by this module.

    Args:
      npz: A mapping (e.g. an open ``NpzFile``) with the keys written by
        ``motion_to_npz_dict``.

    Returns:
      The reconstructed motion.
    """
    betas = npz["betas"] if bool(npz["has_betas"]) else None
    return Motion(
        poses=np.asarray(npz["poses"]),
        trans=np.asarray(npz["trans"]),
        betas=None if betas is None else np.asarray(betas),
        gender=str(npz["gender"]),
        fps=float(npz["fps"]),
        name=str(npz["name"]),
    )


def _read_bytes(data: bytes | str) -> bytes:
    """Return ``data`` as bytes, reading from disk if it is a path.

    Args:
      data: Raw bytes, or a filesystem path to read.

    Returns:
      The raw bytes.
    """
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    with open(data, "rb") as f:
        return f.read()


def _motion_bytes(m: Motion) -> bytes:
    """Serialize a Motion to the raw bytes of an ``.npz`` archive."""
    buffer = io.BytesIO()
    np.savez(buffer, **motion_to_npz_dict(m))
    return buffer.getvalue()


def _load_motion_member(zf: zipfile.ZipFile, member: str) -> Motion:
    """Read and deserialize a Motion from a member of an open archive."""
    with io.BytesIO(zf.read(member)) as buffer:
        with np.load(buffer, allow_pickle=False) as npz:
            return motion_from_npz(npz)


def save_bundle(
    path: str,
    *,
    original: Motion,
    edited: Motion | None = None,
    video: bytes | str | None = None,
    music: bytes | str | None = None,
    music_ext: str = "wav",
    video_params: dict[str, Any] | None = None,
    comments: list[Any] | None = None,
    metrics: dict[str, Any] | None = None,
    source_clip: str = "",
    extra: dict[str, Any] | None = None,
    thumbnail: bytes | str | None = None,
    created: str | None = None,
    modified: str | None = None,
) -> None:
    """Write a full editing session to a ``.motion`` (ZIP) file.

    The manifest stored in the archive has the schema::

        {
          "format": "motion-studio",
          "version": 1,
          "name": str,
          "source_clip": str,
          "created": ISO-8601 str,
          "modified": ISO-8601 str,
          "comments": [...],
          "video_params": {"posX": ..., "scale": ..., ...},
          "bg_removed": bool,
          "metrics": {"ref": {...}, "cur": {...}},
          "has_video": bool,
          "has_music": bool,
          "music_ext": str,
          "gender": str,
          "fps": float,
          "n_persons": int,
          "n_frames": int,
          "extra": {...}
        }

    Args:
      path: Destination path for the ``.motion`` file.
      original: The original (unedited) motion; required.
      edited: The edited motion, or None to omit it from the archive.
      video: Source video as raw bytes or a filesystem path, or None.
      music: Music as raw bytes or a filesystem path, or None.
      music_ext: Extension to store the music under, without the dot.
      video_params: Video placement params (posX, posY, scale, ...).
      comments: User comments to attach to the session.
      metrics: Mapping {"ref": {...}, "cur": {...}} of metric values.
      source_clip: Identifier of the clip the session originated from.
      extra: Arbitrary extra JSON-serializable metadata.
      thumbnail: Preview image as raw bytes or a path, or None.
      created: Creation timestamp (ISO-8601); defaults to now (UTC).
      modified: Last-modified timestamp (ISO-8601); defaults to now (UTC).

    Returns:
      None.
    """
    video_params = dict(video_params or {})
    comments = list(comments or [])
    metrics = dict(metrics or {})
    extra = dict(extra or {})
    music_ext = music_ext.lstrip(".") or "wav"

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    created = created or now
    modified = modified or now

    video_bytes = None if video is None else _read_bytes(video)
    music_bytes = None if music is None else _read_bytes(music)
    thumb_bytes = None if thumbnail is None else _read_bytes(thumbnail)

    manifest: dict[str, Any] = {
        "format": _FORMAT,
        "version": _VERSION,
        "name": original.name,
        "source_clip": source_clip,
        "created": created,
        "modified": modified,
        "comments": comments,
        "video_params": video_params,
        "bg_removed": bool(video_params.get("bg_removed", False)),
        "metrics": metrics,
        "has_video": video_bytes is not None,
        "has_music": music_bytes is not None,
        "music_ext": music_ext,
        "gender": original.gender,
        "fps": float(original.fps),
        "n_persons": original.n_persons,
        "n_frames": original.n_frames,
        "extra": extra,
    }

    # Write to a unique temp file then atomically replace, so a concurrent
    # reader (e.g. the metrics warm-up) never sees a half-written archive and a
    # crash mid-write cannot truncate an existing bundle. The replace is done
    # under the per-bundle lock to serialize it with the metric writer.
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        dir=os.path.dirname(path) or ".",
        prefix=os.path.basename(path) + ".",
        suffix=".tmp",
    )
    os.close(fd)
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                _MANIFEST_NAME,
                json.dumps(manifest, indent=2, sort_keys=True),
            )
            zf.writestr(_ORIGINAL_NAME, _motion_bytes(original))
            if edited is not None:
                zf.writestr(_EDITED_NAME, _motion_bytes(edited))
            if video_bytes is not None:
                zf.writestr(_VIDEO_NAME, video_bytes)
            if music_bytes is not None:
                zf.writestr(f"{_MUSIC_STEM}.{music_ext}", music_bytes)
            if thumb_bytes is not None:
                zf.writestr(_THUMBNAIL_NAME, thumb_bytes)
        with _lock_for(path):
            os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def update_manifest_metrics(path: str, ref_metrics: dict[str, Any]) -> None:
    """Patch a bundle's stored metrics in place, without re-encoding its media.

    Sets ``manifest["metrics"]["ref"]`` to ``ref_metrics`` and rewrites the
    archive, stream-copying every other member (motion npz, video, music) with
    its original compression so the heavy payload is never re-encoded. The write
    goes to a sibling temp file and is renamed atomically.

    Args:
      path: Path to an existing ``.motion`` bundle.
      ref_metrics: The reference metric scores to store (``{name: value}``).

    Raises:
      OSError: If the bundle cannot be read or replaced.
      KeyError: If the archive has no manifest.
    """
    # The whole read-modify-write is held under the per-bundle lock so a
    # concurrent ``save_bundle`` (or another metric write) cannot land between
    # our read and our replace and get clobbered. Unique temp + atomic replace.
    with _lock_for(path):
        fd, tmp = tempfile.mkstemp(
            dir=os.path.dirname(path) or ".",
            prefix=os.path.basename(path) + ".",
            suffix=".tmp",
        )
        os.close(fd)
        try:
            with zipfile.ZipFile(path, "r") as zin:
                manifest = json.loads(zin.read(_MANIFEST_NAME).decode("utf-8"))
                metrics = dict(manifest.get("metrics") or {})
                metrics["ref"] = dict(ref_metrics)
                manifest["metrics"] = metrics
                manifest["modified"] = datetime.datetime.now(
                    datetime.timezone.utc
                ).isoformat()
                with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
                    zout.writestr(
                        _MANIFEST_NAME,
                        json.dumps(manifest, indent=2, sort_keys=True),
                    )
                    for info in zin.infolist():
                        if info.filename == _MANIFEST_NAME:
                            continue
                        # Preserve each member's original compression (video /
                        # music are already-compressed, stored uncompressed).
                        zout.writestr(info, zin.read(info.filename))
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass


def _read_manifest(zf: zipfile.ZipFile) -> dict[str, Any]:
    """Read and validate the manifest of an open ``.motion`` archive.

    Args:
      zf: An open ``.motion`` ZIP archive.

    Returns:
      The parsed manifest dict.

    Raises:
      ValueError: If the archive has no manifest member, or its ``format`` is
        not a Motion Studio bundle.
    """
    if _MANIFEST_NAME not in set(zf.namelist()):
        raise ValueError("not a Motion Studio bundle: missing manifest.json")
    manifest = json.loads(zf.read(_MANIFEST_NAME).decode("utf-8"))
    if manifest.get("format") != _FORMAT:
        raise ValueError(
            "not a Motion Studio bundle: {!r}".format(manifest.get("format"))
        )
    return manifest


def load_bundle_meta(path: str) -> BundleMeta:
    """Read a ``.motion`` file's motions + metadata, leaving media lazy.

    The cheap counterpart to :func:`load_bundle`: it decodes only the manifest
    and the small ``.npz`` motion members, never the (potentially large) video
    or music bytes. Use it on the hot path (``resolve_motion`` / playback) and
    pull media on demand via :meth:`BundleMeta.video_bytes` /
    :meth:`BundleMeta.music_bytes`.

    Args:
      path: Path to the ``.motion`` file to read.

    Returns:
      The reconstructed :class:`BundleMeta`.

    Raises:
      ValueError: If the archive is not a Motion Studio bundle (bad/absent
        manifest).
      KeyError: If the mandatory original motion member is missing.
    """
    with zipfile.ZipFile(path, "r") as zf:
        names = set(zf.namelist())
        manifest = _read_manifest(zf)
        original = _load_motion_member(zf, _ORIGINAL_NAME)
        edited = (
            _load_motion_member(zf, _EDITED_NAME)
            if _EDITED_NAME in names
            else None
        )
        music_ext = manifest.get("music_ext", "wav")
        music_name = f"{_MUSIC_STEM}.{music_ext}"
        has_video = _VIDEO_NAME in names
        has_music = music_name in names

    return BundleMeta(
        original=original,
        edited=edited,
        music_ext=music_ext,
        video_params=dict(manifest.get("video_params", {})),
        comments=list(manifest.get("comments", [])),
        metrics=dict(manifest.get("metrics", {})),
        manifest=manifest,
        has_video=has_video,
        has_music=has_music,
        _path=path,
    )


def load_bundle(path: str) -> Bundle:
    """Read a ``.motion`` file back into a full Bundle (media included).

    Args:
      path: Path to the ``.motion`` file to read.

    Returns:
      The reconstructed Bundle.

    Raises:
      ValueError: If the archive is not a Motion Studio bundle (bad/absent
        manifest).
      KeyError: If the mandatory original motion member is missing.
    """
    with zipfile.ZipFile(path, "r") as zf:
        names = set(zf.namelist())

        manifest = _read_manifest(zf)

        original = _load_motion_member(zf, _ORIGINAL_NAME)
        edited = (
            _load_motion_member(zf, _EDITED_NAME)
            if _EDITED_NAME in names
            else None
        )

        video = zf.read(_VIDEO_NAME) if _VIDEO_NAME in names else None

        music_ext = manifest.get("music_ext", "wav")
        music_name = f"{_MUSIC_STEM}.{music_ext}"
        music = zf.read(music_name) if music_name in names else None

    return Bundle(
        original=original,
        edited=edited,
        video=video,
        music=music,
        music_ext=music_ext,
        video_params=dict(manifest.get("video_params", {})),
        comments=list(manifest.get("comments", [])),
        metrics=dict(manifest.get("metrics", {})),
        manifest=manifest,
    )
