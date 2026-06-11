"""Shared HTTP helpers for the Motion Studio API blueprints.

Small utilities used across the route modules: CORS, JSON/binary responses,
clip/name validation, and turning a ``{N,T,J,joints}`` payload into the array
the refit/metrics code expects.
"""

from __future__ import annotations

import re

import numpy as np
from flask import Response, current_app, jsonify

from .state import ServerState, _is_safe_name

# Headers the browser frontend reads off binary responses.
_EXPOSE = (
    "Content-Disposition, X-Faces-Shape, X-Mesh-Shape, X-Mesh-Time, "
    "X-Refit-Shape, X-Refit-Frames, X-Refit-Err, X-Refit-Time, "
    "X-Metrics"
)

# Upper bounds on edited-joint payload shapes, enforced before any heavy work
# (refit / FK) is scheduled. They cap a trivial denial-of-service where a tiny
# JSON body inflates into a huge GPU allocation. SMPL motions always have
# exactly 24 joints, so ``J`` is an equality, not a ceiling.
_MAX_N = 64  # persons
_MAX_T = 20000  # frames
_SMPL_J = 24  # SMPL joint count (must match smpl.refit.NUM_J)

# A clip/bundle name must be a single plain filename component. The cap and the
# explicit character class reject path traversal, backslashes, NUL/control
# bytes, and absurdly long names that ``_is_safe_name`` alone would let through.
_MAX_NAME_LEN = 128
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def state() -> ServerState:
    """Return the :class:`ServerState` attached to the current app."""
    return current_app.config["MS_STATE"]


def add_cors(resp: Response) -> Response:
    """Expose the binary response headers the frontend reads.

    The frontend is served same-origin from this same app, so no
    ``Access-Control-Allow-*`` grant is needed (and emitting a wildcard one on
    a no-auth, state-mutating API would let any web page drive it). We only set
    ``Access-Control-Expose-Headers`` so the same-origin JavaScript can read the
    custom ``X-*`` headers off octet-stream responses.
    """
    resp.headers["Access-Control-Expose-Headers"] = _EXPOSE
    return resp


def json_error(msg: str, code: int = 400) -> tuple[Response, int]:
    """Return a ``({"ok": False, "error": msg}, code)`` JSON error tuple."""
    return jsonify({"ok": False, "error": msg}), code


def binary(body: bytes, headers: dict[str, str]) -> Response:
    """Return an ``application/octet-stream`` response with ``headers``."""
    resp = Response(body, mimetype="application/octet-stream")
    for k, v in headers.items():
        resp.headers[k] = v
    return resp


def check_name(name: str | None) -> tuple[str | None, str | None]:
    """Validate a clip/bundle name parameter.

    Args:
      name: The candidate name (e.g. from query string).

    Returns:
      ``(name, None)`` if valid, else ``(None, error_message)``.
    """
    if not name:
        return None, "missing 'clip'/'name' parameter"
    if len(name) > _MAX_NAME_LEN or not _SAFE_NAME_RE.match(name):
        return None, "invalid name (allowed: A-Z a-z 0-9 . _ -, <=128 chars)"
    # Belt-and-braces: also honor the shared traversal check in state.py.
    if not _is_safe_name(name):
        return None, "invalid name (no '/', '..', or leading '.')"
    return name, None


def joints_from_payload(payload: dict) -> np.ndarray:
    """Parse ``{N, T, J, joints}`` into an ``(N, T, J, 3)`` float32 array.

    The declared shape is validated and clamped *before* the array is built, so
    an oversized or malformed request is rejected without allocating GPU memory
    or scheduling a refit. All callers wrap this in ``try`` and surface a
    :func:`json_error` (HTTP 400) on the exceptions below.

    Args:
      payload: The decoded JSON request body.

    Returns:
      The reshaped ``(N, T, 24, 3)`` array.

    Raises:
      KeyError: If ``N``, ``T``, ``J`` or ``joints`` is missing.
      ValueError: If a field is non-integer, a shape exceeds its bound, ``J``
        is not the SMPL joint count, or any value is NaN/Inf.
    """
    n = int(payload["N"])
    t = int(payload["T"])
    j = int(payload["J"])
    if n < 1 or n > _MAX_N:
        raise ValueError("N=%d out of range [1, %d]" % (n, _MAX_N))
    if t < 1 or t > _MAX_T:
        raise ValueError("T=%d out of range [1, %d]" % (t, _MAX_T))
    if j != _SMPL_J:
        raise ValueError(
            "J=%d must be the SMPL joint count (%d)" % (j, _SMPL_J)
        )
    joints = np.asarray(payload["joints"], dtype=np.float32).reshape(n, t, j, 3)
    if not np.isfinite(joints).all():
        raise ValueError("joints contain NaN/Inf")
    return joints
