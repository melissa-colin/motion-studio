"""
floor_utils.py
==============

Generic floor-plane geometry for multi-person SMPL motion: fit ONE ground plane
``z = a*x + b*y + c`` shared by all dancers, plus small helpers to measure a
point's signed vertical distance to that plane and the plane's upward normal.

Bodies recovered from monocular video sit at an arbitrary world Z and on a
possibly tilted floor, so a single inclined plane is estimated and subtracted
per vertex (the tilt matters). The robust fit is plain RANSAC (Fischler &
Bolles, CACM 1981) on a cloud of foot points, and the foot-vertex mask comes
from the SMPL (Loper et al., SIGGRAPH Asia 2015) skinning weights, so no
external part-segmentation file is needed. These are standard geometry/IO
utilities.
"""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import torch


# =====================================================================
# 0. Constants
# =====================================================================

_LEFT_FOOT_JOINTS = (7, 10)            # SMPL joints for the left foot-vertex mask
_RIGHT_FOOT_JOINTS = (8, 11)           # SMPL joints for the right foot-vertex mask

RANSAC_BAND = 0.025                    # inlier half-thickness (m): sole thickness + noise
RANSAC_ITERS = 600                     # random hypotheses
RANSAC_SEED = 0                        # deterministic (reproducible floor)


# =====================================================================
# 1. Foot-vertex mask from SMPL skinning weights
#    Uses SMPL (Loper et al., SIGGRAPH Asia 2015) skinning weights; the
#    argmax-dominant-joint mask is OUR OWN (no external part-segmentation file).
# =====================================================================

def foot_vertex_masks(smpl_model) -> Tuple[np.ndarray, np.ndarray]:
    """Indices of the left / right foot vertices, from SMPL LBS skinning weights.

    A vertex "belongs" to a foot if its dominant skinning joint is an ankle/toe
    joint (left {7, 10}, right {8, 11}). No external part-segmentation file needed.
    """
    w = smpl_model.lbs_weights.detach().cpu().numpy()      # (6890, 24)
    dominant_joint = w.argmax(axis=1)                      # (6890,)
    left = np.where(np.isin(dominant_joint, _LEFT_FOOT_JOINTS))[0]
    right = np.where(np.isin(dominant_joint, _RIGHT_FOOT_JOINTS))[0]
    return left, right


# =====================================================================
# 2. Robust ground-plane fit (RANSAC)
#    Algorithm: RANSAC (Fischler & Bolles, CACM 1981). Textbook robust
#    plane fit: fit z = a*x + b*y + c to a point cloud, rejecting outliers via
#    the largest consensus set, then least-squares refit on the inliers.
# =====================================================================

def fit_floor_plane(points, band: float = RANSAC_BAND,
                    iters: int = RANSAC_ITERS, seed: int = RANSAC_SEED):
    """Fit z = a*x + b*y + c to a point cloud by RANSAC.

    Returns ((a, b, c), tilt_deg, inlier_frac):
        tilt_deg    -- angle between the plane normal and vertical (a confidence
                       signal: a real floor is near-flat; big tilt => suspicious).
        inlier_frac -- fraction of points within `band` of the winning plane
                       (the RANSAC consensus = how well the points agree).
    Robust by construction: rare, scattered outliers never form the largest
    consensus set, so they do not drag the plane.
    """
    points = np.asarray(points)
    n = len(points)
    if n < 3:                                              # not enough to define a plane
        return (0.0, 0.0, float(np.median(points[:, 2])) if n else 0.0), 0.0, 0.0
    rng = np.random.default_rng(seed)
    best_inliers, best_count = None, -1
    for _ in range(iters):
        tri = points[rng.choice(n, 3, replace=False)]      # 3 random points -> candidate plane
        normal = np.cross(tri[1] - tri[0], tri[2] - tri[0])
        if abs(normal[2]) < 1e-8:                          # near-vertical triple: skip
            continue
        normal = normal / np.linalg.norm(normal)
        offset = -normal @ tri[0]
        inliers = np.abs(points @ normal + offset) < band  # points close to this plane
        if inliers.sum() > best_count:
            best_count, best_inliers = int(inliers.sum()), inliers
    if best_inliers is None:                               # all triples degenerate
        return (0.0, 0.0, float(np.percentile(points[:, 2], 20))), 90.0, 0.0
    pin = points[best_inliers]                             # least-squares refit on inliers
    a, b, c = np.linalg.lstsq(np.c_[pin[:, 0], pin[:, 1], np.ones(len(pin))],
                              pin[:, 2], rcond=None)[0]
    normal = np.array([-a, -b, 1.0]); normal /= np.linalg.norm(normal)
    tilt_deg = float(np.degrees(np.arccos(min(1.0, abs(normal[2])))))
    return (float(a), float(b), float(c)), tilt_deg, float(best_inliers.mean())


# =====================================================================
# 3. Floor-frame transform
#    Move the body into the floor frame so that z = 0 BECOMES the estimated
#    (possibly tilted) floor, for any metric that wants a flat z = 0 ground.
# =====================================================================

def to_floor_frame(skin_result: Dict, plane: Tuple[float, float, float]) -> Dict:
    """Return a copy of skin_result with vertices/joints in the floor frame.

    Subtracts the plane per vertex: z' = z - (a*x + b*y + c), so the fitted floor
    sits at z = 0 everywhere (the tilt is removed). Useful for any floor-relative
    geometric measure; coordinates that should stay in the raw world frame must
    not be passed through here.
    """
    a, b, c = plane
    out: Dict = {}
    for key in ("v", "Jtr"):
        t = skin_result[key]
        t = t.clone() if isinstance(t, torch.Tensor) else np.array(t, copy=True)
        t[..., 2] = t[..., 2] - (a * t[..., 0] + b * t[..., 1] + c)
        out[key] = t
    return out


# =====================================================================
# 4. Pointwise floor-plane geometry (signed distance + normal)
#    Same z = a*x + b*y + c convention as fit_floor_plane / to_floor_frame.
#    Used by the geometric corrector (corrector.py) to test penetration and
#    rotate feet toward the floor.
# =====================================================================

def signed_distance_to_plane(points: np.ndarray, plane: Tuple[float, float, float]) -> np.ndarray:
    """Signed VERTICAL distance of points to the floor plane z = a*x + b*y + c.

    Positive above the plane, negative below (penetrating). Consistent with
    the sign convention of :func:`to_floor_frame`.

    Args:
        points: (..., 3) array; only x = [...,0], y = [...,1], z = [...,2] used.
        plane:  (a, b, c) of z = a*x + b*y + c.

    Returns:
        (...,) array of signed vertical distances.
    """
    a, b, c = plane
    return points[..., 2] - (a * points[..., 0] + b * points[..., 1] + c)


def plane_normal(plane: Tuple[float, float, float]) -> np.ndarray:
    """Unit upward normal (3,) of the floor plane z = a*x + b*y + c."""
    a, b, c = plane
    n = np.array([-a, -b, 1.0])
    return n / np.linalg.norm(n)


__all__ = [
    "foot_vertex_masks", "fit_floor_plane", "to_floor_frame",
    "signed_distance_to_plane", "plane_normal", "RANSAC_BAND",
]
