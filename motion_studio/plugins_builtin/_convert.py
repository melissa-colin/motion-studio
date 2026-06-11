"""z-up <-> y-up conversion for AIOZ-GDANCE SMPL clips.

The AIOZ-GDANCE pkls store y-up motions. The whole loading pipeline
(``load_raw_gdance_pkl`` -> ``yup2zup`` -> FK) rotates them into the z-up world
frame the editor and corrector work in. To write a clip back out in the exact
original convention we must undo that rotation, which is what :func:`zup2yup`
does.

``zup2yup`` is the exact inverse of ``utils.motion_utils.yup2zup``
(``zup2yup(yup2zup(x)) == x`` to ~1e-7). It is vendored here (copied from the
working pose editor) so this package does not depend on the external
``refit_smpl`` module.

This module is pure numpy on purpose: it sits on the core boot path
(``smpl.io`` imports it), so it must import even when ``torch`` is absent. The
small quaternion helpers below replicate the numerics of the torch versions in
``utils.motion_utils`` exactly (same formulas, same small-angle Taylor terms).
"""

from __future__ import annotations

import numpy as np


def _axis_angle_to_quaternion(axis_angle: np.ndarray) -> np.ndarray:
    """(..., 3) axis-angle -> (..., 4) quaternion (real-part-first).

    Numpy port of ``utils.motion_utils.axis_angle_to_quaternion`` with the same
    small-angle Taylor branch for numerical parity.
    """
    angles = np.linalg.norm(axis_angle, ord=2, axis=-1, keepdims=True)
    half = 0.5 * angles
    eps = 1e-6
    small = np.abs(angles) < eps
    sinc = np.empty_like(angles)
    not_small = ~small
    sinc[not_small] = np.sin(half[not_small]) / angles[not_small]
    sinc[small] = 0.5 - (angles[small] ** 2) / 48.0
    return np.concatenate([np.cos(half), axis_angle * sinc], axis=-1)


def _quaternion_to_axis_angle(quaternions: np.ndarray) -> np.ndarray:
    """(..., 4) quaternion (real-part-first) -> (..., 3) axis-angle.

    Numpy port of ``utils.motion_utils.quaternion_to_axis_angle``.
    """
    norms = np.linalg.norm(quaternions[..., 1:], ord=2, axis=-1, keepdims=True)
    half = np.arctan2(norms, quaternions[..., :1])
    angles = 2 * half
    eps = 1e-6
    small = np.abs(angles) < eps
    sinc = np.empty_like(angles)
    not_small = ~small
    sinc[not_small] = np.sin(half[not_small]) / angles[not_small]
    sinc[small] = 0.5 - (angles[small] ** 2) / 48.0
    return quaternions[..., 1:] / sinc


def _quaternion_raw_multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    aw, ax, ay, az = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    bw, bx, by, bz = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    ow = aw * bw - ax * bx - ay * by - az * bz
    ox = aw * bx + ax * bw + ay * bz - az * by
    oy = aw * by - ax * bz + ay * bw + az * bx
    oz = aw * bz + ax * by - ay * bx + az * bw
    return np.stack((ow, ox, oy, oz), axis=-1)


def _quaternion_multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Hamilton product, real-part-first, then sign-standardize.

    Numpy port of ``utils.motion_utils.quaternion_multiply``.
    """
    out = _quaternion_raw_multiply(a, b)
    return np.where(out[..., 0:1] < 0, -out, out)


def zup2yup(poses_z, trans_z) -> tuple[np.ndarray, np.ndarray]:
    """Rotate a z-up SMPL motion back to the y-up AIOZ-GDANCE convention.

    Exact inverse of ``utils.motion_utils.yup2zup``: applies a -90 degree
    rotation about +X to the root joint axis-angle and to the root translation.
    Pure numpy (no torch) so it stays on the torch-free core boot path.

    Args:
        poses_z: (N, T, 24, 3) axis-angle poses in the z-up world, array-like.
        trans_z: (N, T, 3) root translations in the z-up world, array-like.

    Returns:
        A tuple ``(poses_y, trans_y)`` of numpy float32 arrays in the y-up
        convention, same shapes as the inputs.
    """
    pz = np.asarray(poses_z, dtype=np.float32)
    tz = np.asarray(trans_z, dtype=np.float32)
    root_q = pz[..., :1, :]
    qq = _axis_angle_to_quaternion(root_q)
    # Conjugate of the +90 deg /+X rotation = -90 deg /+X rotation.
    inv = np.array([0.7071068, -0.7071068, 0.0, 0.0], dtype=qq.dtype)
    qq = _quaternion_multiply(inv, qq)  # left multiply (inverse)
    root_q = _quaternion_to_axis_angle(qq)
    py = pz.copy()
    py[..., :1, :] = root_q
    # Inverse of (x, y, z) -> (x, -z, y) is (x, y, z) -> (x, z, -y).
    ty = tz.copy()
    ty[..., 1] = tz[..., 2]
    ty[..., 2] = -tz[..., 1]
    return py.astype(np.float32), ty.astype(np.float32)
