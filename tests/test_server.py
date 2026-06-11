"""HTTP-contract tests for the Motion Studio Flask app.

These drive the app through ``app.test_client()`` and never reach the SMPL /
torch heavy path: the corrector and metrics plugin loaders are monkeypatched to
trivial fakes, and every assertion targets a validation/branch that returns
before any GPU work (bad names, oversized or non-finite payloads, a missing
clip, and the plain ``/workspace`` listing).

The default test-client ``Host`` is ``localhost``, so the loopback guard in
``create_app`` admits these requests without ``--allow-remote``.
"""

from __future__ import annotations

import numpy as np
import pytest

from motion_studio.config import Config
from motion_studio.core.types import Floor, Motion


class _FakeCorrector:
    """A corrector that returns the motion unchanged (identity)."""

    def correct(self, motion: Motion, log=None) -> Motion:  # noqa: D401, ANN001
        return motion


class _FakeMetrics:
    """A metrics plugin that returns one constant scalar."""

    def compute(self, motion: Motion, floor: Floor):  # noqa: D401, ANN001
        return {"dummy": 1.0}


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A test client over an app whose plugin loaders are lightweight fakes."""
    # Patch the loaders at their definition site (core.plugins) and where
    # api_motion imported them by name, so no real plugin (and no torch) loads.
    import motion_studio.core.plugins as plugins
    import motion_studio.server.api_motion as api_motion

    def _fake_load_corrector(spec, **kwargs):
        return _FakeCorrector()

    def _fake_load_metrics(spec, **kwargs):
        return _FakeMetrics()

    for mod in (plugins, api_motion):
        monkeypatch.setattr(
            mod, "load_corrector", _fake_load_corrector, raising=False
        )
        monkeypatch.setattr(
            mod, "load_metrics", _fake_load_metrics, raising=False
        )

    from motion_studio.server.app import create_app

    config = Config(workspace=str(tmp_path / "ws"))
    app = create_app(config)
    app.config.update(TESTING=True)
    return app.test_client()


def _joints_payload(n=1, t=2, j=24, fill=0.0):
    """Build a ``{N, T, J, joints}`` JSON body of constant joints."""
    joints = np.full((n, t, j, 3), fill, dtype=np.float32)
    return {"N": n, "T": t, "J": j, "joints": joints.reshape(-1).tolist()}


# -- name validation / path traversal ---------------------------------------


@pytest.mark.parametrize(
    "bad", ["../etc", "a/b", "..", ".hidden", "a b", "x" * 200, "name;rm", ""]
)
def test_path_traversal_names_rejected(client, bad) -> None:
    """Traversal / unsafe / oversized clip names are rejected with 400."""
    resp = client.get("/load", query_string={"clip": bad})
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_load_missing_clip_is_404(client) -> None:
    """A well-formed but unknown clip name resolves to a 404."""
    resp = client.get("/load", query_string={"clip": "does_not_exist"})
    assert resp.status_code == 404
    assert resp.get_json()["ok"] is False


def test_source_metrics_missing_clip_is_404(client) -> None:
    """``/source_metrics`` on an unknown clip is a clean 404, not a 500."""
    resp = client.get("/source_metrics", query_string={"clip": "ghost"})
    assert resp.status_code == 404


# -- payload-shape validation (refit/metrics) -------------------------------


def test_oversized_n_rejected(client) -> None:
    """An N above the persons ceiling is rejected before any GPU work."""
    body = _joints_payload(n=1, t=2)
    body["N"] = 9999  # declared count far above _MAX_N
    resp = client.post("/refit", json=body)
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_oversized_t_rejected(client) -> None:
    """A T above the frames ceiling is rejected with 400."""
    body = _joints_payload(n=1, t=2)
    body["T"] = 10**9
    resp = client.post("/metrics", json=body)
    assert resp.status_code == 400


def test_wrong_joint_count_rejected(client) -> None:
    """A J that is not the SMPL joint count (24) is rejected with 400."""
    body = {
        "N": 1,
        "T": 1,
        "J": 17,
        "joints": np.zeros((1, 1, 17, 3)).reshape(-1).tolist(),
    }
    resp = client.post("/refit", json=body)
    assert resp.status_code == 400


def test_oversized_iters_rejected(client) -> None:
    """An ``iters`` above the per-request ceiling is rejected with 400."""
    body = _joints_payload(n=1, t=2)
    body["iters"] = 10000
    resp = client.post("/refit", json=body)
    assert resp.status_code == 400
    assert "iters" in resp.get_json()["error"]


def test_non_finite_joints_rejected(client) -> None:
    """Joints containing NaN/Inf are rejected with 400 (not fed to refit)."""
    body = _joints_payload(n=1, t=2, fill=0.0)
    arr = np.zeros((1, 2, 24, 3), dtype=np.float32)
    arr[0, 0, 0, 0] = np.nan
    body["joints"] = arr.reshape(-1).tolist()
    resp = client.post("/refit", json=body)
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_missing_joints_field_rejected(client) -> None:
    """A payload missing the ``joints`` array is a 400, not a 500."""
    resp = client.post("/refit", json={"N": 1, "T": 1, "J": 24})
    assert resp.status_code == 400


# -- happy-path listing / host guard ----------------------------------------


def test_workspace_lists_empty(client) -> None:
    """``/workspace`` returns 200 with an empty bundle list on a fresh ws."""
    resp = client.get("/workspace")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["bundles"] == []
    assert "workspace" in body


def test_clips_empty_without_pkl_dir(client) -> None:
    """``/clips`` returns an empty list when no ``pkl_dir`` is configured."""
    resp = client.get("/clips")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["clips"] == []
    assert body["count"] == 0


def test_clips_lists_pkls_when_pkl_dir_set(client, tmp_path) -> None:
    """With ``pkl_dir`` set, ``/clips`` lists each flat ``*.pkl`` by stem."""
    pkl_dir = tmp_path / "pkls"
    pkl_dir.mkdir()
    (pkl_dir / "clipA.pkl").write_bytes(b"")
    (pkl_dir / "clipB.pkl").write_bytes(b"")
    (pkl_dir / "notes.txt").write_bytes(b"")  # ignored: not a .pkl
    client.application.config["MS_STATE"].config.pkl_dir = str(pkl_dir)

    resp = client.get("/clips")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["count"] == 2
    names = [c["name"] for c in body["clips"]]
    assert names == ["clipA", "clipB"]
    first = body["clips"][0]
    for key in (
        "name",
        "has_video",
        "has_music",
        "converted",
        "custom",
        "mtime",
        "metrics",
    ):
        assert key in first
    assert first["metrics"] is None
    assert first["has_video"] is False
    assert first["has_music"] is False


def test_get_config_returns_new_keys(client) -> None:
    """``/get_config`` exposes the three flat dirs, no legacy ``data_dir``."""
    resp = client.get("/get_config")
    assert resp.status_code == 200
    body = resp.get_json()
    for key in (
        "pkl_dir",
        "videos_dir",
        "audio_dir",
        "smpl_dir",
        "corrector_spec",
        "metrics_spec",
        "has_corrector",
        "has_metrics",
        "workspace",
    ):
        assert key in body, f"/get_config is missing {key!r}"
    assert "data_dir" not in body


def test_set_config_rejects_missing_dir(client, tmp_path) -> None:
    """A provided non-empty dir that does not exist is a 400, not a 500."""
    ghost = str(tmp_path / "does_not_exist")
    resp = client.post("/set_config", json={"pkl_dir": ghost})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_set_config_accepts_existing_pkl_dir(client, tmp_path) -> None:
    """Any existing dir is a valid ``pkl_dir`` (no ``motions_smpl/`` needed)."""
    pkl_dir = tmp_path / "flat_pkls"
    pkl_dir.mkdir()
    (pkl_dir / "clipA.pkl").write_bytes(b"")
    resp = client.post("/set_config", json={"pkl_dir": str(pkl_dir)})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True
    assert body["pkl_dir"] == str(pkl_dir)
    assert body["n_pkl"] == 1


def test_non_loopback_host_forbidden(client) -> None:
    """A non-loopback ``Host`` header is rejected with 403 by the guard."""
    resp = client.get("/workspace", headers={"Host": "evil.example.com"})
    assert resp.status_code == 403


def test_cache_traversal_is_404(client) -> None:
    """A traversal path on the cache route does not escape the cache root."""
    resp = client.get("/cache/../../etc/passwd")
    assert resp.status_code == 404
