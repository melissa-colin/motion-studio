"""Torch-free tests for the plugin loader in ``motion_studio.core.plugins``.

Covers ``_import_class`` resolution from both a dotted-module spec and a
``/path/file.py:Class`` spec, the ``load_corrector``/``load_metrics`` factories,
the ``PluginLoadError`` contract (bad spec, missing class, missing file, bad
separator), sibling-module imports from a file-path plugin, and the class-shape
validation done once at load time. No torch.
"""

from __future__ import annotations

import sys
import textwrap

import pytest

from motion_studio.core import plugins

# A tiny self-contained plugin module: a corrector and a metrics class that
# match the protocol constructor signatures (keyword-only ``__init__``) without
# importing torch/SMPL.
_PLUGIN_SOURCE = textwrap.dedent(
    '''
    """Throwaway plugin used by the loader tests."""


    class TinyCorrector:
        def __init__(self, *, smpl_dir, floor=None):
            self.smpl_dir = smpl_dir
            self.floor = floor

        def correct(self, motion, log=print):
            return motion


    class TinyMetrics:
        def __init__(self, *, smpl_dir):
            self.smpl_dir = smpl_dir

        def compute(self, motion, floor):
            return {"dummy": 0.0}
    '''
)


@pytest.fixture()
def plugin_file(tmp_path):
    """Write the throwaway plugin to a temp .py file; return its path."""
    path = tmp_path / "tiny_plugin.py"
    path.write_text(_PLUGIN_SOURCE)
    return str(path)


@pytest.fixture()
def dotted_plugin(tmp_path):
    """Make the throwaway plugin importable as a dotted module.

    Writes it under a unique package directory placed on ``sys.path``, and
    yields the importable ``module:Class`` prefix (sans class name). The
    directory is removed from ``sys.path`` on teardown.
    """
    pkg_dir = tmp_path / "dotted_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "dotted_plugin_mod.py").write_text(_PLUGIN_SOURCE)
    sys.path.insert(0, str(pkg_dir))
    try:
        yield "dotted_plugin_mod"
    finally:
        try:
            sys.path.remove(str(pkg_dir))
        except ValueError:
            pass
        sys.modules.pop("dotted_plugin_mod", None)


def test_import_class_from_dotted_module(dotted_plugin: str) -> None:
    """A "module:Class" spec resolves to the live class object."""
    cls = plugins._import_class(
        f"{dotted_plugin}:TinyCorrector", method="correct"
    )
    assert cls.__name__ == "TinyCorrector"


def test_import_class_from_file_path(plugin_file: str) -> None:
    """A "/path/file.py:Class" spec loads and returns the class."""
    cls = plugins._import_class(
        f"{plugin_file}:TinyCorrector", method="correct"
    )
    assert cls.__name__ == "TinyCorrector"
    instance = cls(smpl_dir="/nonexistent")
    assert instance.smpl_dir == "/nonexistent"


def test_load_corrector_instantiates(plugin_file: str) -> None:
    """``load_corrector`` builds the class with smpl_dir + floor kwargs."""
    corrector = plugins.load_corrector(
        f"{plugin_file}:TinyCorrector", smpl_dir="/smpl", floor=None
    )
    assert corrector.smpl_dir == "/smpl"
    assert corrector.floor is None
    # The instance honours the corrector protocol.
    assert isinstance(corrector, plugins.MotionCorrector)


def test_load_metrics_instantiates(plugin_file: str) -> None:
    """``load_metrics`` builds the metrics class with the smpl_dir kwarg."""
    metrics = plugins.load_metrics(
        f"{plugin_file}:TinyMetrics", smpl_dir="/smpl"
    )
    assert metrics.smpl_dir == "/smpl"
    assert metrics.compute(None, None) == {"dummy": 0.0}
    assert isinstance(metrics, plugins.MotionMetrics)


# --- PluginLoadError contract -----------------------------------------------


def test_bad_spec_without_colon_raises() -> None:
    """A spec missing the ``:Class`` suffix is rejected up front."""
    with pytest.raises(plugins.PluginLoadError) as excinfo:
        plugins._import_class("collections.OrderedDict", method="correct")
    # The error names the offending spec so the message is actionable.
    assert "collections.OrderedDict" in str(excinfo.value)


def test_missing_class_raises_clear_error(plugin_file: str) -> None:
    """Resolving an absent class name surfaces a clear, spec-naming error."""
    spec = f"{plugin_file}:DoesNotExist"
    with pytest.raises(plugins.PluginLoadError) as excinfo:
        plugins._import_class(spec, method="correct")
    # The message should name the missing class so the user can fix the spec.
    assert "DoesNotExist" in str(excinfo.value)


def test_bad_separator_spec_raises_plugin_load_error() -> None:
    """A separator-but-not-.py spec yields a clear ``PluginLoadError``.

    ``foo/bar:Class`` looks like a path spec (it has a separator) but is not a
    ``.py`` file; a naive loader blows up with an opaque ``AttributeError``.
    The loader must instead raise ``PluginLoadError`` and name the spec.
    """
    spec = "no_such_dir/not_a_module:Whatever"
    with pytest.raises(plugins.PluginLoadError) as excinfo:
        plugins._import_class(spec, method="correct")
    assert spec in str(excinfo.value)


def test_missing_file_path_raises_plugin_load_error(tmp_path) -> None:
    """A file-path spec pointing at a nonexistent .py file fails clearly."""
    spec = "%s:Whatever" % (tmp_path / "absent_plugin.py")
    with pytest.raises(plugins.PluginLoadError) as excinfo:
        plugins._import_class(spec, method="correct")
    assert "absent_plugin.py" in str(excinfo.value)


# --- Sibling-module import from a file-path plugin --------------------------


def test_file_path_plugin_imports_sibling_module(tmp_path) -> None:
    """A file-path plugin can ``import`` a sibling module next to it.

    The loader must put the plugin's own directory on ``sys.path`` while it
    executes, so a plugin split across several files in one folder loads
    without a ``ModuleNotFoundError`` — and must clean that entry up after.
    """
    pkg_dir = tmp_path / "plugin_pkg"
    pkg_dir.mkdir()
    # A sibling helper the main plugin file imports by bare module name.
    (pkg_dir / "helper.py").write_text(
        textwrap.dedent(
            '''
            """Sibling helper imported by the main plugin file."""

            ANSWER = 42
            '''
        )
    )
    (pkg_dir / "main_plugin.py").write_text(
        textwrap.dedent(
            '''
            """Main plugin that imports a sibling module by bare name."""

            import helper


            class SiblingCorrector:
                def __init__(self, *, smpl_dir, floor=None):
                    self.smpl_dir = smpl_dir
                    self.floor = floor
                    self.answer = helper.ANSWER

                def correct(self, motion, log=print):
                    return motion
            '''
        )
    )
    spec = "%s:SiblingCorrector" % (pkg_dir / "main_plugin.py")
    cls = plugins._import_class(spec, method="correct")
    instance = cls(smpl_dir="/smpl")
    assert instance.answer == 42
    # The loader must not leak the plugin dir into ``sys.path`` afterwards.
    assert str(pkg_dir) not in sys.path


# --- Class-shape validation at load time ------------------------------------

# A class shaped like neither protocol: no ``correct`` and no ``compute``.
_SHAPELESS_SOURCE = textwrap.dedent(
    '''
    """A class that satisfies neither plugin protocol."""


    class NotAPlugin:
        def __init__(self, *, smpl_dir, floor=None):
            self.smpl_dir = smpl_dir

        def something_else(self):
            return None
    '''
)

# A class whose ``__init__`` takes positional (not keyword-only) plugin args,
# which the server cannot call with smpl_dir=/floor= by name.
_POSITIONAL_INIT_SOURCE = textwrap.dedent(
    '''
    """A corrector whose init args are positional, violating the contract."""


    class PositionalCorrector:
        def __init__(self, smpl_dir, floor=None):
            self.smpl_dir = smpl_dir

        def correct(self, motion, log=print):
            return motion
    '''
)


def test_load_corrector_validates_missing_method(tmp_path) -> None:
    """A corrector class missing ``correct`` is rejected at load time."""
    path = tmp_path / "shapeless.py"
    path.write_text(_SHAPELESS_SOURCE)
    with pytest.raises(plugins.PluginLoadError) as excinfo:
        plugins.load_corrector(
            f"{path}:NotAPlugin", smpl_dir="/smpl", floor=None
        )
    assert "correct" in str(excinfo.value)


def test_load_metrics_validates_missing_method(tmp_path) -> None:
    """A metrics class missing ``compute`` is rejected at load time."""
    path = tmp_path / "shapeless_metrics.py"
    path.write_text(_SHAPELESS_SOURCE)
    with pytest.raises(plugins.PluginLoadError) as excinfo:
        plugins.load_metrics(f"{path}:NotAPlugin", smpl_dir="/smpl")
    assert "compute" in str(excinfo.value)


def test_load_corrector_validates_positional_init(tmp_path) -> None:
    """A corrector with positional ``__init__`` args is rejected."""
    path = tmp_path / "positional.py"
    path.write_text(_POSITIONAL_INIT_SOURCE)
    with pytest.raises(plugins.PluginLoadError) as excinfo:
        plugins.load_corrector(
            f"{path}:PositionalCorrector", smpl_dir="/smpl", floor=None
        )
    assert "keyword-only" in str(excinfo.value)


def test_non_class_target_rejected(tmp_path) -> None:
    """Pointing the spec at a non-class object fails validation."""
    path = tmp_path / "not_a_class.py"
    path.write_text("not_a_class = 123\n")
    with pytest.raises(plugins.PluginLoadError) as excinfo:
        plugins._import_class(f"{path}:not_a_class", method="correct")
    assert "not a class" in str(excinfo.value)
