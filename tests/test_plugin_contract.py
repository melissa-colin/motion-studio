"""End-to-end contract tests for the shipped example plugins.

Loads the dependency-light ``examples/`` plugins through the public loader on a
small synthetic :class:`~motion_studio.core.types.Motion` and asserts the plugin
contract that is testable without torch/SMPL:

* the identity corrector returns an *equal* Motion (same shapes, same values);
* ``simple_metrics`` returns a ``{str: float}`` mapping of finite values with at
  least one custom key.

Both example plugins are torch-free by construction (see §3.1 of the
improvement plan). If they have not been shipped yet, the whole module skips.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pytest

from motion_studio.core import plugins
from motion_studio.core.types import Floor, Motion

# ``examples/`` lives at the repo root, i.e. two levels up from this package
# (``motion_studio/core/types.py`` -> repo root). Resolve it from the imported
# package so the test works from an editable install or a checkout.
_REPO_ROOT = pathlib.Path(plugins.__file__).resolve().parent.parent.parent
_EXAMPLES_DIR = _REPO_ROOT / "examples"
_IDENTITY_PLUGIN = _EXAMPLES_DIR / "identity_corrector.py"
_METRICS_PLUGIN = _EXAMPLES_DIR / "simple_metrics.py"

pytestmark = pytest.mark.skipif(
    not (_IDENTITY_PLUGIN.exists() and _METRICS_PLUGIN.exists()),
    reason="example plugins not shipped yet (examples/identity_corrector.py, "
    "examples/simple_metrics.py).",
)


def _class_in(path: pathlib.Path, *candidates: str) -> str:
    """Return ``"<path>:<Class>"`` for the first class name found in ``path``.

    The exact class name in the shipped examples is not pinned by the test, so
    we accept a few plausible names and otherwise fall back to the first
    top-level ``class`` declaration in the file.
    """
    source = path.read_text()
    for name in candidates:
        if (f"class {name}") in source:
            return f"{path}:{name}"
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("class "):
            name = stripped[len("class ") :].split("(")[0].split(":")[0].strip()
            return f"{path}:{name}"
    raise AssertionError(f"no top-level class found in {path}")


@pytest.fixture()
def motion() -> Motion:
    """A tiny but well-formed 2-person, 4-frame synthetic Motion."""
    rng = np.random.default_rng(0)
    n_persons, n_frames = 2, 4
    poses = rng.standard_normal((n_persons, n_frames, 24, 3)).astype(np.float64)
    trans = rng.standard_normal((n_persons, n_frames, 3)).astype(np.float64)
    betas = np.zeros((n_persons, 10), dtype=np.float64)
    return Motion(
        poses=poses,
        trans=trans,
        betas=betas,
        gender="neutral",
        fps=30.0,
        name="synthetic",
    )


@pytest.fixture()
def floor() -> Floor:
    """A flat z=0 ground plane."""
    return Floor(plane=(0.0, 0.0, 0.0))


def test_identity_corrector_returns_equal_motion(motion: Motion) -> None:
    """The identity corrector returns a Motion equal to its input."""
    spec = _class_in(
        _IDENTITY_PLUGIN, "IdentityCorrector", "Identity", "NoOpCorrector"
    )
    corrector = plugins.load_corrector(spec, smpl_dir="/unused", floor=None)
    out = corrector.correct(motion)

    # Output-validation contract: right type and identical array shapes.
    assert isinstance(out, Motion)
    assert out.poses.shape == motion.poses.shape
    assert out.trans.shape == motion.trans.shape
    assert out.n_persons == motion.n_persons
    assert out.n_frames == motion.n_frames

    # Identity: values are unchanged and finite.
    np.testing.assert_array_equal(out.poses, motion.poses)
    np.testing.assert_array_equal(out.trans, motion.trans)
    assert np.isfinite(out.poses).all()
    assert np.isfinite(out.trans).all()


def test_identity_corrector_does_not_mutate_input(motion: Motion) -> None:
    """Correcting must not corrupt the caller's arrays in place."""
    spec = _class_in(
        _IDENTITY_PLUGIN, "IdentityCorrector", "Identity", "NoOpCorrector"
    )
    poses_before = motion.poses.copy()
    trans_before = motion.trans.copy()
    corrector = plugins.load_corrector(spec, smpl_dir="/unused", floor=None)
    corrector.correct(motion)
    np.testing.assert_array_equal(motion.poses, poses_before)
    np.testing.assert_array_equal(motion.trans, trans_before)


def test_simple_metrics_returns_finite_str_float_dict(
    motion: Motion, floor: Floor
) -> None:
    """``simple_metrics`` returns a ``{str: float}`` of finite values."""
    spec = _class_in(_METRICS_PLUGIN, "SimpleMetrics", "Metrics")
    metrics = plugins.load_metrics(spec, smpl_dir="/unused")
    result = metrics.compute(motion, floor)

    assert isinstance(result, dict)
    assert result, "metrics plugin returned an empty mapping"
    for key, value in result.items():
        assert isinstance(key, str), f"metric key {key!r} is not a str"
        # Coercible to float and finite — the documented post-condition.
        coerced = float(value)
        assert math.isfinite(coerced), (
            f"metric {key!r} is not finite: {value!r}"
        )


def test_simple_metrics_has_a_custom_key(motion: Motion, floor: Floor) -> None:
    """The example exercises arbitrary keys: at least one beyond the core set.

    The shared metrics contract renders arbitrary keys; the example must show
    this off with at least one key outside the seven well-known names.
    """
    known = {
        "float",
        "penetrate",
        "skate",
        "pfc",
        "jitter",
        "self_pen",
        "inter_pen",
    }
    spec = _class_in(_METRICS_PLUGIN, "SimpleMetrics", "Metrics")
    metrics = plugins.load_metrics(spec, smpl_dir="/unused")
    result = metrics.compute(motion, floor)
    extra = set(result) - known
    assert extra, (
        "simple_metrics should return at least one custom key outside the "
        f"known set; got keys {sorted(result)!r}"
    )
