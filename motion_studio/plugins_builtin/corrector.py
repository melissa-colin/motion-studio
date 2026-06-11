"""Built-in reference auto-correction plugin (``MotionCorrector``).

A deliberately simple, original *floor-grounding* corrector: for every frame it
shifts each dancer's body straight up or down so the lowest body vertex rests
exactly on the floor plane ``z = a*x + b*y + c``. Nothing else is touched --
there is no foot-orientation fix, no skate removal and no inverse kinematics.

It is meant as a clear reference implementation and a sane default, not a
research-grade physics corrector. Bring your own via ``--corrector`` for
anything more sophisticated (see ``docs/PLUGINS.md``).
"""

from __future__ import annotations

from typing import Callable

import torch
from smplx import SMPL

from motion_studio.core.types import Floor, Motion

from .utils.floor_utils import signed_distance_to_plane
from .utils.motion_utils import smpl_mesh_fk


class Corrector:
    """Ground each frame so the lowest body vertex sits on the floor.

    Args:
        smpl_dir: Directory containing the SMPL model files (needed for the
            forward kinematics that locate the lowest vertex of each frame).
        floor: Optional floor plane to ground onto. When omitted a flat
            ``z = 0`` plane is used.
    """

    def __init__(self, *, smpl_dir: str, floor: Floor | None = None) -> None:
        self._smpl_dir = smpl_dir
        self._floor = floor

    def correct(
        self, motion: Motion, log: Callable[[str], None] = print
    ) -> Motion:
        """Return a copy of ``motion`` with every frame grounded on the floor.

        For each dancer and frame, the signed vertical distance of the lowest
        body vertex to the plane is measured and subtracted from the root's
        z translation, so the lowest vertex lands exactly on the plane.

        Args:
            motion: The motion to correct, in the z-up editor world frame.
            log: Callable receiving human-readable log lines.

        Returns:
            A new :class:`Motion` with the same array shapes; only ``trans``
            z-components change.
        """
        plane = (
            self._floor.plane if self._floor is not None else (0.0, 0.0, 0.0)
        )
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        out = motion.copy()
        n_persons, n_frames = motion.poses.shape[:2]
        smpl = SMPL(self._smpl_dir, gender="NEUTRAL", batch_size=n_frames).to(
            device
        )
        for p in range(n_persons):
            verts, _ = smpl_mesh_fk(
                motion.poses[p], motion.trans[p], smpl, device
            )  # (T, 6890, 3)
            # Signed vertical gap of every vertex to the plane, per frame.
            dist = signed_distance_to_plane(verts, plane)  # (T, 6890)
            shift = dist.min(axis=1)  # (T,) lowest vertex distance per frame
            out.trans[p, :, 2] -= shift
        log(
            f"Corrector: grounded {n_persons} dancer(s) over {n_frames} "
            "frame(s) onto the floor plane."
        )
        return out
