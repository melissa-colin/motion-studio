"""Core data types exchanged between Motion Studio and its plugins.

These dataclasses are the *only* contract the editor relies on. A custom
auto-correction or metrics plugin receives and returns these types and never
needs to know how Motion Studio stores motions on disk.
"""

from __future__ import annotations

import dataclasses

import numpy as np


@dataclasses.dataclass
class Motion:
    """A multi-person SMPL motion in the editor z-up world frame.

    Attributes:
      poses: Axis-angle body poses, shape (n_persons, n_frames, 24, 3).
      trans: Root translations, shape (n_persons, n_frames, 3).
      betas: SMPL shape coefficients, shape (n_persons, 10), or None.
      gender: SMPL gender, one of "neutral", "male", "female".
      fps: Sampling rate of the motion, in frames per second.
      name: Human-readable clip name (no path, no extension).
    """

    poses: np.ndarray
    trans: np.ndarray
    betas: np.ndarray | None = None
    gender: str = "neutral"
    fps: float = 30.0
    name: str = ""

    @property
    def n_persons(self) -> int:
        """Number of people in the motion."""
        return int(self.poses.shape[0])

    @property
    def n_frames(self) -> int:
        """Number of frames in the motion."""
        return int(self.poses.shape[1])

    def copy(self) -> Motion:
        """Return a deep copy, arrays included."""
        return Motion(
            poses=np.array(self.poses, copy=True),
            trans=np.array(self.trans, copy=True),
            betas=None
            if self.betas is None
            else np.array(self.betas, copy=True),
            gender=self.gender,
            fps=self.fps,
            name=self.name,
        )


@dataclasses.dataclass
class Floor:
    """An estimated ground plane, written z = a*x + b*y + c.

    Attributes:
      plane: The (a, b, c) coefficients of the plane in the z-up world frame.
    """

    plane: tuple[float, float, float]

    @property
    def normal(self) -> np.ndarray:
        """Unit normal of the plane, pointing up (+z)."""
        a, b, _ = self.plane
        n = np.array([-a, -b, 1.0], dtype=float)
        return n / np.linalg.norm(n)
