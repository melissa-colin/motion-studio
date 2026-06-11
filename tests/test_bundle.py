"""Round-trip tests for the ``.motion`` bundle format.

The package is expected to be installed (``pip install -e .[dev]``), so these
tests import ``motion_studio`` directly and run under pytest only.
"""

from __future__ import annotations

import io
import os

import numpy as np

from motion_studio.bundle import (
    MOTION_EXT,
    Bundle,
    load_bundle,
    motion_from_npz,
    motion_to_npz_dict,
    save_bundle,
)
from motion_studio.core.types import Motion


def _make_motion(name: str = "clip", seed: int = 0) -> Motion:
    """Build a synthetic 2-person, 10-frame motion."""
    rng = np.random.default_rng(seed)
    return Motion(
        poses=rng.standard_normal((2, 10, 24, 3)).astype(np.float64),
        trans=rng.standard_normal((2, 10, 3)).astype(np.float64),
        betas=rng.standard_normal((2, 10)).astype(np.float64),
        gender="female",
        fps=24.0,
        name=name,
    )


def _assert_motion_equal(a: Motion, b: Motion) -> None:
    assert np.allclose(a.poses, b.poses)
    assert np.allclose(a.trans, b.trans)
    assert (a.betas is None) == (b.betas is None)
    if a.betas is not None:
        assert np.allclose(a.betas, b.betas)
    assert a.gender == b.gender
    assert a.fps == b.fps
    assert a.name == b.name


def test_extension_constant() -> None:
    assert MOTION_EXT == ".motion"


def test_motion_npz_helpers_round_trip() -> None:
    m = _make_motion()
    npz_dict = motion_to_npz_dict(m)
    # Simulate a save/load cycle through an in-memory npz.
    buffer = io.BytesIO()
    np.savez(buffer, **npz_dict)
    buffer.seek(0)
    with np.load(buffer, allow_pickle=False) as npz:
        m2 = motion_from_npz(npz)
    _assert_motion_equal(m, m2)


def test_full_round_trip(tmp_path) -> None:
    original = _make_motion("orig", seed=1)
    edited = _make_motion("edit", seed=2)
    video_bytes = b"FAKEVIDEO"
    music_bytes = b"FAKEMUSIC-DATA"
    video_params = {
        "posX": 1.5,
        "posY": -2.0,
        "posZ": 0.0,
        "scale": 1.25,
        "opacity": 0.8,
        "offset_s": 0.33,
        "bg_removed": True,
    }
    comments = ["first note", {"frame": 5, "text": "fix foot"}]
    metrics = {
        "ref": {"penetration": 0.12, "skate": 0.03},
        "cur": {"penetration": 0.05, "skate": 0.02},
    }

    path = os.path.join(tmp_path, "x.motion")
    save_bundle(
        path,
        original=original,
        edited=edited,
        video=video_bytes,
        music=music_bytes,
        music_ext="mp3",
        video_params=video_params,
        comments=comments,
        metrics=metrics,
        source_clip="gBR_sBM_c01",
        extra={"author": "melissa"},
    )

    b = load_bundle(path)
    assert isinstance(b, Bundle)
    _assert_motion_equal(original, b.original)
    _assert_motion_equal(edited, b.edited)
    assert b.video == video_bytes
    assert b.music == music_bytes
    assert b.music_ext == "mp3"
    assert b.video_params == video_params
    assert b.comments == comments
    assert b.metrics == metrics
    assert b.manifest["source_clip"] == "gBR_sBM_c01"
    assert b.manifest["extra"] == {"author": "melissa"}
    assert b.manifest["has_video"] is True
    assert b.manifest["has_music"] is True
    assert b.manifest["bg_removed"] is True
    assert b.manifest["n_persons"] == 2
    assert b.manifest["n_frames"] == 10


def test_no_edited_loads_none(tmp_path) -> None:
    original = _make_motion("orig", seed=3)
    path = os.path.join(tmp_path, "noedit.motion")
    save_bundle(path, original=original)

    b = load_bundle(path)
    _assert_motion_equal(original, b.original)
    assert b.edited is None
    assert b.video is None
    assert b.music is None
    assert b.manifest["has_video"] is False
    assert b.manifest["has_music"] is False


def test_video_and_music_from_path(tmp_path) -> None:
    original = _make_motion("orig", seed=4)
    vid_path = os.path.join(tmp_path, "v.mp4")
    mus_path = os.path.join(tmp_path, "m.wav")
    with open(vid_path, "wb") as f:
        f.write(b"VIDFROMPATH")
    with open(mus_path, "wb") as f:
        f.write(b"MUSFROMPATH")

    path = os.path.join(tmp_path, "frompath.motion")
    save_bundle(
        path,
        original=original,
        video=vid_path,
        music=mus_path,
        music_ext="wav",
    )
    b = load_bundle(path)
    assert b.video == b"VIDFROMPATH"
    assert b.music == b"MUSFROMPATH"
    assert b.music_ext == "wav"
