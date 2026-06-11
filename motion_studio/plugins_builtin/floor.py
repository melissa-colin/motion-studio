"""Built-in reference floor (ground-plane) plugin (``MotionFloor``).

A deliberately simple, generic floor estimator: it forwards the motion through
SMPL, takes the *lowest foot-sole vertex of each dancer on every frame* as a
plain point cloud, and fits a single plane ``z = a*x + b*y + c`` to that cloud
with a textbook RANSAC plane fit shared by all dancers.

It is meant as a clear reference implementation and a sane default, not a
research-grade ground-plane estimator. Bring your own via ``--floor`` for
anything more sophisticated (see ``docs/PLUGINS.md``).
"""

from __future__ import annotations

import numpy as np
import torch
from smplx import SMPL

from motion_studio.core.types import Floor as FloorPlane
from motion_studio.core.types import Motion

from .utils.floor_utils import fit_floor_plane, foot_vertex_masks
from .utils.motion_utils import smpl_mesh_fk


class Floor:
    """Estimate one ground plane from the lowest foot points of a motion.

    Args:
        smpl_dir: Directory containing the SMPL model files (needed for the
            forward kinematics that locate the foot-sole vertices).
    """

    def __init__(self, *, smpl_dir: str) -> None:
        self._smpl_dir = smpl_dir
        self._device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

    def estimate(self, motion: Motion) -> FloorPlane:
        """Fit a generic ground plane to ``motion``'s lowest foot points.

        For each dancer and frame, the lowest vertex of the left foot and of
        the right foot is kept (a generic, height-based selection). The pooled
        cloud is fitted with :func:`fit_floor_plane` (RANSAC) to a single plane
        ``z = a*x + b*y + c`` shared by all dancers.

        Args:
            motion: The motion to estimate the floor for, in the z-up editor
                world frame.

        Returns:
            A :class:`~motion_studio.core.types.Floor` whose ``plane`` is the
            ``(a, b, c)`` of the fitted ground plane.
        """
        n_persons, n_frames = motion.poses.shape[:2]
        smpl = SMPL(self._smpl_dir, gender="NEUTRAL", batch_size=n_frames).to(
            self._device
        )
        left_mask, right_mask = foot_vertex_masks(smpl)

        points: list[np.ndarray] = []
        for p in range(n_persons):
            verts, _joints = smpl_mesh_fk(
                motion.poses[p], motion.trans[p], smpl, self._device
            )  # verts: (T, 6890, 3)
            for mask in (left_mask, right_mask):
                fv = verts[:, mask]  # (T, n_mask, 3)
                lowest_idx = fv[..., 2].argmin(axis=1)  # (T,) per frame
                points.append(fv[np.arange(fv.shape[0]), lowest_idx])

        cloud = (
            np.concatenate(points, axis=0)
            if points
            else np.zeros((0, 3), np.float32)
        )
        plane, _tilt_deg, _inlier_frac = fit_floor_plane(cloud)
        a, b, c = plane
        return FloorPlane(plane=(float(a), float(b), float(c)))
