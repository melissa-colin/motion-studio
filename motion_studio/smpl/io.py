"""Read/write AIOZ-GDANCE SMPL pkls as editor :class:`Motion` objects.

The on-disk AIOZ-GDANCE format is y-up and stores at least:

    smpl_poses: (N, T, 72) or (N, T, 24, 3) axis-angle
    root_trans: (N, T, 3)

The editor works in a z-up world frame. :func:`load_motion_pkl` loads a pkl and
rotates it into z-up; :func:`save_motion_pkl` rotates a z-up :class:`Motion`
back to y-up and writes the pkl, preserving every other key of an existing
template so the file round-trips in the original format.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Union

import numpy as np

from motion_studio.core.types import Motion
from motion_studio.plugins_builtin import _convert
from motion_studio.plugins_builtin.utils.motion_utils import (
    load_raw_gdance_pkl,
    yup2zup,
)

PathLike = Union[str, Path]


def load_motion_pkl(path: PathLike) -> Motion:
    """Load an AIOZ-GDANCE pkl into a z-up :class:`Motion`.

    Args:
        path: Path to the AIOZ-GDANCE .pkl (y-up).

    Returns:
        A :class:`Motion` in the z-up editor world frame, with ``poses`` of
        shape (N, T, 24, 3), ``trans`` of shape (N, T, 3), and ``name`` set to
        the file stem.
    """
    path = Path(path)
    poses_raw, trans_raw, _ = load_raw_gdance_pkl(path)
    trans_z, poses_z, _ = yup2zup(trans_raw, poses_raw)
    n_persons, n_frames = poses_z.shape[:2]
    poses = (
        poses_z.reshape(n_persons, n_frames, 24, 3).numpy().astype(np.float32)
    )
    trans = trans_z.numpy().astype(np.float32)
    return Motion(poses=poses, trans=trans, name=path.stem)


def save_motion_pkl(motion: Motion, path: PathLike) -> None:
    """Write a z-up :class:`Motion` back out as an AIOZ-GDANCE (y-up) pkl.

    If ``path`` already exists, its pkl is used as a template so all non-motion
    keys are preserved; ``smpl_poses`` and ``root_trans`` are overwritten (and
    reshaped to the templates layout). Otherwise a minimal dict with just
    those two keys is written.

    Args:
        motion: The motion to save, in the z-up editor world frame.
        path: Destination .pkl path.

    Returns:
        None.
    """
    path = Path(path)
    poses_yup, trans_yup = _convert.zup2yup(motion.poses, motion.trans)
    if path.exists():
        with open(path, "rb") as fh:
            data = pickle.load(fh)
        poses_shape = np.asarray(data["smpl_poses"]).shape
        trans_shape = np.asarray(data["root_trans"]).shape
        data["smpl_poses"] = np.asarray(poses_yup, dtype=np.float32).reshape(
            poses_shape
        )
        data["root_trans"] = np.asarray(trans_yup, dtype=np.float32).reshape(
            trans_shape
        )
    else:
        n_persons, n_frames = poses_yup.shape[:2]
        data = {
            "smpl_poses": np.asarray(poses_yup, dtype=np.float32).reshape(
                n_persons, n_frames, 72
            ),
            "root_trans": np.asarray(trans_yup, dtype=np.float32),
        }
    with open(path, "wb") as fh:
        pickle.dump(data, fh)
