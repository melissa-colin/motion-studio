"""Info/health/version endpoint tests over the Flask test client.

These three read-only routes let an operator (or the UI) confirm the server is
up, learn its version, and see which plugins and workspace are active:

* ``GET /health``  -> ``{"ok": true}``
* ``GET /version`` -> ``{"version": <__version__>}``
* ``GET /info``    -> includes ``corrector_spec``, ``metrics_spec``,
  ``workspace`` (so the UI can surface the active plugins).

They must not touch the SMPL/torch heavy path, so the plugin loaders are
monkeypatched to trivial fakes. The default test-client ``Host`` is
``localhost``, which the loopback guard admits without ``--allow-remote``.
"""

from __future__ import annotations

import pytest

import motion_studio as ms
from motion_studio.config import Config
from motion_studio.core.types import Floor, Motion


class _FakeCorrector:
    """Identity corrector (never loads torch)."""

    def correct(self, motion: Motion, log=None):  # noqa: D401, ANN001
        return motion


class _FakeMetrics:
    """Constant metrics plugin (never loads torch)."""

    def compute(self, motion: Motion, floor: Floor):  # noqa: D401, ANN001
        return {"dummy": 1.0}


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A test client whose plugin loaders are lightweight fakes."""
    import motion_studio.core.plugins as plugins

    monkeypatch.setattr(
        plugins,
        "load_corrector",
        lambda spec, **kw: _FakeCorrector(),
        raising=False,
    )
    monkeypatch.setattr(
        plugins,
        "load_metrics",
        lambda spec, **kw: _FakeMetrics(),
        raising=False,
    )

    try:
        import motion_studio.server.api_motion as api_motion

        monkeypatch.setattr(
            api_motion,
            "load_corrector",
            lambda spec, **kw: _FakeCorrector(),
            raising=False,
        )
        monkeypatch.setattr(
            api_motion,
            "load_metrics",
            lambda spec, **kw: _FakeMetrics(),
            raising=False,
        )
    except ImportError:
        pass

    from motion_studio.server.app import create_app

    config = Config(
        workspace=str(tmp_path / "ws"),
        corrector_spec="pkg.mod:MyCorrector",
        metrics_spec="pkg.mod:MyMetrics",
    )
    app = create_app(config)
    app.config.update(TESTING=True)
    return app.test_client()


def test_health_ok(client) -> None:
    """``/health`` returns 200 and ``{"ok": true}``."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True


def test_version_matches_package(client) -> None:
    """``/version`` reports the package ``__version__``."""
    resp = client.get("/version")
    assert resp.status_code == 200
    assert resp.get_json()["version"] == ms.__version__


def test_info_reports_plugins_and_workspace(client, tmp_path) -> None:
    """``/info`` surfaces the active corrector/metrics specs and workspace."""
    resp = client.get("/info")
    assert resp.status_code == 200
    body = resp.get_json()
    for key in ("corrector_spec", "metrics_spec", "workspace"):
        assert key in body, f"/info is missing {key!r}"
    assert body["corrector_spec"] == "pkg.mod:MyCorrector"
    assert body["metrics_spec"] == "pkg.mod:MyMetrics"
    assert str(tmp_path / "ws") in body["workspace"]


def test_info_routes_are_get_only_safe(client) -> None:
    """The info routes are read-only: they never 500 on a fresh workspace."""
    for route in ("/health", "/version", "/info"):
        resp = client.get(route)
        assert resp.status_code == 200, f"{route} returned {resp.status_code}"
