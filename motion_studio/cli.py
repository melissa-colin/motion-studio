"""Command-line entry point for Motion Studio.

The CLI has three subcommands and a backward-compatible default:

  * ``serve`` (the default) starts the editor server. Invoking
    ``motion-studio`` with no subcommand, or with the server flags directly,
    is equivalent to ``motion-studio serve ...``. The everyday surface is the
    plugin flags; the data directories and SMPL model dir are set once from the
    UI and persisted to ``workspace/config.json``::

        motion-studio --corrector ./mine.py:Mine --metrics ./mine.py:Score \
            --floor ./mine.py:Floor --port 8815

  * ``correct`` runs the auto-correction plugin headless on one or more SMPL
    motions and writes corrected ``.pkl`` files (no server, no browser).

  * ``metrics`` runs the metrics plugin headless and prints the scores as
    JSON.

Examples:
  motion-studio --port 8815
  motion-studio --corrector ./mine.py:Mine --metrics ./mine.py:Score
  motion-studio correct clip.pkl -o clip_fixed.pkl --smpl-dir ~/smpl/models
  motion-studio correct ./bundles_dir -o ./out --corrector ./mine.py:Mine
  motion-studio metrics clip.motion --smpl-dir ~/smpl/models
"""

from __future__ import annotations

import argparse
import glob
import ipaddress
import json
import os
import sys
from collections.abc import Sequence

from . import __version__
from .config import (
    DEFAULT_CORRECTOR,
    DEFAULT_FLOOR,
    DEFAULT_METRICS,
    DEFAULT_SMPL_DIR,
    DEFAULT_WORKSPACE,
    Config,
    load_persisted,
)

# Filename extensions the headless ``correct`` / ``metrics`` commands accept as
# a single motion input (bundles, raw pkls).
_BUNDLE_EXT = ".motion"
_PKL_EXT = ".pkl"
_MOTION_INPUT_EXTS = (_BUNDLE_EXT, _PKL_EXT)


def _host_is_loopback(host: str) -> bool:
    """Return True if ``host`` binds only the local loopback interface."""
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _add_serve_args(p: argparse.ArgumentParser) -> None:
    """Attach the server (``serve``) options to a parser/subparser.

    The everyday surface is the plugin flags -- ``--corrector``, ``--metrics``,
    ``--floor`` -- plus ``--port``. The data directories (pkl / videos / audio),
    the SMPL model directory and the workspace are configured from the UI and
    persisted to ``workspace/config.json``, so they are not retyped on each
    launch. The networking flags (``--host`` / ``--allow-remote`` /
    ``--workspace``) remain available for advanced/headless use but are hidden
    from ``--help``.

    Args:
      p: The parser (top-level or the ``serve`` subparser) to populate.
    """
    p.add_argument(
        "--corrector",
        dest="corrector_spec",
        default=DEFAULT_CORRECTOR,
        help='Auto-correction plugin as "<module-or-path>:<Class>".',
    )
    p.add_argument(
        "--metrics",
        dest="metrics_spec",
        default=DEFAULT_METRICS,
        help='Metrics plugin as "<module-or-path>:<Class>".',
    )
    p.add_argument(
        "--floor",
        dest="floor_spec",
        default=DEFAULT_FLOOR,
        help='Floor (ground-plane) plugin as "<module-or-path>:<Class>".',
    )
    p.add_argument("--port", type=int, default=8815, help="TCP port.")
    # Advanced / headless: kept working but hidden from --help so the documented
    # surface stays at the three flags above. Data paths live in the UI config.
    p.add_argument(
        "--workspace",
        default=DEFAULT_WORKSPACE,
        help=argparse.SUPPRESS,
    )
    p.add_argument(
        "--host",
        default="127.0.0.1",
        help=argparse.SUPPRESS,
    )
    p.add_argument(
        "--allow-remote",
        dest="allow_remote",
        action="store_true",
        help=argparse.SUPPRESS,
    )


def _build_parser() -> argparse.ArgumentParser:
    """Return the top-level argument parser for ``motion-studio``.

    The parser owns three subcommands (``serve``, ``correct``, ``metrics``)
    and *also* carries the ``serve`` flags at the top level so the bare,
    subcommand-less invocation still launches the server (see :func:`main`).
    """
    p = argparse.ArgumentParser(
        prog="motion-studio",
        description="Multi-person SMPL motion editor with pluggable "
        "auto-correction and metrics.",
    )
    p.add_argument(
        "--version", action="version", version=f"motion-studio {__version__}"
    )

    # Top-level (default = serve) flags: kept so `motion-studio <flags>` with
    # no subcommand keeps starting the server exactly as it always has.
    _add_serve_args(p)

    sub = p.add_subparsers(dest="command", metavar="{serve,correct,metrics}")

    serve = sub.add_parser(
        "serve",
        help="Start the editor server (default).",
        description="Start the Motion Studio editor server.",
    )
    _add_serve_args(serve)

    correct = sub.add_parser(
        "correct",
        help="Run the corrector plugin headless on .pkl/.motion input(s).",
        description="Load SMPL motion(s), run the auto-correction plugin "
        "without a server, and write corrected .pkl file(s).",
    )
    correct.add_argument(
        "input",
        help="Input motion: a .pkl, a .motion bundle, or a "
        "directory of either.",
    )
    correct.add_argument(
        "-o",
        "--output",
        dest="output",
        default=None,
        help="Output .pkl path (single input) or output "
        "directory (directory input). Defaults to "
        "'<input>_corrected.pkl' / '<dir>_corrected/'.",
    )
    correct.add_argument(
        "--corrector",
        dest="corrector_spec",
        default=DEFAULT_CORRECTOR,
        help='Corrector plugin as "<module-or-path>:<Class>".',
    )
    correct.add_argument(
        "--smpl-dir",
        dest="smpl_dir",
        default=DEFAULT_SMPL_DIR,
        help="Directory of SMPL body model files.",
    )
    correct.add_argument(
        "--videos-dir",
        dest="videos_dir",
        default=None,
        help="Unused by correction; accepted for parity with the server flags.",
    )
    correct.add_argument(
        "--floor",
        dest="floor",
        default=None,
        help='Optional ground plane as "a,b,c" (z = a*x + '
        "b*y + c). Omit to let the corrector estimate "
        "it.",
    )

    metrics = sub.add_parser(
        "metrics",
        help="Run the metrics plugin headless and print JSON.",
        description="Load SMPL motion(s), run the metrics plugin without a "
        "server, and print the scores as JSON.",
    )
    metrics.add_argument(
        "input",
        help="Input motion: a .pkl, a .motion bundle, or a "
        "directory of either.",
    )
    metrics.add_argument(
        "--metrics",
        dest="metrics_spec",
        default=DEFAULT_METRICS,
        help='Metrics plugin as "<module-or-path>:<Class>".',
    )
    metrics.add_argument(
        "--smpl-dir",
        dest="smpl_dir",
        default=DEFAULT_SMPL_DIR,
        help="Directory of SMPL body model files.",
    )
    metrics.add_argument(
        "--floor",
        dest="floor",
        default=None,
        help='Optional ground plane as "a,b,c" (z = a*x + '
        "b*y + c). Defaults to z = 0.",
    )
    return p


def _serve(args: argparse.Namespace) -> int:
    """Build the config and run the server from parsed ``serve`` args.

    Args:
      args: The parsed namespace carrying the server flags.

    Returns:
      Process exit code (2 if a non-loopback host is requested without
      ``--allow-remote``).
    """
    if not _host_is_loopback(args.host) and not args.allow_remote:
        print(
            f"error: --host {args.host} is not a loopback address.\n"
            "Motion Studio has no authentication and can execute code from "
            "uploaded files, so it binds loopback only by default.\n"
            "Re-run with --allow-remote if you understand the risk and intend "
            "to expose it on the network.",
            file=sys.stderr,
        )
        return 2
    if not _host_is_loopback(args.host):
        print(
            f"WARNING: binding {args.host} exposes a no-auth API (file "
            "upload can run "
            "code) to every host that can reach this port. Use a firewall / "
            "trusted network only.",
            file=sys.stderr,
        )
    # The data directories (pkl / videos / audio), the SMPL model dir and the
    # plugin specs live in workspace/config.json and are edited from the UI. An
    # explicit CLI flag for a plugin still wins; everything else comes from the
    # saved config, else the built-in default. This is what lets a bare
    # ``motion-studio`` reuse the last session's data instead of any flags.
    saved = load_persisted(args.workspace)

    def _pick(arg_val, key, default):
        if arg_val is not None and arg_val != default:
            return arg_val
        if saved.get(key):
            return saved[key]
        return arg_val if arg_val is not None else default

    config = Config(
        workspace=args.workspace,
        pkl_dir=saved.get("pkl_dir"),
        videos_dir=saved.get("videos_dir"),
        audio_dir=saved.get("audio_dir"),
        smpl_dir=saved.get("smpl_dir") or DEFAULT_SMPL_DIR,
        corrector_spec=_pick(
            args.corrector_spec, "corrector_spec", DEFAULT_CORRECTOR
        ),
        metrics_spec=_pick(args.metrics_spec, "metrics_spec", DEFAULT_METRICS),
        floor_spec=_pick(args.floor_spec, "floor_spec", DEFAULT_FLOOR),
        floors_json=saved.get("floors_json"),
        host=args.host,
        port=args.port,
    )
    config.ensure_dirs()
    config.save()
    # Imported lazily so --help / non-serve subcommands work without the heavy
    # server stack.
    from .server.app import run

    run(config, allow_remote=args.allow_remote)
    return 0


def _parse_floor(spec: str | None):
    """Parse a ``"a,b,c"`` floor spec into a :class:`Floor`, or None.

    Args:
      spec: A ``"a,b,c"`` string, or None.

    Returns:
      A ``Floor`` instance, or None if ``spec`` is None/empty.

    Raises:
      ValueError: If ``spec`` is not three comma-separated numbers.
    """
    if not spec:
        return None
    from .core.types import Floor

    parts = spec.split(",")
    if len(parts) != 3:
        raise ValueError(
            f'floor must be three comma-separated numbers "a,b,c", got {spec!r}'
        )
    return Floor(plane=tuple(float(x) for x in parts))


def _load_motion(path: str):
    """Load one motion from a ``.pkl`` or ``.motion`` file.

    The loaders are reached through their module (``smpl.io`` / ``bundle``)
    rather than bound names so a caller/test can monkeypatch them.

    Args:
      path: Path to a raw SMPL ``.pkl`` or a ``.motion`` bundle.

    Returns:
      The loaded :class:`Motion` (the edited variant of a bundle when present,
      else the original).

    Raises:
      ValueError: If the file extension is not ``.pkl`` or ``.motion``.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext == _PKL_EXT:
        from .smpl import io as smpl_io

        return smpl_io.load_motion_pkl(path)
    if ext == _BUNDLE_EXT:
        from . import bundle

        b = bundle.load_bundle(path)
        return b.edited if b.edited is not None else b.original
    raise ValueError(
        f"unsupported input {path!r}: expected a .pkl or .motion file"
    )


def _save_corrected(original, fixed, dst: str) -> None:
    """Write the corrected motion to ``dst``, choosing the writer by extension.

    A ``.motion`` destination is written as a fresh bundle (``original`` as the
    original, ``fixed`` as the edited session); anything else is written as a
    raw SMPL ``.pkl``. The writers are reached through their module so tests
    can monkeypatch them.

    Args:
      original: The input :class:`Motion` (stored as the bundle's original).
      fixed: The corrected :class:`Motion` to persist.
      dst: Destination path (``.motion`` -> bundle, else ``.pkl``).
    """
    if os.path.splitext(dst)[1].lower() == _BUNDLE_EXT:
        from . import bundle

        bundle.save_bundle(dst, original=original, edited=fixed)
    else:
        from .smpl import io as smpl_io

        smpl_io.save_motion_pkl(fixed, dst)


def _collect_inputs(path: str) -> list[str]:
    """Return the list of motion files named by ``path``.

    Args:
      path: A single ``.pkl``/``.motion`` file, or a directory containing
        either.

    Returns:
      Sorted list of motion file paths.

    Raises:
      FileNotFoundError: If ``path`` does not exist.
      ValueError: If a directory holds no ``.pkl``/``.motion`` files, or a file
        has an unsupported extension.
    """
    if os.path.isdir(path):
        found: list[str] = []
        for ext in _MOTION_INPUT_EXTS:
            found.extend(glob.glob(os.path.join(path, "*" + ext)))
        if not found:
            raise ValueError(
                f"no .pkl or .motion files under directory {path!r}"
            )
        return sorted(found)
    if os.path.isfile(path):
        ext = os.path.splitext(path)[1].lower()
        if ext not in _MOTION_INPUT_EXTS:
            raise ValueError(
                f"unsupported input {path!r}: expected a .pkl or .motion file"
            )
        return [path]
    raise FileNotFoundError(f"no such input: {path!r}")


def _correct(args: argparse.Namespace) -> int:
    """Run the corrector plugin headless and write corrected ``.pkl``(s).

    A single file input writes one corrected ``.pkl`` (to ``-o`` or
    ``<stem>_corrected.pkl``). A directory input writes one corrected
    ``<name>_corrected.pkl`` per motion into ``-o`` (or ``<dir>_corrected/``).

    Args:
      args: The parsed ``correct`` namespace.

    Returns:
      Process exit code (0 on success, 1 on a load/plugin/IO error).
    """
    # Reached through the module so the loader can be monkeypatched in tests.
    from .core import plugins

    try:
        floor = _parse_floor(args.floor)
        inputs = _collect_inputs(args.input)
    except (ValueError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    is_dir = os.path.isdir(args.input)
    out_dir = None
    out_path = None
    if is_dir:
        out_dir = args.output or (args.input.rstrip(os.sep) + "_corrected")
        os.makedirs(out_dir, exist_ok=True)
    elif args.output:
        out_path = args.output
    else:
        stem = os.path.splitext(args.input)[0]
        out_path = stem + "_corrected" + _PKL_EXT

    try:
        corrector = plugins.load_corrector(
            args.corrector_spec, smpl_dir=args.smpl_dir, floor=floor
        )
    except plugins.PluginLoadError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    for src in inputs:
        try:
            motion = _load_motion(src)
            fixed = corrector.correct(
                motion, log=lambda m: print(m, file=sys.stderr)
            )
        except Exception as e:  # noqa: BLE001 - surfaced as a CLI error
            print(f"error: failed to correct {src!r}: {e}", file=sys.stderr)
            return 1
        if is_dir:
            name = os.path.splitext(os.path.basename(src))[0]
            dst = os.path.join(out_dir, name + "_corrected" + _PKL_EXT)
        else:
            dst = out_path
        try:
            _save_corrected(motion, fixed, dst)
        except Exception as e:  # noqa: BLE001 - surfaced as a CLI error
            print(f"error: failed to write {dst!r}: {e}", file=sys.stderr)
            return 1
        print(f"wrote {dst}")
    return 0


def _metrics(args: argparse.Namespace) -> int:
    """Run the metrics plugin headless and print the scores as JSON.

    A single input prints one ``{metric: value}`` object. A directory prints a
    ``{clip_name: {metric: value}}`` object covering every motion found.

    Args:
      args: The parsed ``metrics`` namespace.

    Returns:
      Process exit code (0 on success, 1 on a load/plugin/IO error).
    """
    # Reached through the module so the loader can be monkeypatched in tests.
    from .core import plugins
    from .core.types import Floor

    try:
        floor = _parse_floor(args.floor) or Floor(plane=(0.0, 0.0, 0.0))
        inputs = _collect_inputs(args.input)
    except (ValueError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        plugin = plugins.load_metrics(args.metrics_spec, smpl_dir=args.smpl_dir)
    except plugins.PluginLoadError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    is_dir = os.path.isdir(args.input)
    results = {}
    for src in inputs:
        try:
            motion = _load_motion(src)
            scores = plugin.compute(motion, floor)
        except Exception as e:  # noqa: BLE001 - surfaced as a CLI error
            print(f"error: failed to score {src!r}: {e}", file=sys.stderr)
            return 1
        clean = {str(k): float(v) for k, v in dict(scores).items()}
        if is_dir:
            results[os.path.splitext(os.path.basename(src))[0]] = clean
        else:
            results = clean
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and dispatch to the selected subcommand.

    With no subcommand (or with the server flags given directly), the server
    is started, preserving the historical ``motion-studio <flags>`` launch.

    Args:
      argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
      Process exit code.
    """
    args = _build_parser().parse_args(argv)
    command = getattr(args, "command", None)
    if command in (None, "serve"):
        return _serve(args)
    if command == "correct":
        return _correct(args)
    if command == "metrics":
        return _metrics(args)
    # argparse restricts choices, so this is unreachable in practice.
    print(f"error: unknown command {command!r}", file=sys.stderr)
    return 2
