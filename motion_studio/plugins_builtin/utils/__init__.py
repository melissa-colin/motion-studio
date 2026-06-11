"""Generic SMPL / geometry helpers backing the built-in reference plugins.

Two submodules:

* :mod:`utils.motion_utils` -- rotation conversions, ``yup2zup``, SMPL FK,
  and motion-feature assembly. Keeps the raw world Z so geometric artifacts
  (foot-ground penetration / float) stay measurable.
* :mod:`utils.floor_utils` -- floor-plane geometry and estimation helpers
  (signed distance to the plane, plane normal, RANSAC ground fit on a foot
  point cloud) used by the built-in corrector and metrics.

Only ``motion_utils`` symbols are re-exported here (the pure-Python motion
helpers). Import ``floor_utils`` from its submodule directly.
"""

from .motion_utils import (  # noqa: F401
    DEFAULT_FPS,
    GDanceRawSample,
    MotionReprSpec,
    SMPL_NUM_JOINTS,
    SMPL_PARENTS,
    SMPLSkeleton,
    SUPPORTED_ENTRIES,
    align_vectors_rotation,
    assemble_motion_repr,
    axis_angle_to_6d,
    axis_angle_to_matrix,
    axis_angle_to_quaternion,
    forward_kinematics,
    global_rotation_chain,
    load_raw_gdance_pkl,
    matrix_to_axis_angle,
    matrix_to_quaternion,
    matrix_to_rotation_6d,
    preprocess_raw_pkl,
    quat_rotate,
    quaternion_apply,
    quaternion_invert,
    quaternion_multiply,
    quaternion_to_axis_angle,
    quaternion_to_matrix,
    recenter_xy,
    rotation_6d_to_axis_angle,
    rotation_6d_to_matrix,
    smpl_forward_one_person,
    smpl_mesh_fk,
    yup2zup,
)

__all__ = [
    "DEFAULT_FPS",
    "GDanceRawSample", "MotionReprSpec",
    "SMPL_NUM_JOINTS", "SMPL_PARENTS",
    "SMPLSkeleton", "SUPPORTED_ENTRIES",
    "align_vectors_rotation", "global_rotation_chain",
    "assemble_motion_repr",
    "axis_angle_to_6d", "axis_angle_to_matrix", "axis_angle_to_quaternion",
    "forward_kinematics", "load_raw_gdance_pkl",
    "matrix_to_axis_angle", "matrix_to_quaternion", "matrix_to_rotation_6d",
    "preprocess_raw_pkl",
    "quat_rotate", "quaternion_apply", "quaternion_invert",
    "quaternion_multiply", "quaternion_to_axis_angle", "quaternion_to_matrix",
    "recenter_xy",
    "rotation_6d_to_axis_angle", "rotation_6d_to_matrix",
    "smpl_forward_one_person", "smpl_mesh_fk",
    "yup2zup",
]
