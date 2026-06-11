"""Shared pytest configuration for the Motion Studio test suite.

Two test markers split the heavy lanes from the torch-free core:

* ``torch``  — needs PyTorch (and usually a GPU-free CPU build).
* ``smpl``   — needs a local SMPL model directory.

``smpl``-marked tests are skipped automatically unless ``SMPL_DIR`` points at a
directory of SMPL model files, so the torch-free CI lane (and any developer
without the licensed models) can still run the full collection cleanly.
"""

from __future__ import annotations

import os

import pytest

# Register the markers here too so the suite is self-contained even if
# ``[tool.pytest.ini_options].markers`` is not present in pyproject.toml. When
# both define a marker, this registration is harmless (no duplicate warning).
_MARKERS = (
    "torch: test requires PyTorch.",
    "smpl: test requires a local SMPL model directory (env SMPL_DIR).",
)


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    for marker in _MARKERS:
        config.addinivalue_line("markers", marker)


@pytest.fixture(autouse=True)
def _isolate_default_workspace(monkeypatch, tmp_path_factory) -> None:
    """Never let a test touch a real ``~/MotionStudio``.

    A test that drives the CLI / builds a ``Config`` without an explicit
    workspace would otherwise default to ``DEFAULT_WORKSPACE``
    (``~/MotionStudio``) and could read, migrate, or overwrite the developer's
    actual ``config.json`` / bundles. Point the default at a throwaway dir for
    every test as a safety net.
    """
    ws = str(tmp_path_factory.mktemp("ms-default-ws"))
    monkeypatch.setattr(
        "motion_studio.config.DEFAULT_WORKSPACE", ws, raising=False
    )
    monkeypatch.setattr(
        "motion_studio.cli.DEFAULT_WORKSPACE", ws, raising=False
    )


@pytest.fixture(autouse=True)
def _skip_smpl_without_model_dir(request: pytest.FixtureRequest) -> None:
    """Skip ``@pytest.mark.smpl`` tests when ``SMPL_DIR`` is unset/invalid."""
    if request.node.get_closest_marker("smpl") is None:
        return
    smpl_dir = os.environ.get("SMPL_DIR")
    if not smpl_dir or not os.path.isdir(smpl_dir):
        pytest.skip("SMPL_DIR is unset or not a directory; skipping SMPL test.")
