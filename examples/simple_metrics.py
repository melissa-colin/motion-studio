"""A pure-numpy ``MotionMetrics`` plugin with custom metric keys.

This metrics plugin computes a couple of trivial *geometric* quantities
straight from the motion arrays. It needs **no torch, no smplx, and no SMPL
model files** -- only :mod:`numpy`. It exists to:

  * show how to author a metrics plugin from scratch,
  * demonstrate that the editor's metrics panel renders *whatever* keys a
    plugin returns, including keys it has never seen before. The keys here
    (``root_height``, ``bbox_volume``, ``travel``) are not in the built-in
    set, so they appear with raw-key labels appended after the known metrics.

Point Motion Studio at it with::

    motion-studio --metrics ./examples/simple_metrics.py:SimpleMetrics

A metrics plugin is any class satisfying
``motion_studio.core.plugins.MotionMetrics``::

    def __init__(self, *, smpl_dir: str) -> None
    def compute(self, motion: Motion, floor: Floor) -> Dict[str, float]

The returned mapping is ``{metric_name: float}`` with arbitrary string keys;
see ``docs/PLUGINS.md`` for how keys map onto the panel.
"""

from __future__ import annotations

import numpy as np

from motion_studio.core.types import Floor, Motion


class SimpleMetrics:
    """Geometric, SMPL-free motion metrics.

    Args:
        smpl_dir: Directory of SMPL body model files. Unused here, but part of
            the metrics constructor contract (the built-in metrics plugin runs
            SMPL forward kinematics and needs it).
    """

    def __init__(self, *, smpl_dir: str) -> None:
        self._smpl_dir = smpl_dir

    def compute(self, motion: Motion, floor: Floor) -> dict[str, float]:
        """Compute three trivial geometric metrics from the motion arrays.

        Everything is derived from ``motion.trans`` (root translations,
        shape ``(N, T, 3)``) so no body model is required.

        Args:
            motion: The motion to score, in the z-up editor world frame.
            floor: The ground plane (unused; part of the compute signature).

        Returns:
            A mapping with three custom keys:

              * ``root_height``: mean root height above z=0, world units.
              * ``bbox_volume``: volume of the axis-aligned bounding box that
                encloses every root over the whole clip, world units cubed.
              * ``travel``: total horizontal path length summed over dancers,
                world units.
        """
        trans = np.asarray(motion.trans, dtype=np.float64)  # (N, T, 3)
        del floor  # Not needed for these purely geometric metrics.

        root_height = float(np.mean(trans[..., 2]))

        flat = trans.reshape(-1, 3)
        span = flat.max(axis=0) - flat.min(axis=0)  # (3,)
        bbox_volume = float(np.prod(span))

        steps = np.diff(trans[..., :2], axis=1)  # (N, T-1, 2)
        travel = float(np.sum(np.linalg.norm(steps, axis=-1)))

        return {
            "root_height": root_height,
            "bbox_volume": bbox_volume,
            "travel": travel,
        }
