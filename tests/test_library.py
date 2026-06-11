"""Dataset-discovery tests for :mod:`motion_studio.library`.

:func:`scan_dataset` only walks the (flat) ``pkl_dir`` and stem-matches files
from the optional ``videos_dir`` / ``audio_dir``; it never decodes a pkl, so
these tests build empty placeholder files and stay torch-free.
"""

from __future__ import annotations

import os

import pytest

from motion_studio import library


def _touch(path: str) -> None:
    """Create an empty placeholder file (parent dirs assumed to exist)."""
    with open(path, "wb"):
        pass


def _make_dirs(root, motions, musics=(), videos=()):
    """Build flat pkl/audio/video dirs under ``root`` and return their paths.

    Args:
      root: A ``tmp_path`` directory.
      motions: Iterable of clip stems to create as ``pkl_dir/<stem>.pkl``.
      musics: Iterable of ``(stem, ext)`` music files in ``audio_dir``.
      videos: Iterable of ``(stem, ext)`` video files in ``videos_dir``.

    Returns:
      A ``(pkl_dir, videos_dir, audio_dir)`` tuple of created directory paths.
    """
    pkl_dir = os.path.join(str(root), "pkls")
    videos_dir = os.path.join(str(root), "videos")
    audio_dir = os.path.join(str(root), "audio")
    for d in (pkl_dir, videos_dir, audio_dir):
        os.makedirs(d, exist_ok=True)
    for stem in motions:
        _touch(os.path.join(pkl_dir, stem + ".pkl"))
    for stem, ext in musics:
        _touch(os.path.join(audio_dir, stem + ext))
    for stem, ext in videos:
        _touch(os.path.join(videos_dir, stem + ext))
    return pkl_dir, videos_dir, audio_dir


def test_scan_dataset_stem_matches_and_sorts(tmp_path) -> None:
    """Music/video are matched by stem; entries come back sorted by name."""
    pkl_dir, videos_dir, audio_dir = _make_dirs(
        tmp_path,
        motions=["clipB", "clipA", "clipC"],
        musics=[("clipA", ".wav"), ("clipB", ".mp3")],
        videos=[("clipA", ".mp4"), ("clipC", ".mov")],
    )
    entries = library.scan_dataset(
        pkl_dir, videos_dir=videos_dir, audio_dir=audio_dir
    )

    assert [e.name for e in entries] == ["clipA", "clipB", "clipC"]
    by_name = {e.name: e for e in entries}
    assert by_name["clipA"].music_path.endswith("clipA.wav")
    assert by_name["clipA"].video_path.endswith("clipA.mp4")
    assert by_name["clipB"].music_path.endswith("clipB.mp3")
    assert by_name["clipB"].video_path is None  # no matching video
    assert by_name["clipC"].music_path is None  # no matching music
    assert by_name["clipC"].video_path.endswith("clipC.mov")
    # Every motion path points at the .pkl we created.
    for e in entries:
        assert e.motion_path.endswith(e.name + ".pkl")
        assert os.path.isfile(e.motion_path)


def test_scan_dataset_matches_video_and_music_from_their_dirs(tmp_path) -> None:
    """Video comes from ``videos_dir``, music from ``audio_dir``."""
    pkl_dir, videos_dir, audio_dir = _make_dirs(
        tmp_path,
        motions=["clipA"],
        musics=[("clipA", ".flac")],
        videos=[("clipA", ".webm")],
    )

    entries = library.scan_dataset(
        pkl_dir, videos_dir=videos_dir, audio_dir=audio_dir
    )
    assert len(entries) == 1
    assert entries[0].video_path.endswith("clipA.webm")
    assert os.path.dirname(entries[0].video_path) == videos_dir
    assert entries[0].music_path.endswith("clipA.flac")
    assert os.path.dirname(entries[0].music_path) == audio_dir


def test_scan_dataset_without_media_dirs_leaves_them_none(tmp_path) -> None:
    """Omitting ``videos_dir`` / ``audio_dir`` yields entries with no media."""
    pkl_dir, _videos_dir, _audio_dir = _make_dirs(tmp_path, motions=["clipA"])
    entries = library.scan_dataset(pkl_dir)
    assert len(entries) == 1
    assert entries[0].video_path is None
    assert entries[0].music_path is None


def test_scan_dataset_empty_when_no_motions(tmp_path) -> None:
    """An existing-but-empty ``pkl_dir`` yields no entries (no error)."""
    pkl_dir, _videos_dir, _audio_dir = _make_dirs(tmp_path, motions=[])
    assert library.scan_dataset(pkl_dir) == []


def test_scan_dataset_missing_pkl_dir_raises(tmp_path) -> None:
    """A ``pkl_dir`` that is not a directory raises FileNotFoundError."""
    missing = os.path.join(str(tmp_path), "not_a_dir")
    with pytest.raises(FileNotFoundError):
        library.scan_dataset(missing)


def test_entry_for_clip_hit(tmp_path) -> None:
    """``entry_for_clip`` resolves a present clip with matched media."""
    pkl_dir, videos_dir, audio_dir = _make_dirs(
        tmp_path,
        motions=["clipA"],
        musics=[("clipA", ".wav")],
        videos=[("clipA", ".mp4")],
    )
    entry = library.entry_for_clip(
        pkl_dir, "clipA", videos_dir=videos_dir, audio_dir=audio_dir
    )
    assert entry is not None
    assert entry.name == "clipA"
    assert entry.motion_path.endswith("clipA.pkl")
    assert entry.music_path.endswith("clipA.wav")
    assert entry.video_path.endswith("clipA.mp4")


def test_entry_for_clip_miss_returns_none(tmp_path) -> None:
    """``entry_for_clip`` returns None when the ``<name>.pkl`` is absent."""
    pkl_dir, _videos_dir, _audio_dir = _make_dirs(tmp_path, motions=["clipA"])
    assert library.entry_for_clip(pkl_dir, "ghost") is None


def test_clip_ytid_takes_first_11_chars() -> None:
    """``clip_ytid`` returns the leading 11-char youtube id of a clip name."""
    assert library.clip_ytid("-4yoUMiBwXg_01_0_960") == "-4yoUMiBwXg"
    assert library.clip_ytid("abcdefghijk") == "abcdefghijk"
    # Shorter-than-11 names are returned verbatim.
    assert library.clip_ytid("short") == "short"


def test_bundle_path_for_uses_bundles_subdir() -> None:
    """``bundle_path_for`` places ``<name>.motion`` under ``bundles/``."""
    path = library.bundle_path_for("/ws", "clipA")
    assert path == os.path.join(
        "/ws", "bundles", "clipA" + library.bundle.MOTION_EXT
    )
