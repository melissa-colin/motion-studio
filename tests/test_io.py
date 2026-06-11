"""SMPL pkl I/O tests for :mod:`motion_studio.smpl.io`.

These exercise the AIOZ-GDANCE pkl reader/writer around a synthetic
:class:`Motion`. The writer (:func:`save_motion_pkl`) and the pure-numpy
``_convert.zup2yup`` sit on the torch-free core boot path, so the
template-key-preservation and serialization-shape tests run on the torch-free
lane. The *full* z-up <-> y-up round-trip through :func:`load_motion_pkl` and
the ``zup2yup(yup2zup(x)) == x`` identity go through the torch helpers in
``utils.motion_utils`` and are marked ``torch``.
"""

from __future__ import annotations

import pickle

import numpy as np
import pytest

from motion_studio.core.types import Motion
from motion_studio.plugins_builtin import _convert
from motion_studio.smpl import io as smpl_io


def _make_motion(name: str = "clip", seed: int = 0) -> Motion:
    """Build a synthetic 2-person, 6-frame z-up motion."""
    rng = np.random.default_rng(seed)
    return Motion(
        poses=rng.standard_normal((2, 6, 24, 3)).astype(np.float32),
        trans=rng.standard_normal((2, 6, 3)).astype(np.float32),
        name=name,
    )


def test_save_fresh_writes_minimal_yup_dict(tmp_path) -> None:
    """A save to a non-existent path writes just the two motion keys."""
    motion = _make_motion(seed=1)
    path = tmp_path / "fresh.pkl"
    smpl_io.save_motion_pkl(motion, str(path))

    with open(path, "rb") as fh:
        data = pickle.load(fh)
    assert set(data.keys()) == {"smpl_poses", "root_trans"}
    # smpl_poses is flattened to (N, T, 72), root_trans stays (N, T, 3).
    assert data["smpl_poses"].shape == (2, 6, 72)
    assert data["root_trans"].shape == (2, 6, 3)
    assert data["smpl_poses"].dtype == np.float32
    assert data["root_trans"].dtype == np.float32


def test_save_preserves_template_keys_and_layout(tmp_path) -> None:
    """Saving onto an existing pkl keeps every non-motion key and its shape."""
    path = tmp_path / "templated.pkl"
    template = {
        "smpl_poses": np.zeros((2, 6, 72), dtype=np.float32),
        "root_trans": np.zeros((2, 6, 3), dtype=np.float32),
        "smpl_scaling": np.ones((2, 1), dtype=np.float32),
        "frame_scores": np.arange(6, dtype=np.float32),
        "source_video": "abc123",
    }
    with open(path, "wb") as fh:
        pickle.dump(template, fh)

    motion = _make_motion(seed=2)
    smpl_io.save_motion_pkl(motion, str(path))

    with open(path, "rb") as fh:
        data = pickle.load(fh)
    # Every template key survives, including the non-motion ones.
    assert set(data.keys()) == set(template.keys())
    assert data["source_video"] == "abc123"
    assert np.array_equal(data["smpl_scaling"], template["smpl_scaling"])
    assert np.array_equal(data["frame_scores"], template["frame_scores"])
    # Motion arrays are overwritten but reshaped back to the template layout.
    assert data["smpl_poses"].shape == (2, 6, 72)
    assert data["root_trans"].shape == (2, 6, 3)
    assert not np.array_equal(data["smpl_poses"], template["smpl_poses"])


def test_save_reshapes_to_24x3_template(tmp_path) -> None:
    """A (N, T, 24, 3) template forces the saved poses back to that layout."""
    path = tmp_path / "joints4d.pkl"
    template = {
        "smpl_poses": np.zeros((2, 6, 24, 3), dtype=np.float32),
        "root_trans": np.zeros((2, 6, 3), dtype=np.float32),
    }
    with open(path, "wb") as fh:
        pickle.dump(template, fh)

    smpl_io.save_motion_pkl(_make_motion(seed=3), str(path))
    with open(path, "rb") as fh:
        data = pickle.load(fh)
    assert data["smpl_poses"].shape == (2, 6, 24, 3)


def test_zup2yup_root_translation_is_pure_numpy() -> None:
    """The numpy ``zup2yup`` maps (x, y, z) -> (x, z, -y) on translations."""
    poses = np.zeros((1, 4, 24, 3), dtype=np.float32)
    trans = np.array(
        [
            [
                [1.0, 2.0, 3.0],
                [4.0, 5.0, 6.0],
                [0.0, 0.0, 0.0],
                [-1.0, 2.0, -3.0],
            ]
        ],
        dtype=np.float32,
    )
    poses_y, trans_y = _convert.zup2yup(poses, trans)
    assert isinstance(poses_y, np.ndarray)
    assert isinstance(trans_y, np.ndarray)
    # (x, y, z) -> (x, z, -y).
    expected = trans.copy()
    expected[..., 1] = trans[..., 2]
    expected[..., 2] = -trans[..., 1]
    assert np.allclose(trans_y, expected, atol=1e-6)


@pytest.mark.torch
def test_zup2yup_inverts_yup2zup() -> None:
    """``zup2yup(yup2zup(x)) == x`` to ~1e-6 (the documented inverse)."""
    import torch

    from motion_studio.plugins_builtin.utils.motion_utils import yup2zup

    rng = np.random.default_rng(7)
    trans = rng.standard_normal((2, 5, 3)).astype(np.float32)
    poses = rng.standard_normal((2, 5, 24, 3)).astype(np.float32)

    trans_z, poses_z, _ = yup2zup(
        torch.from_numpy(trans), torch.from_numpy(poses)
    )
    poses_back, trans_back = _convert.zup2yup(poses_z.numpy(), trans_z.numpy())

    assert np.allclose(trans_back, trans, atol=1e-5)
    assert np.allclose(poses_back, poses, atol=1e-5)


@pytest.mark.torch
def test_save_load_round_trips_through_yup(tmp_path) -> None:
    """A z-up Motion saved and reloaded comes back equal to ~1e-5."""
    motion = _make_motion(name="rt", seed=11)
    path = tmp_path / "rt.pkl"
    smpl_io.save_motion_pkl(motion, str(path))

    loaded = smpl_io.load_motion_pkl(str(path))
    assert loaded.poses.shape == motion.poses.shape
    assert loaded.trans.shape == motion.trans.shape
    assert loaded.name == "rt"
    assert np.allclose(loaded.poses, motion.poses, atol=1e-5)
    assert np.allclose(loaded.trans, motion.trans, atol=1e-5)
