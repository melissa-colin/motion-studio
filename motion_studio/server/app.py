"""Flask application factory and runner for the Motion Studio server.

:func:`create_app` builds the Flask app, attaches the shared
:class:`~motion_studio.server.state.ServerState`, registers the API blueprints
and serves the bundled frontend from ``motion_studio/static/`` at ``/``.
:func:`run` binds and serves it. ``motion_studio.cli`` imports :func:`run`.
"""

from __future__ import annotations

import ipaddress
import os
from urllib.parse import urlsplit

from flask import Flask, jsonify, request, send_from_directory

from motion_studio import __version__
from motion_studio.config import Config

from . import api_bundle, api_motion, api_video
from .common import add_cors
from .state import ServerState

_STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")

# Upload ceiling (~300 MiB): big enough for a .motion bundle with embedded
# video/music, small enough to bound memory and refuse a hostile upload early.
_MAX_CONTENT_LENGTH = 300 * 1024 * 1024

# Hostnames that name the loopback interface (DNS-rebinding-safe by default).
_LOOPBACK_NAMES = frozenset(("localhost",))


def _count_bundles(workspace: str) -> int:
    """Return the number of ``.motion`` bundles in ``workspace/bundles``.

    Args:
      workspace: The server workspace root.

    Returns:
      The count of ``*.motion`` files directly under ``bundles/``, or 0 if the
      directory does not exist or cannot be listed.
    """
    bundles_dir = os.path.join(workspace, "bundles")
    try:
        return sum(1 for n in os.listdir(bundles_dir) if n.endswith(".motion"))
    except OSError:
        return 0


def _host_is_loopback(host_header: str) -> bool:
    """Return True if a ``Host`` header names the local loopback interface.

    Accepts ``localhost``, an IPv4/IPv6 loopback literal (optionally bracketed),
    with or without a ``:port`` suffix. Anything else (a public hostname, a LAN
    name, an attacker-controlled rebinding domain) returns False.
    """
    if not host_header:
        return False
    host = host_header.strip()
    # Split off the port. IPv6 literals are bracketed: ``[::1]:8815``.
    if host.startswith("["):
        end = host.find("]")
        if end == -1:
            return False
        hostname = host[1:end]
    else:
        hostname = host.rsplit(":", 1)[0] if ":" in host else host
    hostname = hostname.lower()
    if hostname in _LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


def create_app(config: Config, allow_remote: bool = False) -> Flask:
    """Build and configure the Motion Studio Flask app.

    Args:
      config: The resolved server configuration.
      allow_remote: If True, accept requests whose ``Host``/``Origin`` names
        the configured non-loopback bind address (opt-in remote access).
        When False (the default) only loopback Hosts are served.

    Returns:
      A ready-to-serve Flask application.
    """
    config.ensure_dirs()
    app = Flask(__name__, static_folder=None)
    app.config["MS_STATE"] = ServerState(config)
    app.config["MAX_CONTENT_LENGTH"] = _MAX_CONTENT_LENGTH
    app.config["MS_ALLOW_REMOTE"] = bool(allow_remote)

    app.register_blueprint(api_motion.bp)
    app.register_blueprint(api_bundle.bp)
    app.register_blueprint(api_video.bp)

    @app.before_request
    def _guard_host():
        """Reject cross-origin / DNS-rebinding requests.

        A browser sends the page's hostname in ``Host`` (and ``Origin`` on
        cross-origin POSTs). Pinning both to the loopback interface stops a
        malicious web page from rebinding a domain to 127.0.0.1 and driving
        this no-auth, state-mutating API. ``--allow-remote`` relaxes the Host
        check to the operator's chosen bind address.
        """
        if app.config.get("MS_ALLOW_REMOTE"):
            return None
        if not _host_is_loopback(request.host):
            return ("forbidden: non-loopback Host", 403)
        origin = request.headers.get("Origin")
        if origin:
            netloc = urlsplit(origin).netloc
            if not _host_is_loopback(netloc):
                return ("forbidden: cross-origin request", 403)
        return None

    @app.after_request
    def _cors(resp):
        return add_cors(resp)

    @app.route("/health")
    def _health():
        """Liveness probe: 200 ``{"ok": true}`` if the app is serving."""
        return jsonify({"ok": True})

    @app.route("/version")
    def _version():
        """Return the running Motion Studio version."""
        return jsonify({"version": __version__})

    @app.route("/info")
    def _info():
        """Return non-sensitive server configuration for clients/probes.

        Exposes the version, the configured plugin specs, the workspace path,
        whether a ``pkl_dir`` is configured, and how many ``.motion`` bundles
        the workspace currently holds. No secrets, motion contents, or SMPL
        paths are included.
        """
        return jsonify(
            {
                "version": __version__,
                "corrector_spec": config.corrector_spec,
                "metrics_spec": config.metrics_spec,
                "workspace": config.workspace,
                "has_pkl_dir": bool(config.pkl_dir),
                "n_bundles": _count_bundles(config.workspace),
            }
        )

    @app.route("/cache/<path:path>")
    def _cache(path: str):
        """Serve a cached per-clip background frame (or nobg PNG)."""
        if ".." in path:
            return ("not found", 404)
        cache_root = os.path.join(config.workspace, "cache")
        full = os.path.join(cache_root, path)
        if not os.path.isfile(full):
            return ("not found", 404)
        return send_from_directory(cache_root, path)

    @app.route("/", defaults={"path": "index.html"})
    @app.route("/<path:path>")
    def _static(path: str):
        """Serve a file from the bundled frontend ``static/`` directory."""
        full = os.path.join(_STATIC_DIR, path)
        if not os.path.isfile(full):
            return ("not found", 404)
        return send_from_directory(_STATIC_DIR, path)

    # Warm each bundle's reference metrics in the background when a real
    # (non-default) metrics plugin is configured, so the library list is
    # sortable by metric without blocking startup. The identity default is
    # skipped (keeps tests / plain launches light).
    from motion_studio.config import DEFAULT_METRICS

    if config.metrics_spec and config.metrics_spec != DEFAULT_METRICS:
        from . import jobs

        jobs.start_metrics(app.config["MS_STATE"])

    return app


def run(config: Config, allow_remote: bool = False) -> None:
    """Create the app and serve it on ``config.host:config.port``.

    Args:
      config: The resolved server configuration.
      allow_remote: Opt-in to serving requests from a non-loopback bind
        address; forwarded to :func:`create_app`.
    """
    app = create_app(config, allow_remote=allow_remote)
    app.run(host=config.host, port=config.port, threaded=True)
