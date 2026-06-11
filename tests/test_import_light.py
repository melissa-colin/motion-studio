"""Torch-free import smoke tests for the core boot path.

The package advertises a flask-only core install:
``import motion_studio.library``
and ``from motion_studio.server import app`` must succeed even when PyTorch is
not installed. Historically ``smpl/io.py`` pulled in
``plugins_builtin._convert``
and ``utils/motion_utils.py``, both of which imported ``torch`` at module top,
so a fresh ``pip install .`` crashed on ``import motion-studio``.

These tests simulate torch being absent by installing a meta-path finder that
makes ``import torch`` raise :class:`ImportError`, then assert the core modules
still import (and that pulling them in does not drag torch back in). They are
deliberately *not* marked ``torch`` so they run on the torch-free CI lane and on
any developer machine without torch.
"""

from __future__ import annotations

import importlib
import importlib.abc
import sys

import pytest

# Modules that must import with torch absent.
_CORE_MODULES = (
    "motion_studio.library",
    "motion_studio.bundle",
    "motion_studio.config",
    "motion_studio.smpl.io",
)


class _BlockTorchFinder(importlib.abc.MetaPathFinder):
    """A meta-path finder that makes any ``import torch`` raise ImportError."""

    def find_spec(self, name, path, target=None):  # noqa: D401, ANN001
        if name == "torch" or name.startswith("torch."):
            raise ImportError(
                "torch is blocked by _BlockTorchFinder for this test."
            )
        return None


@pytest.fixture
def torch_absent(monkeypatch: pytest.MonkeyPatch):
    """Make ``import torch`` fail and evict torch + target modules from cache.

    Yields nothing; restores ``sys.meta_path`` and ``sys.modules`` afterward via
    monkeypatch so the rest of the suite (which may legitimately use torch) is
    unaffected.
    """
    # Drop any cached torch and the core modules so they re-import cleanly under
    # the block. monkeypatch.delitem(raising=False) restores them on teardown.
    for name in list(sys.modules):
        if (
            name == "torch"
            or name.startswith("torch.")
            or name in _CORE_MODULES
        ):
            monkeypatch.delitem(sys.modules, name, raising=False)

    finder = _BlockTorchFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])
    yield


def test_torch_is_actually_blocked(torch_absent) -> None:
    """Sanity check: the fixture really does prevent importing torch."""
    with pytest.raises(ImportError):
        importlib.import_module("torch")


@pytest.mark.parametrize("module_name", _CORE_MODULES)
def test_core_module_imports_without_torch(
    torch_absent, module_name: str
) -> None:
    """Each core module imports cleanly while torch is unavailable."""
    module = importlib.import_module(module_name)
    assert module is not None
    # Importing the core boot path must not have pulled torch back in.
    assert "torch" not in sys.modules, (
        f"importing {module_name} imported torch (broke the torch-free boot)."
    )


def test_convert_zup2yup_is_pure_numpy(torch_absent) -> None:
    """``_convert.zup2yup`` runs without torch and returns numpy arrays."""
    import numpy as np

    convert = importlib.import_module("motion_studio.plugins_builtin._convert")
    poses = np.zeros((1, 3, 24, 3), dtype=np.float32)
    trans = np.ones((1, 3, 3), dtype=np.float32)
    poses_y, trans_y = convert.zup2yup(poses, trans)
    assert isinstance(poses_y, np.ndarray)
    assert isinstance(trans_y, np.ndarray)
    assert poses_y.shape == poses.shape
    assert trans_y.shape == trans.shape
    assert "torch" not in sys.modules
