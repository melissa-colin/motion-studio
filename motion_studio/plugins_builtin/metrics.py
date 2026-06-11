"""Built-in reference metrics plugin (``MotionMetrics``).

A small set of original, purely *geometric* quality numbers computed from the
SMPL forward-kinematics vertices and joints of the motion against the supplied
floor plane ``z = a*x + b*y + c``. These are simple reference metrics, not the
research-grade physics-plausibility suite; bring your own via ``--metrics`` for
anything more elaborate (see ``docs/PLUGINS.md``).

Returned keys (all floats):

* ``floor_penetration`` -- mean depth (mm) of vertices that sit below the
  floor, averaged over frames (0 when nothing penetrates).
* ``float`` -- mean gap (mm) of the lowest vertex above the floor on
  near-contact frames (frames whose lowest vertex is within a small band of
  the plane), i.e. how far the body hovers when it should be touching.
* ``height`` -- mean root height above the floor, in metres.
* ``jitter`` -- mean magnitude of per-joint acceleration, a smoothness proxy
  (lower is smoother), in metres per second squared.
"""

from __future__ import annotations

import numpy as np
import torch
from smplx import SMPL

from motion_studio.core.types import Floor, Motion

from .utils.floor_utils import signed_distance_to_plane
from .utils.motion_utils import smpl_mesh_fk

# A vertex within this vertical band of the plane counts as "near contact",
# used to decide which frames contribute to the ``float`` gap.
_CONTACT_BAND_M = 0.05


class Metrics:
    """Geometric reference metrics for the editor.

    Args:
        smpl_dir: Directory containing the SMPL model files (for the forward
            kinematics that produce the vertices/joints scored below).
    """

    def __init__(self, *, smpl_dir: str) -> None:
        self._smpl_dir = smpl_dir
        self._device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

    def compute(self, motion: Motion, floor: Floor) -> dict[str, float]:
        """Compute the geometric metrics for ``motion`` against ``floor``.

        Args:
            motion: The motion to score, in the z-up editor world frame.
            floor: The ground plane to score against.

        Returns:
            A mapping ``{metric_name: float}`` (see the module docstring for
            the keys).
        """
        n_persons, n_frames = motion.poses.shape[:2]
        smpl = SMPL(self._smpl_dir, gender="NEUTRAL", batch_size=n_frames).to(
            self._device
        )
        verts_per_person, joints_per_person = [], []
        for p in range(n_persons):
            verts, joints = smpl_mesh_fk(
                motion.poses[p], motion.trans[p], smpl, self._device
            )
            verts_per_person.append(verts)
            joints_per_person.append(joints)
        verts = np.stack(verts_per_person, axis=0)  # (N, T, 6890, 3)
        joints = np.stack(joints_per_person, axis=0)  # (N, T, 24, 3)

        dist = signed_distance_to_plane(verts, floor.plane)  # (N, T, 6890)
        lowest = dist.min(axis=2)  # (N, T) signed gap of the lowest vertex

        # Penetration: mean depth (mm) of vertices below the plane.
        below = np.clip(-dist, 0.0, None)
        penetration_mm = float(below.mean()) * 1000.0

        # Float: on frames where the body is near the floor, how far the
        # lowest vertex still hovers above it (mm).
        near = lowest < _CONTACT_BAND_M
        if near.any():
            gaps = np.clip(lowest[near], 0.0, None)
            float_mm = float(gaps.mean()) * 1000.0
        else:
            float_mm = 0.0

        # Height: mean root (pelvis = joint 0) height above the plane (m).
        root_dist = signed_distance_to_plane(joints[:, :, 0], floor.plane)
        height_m = float(root_dist.mean())

        # Jitter: mean joint acceleration magnitude (m/s^2), a smoothness
        # proxy. Acceleration is the second time-difference scaled by fps^2.
        if n_frames >= 3:
            accel = np.diff(joints, n=2, axis=1) * (motion.fps**2)
            jitter = float(np.linalg.norm(accel, axis=-1).mean())
        else:
            jitter = 0.0

        return {
            "floor_penetration": penetration_mm,
            "float": float_mm,
            "height": height_m,
            "jitter": jitter,
        }
