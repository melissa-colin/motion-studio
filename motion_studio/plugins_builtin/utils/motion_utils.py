"""
motion_utils.py
===============

All non-rendering motion-processing utilities for AIOZ-GDANCE: rotation
conversions, yup2zup, SMPL forward kinematics, XY recentering, and customizable
motion-feature assembly. Plus a single end-to-end ``preprocess_raw_pkl`` that
runs the whole pipeline on one raw GDance pkl.

All functions expect torch tensors unless noted. Person/group dimensions are
kept explicit so multi-person sequences round-trip cleanly. Default fps = 30.
"""

from __future__ import annotations

import os
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np

# NOTE: ``torch`` is imported lazily, inside the functions that need it, rather
# than at module top. This keeps the numeric/io helpers (``load_raw_gdance_pkl``,
# ``yup2zup``, the rotation conversions used only for their numpy round-trip in
# ``smpl.io``) importable when torch is absent, so the flask-only core install
# (``import motion_studio.library`` / ``from motion_studio.server import app``)
# does not crash on a missing torch. Type hints stay as ``torch.Tensor`` because
# ``from __future__ import annotations`` defers their evaluation to strings.


# =====================================================================
# 0. Constants
# =====================================================================

DEFAULT_FPS = 30

SMPL_NUM_JOINTS = 24

# Canonical SMPL parent indices (24 body joints).
SMPL_PARENTS = [
    -1, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9,
    12, 13, 14, 16, 17, 18, 19, 20, 21,
]

# Default rest-pose joint offsets for SMPL (mean-shape, y-up).
SMPL_OFFSETS_YUP = [
    [0.0, 0.0, 0.0],
    [0.05858135, -0.08228004, -0.01766408],
    [-0.06030973, -0.09051332, -0.01354254],
    [0.00443945,  0.12440352, -0.03838522],
    [0.04345142, -0.38646945,  0.008037],
    [-0.04325663, -0.38368791, -0.00484304],
    [0.00448844,  0.1379564,   0.02682033],
    [-0.01479032, -0.42687458, -0.037428],
    [0.01905555, -0.4200455,  -0.03456167],
    [-0.00226458,  0.05603239,  0.00285505],
    [0.04105436, -0.06028581,  0.12204243],
    [-0.03483987, -0.06210566,  0.13032329],
    [-0.0133902,   0.21163553, -0.03346758],
    [0.07170245,  0.11399969, -0.01889817],
    [-0.08295366,  0.11247234, -0.02370739],
    [0.01011321,  0.08893734,  0.05040987],
    [0.12292141,  0.04520509, -0.019046],
    [-0.11322832,  0.04685326, -0.00847207],
    [0.2553319,  -0.01564902, -0.02294649],
    [-0.26012748, -0.01436928, -0.03126873],
    [0.26570925,  0.01269811, -0.00737473],
    [-0.26910836,  0.00679372, -0.00602676],
    [0.08669055, -0.01063603, -0.01559429],
    [-0.0887537,  -0.00865157, -0.01010708],
]


# =====================================================================
# 1. Rotation conversions (subset of pytorch3d.transforms / GDlatent)
# =====================================================================

def _sqrt_positive_part(x: torch.Tensor) -> torch.Tensor:
    import torch
    ret = torch.zeros_like(x)
    positive_mask = x > 0
    ret[positive_mask] = torch.sqrt(x[positive_mask])
    return ret


def _copysign(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    import torch
    signs_differ = (a < 0) != (b < 0)
    return torch.where(signs_differ, -a, a)


def axis_angle_to_quaternion(axis_angle: torch.Tensor) -> torch.Tensor:
    """(..., 3) axis-angle -> (..., 4) quaternion (real-part-first)."""
    import torch
    angles = torch.norm(axis_angle, p=2, dim=-1, keepdim=True)
    half = 0.5 * angles
    eps = 1e-6
    small = angles.abs() < eps
    sinc = torch.empty_like(angles)
    sinc[~small] = torch.sin(half[~small]) / angles[~small]
    sinc[small] = 0.5 - (angles[small] ** 2) / 48.0
    return torch.cat([torch.cos(half), axis_angle * sinc], dim=-1)


def quaternion_to_axis_angle(quaternions: torch.Tensor) -> torch.Tensor:
    """(..., 4) quaternion (real-part-first) -> (..., 3) axis-angle."""
    import torch
    norms = torch.norm(quaternions[..., 1:], p=2, dim=-1, keepdim=True)
    half = torch.atan2(norms, quaternions[..., :1])
    angles = 2 * half
    eps = 1e-6
    small = angles.abs() < eps
    sinc = torch.empty_like(angles)
    sinc[~small] = torch.sin(half[~small]) / angles[~small]
    sinc[small] = 0.5 - (angles[small] ** 2) / 48.0
    return quaternions[..., 1:] / sinc


def quaternion_to_matrix(quaternions: torch.Tensor) -> torch.Tensor:
    """(..., 4) quaternion -> (..., 3, 3) rotation matrix."""
    import torch
    r, i, j, k = torch.unbind(quaternions, -1)
    two_s = 2.0 / (quaternions * quaternions).sum(-1)
    o = torch.stack((
        1 - two_s * (j * j + k * k),
        two_s * (i * j - k * r),
        two_s * (i * k + j * r),
        two_s * (i * j + k * r),
        1 - two_s * (i * i + k * k),
        two_s * (j * k - i * r),
        two_s * (i * k - j * r),
        two_s * (j * k + i * r),
        1 - two_s * (i * i + j * j),
    ), -1)
    return o.reshape(quaternions.shape[:-1] + (3, 3))


def matrix_to_quaternion(matrix: torch.Tensor) -> torch.Tensor:
    """(..., 3, 3) rotation matrix -> (..., 4) quaternion (real-part-first)."""
    import torch
    if matrix.size(-1) != 3 or matrix.size(-2) != 3:
        raise ValueError(f"Invalid rotation matrix shape {matrix.shape}.")
    m00 = matrix[..., 0, 0]; m11 = matrix[..., 1, 1]; m22 = matrix[..., 2, 2]
    o0 = 0.5 * _sqrt_positive_part(1 + m00 + m11 + m22)
    x  = 0.5 * _sqrt_positive_part(1 + m00 - m11 - m22)
    y  = 0.5 * _sqrt_positive_part(1 - m00 + m11 - m22)
    z  = 0.5 * _sqrt_positive_part(1 - m00 - m11 + m22)
    o1 = _copysign(x, matrix[..., 2, 1] - matrix[..., 1, 2])
    o2 = _copysign(y, matrix[..., 0, 2] - matrix[..., 2, 0])
    o3 = _copysign(z, matrix[..., 1, 0] - matrix[..., 0, 1])
    return torch.stack((o0, o1, o2, o3), -1)


def axis_angle_to_matrix(axis_angle: torch.Tensor) -> torch.Tensor:
    return quaternion_to_matrix(axis_angle_to_quaternion(axis_angle))


def matrix_to_axis_angle(matrix: torch.Tensor) -> torch.Tensor:
    return quaternion_to_axis_angle(matrix_to_quaternion(matrix))


def align_vectors_rotation(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    """Minimal rotation matrix (3, 3) mapping unit vector ``source`` onto ``target``.

    Rodrigues rotation about the axis ``source x target`` by the angle between
    them. Inputs are normalized internally; returns identity if they are already
    (anti)parallel. Pure numpy in / numpy out.
    """
    import torch
    source = source / (np.linalg.norm(source) + 1e-12)
    target = target / (np.linalg.norm(target) + 1e-12)
    cross = np.cross(source, target)
    sin = np.linalg.norm(cross)
    cos = float(np.dot(source, target))
    if sin < 1e-8:
        return np.eye(3)
    axis = cross / sin
    angle = np.arccos(np.clip(cos, -1.0, 1.0))
    return axis_angle_to_matrix(torch.tensor((axis * angle).astype(np.float32))).numpy()


def global_rotation_chain(pose_frame: np.ndarray, chain: Sequence[int]) -> torch.Tensor:
    """Global rotation (3, 3) of the last joint of a kinematic ``chain``.

    Composes the local axis-angle rotations of the joints in ``chain`` (root
    first) into the world-space orientation of the chain's tip.

    Args:
        pose_frame: (24, 3) axis-angle pose for ONE frame; ``pose_frame[0]`` is
            the root (global_orient).
        chain: ordered joint indices from root down to the target joint, e.g.
            ``[0, 1, 4, 7]`` (root -> lhip -> lknee -> lankle).

    Returns:
        (3, 3) global rotation matrix of the last joint in ``chain``.
    """
    import torch
    aa = torch.from_numpy(np.asarray(pose_frame)[list(chain)].astype(np.float32))   # (k, 3)
    rots = axis_angle_to_matrix(aa)                                                  # (k, 3, 3)
    global_rot = torch.eye(3)
    for i in range(rots.shape[0]):
        global_rot = global_rot @ rots[i]
    return global_rot


def matrix_to_rotation_6d(matrix: torch.Tensor) -> torch.Tensor:
    """Zhou et al. continuous 6D representation: keep the first two rows of R."""
    return matrix[..., :2, :].clone().reshape(*matrix.size()[:-2], 6)


def rotation_6d_to_matrix(d6: torch.Tensor) -> torch.Tensor:
    """Gram-Schmidt to recover a rotation matrix from the 6D representation."""
    import torch
    import torch.nn.functional as F
    a1, a2 = d6[..., :3], d6[..., 3:]
    b1 = F.normalize(a1, dim=-1)
    b2 = a2 - (b1 * a2).sum(-1, keepdim=True) * b1
    b2 = F.normalize(b2, dim=-1)
    b3 = torch.cross(b1, b2, dim=-1)
    return torch.stack((b1, b2, b3), dim=-2)


def axis_angle_to_6d(ax: torch.Tensor) -> torch.Tensor:
    """(..., 3) axis-angle -> (..., 6) 6D rotation. Equivalent to ax_to_6v in GDlatent."""
    assert ax.shape[-1] == 3
    return matrix_to_rotation_6d(axis_angle_to_matrix(ax))


def rotation_6d_to_axis_angle(d6: torch.Tensor) -> torch.Tensor:
    """(..., 6) 6D rotation -> (..., 3) axis-angle. Equivalent to ax_from_6v in GDlatent."""
    assert d6.shape[-1] == 6
    return matrix_to_axis_angle(rotation_6d_to_matrix(d6))


def _quaternion_raw_multiply(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    import torch
    aw, ax, ay, az = torch.unbind(a, -1)
    bw, bx, by, bz = torch.unbind(b, -1)
    ow = aw * bw - ax * bx - ay * by - az * bz
    ox = aw * bx + ax * bw + ay * bz - az * by
    oy = aw * by - ax * bz + ay * bw + az * bx
    oz = aw * bz + ax * by - ay * bx + az * bw
    return torch.stack((ow, ox, oy, oz), -1)


def _standardize_quaternion(q: torch.Tensor) -> torch.Tensor:
    import torch
    return torch.where(q[..., 0:1] < 0, -q, q)


def quaternion_multiply(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    """Hamilton product, real-part-first, then sign-standardize."""
    return _standardize_quaternion(_quaternion_raw_multiply(a, b))


def quaternion_invert(q: torch.Tensor) -> torch.Tensor:
    return q * q.new_tensor([1.0, -1.0, -1.0, -1.0])


def quaternion_apply(q: torch.Tensor, p: torch.Tensor) -> torch.Tensor:
    """Rotate a 3D point by a quaternion (real-part-first)."""
    import torch
    if p.size(-1) != 3:
        raise ValueError(f"Points are not in 3D: {p.shape}.")
    real = p.new_zeros(p.shape[:-1] + (1,))
    pq = torch.cat((real, p), -1)
    out = _quaternion_raw_multiply(_quaternion_raw_multiply(q, pq), quaternion_invert(q))
    return out[..., 1:]


def _axis_angle_rotation_matrix(axis: str, angle: torch.Tensor) -> torch.Tensor:
    """Single-axis rotation matrix (X/Y/Z) for an angle in radians."""
    import torch
    c, s = torch.cos(angle), torch.sin(angle)
    one = torch.ones_like(angle); zero = torch.zeros_like(angle)
    if axis == "X":
        flat = (one, zero, zero, zero, c, -s, zero, s, c)
    elif axis == "Y":
        flat = (c, zero, s, zero, one, zero, -s, zero, c)
    elif axis == "Z":
        flat = (c, -s, zero, s, c, zero, zero, zero, one)
    else:
        raise ValueError(f"axis must be one of X/Y/Z, got {axis}")
    return torch.stack(flat, -1).reshape(angle.shape + (3, 3))


def quat_rotate(q: torch.Tensor, v: torch.Tensor) -> torch.Tensor:
    """Rotate vector(s) v by quaternion(s) q (real-part-first). Broadcasts the
    leading dims; q and v are normalized internally to be robust to small drift.
    """
    import torch
    if torch.any(torch.isnan(q)) or torch.any(torch.isnan(v)):
        raise ValueError("quat_rotate: NaN in inputs.")
    original_shape = v.shape
    q = q.contiguous().view(-1, 4)
    v = v.contiguous().view(-1, 3)
    q = q / torch.clamp(torch.norm(q, dim=-1, keepdim=True), min=1e-8)
    qw, qvec = q[:, :1], q[:, 1:]
    qv = torch.cross(qvec, v, dim=-1)
    qqv = torch.cross(qvec, qv, dim=-1)
    return (v + 2 * qw * qv + 2 * qqv).view(original_shape)


# =====================================================================
# 2. y-up -> z-up reorientation
# =====================================================================

def yup2zup(
    root_pos: torch.Tensor,
    local_q: torch.Tensor,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Rotate a y-up motion sequence into the z-up convention used by the rest of
    the pipeline (and by all the visualizers/renderers downstream).

    Reproduces ``utils.motion.yup2zup`` from GDlatent.

    Args:
        root_pos: (..., T, 3) root translations in y-up world.
        local_q:  (..., T, J=24, 3) axis-angle pose for each joint, root-relative.
                  Note: ``local_q[..., 0, :]`` is the *root* axis-angle.

    Returns:
        root_pos_zup: (..., T, 3) root translation, rotated 90 degrees about +X.
        local_q_zup:  same shape as ``local_q`` but the root joint axis-angle has
                      been rotated 90 degrees about +X (left-multiplied as a quaternion).
        root_q_quat:  (..., T, 1, 4) the post-rotation root quaternion
                      (kept around because downstream uses ``quat_rotate(root_q_rep, ...)``).
    """
    import torch
    root_q = local_q[..., :1, :]                    # (..., T, 1, 3)
    root_q_quat = axis_angle_to_quaternion(root_q)  # (..., T, 1, 4)
    # 90-degree rotation about +X expressed as a (w, x, y, z) quaternion.
    rotation = torch.tensor(
        [0.7071068, 0.7071068, 0.0, 0.0],
        dtype=root_q_quat.dtype,
        device=root_q_quat.device,
    )
    root_q_quat = quaternion_multiply(rotation, root_q_quat)  # left multiply
    root_q = quaternion_to_axis_angle(root_q_quat)
    local_q = local_q.clone()
    local_q[..., :1, :] = root_q
    # Rotate the root translation: (x, y, z) -> (x, -z, y).
    angle = torch.tensor(np.pi / 2, dtype=root_pos.dtype, device=root_pos.device)
    rot_mat = _axis_angle_rotation_matrix("X", angle)
    root_pos = torch.einsum("ij,...j->...i", rot_mat, root_pos)
    return root_pos, local_q, root_q_quat


# =====================================================================
# 3. SMPL forward kinematics (24-joint, no betas)
# =====================================================================

class SMPLSkeleton:
    """SMPL 24-joint kinematic tree using the canonical mean-shape rest pose.

    Pass ``up_axis='z'`` if the input motion was *retargeted* assuming a z-up
    rest pose (PM01-retargeted GDance). For raw GDance (y-up native), call
    :func:`yup2zup` first and then leave ``up_axis='y'``.
    """

    def __init__(self, device: Optional[Union[str, torch.device]] = None, up_axis: str = "y"):
        import torch
        offsets = SMPL_OFFSETS_YUP
        if up_axis == "z":
            # +y_rest -> +z_world: (x, y, z) -> (x, -z, y).
            offsets = [[o[0], -o[2], o[1]] for o in offsets]
        elif up_axis != "y":
            raise ValueError(f"SMPLSkeleton: unsupported up_axis={up_axis!r}")
        self._offsets = torch.tensor(offsets, dtype=torch.float32, device=device)
        self._parents = np.array(SMPL_PARENTS)
        self.up_axis = up_axis
        self._compute_metadata()

    def _compute_metadata(self) -> None:
        self._has_children = np.zeros(len(self._parents), dtype=bool)
        for i, p in enumerate(self._parents):
            if p != -1:
                self._has_children[p] = True

    def forward(self, rotations: torch.Tensor, root_positions: torch.Tensor) -> torch.Tensor:
        """
        Args:
            rotations:      (N, T, J, 3) axis-angle joint rotations.
            root_positions: (N, T, 3)    root translation.

        Returns:
            positions: (N, T, J, 3) world-space joint positions.
        """
        import torch
        assert rotations.dim() == 4 and root_positions.dim() == 3
        q = axis_angle_to_quaternion(rotations)
        expanded_offsets = self._offsets.expand(
            q.shape[0], q.shape[1], self._offsets.shape[0], self._offsets.shape[1]
        )
        positions_world: List[torch.Tensor] = []
        rotations_world: List[Optional[torch.Tensor]] = []
        for i in range(self._offsets.shape[0]):
            if self._parents[i] == -1:
                positions_world.append(root_positions)
                rotations_world.append(q[:, :, 0])
            else:
                positions_world.append(
                    quaternion_apply(
                        rotations_world[self._parents[i]], expanded_offsets[:, :, i]
                    ) + positions_world[self._parents[i]]
                )
                if self._has_children[i]:
                    rotations_world.append(
                        quaternion_multiply(rotations_world[self._parents[i]], q[:, :, i])
                    )
                else:
                    rotations_world.append(None)
        return torch.stack(positions_world, dim=3).permute(0, 1, 3, 2)


def forward_kinematics(
    local_q: torch.Tensor,
    root_pos: torch.Tensor,
    up_axis: str = "y",
    device: Optional[Union[str, torch.device]] = None,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    SMPL FK + frame-difference velocity.

    Args:
        local_q:  (N, T, J=24, 3) axis-angle.
        root_pos: (N, T, 3) root translation in the same world frame as ``up_axis``.
        up_axis:  'y' for y-up SMPL rest pose (the default); 'z' for z-up rest pose
                  (PM01-retargeted GDance).

    Returns:
        positions: (N, T, 24, 3) world joint positions.
        velocity:  (N, T, 24, 3) frame-to-frame velocity (zero at t=0).
    """
    import torch
    skel = SMPLSkeleton(device=device, up_axis=up_axis)
    positions = skel.forward(local_q, root_pos)
    velocity = torch.zeros_like(positions)
    velocity[:, 1:] = positions[:, 1:] - positions[:, :-1]
    return positions, velocity


# =====================================================================
# 4. SMPL mesh forward (smplx)
# =====================================================================


def smpl_forward_one_person(smpl_poses, root_trans, smpl_model, device=None):
    """Per-dancer SMPL **mesh** forward -> ``{'v': (T,6890,3), 'Jtr': (T,24,3)}``.

    Args:
        smpl_poses: (T, 72) axis-angle pose for ONE dancer, numpy, z-up world.
        root_trans: (T, 3) root translation for that dancer, numpy.
        smpl_model: a prebuilt ``smplx.SMPL`` already on ``device`` (built once by
            the caller and reused across dancers; batch_size=1 is fine).
        device: torch device; defaults to cuda if available.

    Returns:
        ``{'v': (T, 6890, 3), 'Jtr': (T, 24, 3)}`` torch tensors on CPU, z-up world.
    """
    import torch
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    global_orient = torch.from_numpy(smpl_poses[:, :3].astype(np.float32)).to(device)
    body_pose     = torch.from_numpy(smpl_poses[:, 3:].astype(np.float32)).to(device)
    transl        = torch.from_numpy(root_trans.astype(np.float32)).to(device)
    with torch.no_grad():
        out = smpl_model(global_orient=global_orient, body_pose=body_pose, transl=transl)

    return {
        "v": out.vertices.detach().cpu(),
        "Jtr": out.joints.detach().cpu()[:, :SMPL_NUM_JOINTS],
    }


def smpl_mesh_fk(poses, root_trans, smpl_model, device=None) -> Tuple[np.ndarray, np.ndarray]:
    """Per-dancer SMPL mesh FK returning **numpy** ``(verts, joints)``.

    Thin numpy-facing wrapper over :func:`smpl_forward_one_person`: accepts the
    ``(T, 24, 3)`` axis-angle layout used by the geometric corrector, reshapes to
    ``(T, 72)`` internally, and unpacks the dict.

    Args:
        poses: (T, 24, 3) axis-angle pose for ONE dancer, numpy, z-up world.
        root_trans: (T, 3) root translation for that dancer, numpy.
        smpl_model: prebuilt ``smplx.SMPL`` on ``device``.
        device: torch device; defaults to cuda if available.

    Returns:
        verts: (T, 6890, 3) numpy vertices.
        joints: (T, 24, 3) numpy joints.
    """
    T = poses.shape[0]
    out = smpl_forward_one_person(poses.reshape(T, 72), root_trans, smpl_model, device)
    return out["v"].numpy(), out["Jtr"].numpy()


# =====================================================================
# 5. XY recentering
# =====================================================================
#
# Note: we intentionally do *not* expose a floor-adjustment helper here.
# A per-clip feet-median floor (plus a safety push to keep the root above it)
# is a visualization heuristic that distorts foot-ground penetration / float --
# the very geometric artifacts the metrics measure. So this pipeline keeps the
# raw world Z untouched.

def recenter_xy(
    positions: torch.Tensor,
    center: torch.Tensor,
    already_zup: bool = True,
) -> torch.Tensor:
    """Translate ``positions`` in the XY plane so a given ``center`` sits at the origin.

    Args:
        positions:   (N, T, J, 3) z-up joint positions.
        center:      (N, 3) or (3,) world-space center to subtract.
                     If ``already_zup`` is False, the input is taken to be in the *y-up*
                     center JSON convention used in GDlatent and is converted internally
                     (this matches ``GroupDanceDataset.move_floor_gdance``).
        already_zup: True if ``center`` is already in the z-up world frame.

    Returns:
        positions: same shape as input, with the XY of ``center`` removed.
    """
    import torch
    positions = positions.clone()
    if center.dim() == 1:
        center = center.unsqueeze(0).expand(positions.shape[0], -1)
    if already_zup:
        center_xy = center * torch.tensor([1.0, 1.0, 0.0], dtype=center.dtype, device=center.device)
    else:
        # GDlatent's legacy path: center JSON is *not* yup2zup-rotated yet.
        center_xy = center.clone()
        center_xy[:, 1] = -center_xy[:, 2]
        center_xy[:, 2] = 0.0
    positions = positions - center_xy[:, None, None, :]
    return positions


# =====================================================================
# 6. Customizable motion-representation assembly
# =====================================================================

# Order of channels in the final flat motion vector. The example script below
# uses these names verbatim. Each entry maps to a (N, T, C) tensor produced
# from the SMPL FK pipeline.

SUPPORTED_ENTRIES = (
    "contacts",          # (N, T, F)        binary feet contact label, F = #feet joints
    "root_pos",           # (N, T, 3)        full root xyz
    "root_pos_xy",        # (N, T, 2)        just root XY
    "root_height",        # (N, T, 1)        root z
    "root_velocity_xy",   # (N, T, 2)        root XY frame-difference velocity
    "local_6d",           # (N, T, 24*6=144) per-joint 6D rotation
    "local_velocity",     # (N, T, 24*3=72)  per-joint velocity rotated into root-local frame
    "joint_positions",    # (N, T, 24*3=72)  world-space joint positions (flattened)
    "joint_velocity",     # (N, T, 24*3=72)  world-space joint velocity (flattened)
)


@dataclass
class MotionReprSpec:
    """Schema describing the contents of an assembled motion vector."""
    entries: List[str]
    slices: Dict[str, slice]
    dim: int

    def split(self, motion: torch.Tensor) -> Dict[str, torch.Tensor]:
        """Convenience: slice a (..., dim) vector back into its named components."""
        if motion.shape[-1] != self.dim:
            raise ValueError(f"Expected last dim {self.dim}, got {motion.shape[-1]}.")
        return {name: motion[..., s] for name, s in self.slices.items()}


def assemble_motion_repr(
    *,
    local_q: torch.Tensor,
    root_pos: torch.Tensor,
    positions: torch.Tensor,
    velocity: torch.Tensor,
    contacts: torch.Tensor,
    entries: Sequence[str] = ("contacts", "root_pos", "local_6d"),
) -> Tuple[torch.Tensor, MotionReprSpec]:
    """Assemble a flat motion vector from primitive features.

    Inputs are the outputs of :func:`forward_kinematics` plus a caller-supplied
    foot-contact label (after any floor / centering step), so this function does
    no geometry on its own. It just concatenates the requested entries in the
    requested order and returns a schema describing the layout.

    Default ``entries`` give the minimal motion representation Melissa asked for:
    ``[contacts, root_pos, local_6d]`` -> (N, T, 4 + 3 + 144) = (N, T, 151).

    Args:
        local_q:    (N, T, 24, 3) axis-angle pose. local_q[..., 0, :] is the root.
        root_pos:   (N, T, 3) root translation (after floor / center adjustments).
        positions:  (N, T, 24, 3) FK joint positions (consistent with ``local_q``+``root_pos``).
        velocity:   (N, T, 24, 3) frame-difference joint velocity.
        contacts:   (N, T, F) binary feet contact label.
        entries:    ordered list of entry names from :data:`SUPPORTED_ENTRIES`.

    Returns:
        motion: (N, T, dim) flat motion vector.
        spec:   :class:`MotionReprSpec` describing each entry's channel slice.
    """
    import torch
    N, T, J, _ = local_q.shape
    parts: List[torch.Tensor] = []
    slices: Dict[str, slice] = {}
    cursor = 0

    # Precompute reusable derived tensors only if needed.
    need_local_6d = "local_6d" in entries
    need_local_velocity = "local_velocity" in entries
    need_root_vel = "root_velocity_xy" in entries

    if need_local_6d:
        local_6d = axis_angle_to_6d(local_q).reshape(N, T, J * 6)

    if need_local_velocity:
        # Root-frame local velocity, matching legacy_velo's "local_velocity" channel.
        root_q = axis_angle_to_quaternion(local_q[:, :, :1, :])      # (N, T, 1, 4)
        root_q_rep = root_q.repeat(1, 1, J, 1)                       # (N, T, J, 4)
        loc_v = torch.zeros_like(velocity)
        loc_v[:, 1:] = quat_rotate(root_q_rep[:, :-1], velocity[:, 1:])
        local_velocity = loc_v.reshape(N, T, J * 3)

    if need_root_vel:
        r_vel = torch.zeros((N, T, 3), dtype=velocity.dtype, device=velocity.device)
        r_vel[:, 1:] = velocity[:, 1:, 0, :]
        root_velocity_xy = r_vel[..., :2]

    for name in entries:
        if name == "contacts":
            tensor = contacts
        elif name == "root_pos":
            tensor = root_pos
        elif name == "root_pos_xy":
            tensor = root_pos[..., :2]
        elif name == "root_height":
            tensor = root_pos[..., 2:3]
        elif name == "root_velocity_xy":
            tensor = root_velocity_xy
        elif name == "local_6d":
            tensor = local_6d
        elif name == "local_velocity":
            tensor = local_velocity
        elif name == "joint_positions":
            tensor = positions.reshape(N, T, J * 3)
        elif name == "joint_velocity":
            tensor = velocity.reshape(N, T, J * 3)
        else:
            raise ValueError(
                f"Unknown entry {name!r}. Supported: {SUPPORTED_ENTRIES}."
            )
        c = tensor.shape[-1]
        parts.append(tensor)
        slices[name] = slice(cursor, cursor + c)
        cursor += c

    motion = torch.cat(parts, dim=-1).contiguous().float()
    if torch.isinf(motion).any() or torch.isnan(motion).any():
        raise ValueError("assemble_motion_repr: produced motion contains NaN/Inf.")
    spec = MotionReprSpec(entries=list(entries), slices=slices, dim=cursor)
    return motion, spec


# =====================================================================
# 7. End-to-end raw-pkl processor (long sequences, no slicing)
# =====================================================================

@dataclass
class GDanceRawSample:
    """One raw GDance sample, ready for downstream processing.

    Tensor layout convention (matches GDlatent.dataset.gdance):
        - first dim is *person* (dancer); persons in a clip share the time axis.
        - second dim is *time* T.

    World frame: z-up after ``yup2zup``. The raw world Z is preserved -- we do
    not subtract a per-clip floor estimate, so foot-ground penetration / float
    can be measured directly in this frame.
    """
    name: str                            # sequence id (filename stem)
    smpl_poses: torch.Tensor              # (N_persons, T, 24, 3) axis-angle, z-up after preprocess
    root_trans: torch.Tensor              # (N_persons, T, 3)     z-up after preprocess (raw world Z)
    positions: torch.Tensor               # (N_persons, T, 24, 3) FK joint positions, z-up (raw world Z)
    velocity:  torch.Tensor               # (N_persons, T, 24, 3) frame-difference velocity
    fps: int = DEFAULT_FPS


# Module/qualname pairs an AIOZ-GDANCE pkl legitimately needs to rebuild its
# numpy arrays. numpy moved ``core`` -> ``_core`` in 2.0, so both spellings are
# allowed. Everything else (``os.system``, ``builtins.eval``, ``subprocess`` ...)
# is rejected, which is what defeats the pickle RCE: ``find_class`` is the only
# hook an attacker can use to get arbitrary callables out of a pickle stream.
_SAFE_GLOBALS = frozenset({
    ("numpy", "ndarray"),
    ("numpy", "dtype"),
    ("numpy.core.multiarray", "_reconstruct"),
    ("numpy.core.multiarray", "scalar"),
    ("numpy._core.multiarray", "_reconstruct"),
    ("numpy._core.multiarray", "scalar"),
    # Safe builtin containers/scalars that may appear as reduce targets.
    ("builtins", "dict"),
    ("builtins", "list"),
    ("builtins", "tuple"),
    ("builtins", "set"),
    ("builtins", "frozenset"),
    ("builtins", "int"),
    ("builtins", "float"),
    ("builtins", "complex"),
    ("builtins", "bool"),
    ("builtins", "str"),
    ("builtins", "bytes"),
    ("builtins", "bytearray"),
})


class _SafeUnpickler(pickle.Unpickler):
    """A restricted unpickler that only resolves a numpy/builtins whitelist.

    Untrusted ``.pkl`` files are an arbitrary-code-execution vector: the pickle
    VM can call any importable callable via ``find_class`` + ``REDUCE``. This
    subclass overrides :meth:`find_class` to allow *only* the
    ``(module, name)`` pairs in :data:`_SAFE_GLOBALS` (numpy array reconstruction
    plus safe builtin scalars/containers) and raises
    :class:`pickle.UnpicklingError` on anything else, so a crafted pkl cannot
    smuggle in ``os.system``, ``eval``, etc. Plain scalars, strings, dicts,
    lists and tuples decode normally (they use opcodes, not ``find_class``).
    """

    def find_class(self, module: str, name: str):
        if (module, name) in _SAFE_GLOBALS:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(
            f"Refusing to unpickle disallowed global {module}.{name!r}. "
            "Only numpy array reconstruction and safe builtins are permitted."
        )


def _safe_pickle_load(fh) -> object:
    """``pickle.load`` restricted to the numpy/builtins whitelist (no RCE)."""
    return _SafeUnpickler(fh).load()


def load_raw_gdance_pkl(
    pkl_path: Union[str, Path],
) -> Tuple[torch.Tensor, torch.Tensor, str]:
    """Read one raw GDance pkl and return its (smpl_poses, root_trans, name).

    The pkl is expected to contain the keys documented in GDance/README.txt:
        smpl_poses: (num_persons, num_frames, 72) axis-angle
        root_trans: (num_persons, num_frames, 3)

    The file is decoded with a :class:`_SafeUnpickler` that whitelists only
    numpy array reconstruction and safe builtin scalars/containers, so a
    malicious ``.pkl`` cannot execute arbitrary code on load.
    """
    import torch
    pkl_path = Path(pkl_path)
    with open(pkl_path, "rb") as fh:
        data = _safe_pickle_load(fh)
    smpl_poses = np.asarray(data["smpl_poses"], dtype=np.float32)
    root_trans = np.asarray(data["root_trans"], dtype=np.float32)
    if smpl_poses.ndim == 2:
        smpl_poses = smpl_poses[None, ...]
    if root_trans.ndim == 2:
        root_trans = root_trans[None, ...]
    N, T = smpl_poses.shape[:2]
    if smpl_poses.shape[-1] == 72:
        smpl_poses = smpl_poses.reshape(N, T, SMPL_NUM_JOINTS, 3)
    elif smpl_poses.ndim != 4 or smpl_poses.shape[2:] != (SMPL_NUM_JOINTS, 3):
        raise ValueError(f"unexpected smpl_poses shape {smpl_poses.shape} in {pkl_path}")
    return torch.from_numpy(smpl_poses), torch.from_numpy(root_trans), pkl_path.stem


def preprocess_raw_pkl(
    pkl_path: Union[str, Path],
    *,
    apply_yup2zup: bool = True,
    verbose: bool = True,
) -> GDanceRawSample:
    """Full single-pkl preprocess pipeline for raw GDance data.

    Pipeline:
        load pkl
        --> (optional) yup2zup rotation of root pose + root quaternion
        --> SMPL FK (24 joints) using a y-up rest pose (since yup2zup already
            rotated *the data* into z-up; rest pose offsets stay y-up)

    The raw world Z is kept as-is on purpose: any per-clip floor estimate
    would distort the foot-ground penetration / float artifacts that the
    metrics measure. Compute the floor (or leave it as a free variable) inside
    whatever metric step follows, not here.

    For downstream channel assembly use :func:`assemble_motion_repr`.
    """
    smpl_poses, root_trans, name = load_raw_gdance_pkl(pkl_path)
    # smpl_poses: (N_persons, T, 24, 3); root_trans: (N_persons, T, 3).
    if apply_yup2zup:
        root_trans, smpl_poses, _root_q = yup2zup(root_trans, smpl_poses)
        fk_up_axis = "y"     # data is now z-up, rest pose stays y-up
    else:
        fk_up_axis = "z"     # data was already z-up; rotate rest pose to z-up

    positions, velocity = forward_kinematics(smpl_poses, root_trans, up_axis=fk_up_axis)

    if verbose:
        print(f"[preprocess] {name}: persons={positions.shape[0]} frames={positions.shape[1]}")
        print(f"[preprocess] raw world Z: root_z min={root_trans[..., 2].min():.4f}  "
              f"max={root_trans[..., 2].max():.4f}; "
              f"all-joint z min={positions[..., 2].min():.4f}")

    return GDanceRawSample(
        name=name,
        smpl_poses=smpl_poses,
        root_trans=root_trans,
        positions=positions,
        velocity=velocity,
    )


__all__ = [
    # rotation conversions
    "axis_angle_to_quaternion", "quaternion_to_axis_angle",
    "axis_angle_to_matrix", "matrix_to_axis_angle",
    "quaternion_to_matrix", "matrix_to_quaternion",
    "axis_angle_to_6d", "rotation_6d_to_axis_angle",
    "matrix_to_rotation_6d", "rotation_6d_to_matrix",
    "quaternion_multiply", "quaternion_invert", "quaternion_apply", "quat_rotate",
    "align_vectors_rotation", "global_rotation_chain",
    # geometry
    "yup2zup", "SMPLSkeleton", "forward_kinematics", "smpl_forward_one_person",
    "smpl_mesh_fk", "recenter_xy",
    # motion representation
    "SUPPORTED_ENTRIES", "MotionReprSpec", "assemble_motion_repr",
    # raw-pkl pipeline
    "GDanceRawSample", "load_raw_gdance_pkl", "preprocess_raw_pkl",
    # constants
    "SMPL_NUM_JOINTS", "SMPL_PARENTS", "DEFAULT_FPS",
]
