"""Plugin contracts for auto-correction, metrics and floor, plus their loaders.

Motion Studio never imports a concrete corrector, metrics or floor
implementation directly. It loads whatever class the user points it at
(built-in or custom), as long as the class satisfies one of the
runtime-checkable protocols below. The class is (re)imported on every call, so
editing the source file takes effect on the next click without restarting the
server.

Protocol post-conditions (enforced by the server, not the type checker):
  * ``MotionCorrector.correct`` MUST return a :class:`Motion` whose ``poses``
    and ``trans`` have the *same shapes* as the input and contain only finite
    values. The server rejects (HTTP 4xx) any output that violates this.
  * ``MotionMetrics.compute`` MUST return a mapping whose keys are strings and
    whose values are real numbers; the server coerces them to ``float`` and
    drops any non-finite entry before returning them to the editor.
  * ``MotionFloor.estimate`` MUST return a :class:`Floor` (a single ground
    plane) for the given motion.

``runtime_checkable`` only checks that the method *names* exist; the loader in
this module additionally validates signatures (callable method, keyword-only
init) once at load time so a misshapen plugin fails fast with a clear message.
"""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import os
import sys
from typing import Callable, Protocol, runtime_checkable

from .types import Floor, Motion


@runtime_checkable
class MotionCorrector(Protocol):
    """Auto-correction plugin: maps a Motion to a corrected Motion.

    Post-condition (enforced by the server): ``correct`` returns a
    :class:`Motion` with the same ``poses``/``trans`` shapes as its input and
    only finite values.
    """

    def __init__(
        self, *, smpl_dir: str, floor: Floor | None = None
    ) -> None: ...

    def correct(
        self, motion: Motion, log: Callable[[str], None] = print
    ) -> Motion:
        """Return a corrected copy of ``motion`` (same array shapes)."""
        ...


@runtime_checkable
class MotionMetrics(Protocol):
    """Metrics plugin: scores a Motion against a Floor.

    Post-condition (enforced by the server): ``compute`` returns a mapping
    from ``str`` keys to real numbers. The server coerces values to ``float``
    and drops non-finite ones; keys are displayed as-is in the editor panel.
    """

    def __init__(self, *, smpl_dir: str) -> None: ...

    def compute(self, motion: Motion, floor: Floor) -> dict[str, float]:
        """Return a mapping {metric_name: value}; keys are displayed as-is."""
        ...


@runtime_checkable
class MotionFloor(Protocol):
    """Floor plugin: estimates one ground plane for a Motion.

    Post-condition (enforced by the server): ``estimate`` returns a
    :class:`Floor` whose ``plane`` is the ``(a, b, c)`` of ``z = a*x + b*y + c``
    in the z-up world frame. The built-in default fits a generic RANSAC plane
    to the lowest foot points; swap in your own via ``--floor``.
    """

    def __init__(self, *, smpl_dir: str) -> None: ...

    def estimate(self, motion: Motion) -> Floor:
        """Return the estimated ground plane for ``motion``."""
        ...


class PluginLoadError(Exception):
    """A plugin spec could not be loaded into a usable class.

    Raised for any failure while resolving ``"<module-or-path>:<Class>"`` into
    a validated class: malformed spec, missing file, an import/loader error, a
    missing class, or a class whose ``__init__``/``correct``/``compute`` does
    not match the expected contract.

    Attributes:
      spec: The offending plugin spec string.
      cause: The underlying exception, if any (also chained via ``__cause__``).
    """

    def __init__(
        self, spec: str, message: str, cause: BaseException | None = None
    ) -> None:
        self.spec = spec
        self.cause = cause
        super().__init__(f"plugin {spec!r}: {message}")


def _module_name_for(target: str) -> str:
    """Return a unique, importable module name for a file-path plugin.

    Distinct plugin files get distinct ``sys.modules`` entries so tracebacks,
    dataclasses and pickling resolve to the right module instead of all
    sharing one opaque name.

    Args:
      target: The filesystem path to the plugin ``.py`` file.

    Returns:
      A module name of the form ``_ms_plugin_<sanitized-abspath>``.
    """
    abspath = os.path.abspath(target)
    sanitized = "".join(c if c.isalnum() else "_" for c in abspath)
    return f"_ms_plugin_{sanitized}"


def _load_from_file(spec: str, target: str):
    """Exec a file-path plugin module, with its directory importable.

    The plugin file's own directory is placed at ``sys.path[0]`` for the
    duration of ``exec_module`` so the file can ``import`` sibling modules,
    then removed again to avoid polluting the import path.

    Args:
      spec: The full plugin spec (for error messages).
      target: The filesystem path to the plugin ``.py`` file.

    Returns:
      The executed module object.

    Raises:
      PluginLoadError: If the file is missing, the import machinery yields no
        loader, or executing the module fails.
    """
    if not os.path.isfile(target):
        raise PluginLoadError(spec, f"no such plugin file: {target}")
    mod_name = _module_name_for(target)
    mod_spec = importlib.util.spec_from_file_location(mod_name, target)
    if mod_spec is None or mod_spec.loader is None:
        raise PluginLoadError(
            spec,
            f"cannot build an import spec for {target} (not a Python module "
            "file?)",
        )
    module = importlib.util.module_from_spec(mod_spec)
    plugin_dir = os.path.dirname(os.path.abspath(target))
    sys.path.insert(0, plugin_dir)
    sys.modules[mod_name] = module
    try:
        mod_spec.loader.exec_module(module)
    except Exception as e:  # noqa: BLE001 - re-raised as PluginLoadError
        sys.modules.pop(mod_name, None)
        raise PluginLoadError(
            spec, f"error while importing plugin file: {e}", e
        ) from e
    finally:
        try:
            sys.path.remove(plugin_dir)
        except ValueError:
            pass
    return module


def _validate_class(spec: str, cls, *, method: str) -> None:
    """Assert ``cls`` matches the corrector/metrics contract.

    Checks that ``cls`` is a class exposing a callable ``method``
    (``correct`` or ``compute``) and that its ``__init__`` accepts its plugin
    arguments as keyword-only parameters.

    Args:
      spec: The plugin spec (for error messages).
      cls: The resolved class object.
      method: The required instance method name, ``"correct"`` or
        ``"compute"``.

    Raises:
      PluginLoadError: If ``cls`` is not a class, lacks a callable ``method``,
        or its ``__init__`` exposes the plugin args as positional parameters.
    """
    if not inspect.isclass(cls):
        raise PluginLoadError(
            spec, f"{cls!r} is not a class (got {type(cls).__name__})"
        )
    fn = getattr(cls, method, None)
    if fn is None or not callable(fn):
        raise PluginLoadError(
            spec,
            f"class {cls.__name__} has no callable {method}() method",
        )
    try:
        init_sig = inspect.signature(cls.__init__)
    except (TypeError, ValueError) as e:
        raise PluginLoadError(
            spec, f"cannot introspect {cls.__name__}.__init__: {e}", e
        ) from e
    # Every init parameter other than ``self`` (and ``*args``/``**kwargs``)
    # must be keyword-only, so the server can pass smpl_dir=/floor= by name.
    for name, param in init_sig.parameters.items():
        if name == "self":
            continue
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        if param.kind != inspect.Parameter.KEYWORD_ONLY:
            raise PluginLoadError(
                spec,
                f"{cls.__name__}.__init__ parameter {name!r} must be "
                "keyword-only "
                "(declare __init__ as 'def __init__(self, *, ...)')",
            )


def _import_class(spec: str, *, method: str):
    """Import and validate a class from a plugin spec.

    The target module is re-imported on every call so edits to a dotted-module
    plugin source take effect without restarting the server. (For file-path
    plugins the named module is re-exec'd; its imported dependencies stay
    cached.)

    Args:
      spec: A dotted module path or a filesystem path to a ``.py`` file,
        joined to the class name by a colon (e.g. ``"my_pkg.mod:MyCorrector"``
        or ``"/home/me/mine.py:MyCorrector"``).
      method: The instance method the class must expose, ``"correct"`` or
        ``"compute"``; used to validate the loaded class.

    Returns:
      The freshly imported, validated class object.

    Raises:
      PluginLoadError: If ``spec`` is malformed, the module/file cannot be
        imported, the class is absent, or the class fails contract validation.
    """
    if ":" not in spec:
        raise PluginLoadError(
            spec, 'spec must be "<module>:<Class>" or "<path.py>:<Class>"'
        )
    target, cls_name = spec.rsplit(":", 1)
    if not target or not cls_name:
        raise PluginLoadError(
            spec, 'spec must be "<module>:<Class>" or "<path.py>:<Class>"'
        )
    if target.endswith(".py") or os.path.sep in target:
        module = _load_from_file(spec, target)
    else:
        try:
            module = importlib.reload(importlib.import_module(target))
        except Exception as e:  # noqa: BLE001 - re-raised as PluginLoadError
            raise PluginLoadError(
                spec, f"cannot import module {target!r}: {e}", e
            ) from e
    try:
        cls = getattr(module, cls_name)
    except AttributeError as e:
        raise PluginLoadError(
            spec, f"module has no class {cls_name!r}", e
        ) from e
    _validate_class(spec, cls, method=method)
    return cls


def load_corrector(
    spec: str, *, smpl_dir: str, floor: Floor | None = None
) -> MotionCorrector:
    """Instantiate the corrector plugin named by ``spec``.

    Args:
      spec: The corrector plugin spec, ``"<module-or-path>:<Class>"``.
      smpl_dir: Directory containing the SMPL model files.
      floor: Optional ground plane passed to the corrector.

    Returns:
      A ready-to-use corrector instance.

    Raises:
      PluginLoadError: If ``spec`` cannot be resolved into a valid corrector
        class or the class cannot be instantiated.
    """
    cls = _import_class(spec, method="correct")
    try:
        return cls(smpl_dir=smpl_dir, floor=floor)
    except Exception as e:  # noqa: BLE001 - re-raised as PluginLoadError
        raise PluginLoadError(
            spec, f"error constructing corrector: {e}", e
        ) from e


def load_metrics(spec: str, *, smpl_dir: str) -> MotionMetrics:
    """Instantiate the metrics plugin named by ``spec``.

    Args:
      spec: The metrics plugin spec, ``"<module-or-path>:<Class>"``.
      smpl_dir: Directory containing the SMPL model files.

    Returns:
      A ready-to-use metrics instance.

    Raises:
      PluginLoadError: If ``spec`` cannot be resolved into a valid metrics
        class or the class cannot be instantiated.
    """
    cls = _import_class(spec, method="compute")
    try:
        return cls(smpl_dir=smpl_dir)
    except Exception as e:  # noqa: BLE001 - re-raised as PluginLoadError
        raise PluginLoadError(
            spec, f"error constructing metrics: {e}", e
        ) from e


def load_floor(spec: str, *, smpl_dir: str) -> MotionFloor:
    """Instantiate the floor plugin named by ``spec``.

    Args:
      spec: The floor plugin spec, ``"<module-or-path>:<Class>"``.
      smpl_dir: Directory containing the SMPL model files.

    Returns:
      A ready-to-use floor estimator instance.

    Raises:
      PluginLoadError: If ``spec`` cannot be resolved into a valid floor class
        or the class cannot be instantiated.
    """
    cls = _import_class(spec, method="estimate")
    try:
        return cls(smpl_dir=smpl_dir)
    except Exception as e:  # noqa: BLE001 - re-raised as PluginLoadError
        raise PluginLoadError(spec, f"error constructing floor: {e}", e) from e
