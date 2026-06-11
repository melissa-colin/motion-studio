"""Public-API surface tests: ``import motion_studio as ms`` is a real library.

The package pitches itself as an importable library, not only a server. These
tests pin the promised top-level surface: the data model (:class:`Motion`,
:class:`Floor`), the bundle I/O (:func:`load_bundle`, :func:`save_bundle`), the
plugin loaders (:func:`load_corrector`, :func:`load_metrics`), the dataset
scanner (:func:`scan_dataset`), the runtime :class:`Config`, and the package
``__version__`` — all re-exported at the top level and listed in ``__all__``.

Crucially the whole surface must import **without torch**: the advertised
flask-only core install must expose the library API even when PyTorch is
absent. We assert that here too, by blocking ``import torch`` and re-importing
the package from a clean module cache.
"""

from __future__ import annotations

import importlib
import importlib.abc
import sys

import pytest

# The names the package promises at the top level (and in ``__all__``).
_EXPECTED_EXPORTS = (
    "Motion",
    "Floor",
    "load_bundle",
    "save_bundle",
    "load_corrector",
    "load_metrics",
    "scan_dataset",
    "Config",
    "__version__",
)


def test_top_level_exports_present() -> None:
    """Every promised name is reachable as ``motion_studio.<name>``."""
    import motion_studio as ms

    for name in _EXPECTED_EXPORTS:
        assert hasattr(ms, name), f"motion_studio is missing {name!r}"


def test_all_lists_the_public_surface() -> None:
    """``__all__`` exists and lists exactly the documented public names."""
    import motion_studio as ms

    assert hasattr(ms, "__all__"), "motion_studio defines no __all__"
    exported = set(ms.__all__)
    # ``__version__`` is a dunder; it need not appear in __all__, but every
    # other promised name must.
    expected = set(_EXPECTED_EXPORTS) - {"__version__"}
    missing = expected - exported
    assert not missing, f"__all__ omits public names: {sorted(missing)}"
    # Everything __all__ advertises must actually be importable.
    for name in ms.__all__:
        assert hasattr(ms, name), f"__all__ lists {name!r} but it is absent"


def test_version_is_a_nonempty_string() -> None:
    """``__version__`` is a non-empty string (read by /version, pyproject)."""
    import motion_studio as ms

    assert isinstance(ms.__version__, str)
    assert ms.__version__.strip()


def test_reexports_are_the_canonical_objects() -> None:
    """The re-exports are the same objects as their defining modules expose."""
    import motion_studio as ms
    from motion_studio.bundle import load_bundle, save_bundle
    from motion_studio.config import Config
    from motion_studio.core.plugins import load_corrector, load_metrics
    from motion_studio.core.types import Floor, Motion
    from motion_studio.library import scan_dataset

    assert ms.Motion is Motion
    assert ms.Floor is Floor
    assert ms.load_bundle is load_bundle
    assert ms.save_bundle is save_bundle
    assert ms.load_corrector is load_corrector
    assert ms.load_metrics is load_metrics
    assert ms.scan_dataset is scan_dataset
    assert ms.Config is Config


# -- torch-free guarantee ----------------------------------------------------


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
    """Block ``import torch`` and evict motion_studio from the module cache.

    Restores ``sys.meta_path`` and ``sys.modules`` on teardown via monkeypatch,
    so the rest of the suite is unaffected.
    """
    for name in list(sys.modules):
        if (
            name == "torch"
            or name.startswith("torch.")
            or name == "motion_studio"
            or name.startswith("motion_studio.")
        ):
            monkeypatch.delitem(sys.modules, name, raising=False)

    finder = _BlockTorchFinder()
    monkeypatch.setattr(sys, "meta_path", [finder, *sys.meta_path])
    yield


def test_public_surface_imports_without_torch(torch_absent) -> None:
    """``import motion_studio`` exposes the full surface with torch absent."""
    ms = importlib.import_module("motion_studio")
    for name in _EXPECTED_EXPORTS:
        assert hasattr(ms, name), f"motion_studio is missing {name!r}"
    # The library import must not have dragged torch in.
    assert "torch" not in sys.modules, (
        "importing motion_studio pulled torch in (broke the torch-free core)."
    )
