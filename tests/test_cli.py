"""CLI tests: argument parsing and subcommand dispatch, no heavy work.

The ``motion-studio`` command must keep its bare/``serve`` server form working
(the live demo restarts with exactly ``motion-studio --host ... --port ...``),
and also offer headless ``correct`` / ``metrics`` subcommands plus
``--version``. These tests drive :func:`motion_studio.cli.main` with crafted
argv and **patch every heavy seam**:

* the server runner ``motion_studio.server.app.run`` (never actually binds),
* the plugin loaders ``load_corrector`` / ``load_metrics`` (never load torch),
* the motion I/O ``load_motion_pkl`` / ``save_motion_pkl`` / ``load_bundle``
  (never touch real SMPL files).

So the suite stays torch-free and starts no server. We assert the parser accepts
the documented flags and that each subcommand routes to the right seam with the
right spec.

The CLI imports its heavy helpers lazily *inside* each subcommand from
``motion_studio.core.plugins`` / ``motion_studio.smpl.io`` / ``motion_studio.
bundle``, so we patch them at those definition sites.
"""

from __future__ import annotations

import numpy as np
import pytest

from motion_studio import cli
from motion_studio import config as ms_config
from motion_studio.config import DEFAULT_CORRECTOR, DEFAULT_METRICS
from motion_studio.core.types import Floor, Motion


def _toy_motion(name: str = "toy") -> Motion:
    """Build a tiny valid Motion (1 person, 2 frames) without torch."""
    return Motion(
        poses=np.zeros((1, 2, 24, 3), dtype=np.float32),
        trans=np.zeros((1, 2, 3), dtype=np.float32),
        betas=None,
        gender="neutral",
        fps=30.0,
        name=name,
    )


class _FakeCorrector:
    """Identity corrector that records that it ran."""

    ran = False

    def correct(self, motion: Motion, log=None):  # noqa: D401, ANN001
        type(self).ran = True
        return motion


class _FakeMetrics:
    """Metrics plugin returning one constant scalar."""

    def compute(self, motion: Motion, floor: Floor):  # noqa: D401, ANN001
        return {"dummy": 1.0}


@pytest.fixture
def patch_motion_io(monkeypatch):
    """Patch ``load_motion_pkl`` / ``save_motion_pkl`` to torch-free fakes.

    Returns a dict that records the path passed to ``save_motion_pkl``.
    """
    saved = {}
    monkeypatch.setattr(
        "motion_studio.smpl.io.load_motion_pkl",
        lambda path: _toy_motion(),
        raising=False,
    )

    def _fake_save(motion, path):  # noqa: ANN001
        saved["path"] = path
        saved["motion"] = motion

    monkeypatch.setattr(
        "motion_studio.smpl.io.save_motion_pkl", _fake_save, raising=False
    )
    return saved


# -- bare / serve : the server form must keep parsing -------------------------


def test_bare_invocation_starts_server_via_run(monkeypatch) -> None:
    """No subcommand: build a Config and call ``run`` (server form)."""
    calls = {}

    def _fake_run(config, allow_remote=False):  # noqa: ANN001
        calls["config"] = config
        calls["allow_remote"] = allow_remote

    monkeypatch.setattr("motion_studio.server.app.run", _fake_run)
    rc = cli.main(["--port", "8905", "--workspace", "/tmp/ms-test-ws"])
    assert rc == 0
    assert calls, "bare invocation did not reach the server runner"
    assert calls["config"].port == 8905
    assert calls["config"].workspace == "/tmp/ms-test-ws"


def test_serve_flags_parse(monkeypatch) -> None:
    """The documented serve flags (host/port/workspace + plugins) still run."""
    monkeypatch.setattr("motion_studio.server.app.run", lambda *a, **k: None)
    rc = cli.main(
        [
            "--host",
            "127.0.0.1",
            "--port",
            "8815",
            "--workspace",
            "/tmp/ws",
            "--corrector",
            "my.mod:Mine",
            "--metrics",
            "my.mod:Score",
        ]
    )
    assert rc == 0


@pytest.mark.parametrize(
    "flag", ["--data", "--videos-dir", "--smpl-dir", "--floors-json"]
)
def test_removed_serve_data_flags_rejected(monkeypatch, flag) -> None:
    """The data-dir flags are gone from serve; argparse exits 2 on them."""
    monkeypatch.setattr(
        "motion_studio.server.app.run",
        lambda *a, **k: pytest.fail("server must not start"),
    )
    with pytest.raises(SystemExit) as exc:
        cli.main([flag, "/tmp/x"])
    assert exc.value.code == 2


def test_serve_reads_data_dirs_from_persisted_config(
    monkeypatch, tmp_path
) -> None:
    """Data dirs come only from ``workspace/config.json``, not CLI flags."""
    import json

    pkl_dir = tmp_path / "pkls"
    pkl_dir.mkdir()
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "config.json").write_text(
        json.dumps({"pkl_dir": str(pkl_dir), "smpl_dir": "/tmp/smpl"})
    )

    calls = {}
    monkeypatch.setattr(
        "motion_studio.server.app.run",
        lambda config, **k: calls.setdefault("config", config),
    )
    rc = cli.main(["--workspace", str(ws), "--port", "8816"])
    assert rc == 0
    assert calls["config"].pkl_dir == str(pkl_dir)
    assert calls["config"].smpl_dir == "/tmp/smpl"


def test_serve_subcommand_starts_server(monkeypatch, tmp_path) -> None:
    """An explicit ``serve`` subcommand routes to the server runner too."""
    calls = {}
    monkeypatch.setattr(
        "motion_studio.server.app.run",
        lambda config, **k: calls.setdefault("config", config),
    )
    # Point at a throwaway workspace so the test never reads/writes a real
    # ~/MotionStudio/config.json on the developer's machine.
    rc = cli.main(["serve", "--port", "8906", "--workspace", str(tmp_path)])
    assert rc == 0
    assert calls["config"].port == 8906


def test_non_loopback_host_without_allow_remote_refused(monkeypatch) -> None:
    """A non-loopback ``--host`` without ``--allow-remote`` exits non-zero."""
    monkeypatch.setattr(
        "motion_studio.server.app.run",
        lambda *a, **k: pytest.fail("server must not start"),
    )
    rc = cli.main(["--host", "0.0.0.0", "--port", "8907"])
    assert rc != 0


# -- persisted-config migration ----------------------------------------------


def test_load_persisted_migrates_legacy_data_dir(tmp_path) -> None:
    """A legacy ``data_dir`` migrates to ``pkl_dir`` / ``audio_dir``."""
    import json

    data_dir = tmp_path / "GDance"
    (data_dir / "motions_smpl").mkdir(parents=True)
    (data_dir / "musics").mkdir(parents=True)
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ms_config.CONFIG_FILE_NAME).write_text(
        json.dumps({"data_dir": str(data_dir)})
    )

    persisted = ms_config.load_persisted(str(ws))
    assert persisted["pkl_dir"] == str(data_dir / "motions_smpl")
    assert persisted["audio_dir"] == str(data_dir / "musics")
    # The legacy key is not itself a persisted field, so it is dropped.
    assert "data_dir" not in persisted


def test_load_persisted_legacy_data_dir_without_subdirs(tmp_path) -> None:
    """Without a ``motions_smpl/`` subdir, ``data_dir`` maps straight to pkl."""
    import json

    data_dir = tmp_path / "flat"
    data_dir.mkdir()
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ms_config.CONFIG_FILE_NAME).write_text(
        json.dumps({"data_dir": str(data_dir)})
    )

    persisted = ms_config.load_persisted(str(ws))
    assert persisted["pkl_dir"] == str(data_dir)
    assert "audio_dir" not in persisted  # no musics/ subdir


# -- --version ----------------------------------------------------------------


def test_version_flag_prints_version(monkeypatch, capsys) -> None:
    """``--version`` prints the package version and exits 0 (no server)."""
    import motion_studio as ms

    monkeypatch.setattr(
        "motion_studio.server.app.run",
        lambda *a, **k: pytest.fail("server must not start"),
    )
    # argparse's ``action="version"`` raises SystemExit(0).
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert (exc.value.code or 0) == 0
    out = capsys.readouterr()
    assert ms.__version__ in (out.out + out.err)


# -- correct <input> ----------------------------------------------------------


def test_correct_subcommand_dispatches(
    monkeypatch, tmp_path, patch_motion_io
) -> None:
    """``correct IN -o OUT`` loads, runs the corrector, writes a .pkl."""
    _FakeCorrector.ran = False
    monkeypatch.setattr(
        "motion_studio.core.plugins.load_corrector",
        lambda spec, **kw: _FakeCorrector(),
    )

    in_path = tmp_path / "in.pkl"
    in_path.write_bytes(b"")  # must exist for _collect_inputs
    out_path = tmp_path / "out.pkl"
    rc = cli.main(
        [
            "correct",
            str(in_path),
            "-o",
            str(out_path),
            "--smpl-dir",
            str(tmp_path),
        ]
    )

    assert rc == 0
    assert _FakeCorrector.ran, "the corrector's correct() was never called"
    assert patch_motion_io.get("path") == str(out_path)


def test_correct_reads_motion_bundle(
    monkeypatch, tmp_path, patch_motion_io
) -> None:
    """A ``.motion`` input is read via ``load_bundle`` (not load_motion_pkl)."""
    _FakeCorrector.ran = False

    class _Bundle:
        original = _toy_motion()
        edited = None

    monkeypatch.setattr(
        "motion_studio.bundle.load_bundle",
        lambda path: _Bundle(),
        raising=False,
    )
    monkeypatch.setattr(
        "motion_studio.core.plugins.load_corrector",
        lambda spec, **kw: _FakeCorrector(),
    )

    in_path = tmp_path / "in.motion"
    in_path.write_bytes(b"")
    rc = cli.main(
        [
            "correct",
            str(in_path),
            "-o",
            str(tmp_path / "o.pkl"),
            "--smpl-dir",
            str(tmp_path),
        ]
    )
    assert rc == 0
    assert _FakeCorrector.ran


def test_correct_subcommand_honors_corrector_spec(
    monkeypatch, tmp_path, patch_motion_io
) -> None:
    """``--corrector SPEC`` is forwarded to ``load_corrector``."""
    seen = {}

    def _fake_load(spec, **kw):  # noqa: ANN001
        seen["spec"] = spec
        return _FakeCorrector()

    monkeypatch.setattr("motion_studio.core.plugins.load_corrector", _fake_load)

    in_path = tmp_path / "in.pkl"
    in_path.write_bytes(b"")
    rc = cli.main(
        [
            "correct",
            str(in_path),
            "-o",
            str(tmp_path / "out.pkl"),
            "--corrector",
            "my.mod:MyCorrector",
            "--smpl-dir",
            str(tmp_path),
        ]
    )
    assert rc == 0
    assert seen.get("spec") == "my.mod:MyCorrector"


def test_correct_default_corrector_spec(
    monkeypatch, tmp_path, patch_motion_io
) -> None:
    """Without ``--corrector`` the built-in default spec is used."""
    seen = {}
    monkeypatch.setattr(
        "motion_studio.core.plugins.load_corrector",
        lambda spec, **kw: seen.update(spec=spec) or _FakeCorrector(),
    )

    in_path = tmp_path / "in.pkl"
    in_path.write_bytes(b"")
    cli.main(
        [
            "correct",
            str(in_path),
            "-o",
            str(tmp_path / "o.pkl"),
            "--smpl-dir",
            str(tmp_path),
        ]
    )
    assert seen.get("spec") == DEFAULT_CORRECTOR


# -- metrics <input> ----------------------------------------------------------


def test_metrics_subcommand_dispatches(monkeypatch, tmp_path, capsys) -> None:
    """``metrics IN`` loads the motion and runs the metrics plugin."""
    computed = {}

    class _RecordingMetrics:
        def compute(self, motion, floor):  # noqa: D401, ANN001
            computed["ran"] = True
            return {"dummy": 1.0}

    monkeypatch.setattr(
        "motion_studio.smpl.io.load_motion_pkl",
        lambda path: _toy_motion(),
        raising=False,
    )
    monkeypatch.setattr(
        "motion_studio.core.plugins.load_metrics",
        lambda spec, **kw: _RecordingMetrics(),
    )

    in_path = tmp_path / "in.pkl"
    in_path.write_bytes(b"")
    rc = cli.main(["metrics", str(in_path), "--smpl-dir", str(tmp_path)])
    assert rc == 0
    assert computed.get("ran"), "the metrics plugin's compute() was not called"
    # The scores are printed as JSON on stdout.
    out = capsys.readouterr().out
    assert "dummy" in out


def test_metrics_subcommand_honors_metrics_spec(monkeypatch, tmp_path) -> None:
    """``--metrics SPEC`` is forwarded to ``load_metrics``."""
    seen = {}
    monkeypatch.setattr(
        "motion_studio.smpl.io.load_motion_pkl",
        lambda path: _toy_motion(),
        raising=False,
    )

    def _fake_load(spec, **kw):  # noqa: ANN001
        seen["spec"] = spec
        return _FakeMetrics()

    monkeypatch.setattr("motion_studio.core.plugins.load_metrics", _fake_load)

    in_path = tmp_path / "in.pkl"
    in_path.write_bytes(b"")
    rc = cli.main(
        [
            "metrics",
            str(in_path),
            "--metrics",
            "my.mod:MyMetrics",
            "--smpl-dir",
            str(tmp_path),
        ]
    )
    assert rc == 0
    assert seen.get("spec") == "my.mod:MyMetrics"


def test_metrics_default_spec(monkeypatch, tmp_path) -> None:
    """Without ``--metrics`` the built-in default spec is used."""
    seen = {}
    monkeypatch.setattr(
        "motion_studio.smpl.io.load_motion_pkl",
        lambda path: _toy_motion(),
        raising=False,
    )
    monkeypatch.setattr(
        "motion_studio.core.plugins.load_metrics",
        lambda spec, **kw: seen.update(spec=spec) or _FakeMetrics(),
    )

    in_path = tmp_path / "in.pkl"
    in_path.write_bytes(b"")
    cli.main(["metrics", str(in_path), "--smpl-dir", str(tmp_path)])
    assert seen.get("spec") == DEFAULT_METRICS


# -- parser smoke -------------------------------------------------------------


def test_help_does_not_start_server(monkeypatch) -> None:
    """``--help`` prints usage and exits 0 without importing the server."""
    monkeypatch.setattr(
        "motion_studio.server.app.run",
        lambda *a, **k: pytest.fail("server must not start"),
    )
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
