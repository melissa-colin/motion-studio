"""A no-op ``MotionCorrector`` plugin: the minimal correction contract.

This is the smallest possible auto-correction plugin. It returns the input
motion unchanged, so it is useful as:

  * a copy-paste starting point for your own corrector,
  * a way to confirm the plugin wiring end to end (load -> correct -> reload)
    without depending on torch, smplx, or any SMPL model files.

Point Motion Studio at it with::

    motion-studio --corrector ./examples/identity_corrector.py:IdentityCorrector

A corrector is any class satisfying the
``motion_studio.core.plugins.MotionCorrector`` protocol::

    def __init__(self, *, smpl_dir: str, floor: Optional[Floor] = None) -> None
    def correct(self, motion: Motion, log=print) -> Motion

The returned :class:`~motion_studio.core.types.Motion` must keep the same array
shapes as the input (``poses`` of shape ``(N, T, 24, 3)`` and ``trans`` of
shape ``(N, T, 3)``); see ``docs/PLUGINS.md`` for the full contract.
"""

from __future__ import annotations

from typing import Callable

from motion_studio.core.types import Floor, Motion


class IdentityCorrector:
    """Return the input motion unchanged.

    Args:
        smpl_dir: Directory of SMPL body model files. Unused here, but part of
            the corrector constructor contract (the built-in corrector needs
            it for forward kinematics).
        floor: Optional ground plane to correct against. Unused here.
    """

    def __init__(self, *, smpl_dir: str, floor: Floor | None = None) -> None:
        self._smpl_dir = smpl_dir
        self._floor = floor

    def correct(
        self, motion: Motion, log: Callable[[str], None] = print
    ) -> Motion:
        """Return a deep copy of ``motion`` with no changes.

        Args:
            motion: The motion to "correct", in the z-up editor world frame.
            log: Callable receiving human-readable log lines, surfaced in the
                editor. Defaults to :func:`print`.

        Returns:
            A new :class:`~motion_studio.core.types.Motion`, identical to the
            input but a distinct object (so the editor can diff against the
            original safely).
        """
        log("IdentityCorrector: returning the motion unchanged.")
        return motion.copy()
