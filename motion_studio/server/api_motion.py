"""Session / motion endpoints: clips, load, mesh, refit, metrics, correct.

These routes carry the SMPL-heavy work; every one of them that touches torch /
SMPL serializes on the global ``heavy_lock`` and lazily imports torch on first
use. The corrector and metrics *plugins* are loaded fresh on each call so
editing the plugin file takes effect without restarting the server.
"""

from __future__ import annotations

import os
import time

import numpy as np
from flask import Blueprint, jsonify, request

from motion_studio.core.plugins import (
    PluginLoadError,
    load_corrector,
    load_floor,
    load_metrics,
)
from motion_studio.core.types import Floor, Motion

from . import loaders
from .common import binary, check_name, joints_from_payload, json_error, state
from .state import HeavyBusyError

bp = Blueprint("motion", __name__)


def _round_floor_meta(plane) -> dict:
    """Return ``{plane, tilt_deg}`` for a z = a*x + b*y + c plane."""
    a, b, c = float(plane[0]), float(plane[1]), float(plane[2])
    tilt = float(np.degrees(np.arctan(np.hypot(a, b))))
    return {"plane": [a, b, c], "tilt_deg": round(tilt, 4)}


# Hard ceiling on refit iterations: bounds the per-request GPU time so a single
# request cannot pin the heavy lock for an unbounded stretch.
_MAX_ITERS = 500


def _parse_iters(payload: dict, default: int) -> int:
    """Parse and clamp the ``iters`` field to ``[1, _MAX_ITERS]``.

    Args:
      payload: The decoded JSON request body.
      default: The value to use when ``iters`` is absent.

    Returns:
      A validated iteration count.

    Raises:
      ValueError: If ``iters`` is present but not a positive integer or
        exceeds :data:`_MAX_ITERS`. Callers parse this inside their ``try`` so
        the request fails with a JSON 400, not a raw HTML 500.
    """
    iters = int(payload.get("iters", default))
    if iters < 1 or iters > _MAX_ITERS:
        raise ValueError("iters=%d out of range [1, %d]" % (iters, _MAX_ITERS))
    return iters


def _parse_fps(payload: dict, default: float) -> float:
    """Parse and bound-check the ``fps`` field (``0 < fps <= 1000``).

    Raises:
      ValueError: If ``fps`` is non-numeric or out of range.
    """
    fps = float(payload.get("fps", default))
    if not np.isfinite(fps) or fps <= 0 or fps > 1000:
        raise ValueError(f"fps={fps!r} out of range (0, 1000]")
    return fps


def _plugin_is_real(spec: str) -> bool:
    """Return True if ``spec`` names a user/research plugin, not the no-op.

    The built-in defaults are identity placeholders; the UI uses this to decide
    whether to show metric columns / auto-compute metrics.
    """
    from motion_studio.config import DEFAULT_CORRECTOR, DEFAULT_METRICS

    return bool(spec) and spec not in (DEFAULT_CORRECTOR, DEFAULT_METRICS)


def _count_pkl(pkl_dir: str | None) -> int:
    """Return the number of ``*.pkl`` files in ``pkl_dir`` (0 if unset)."""
    if not pkl_dir or not os.path.isdir(pkl_dir):
        return 0
    return sum(1 for f in os.listdir(pkl_dir) if f.endswith(".pkl"))


@bp.get("/clips")
def clips():
    """List the raw ``.pkl`` clips available under ``pkl_dir``."""
    st = state()
    c = st.config
    out = []
    if c.pkl_dir and os.path.isdir(c.pkl_dir):
        vexts = (".mp4", ".mov", ".webm", ".mkv")
        mexts = (".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac")

        def _has(folder, name, exts):
            return bool(folder) and any(
                os.path.isfile(os.path.join(folder, name + e)) for e in exts
            )

        for fn in sorted(os.listdir(c.pkl_dir)):
            if not fn.endswith(".pkl"):
                continue
            name = fn[:-4]
            out.append(
                {
                    "name": name,
                    "has_video": _has(c.videos_dir, name, vexts),
                    "has_music": _has(c.audio_dir, name, mexts),
                    "converted": os.path.isfile(st.bundle_path(name)),
                    "custom": False,
                    "mtime": os.path.getmtime(os.path.join(c.pkl_dir, fn)),
                    "metrics": None,
                }
            )
    return jsonify({"clips": out, "count": len(out)})


@bp.get("/get_config")
def get_config():
    """Return the editable data-source settings for the UI Source panel."""
    c = state().config
    return jsonify(
        {
            "pkl_dir": c.pkl_dir,
            "videos_dir": c.videos_dir,
            "audio_dir": c.audio_dir,
            "smpl_dir": c.smpl_dir,
            "corrector_spec": c.corrector_spec,
            "metrics_spec": c.metrics_spec,
            "has_corrector": _plugin_is_real(c.corrector_spec),
            "has_metrics": _plugin_is_real(c.metrics_spec),
            "workspace": c.workspace,
        }
    )


@bp.get("/list_dir")
def list_dir():
    """List sub-folders of a path -- the folder picker for the Source panel."""
    raw = request.args.get("path") or os.path.expanduser("~")
    path = os.path.abspath(os.path.expanduser(raw))
    if not os.path.isdir(path):
        return json_error("pas un dossier : %r" % path, 400)
    try:
        names = os.listdir(path)
        dirs = sorted(
            d
            for d in names
            if not d.startswith(".") and os.path.isdir(os.path.join(path, d))
        )
        has_pkl = any(f.endswith(".pkl") for f in names)
    except OSError as e:
        return json_error(str(e), 400)
    parent = os.path.dirname(path)
    return jsonify(
        {
            "path": path,
            "parent": parent if parent != path else None,
            "dirs": dirs,
            "has_pkl": has_pkl,
        }
    )


@bp.post("/set_config")
def set_config():
    """Apply data-source settings from the UI (no restart) and persist them.

    Each of ``pkl_dir`` / ``videos_dir`` / ``audio_dir`` / ``smpl_dir`` is an
    independent folder; a non-empty value must be an existing directory.
    """
    st = state()
    c = st.config
    p = request.get_json(silent=True) or {}

    def _norm(v):
        return (v.strip() or None) if isinstance(v, str) else v

    # Validate any provided directory exists before mutating the live config.
    labels = {
        "pkl_dir": "dossier pkl",
        "videos_dir": "dossier vidéos",
        "audio_dir": "dossier audio",
        "smpl_dir": "dossier SMPL",
    }
    for key, label in labels.items():
        if key in p:
            val = _norm(p[key])
            if val and not os.path.isdir(val):
                return json_error("%s introuvable : %r" % (label, val), 400)

    if "pkl_dir" in p:
        c.pkl_dir = _norm(p["pkl_dir"])
    if "videos_dir" in p:
        c.videos_dir = _norm(p["videos_dir"])
    if "audio_dir" in p:
        c.audio_dir = _norm(p["audio_dir"])
    if "smpl_dir" in p:
        sd = _norm(p["smpl_dir"])
        if sd and sd != c.smpl_dir:
            c.smpl_dir = sd
            st.reset_dataset_caches()
    for key in ("corrector_spec", "metrics_spec"):
        if key in p and _norm(p[key]):
            setattr(c, key, _norm(p[key]))
    c.save()
    n_bundles = 0
    bundles_dir = os.path.join(c.workspace, "bundles")
    if os.path.isdir(bundles_dir):
        n_bundles = sum(
            1 for f in os.listdir(bundles_dir) if f.endswith(".motion")
        )
    return jsonify(
        {
            "ok": True,
            "n_pkl": _count_pkl(c.pkl_dir),
            "n_bundles": n_bundles,
            "pkl_dir": c.pkl_dir,
            "videos_dir": c.videos_dir,
            "audio_dir": c.audio_dir,
            "smpl_dir": c.smpl_dir,
        }
    )


@bp.get("/load")
def load():
    """Load a raw clip (or its bundle) into an editor scene."""
    st = state()
    clip, err = check_name(request.args.get("clip"))
    if err:
        return json_error(err)
    motion, where = loaders.resolve_motion(st, clip)
    if motion is None:
        return json_error(f"unknown clip: {clip}", 404)
    scene = {}
    scene["floor"] = None
    scene["floors"] = {}
    scene["floor_meta"] = {}
    scene["bg_offset"] = None
    scene["bg_version"] = 0
    bundle = loaders.load_bundle_for(st, clip) if where == "bundle" else None
    # Resolve the background video (bundle bytes -> cache, or raw smpl_videos/).
    offset_s = 0.0
    if bundle is not None:
        video_path = loaders.bundle_video_file(st, clip, bundle)
        offset_s = float(bundle.video_params.get("bg_offset", 0.0) or 0.0)
    else:
        video_path = loaders.raw_video_path(st, clip)
    try:
        with st.heavy():
            built = loaders.scene_from_motion(st, motion, source="original")
            scene.update(built)
            loaders.attach_frames(st, scene, clip, motion, video_path, offset_s)
            loaders.attach_floor(st, scene, clip, motion)
    except HeavyBusyError as e:
        return json_error(str(e), 503)
    scene["source"] = request.args.get("source", "original")
    # Version token for immutable mesh-frame caching (busts on re-save / edit).
    scene["mesh_version"] = st.clip_mtime(clip)
    if bundle is not None:
        loaders.attach_bundle_media(st, scene, bundle)
        # Show the starting ("départ") metrics on open without the user asking:
        # compute+cache them once if the bundle has none yet.
        if not (scene.get("metrics") or {}).get("ref"):
            from . import jobs

            scores = jobs.compute_and_cache_ref(st, clip, motion)
            if scores:
                scene.setdefault("metrics", {})["ref"] = scores
    return jsonify(scene)


def _resolve_mesh_state(st, clip: str):
    """Return ``(mesh_state, error_response)`` for ``clip`` on the hot path.

    Tries the per-clip mesh cache keyed by ``(clip, mtime)`` first; only on a
    miss does it read + unzip the ``.motion`` (or raw pkl) to resolve the
    Motion and build the mesh state. This keeps playback (every ``/mesh_frame``
    / ``/mesh_faces``) off the ~150 MB/s archive re-read path. On the build
    path it holds the heavy lock with a timeout (503 on contention).

    Args:
      st: The server state.
      clip: Validated clip / bundle name.

    Returns:
      ``(mesh_state, None)`` on success, or ``(None, response_tuple)`` where the
      response is a :func:`json_error` to return directly.
    """
    mtime = st.clip_mtime(clip)
    mesh = st.mesh_state_if_present(clip, mtime)
    if mesh is not None:
        return mesh, None
    motion, _where = loaders.resolve_motion(st, clip)
    if motion is None:
        return None, json_error(f"unknown clip: {clip}", 404)
    try:
        with st.heavy():
            mesh = st.mesh_state(clip, mtime, motion)
    except HeavyBusyError as e:
        return None, json_error(str(e), 503)
    return mesh, None


@bp.get("/mesh_faces")
def mesh_faces():
    """Return the SMPL faces of a clip as binary int32 ``(F, 3)``."""
    st = state()
    clip, err = check_name(request.args.get("clip"))
    if err:
        return json_error(err)
    mesh, err_resp = _resolve_mesh_state(st, clip)
    if err_resp is not None:
        return err_resp
    faces = np.ascontiguousarray(mesh.faces, dtype="<i4")
    return binary(
        faces.tobytes(),
        {
            "X-Faces-Shape": ",".join(map(str, faces.shape)),
            "Cache-Control": "public, max-age=31536000, immutable",
        },
    )


@bp.get("/mesh_frame")
def mesh_frame():
    """Return the SMPL vertices of one frame as binary float32 ``(N, V, 3)``."""
    st = state()
    clip, err = check_name(request.args.get("clip"))
    if err:
        return json_error(err)
    try:
        frame = int(request.args.get("frame", "0"))
    except (TypeError, ValueError):
        return json_error("invalid 'frame'")
    mesh, err_resp = _resolve_mesh_state(st, clip)
    if err_resp is not None:
        return err_resp
    n_frames = int(mesh.n_frames)
    if frame < 0 or frame >= n_frames:
        return json_error("frame %d out of range [0, %d)" % (frame, n_frames))
    from motion_studio.smpl import convert

    try:
        with st.heavy():
            t0 = time.time()
            try:
                verts = convert.verts_for_frame(mesh, frame)
            except IndexError as e:
                return json_error(str(e))
            dt = time.time() - t0
    except HeavyBusyError as e:
        return json_error(str(e), 503)
    # float16 halves the bytes over the wire (the bottleneck is the client's
    # link, not the ~3 ms server compute); ~1 mm vertex error is invisible in
    # the editor. The response is deterministic for a given (clip, source,
    # frame, version) so it is cached immutably -- the frontend appends a
    # ``&v=<mtime>`` version param, so re-saving the clip busts the cache.
    v = np.ascontiguousarray(verts, dtype="<f2")
    return binary(
        v.tobytes(),
        {
            "X-Mesh-Shape": ",".join(map(str, v.shape)),
            "X-Mesh-Time": f"{dt:.3f}",
            "X-Mesh-Dtype": "f16",
            "Cache-Control": "public, max-age=31536000, immutable",
        },
    )


@bp.get("/foot_masks")
def foot_masks():
    """Return SMPL sole vertex indices ``{"left": [...], "right": [...]}``."""
    st = state()
    try:
        with st.heavy():
            masks = st.foot_masks()
    except HeavyBusyError as e:
        return json_error(str(e), 503)
    return jsonify(masks)


def _init_pkl_for(st, clip: str | None) -> str | None:
    """Return a refit init pkl for ``clip`` (raw pkl if it exists)."""
    if not clip:
        return None
    pkl = st.raw_pkl_path(clip)
    return pkl if pkl and os.path.isfile(pkl) else None


def _refit_init(st, clip: str | None, motion: Motion | None):
    """Return ``(pose_init, trans_init, init_pkl)`` to seed a refit.

    Prefers the in-memory motion (bundle/raw) as init; falls back to a raw pkl
    path so a non-edited clip starts at ~zero error.
    """
    if motion is not None:
        return (
            np.asarray(motion.poses, dtype=np.float32),
            np.asarray(motion.trans, dtype=np.float32),
            None,
        )
    return None, None, _init_pkl_for(st, clip)


@bp.post("/refit")
def refit():
    """Fit SMPL to edited joints; return binary verts ``(N, Tsel, V, 3)``."""
    st = state()
    payload = request.get_json(silent=True) or {}
    try:
        joints = joints_from_payload(payload)
        iters = _parse_iters(payload, 150)
    except (KeyError, ValueError, TypeError) as e:
        return json_error(f"malformed payload: {e}")
    frames = payload.get("frames")
    clip = payload.get("clip")
    motion = None
    if clip:
        motion, _ = loaders.resolve_motion(st, clip)
    pose_init, trans_init, init_pkl = _refit_init(st, clip, motion)
    from motion_studio.smpl import refit as refit_mod

    try:
        with st.heavy():
            t0 = time.time()
            res = refit_mod.refit(
                st.config.smpl_dir,
                joints,
                pose_init=pose_init,
                trans_init=trans_init,
                frames=frames,
                iters=iters,
                want_verts=True,
                init_pkl=init_pkl,
            )
            dt = time.time() - t0
    except HeavyBusyError as e:
        return json_error(str(e), 503)
    except Exception as e:  # noqa: BLE001 - surface as 500 JSON
        return json_error(f"refit failed: {e}", 500)
    verts = np.ascontiguousarray(res["verts"], dtype="<f4")
    eb = float(res["err_before"].mean())
    ea = float(res["err_after"].mean())
    return binary(
        verts.tobytes(),
        {
            "X-Refit-Shape": ",".join(map(str, verts.shape)),
            "X-Refit-Frames": ",".join(map(str, res["frames"])),
            "X-Refit-Err": f"{eb:.5f},{ea:.5f}",
            "X-Refit-Time": f"{dt:.2f}",
        },
    )


@bp.post("/metrics")
def metrics():
    """Refit edited joints and score them with the metrics plugin."""
    st = state()
    payload = request.get_json(silent=True) or {}
    try:
        joints = joints_from_payload(payload)
        iters = _parse_iters(payload, 80)
        fps = _parse_fps(payload, 30)
    except (KeyError, ValueError, TypeError) as e:
        return json_error(f"malformed payload: {e}")
    frames = payload.get("frames")
    clip = payload.get("clip")
    plane = payload.get("plane")
    want_verts = bool(payload.get("want_verts", False))
    motion = None
    if clip:
        motion, _ = loaders.resolve_motion(st, clip)
    pose_init, trans_init, init_pkl = _refit_init(st, clip, motion)

    from motion_studio.smpl import refit as refit_mod

    betas = motion.betas if motion is not None else None
    gender = motion.gender if motion is not None else "neutral"
    try:
        with st.heavy():
            t0 = time.time()
            res = refit_mod.refit(
                st.config.smpl_dir,
                joints,
                pose_init=pose_init,
                trans_init=trans_init,
                frames=frames,
                iters=iters,
                want_verts=True,
                init_pkl=init_pkl,
            )
            verts = res["verts"]
            sel = res["frames"]
            # Score the refit poses/trans (already restricted to ``sel``)
            # through the configured metrics plugin so /metrics honors
            # config.metrics_spec like /correct_motion and /source_metrics.
            refit_motion = Motion(
                poses=np.asarray(res["poses"], dtype=np.float32),
                trans=np.asarray(res["trans"], dtype=np.float32),
                betas=betas,
                gender=gender,
                fps=fps,
                name=clip or "",
            )
            vals = _metrics_for_motion(st, refit_motion, plane)
            dt = time.time() - t0
        eb = float(res["err_before"].mean())
        ea = float(res["err_after"].mean())
    except HeavyBusyError as e:
        return json_error(str(e), 503)
    except PluginLoadError as e:
        return json_error(f"/metrics plugin load failed: {e}", 422)
    except Exception as e:  # noqa: BLE001
        return json_error(f"/metrics failed: {e}", 500)

    if want_verts:
        import json

        v = np.ascontiguousarray(verts, dtype="<f4")
        return binary(
            v.tobytes(),
            {
                "X-Refit-Shape": ",".join(map(str, v.shape)),
                "X-Refit-Frames": ",".join(map(str, sel)),
                "X-Refit-Err": f"{eb:.5f},{ea:.5f}",
                "X-Metrics": json.dumps(vals),
                "X-Refit-Time": f"{dt:.2f}",
            },
        )
    return jsonify(
        {
            "ok": True,
            "frames": list(sel),
            "metrics": vals,
            "err_before": round(eb, 5),
            "err_after": round(ea, 5),
            "time_s": round(dt, 2),
        }
    )


def _coerce_metrics(raw) -> dict[str, float]:
    """Coerce a plugin metrics mapping to ``{str: float}``, dropping bad values.

    Enforces the :class:`~motion_studio.core.plugins.MotionMetrics` output
    post-condition: keys become ``str``, values become finite ``float``. Any
    entry whose value is ``None``, non-numeric, or non-finite (NaN / inf) is
    silently dropped so the editor only ever receives clean numbers.

    Args:
      raw: The mapping returned by a metrics plugin's ``compute``.

    Returns:
      A new dict with string keys and finite float values.

    Raises:
      ValueError: If ``raw`` is not a mapping at all.
    """
    if not isinstance(raw, dict):
        raise ValueError(
            f"metrics plugin must return a dict, got {type(raw).__name__}"
        )
    out: dict[str, float] = {}
    for key, value in raw.items():
        if value is None:
            continue
        try:
            fval = float(value)
        except (TypeError, ValueError):
            continue
        if not np.isfinite(fval):
            continue
        out[str(key)] = fval
    return out


def _metrics_for_motion(st, motion: Motion, plane) -> dict[str, float]:
    """Score ``motion`` with the configured metrics plugin against ``plane``.

    Single code path shared by ``/metrics``, ``/correct_motion`` and
    ``/source_metrics`` so all three honor ``config.metrics_spec`` and return
    the same ``{str: float}`` shape.

    Args:
      st: The server state (carries ``config.metrics_spec``/``smpl_dir``).
      motion: The motion to score, in the z-up editor world frame.
      plane: The ``(a, b, c)`` floor plane, or None for ``z = 0``.

    Returns:
      A mapping ``{metric_name: value}`` with finite float values.
    """
    floor = Floor(plane=tuple(plane) if plane else (0.0, 0.0, 0.0))
    plugin = load_metrics(st.config.metrics_spec, smpl_dir=st.config.smpl_dir)
    return _coerce_metrics(plugin.compute(motion, floor))


def _validate_corrected(orig: Motion, out) -> Motion:
    """Enforce the ``MotionCorrector.correct`` output post-condition.

    Asserts the plugin returned a :class:`Motion` whose ``poses``/``trans``
    match the input shapes and contain only finite values.

    Args:
      orig: The motion handed to the corrector.
      out: Whatever the corrector returned.

    Returns:
      ``out`` unchanged, once validated.

    Raises:
      ValueError: If ``out`` is not a Motion, its array shapes differ from
        ``orig``, or any pose/translation value is non-finite. Callers map
        this to an HTTP 4xx.
    """
    if not isinstance(out, Motion):
        raise ValueError(
            f"corrector must return a Motion, got {type(out).__name__}"
        )
    op = np.asarray(orig.poses)
    ot = np.asarray(orig.trans)
    cp = np.asarray(out.poses)
    ct = np.asarray(out.trans)
    if cp.shape != op.shape:
        raise ValueError(
            f"corrected poses shape {cp.shape} != input {op.shape}"
        )
    if ct.shape != ot.shape:
        raise ValueError(
            f"corrected trans shape {ct.shape} != input {ot.shape}"
        )
    if not (np.isfinite(cp).all() and np.isfinite(ct).all()):
        raise ValueError("corrected motion contains non-finite values")
    return out


@bp.post("/correct_motion")
def correct_motion():
    """Run the corrector plugin (fresh) and return FK joints + metrics."""
    st = state()
    clip, err = check_name(request.args.get("clip"))
    if err:
        return json_error(err)
    mode = request.args.get("mode", "raw")
    if mode not in ("raw", "edited"):
        mode = "raw"

    if mode == "edited":
        payload = request.get_json(silent=True) or {}
        try:
            joints = joints_from_payload(payload)
        except (KeyError, ValueError, TypeError) as e:
            return json_error(f"malformed payload: {e}")
        base, _ = loaders.resolve_motion(st, clip)
        if base is None:
            return json_error(f"unknown clip: {clip}", 404)
        pose_init = np.asarray(base.poses, dtype=np.float32)
        trans_init = np.asarray(base.trans, dtype=np.float32)
        from motion_studio.smpl import refit as refit_mod

        try:
            with st.heavy():
                res = refit_mod.refit(
                    st.config.smpl_dir,
                    joints,
                    pose_init=pose_init,
                    trans_init=trans_init,
                    frames=None,
                    iters=150,
                    want_verts=False,
                )
        except HeavyBusyError as e:
            return json_error(str(e), 503)
        except Exception as e:  # noqa: BLE001
            return json_error(f"/correct_motion refit failed: {e}", 500)
        motion = Motion(
            poses=np.asarray(res["poses"], dtype=np.float32),
            trans=np.asarray(res["trans"], dtype=np.float32),
            betas=base.betas,
            gender=base.gender,
            fps=base.fps,
            name=clip,
        )
    else:
        motion, _ = loaders.resolve_motion(st, clip)
        if motion is None:
            return json_error(f"unknown clip: {clip}", 404)

    from motion_studio.smpl import convert

    log_lines = []
    floor = None
    plane = request.args.get("plane")
    if plane:
        try:
            floor = Floor(plane=tuple(float(x) for x in plane.split(",")))
        except ValueError:
            floor = None
    try:
        with st.heavy():
            t0 = time.time()
            corrector = load_corrector(
                st.config.corrector_spec,
                smpl_dir=st.config.smpl_dir,
                floor=floor,
            )
            corrected = corrector.correct(motion, log=log_lines.append)
            corrected = _validate_corrected(motion, corrected)
            joints, fps, _v, _f = convert.fk_joints(
                corrected, st.config.smpl_dir, want_mesh=False
            )
            metrics_vals = None
            try:
                metrics_vals = _metrics_for_motion(st, corrected, None)
            except Exception as e:  # noqa: BLE001
                log_lines.append(f"metrics failed: {e}")
            dt = time.time() - t0
    except HeavyBusyError as e:
        return json_error(str(e), 503)
    except PluginLoadError as e:
        return json_error(f"/correct_motion plugin load failed: {e}", 422)
    except ValueError as e:
        return json_error(f"/correct_motion invalid plugin output: {e}", 422)
    except Exception as e:  # noqa: BLE001
        return json_error(f"/correct_motion failed: {e}", 500)

    n, t, j, _ = joints.shape
    return jsonify(
        {
            "ok": True,
            "N": int(n),
            "T": int(t),
            "J": int(j),
            "joints": np.round(joints, 5).reshape(-1).tolist(),
            "metrics": metrics_vals,
            "mode": mode,
            "time_s": round(dt, 1),
            "log": "\n".join(log_lines),
        }
    )


@bp.post("/recompute_floor")
def recompute_floor():
    """Re-estimate the floor via the configured floor plugin on edited joints.

    Refits SMPL to the edited joints, builds a :class:`Motion` from the refit
    poses/trans (betas/gender/fps from the source motion when available, else
    neutral / 30 fps) and hands it to the floor plugin named by
    ``config.floor_spec`` to obtain a single ground plane.
    """
    st = state()
    clip, err = check_name(request.args.get("clip"))
    if err:
        return json_error(err)
    payload = request.get_json(silent=True) or {}
    try:
        joints = joints_from_payload(payload)
        iters = _parse_iters(payload, 120)
    except (KeyError, ValueError, TypeError) as e:
        return json_error(f"malformed payload: {e}")
    motion = None
    if clip:
        motion, _ = loaders.resolve_motion(st, clip)
    pose_init, trans_init, init_pkl = _refit_init(st, clip, motion)

    from motion_studio.smpl import refit as refit_mod

    betas = motion.betas if motion is not None else None
    gender = motion.gender if motion is not None else "neutral"
    fps = motion.fps if motion is not None else 30.0
    try:
        with st.heavy():
            t0 = time.time()
            res = refit_mod.refit(
                st.config.smpl_dir,
                joints,
                pose_init=pose_init,
                trans_init=trans_init,
                frames=None,
                iters=iters,
                want_verts=True,
                init_pkl=init_pkl,
            )
            refit_motion = Motion(
                poses=np.asarray(res["poses"], dtype=np.float32),
                trans=np.asarray(res["trans"], dtype=np.float32),
                betas=betas,
                gender=gender,
                fps=fps,
                name=clip or "",
            )
            floor = load_floor(
                st.config.floor_spec, smpl_dir=st.config.smpl_dir
            ).estimate(refit_motion)
            plane = floor.plane
            dt = time.time() - t0
    except HeavyBusyError as e:
        return json_error(str(e), 503)
    except PluginLoadError as e:
        return json_error(f"/recompute_floor plugin load failed: {e}", 422)
    except Exception as e:  # noqa: BLE001
        return json_error(f"/recompute_floor failed: {e}", 500)
    meta = _round_floor_meta(plane)
    return jsonify(
        {
            "ok": True,
            "clip": clip,
            "plane": meta["plane"],
            "tilt_deg": meta["tilt_deg"],
            "cam_tilt_deg": None,
            "n_contacts": 0,
            "time_s": round(dt, 2),
        }
    )


@bp.post("/source_metrics")
@bp.get("/source_metrics")
def source_metrics():
    """Return the metrics-plugin scores of a clip's stored motion."""
    st = state()
    clip, err = check_name(request.args.get("clip"))
    if err:
        return json_error(err)
    motion, _where = loaders.resolve_motion(st, clip)
    if motion is None:
        return json_error(f"unknown clip: {clip}", 404)
    try:
        with st.heavy():
            vals = _metrics_for_motion(st, motion, None)
    except HeavyBusyError as e:
        return json_error(str(e), 503)
    except PluginLoadError as e:
        return json_error(f"/source_metrics plugin load failed: {e}", 422)
    except Exception as e:  # noqa: BLE001
        return json_error(f"/source_metrics failed: {e}", 500)
    return jsonify({"ok": True, "metrics": vals})


@bp.get("/metrics_status")
def metrics_status():
    """Return the background metrics warm-up progress."""
    from . import jobs

    return jsonify(jobs.metrics_status())


@bp.post("/metrics_all")
def metrics_all():
    """(Re)start the background pass that caches every bundle's metrics."""
    from . import jobs

    st = state()
    started = jobs.start_metrics(st, force=True)
    return jsonify({"ok": True, "started": started})
