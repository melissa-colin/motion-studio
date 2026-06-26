"""Workspace, ``.motion`` bundle, export, comments and floor endpoints.

These routes manage the workspace side of the editor: listing and importing
clips into ``.motion`` bundles, loading/saving sessions, exporting a corrected
SMPL ``.pkl``, and the lighter comment / manual-floor metadata.
"""

from __future__ import annotations

import datetime
import json
import os
import pickle
import re
import threading
import time

import numpy as np
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from motion_studio import bundle as bundle_mod
from motion_studio import library
from motion_studio.core.types import Motion

from . import loaders, video_cache
from .common import binary, check_name, joints_from_payload, json_error, state
from .state import HeavyBusyError

bp = Blueprint("bundle", __name__)

_comments_lock = threading.Lock()
_tags_lock = threading.Lock()

# Bounds on user labels so the store stays small and the UI tidy.
_MAX_TAG_LEN = 40
_MAX_TAGS_PER_CLIP = 20

# Media file extensions are echoed into Content-Type and into the ``.motion``
# zip member name; constrain them to a short lowercase-alphanumeric token so an
# attacker-controlled upload filename cannot smuggle header or path content.
_EXT_RE = re.compile(r"^[a-z0-9]{1,5}$")
_DEFAULT_MUSIC_EXT = "wav"

# Largest media upload accepted by /import and /bundle/set_media (256 MiB).
# Source videos in the dataset run ~16 MiB; this leaves generous headroom while
# rejecting absurd uploads before they are buffered into the bundle.
_MAX_MEDIA_BYTES = 256 * 1024 * 1024
_VIDEO_KIND = "video"
_MUSIC_KIND = "music"


def _read_upload(upload) -> bytes | None:
    """Read an upload's bytes, enforcing the size cap before fully buffering it.

    ``FileStorage.read()`` would buffer the whole upload before any size check;
    this reads in bounded chunks and aborts as soon as the cap is exceeded so a
    huge upload is not held entirely in memory.

    Args:
      upload: A Werkzeug ``FileStorage`` from ``request.files``.

    Returns:
      The upload bytes, or None if it exceeds ``_MAX_MEDIA_BYTES``.
    """
    chunks = []
    total = 0
    while True:
        chunk = upload.stream.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > _MAX_MEDIA_BYTES:
            return None
        chunks.append(chunk)
    return b"".join(chunks)


def _safe_music_ext(filename: str | None) -> str:
    """Return the allowlisted lowercase music extension for an upload filename.

    The extension flows into the ``audio/<ext>`` Content-Type and into the
    bundle's stored ``music_ext``; anything that is not a short
    lowercase-alphanumeric token falls back to ``wav``.

    Args:
      filename: The client-supplied upload filename, or None.

    Returns:
      A safe extension matching ``^[a-z0-9]{1,5}$``, defaulting to ``wav``.
    """
    ext = os.path.splitext(filename or "")[1].lstrip(".").lower()
    return ext if _EXT_RE.match(ext) else _DEFAULT_MUSIC_EXT


@bp.get("/workspace")
def workspace():
    """List the ``.motion`` bundles saved in the workspace."""
    st = state()
    root = os.path.join(st.config.workspace, "bundles")
    out = []
    if os.path.isdir(root):
        for fn in sorted(os.listdir(root)):
            if not fn.endswith(bundle_mod.MOTION_EXT):
                continue
            path = os.path.join(root, fn)
            name = fn[: -len(bundle_mod.MOTION_EXT)]
            entry = {"name": name, "mtime": os.path.getmtime(path)}
            try:
                with __import__("zipfile").ZipFile(path) as zf:
                    man = json.loads(zf.read("manifest.json").decode("utf-8"))
                entry.update(
                    {
                        "source_clip": man.get("source_clip", ""),
                        "has_video": bool(man.get("has_video")),
                        "has_music": bool(man.get("has_music")),
                        "metrics": man.get("metrics", {}),
                    }
                )
            except Exception:  # noqa: BLE001 - skip unreadable manifest
                entry.update(
                    {
                        "source_clip": "",
                        "has_video": False,
                        "has_music": False,
                        "metrics": {},
                    }
                )
            out.append(entry)
    return jsonify({"workspace": st.config.workspace, "bundles": out})


@bp.post("/import_folder")
def import_folder():
    """Start a background import of a pkl folder into ``.motion`` bundles.

    Body (all optional; each falls back to the configured directory):
    ``{pkl_dir, videos_dir, audio_dir}``. Returns immediately; progress is
    polled from ``/import_status``. On completion a metrics warm-up is kicked
    automatically so the new bundles become sortable by metric.
    """
    from . import jobs

    st = state()
    p = request.get_json(silent=True) or {}

    def _dir(key, fallback):
        val = p.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
        return fallback

    pkl_dir = _dir("pkl_dir", st.config.pkl_dir)
    videos_dir = _dir("videos_dir", st.config.videos_dir)
    audio_dir = _dir("audio_dir", st.config.audio_dir)
    if not pkl_dir:
        return json_error("aucun dossier pkl configuré ou fourni", 400)
    if not os.path.isdir(pkl_dir):
        return json_error("dossier pkl introuvable : %r" % pkl_dir, 404)
    if not jobs.start_import(st, pkl_dir, videos_dir, audio_dir):
        return json_error("un import est déjà en cours", 409)
    return jsonify({"ok": True, "job": "import"})


@bp.get("/import_status")
def import_status():
    """Return the background folder-import progress."""
    from . import jobs

    return jsonify(jobs.import_status())


@bp.post("/import_clip")
def import_clip():
    """Convert a single ``pkl_dir/<name>.pkl`` clip into a ``.motion`` bundle.

    Body: ``{name}``. Matches the clip's video/audio (by exact name) from the
    configured ``videos_dir`` / ``audio_dir`` and writes the bundle, returning
    its name so the caller can load it with ``/bundle/load``.
    """
    st = state()
    p = request.get_json(silent=True) or {}
    name, err = check_name(p.get("name"))
    if err:
        return json_error(err)
    if not st.config.pkl_dir:
        return json_error("aucun dossier pkl configuré", 400)
    entry = library.entry_for_clip(
        st.config.pkl_dir,
        name,
        videos_dir=st.config.videos_dir,
        audio_dir=st.config.audio_dir,
    )
    if entry is None:
        return json_error("clip introuvable : %r" % name, 404)
    try:
        library.import_entry(entry, st.config.workspace)
    except Exception as e:  # noqa: BLE001
        return json_error("/import_clip failed: %s" % e, 500)
    return jsonify({"ok": True, "name": name})


@bp.get("/bundle/load")
def bundle_load():
    """Load a ``.motion`` bundle into an editor scene."""
    st = state()
    name, err = check_name(request.args.get("name"))
    if err:
        return json_error(err)
    b = loaders.load_bundle_for(st, name)
    if b is None:
        return json_error(f"unknown bundle: {name}", 404)
    video_path = loaders.bundle_video_file(st, name, b)
    offset_s = float(b.video_params.get("bg_offset", 0.0) or 0.0)
    try:
        with st.heavy():
            scene = loaders.scene_from_motion(st, b.original, source="bundle")
            scene["bg_version"] = 0
            loaders.attach_frames(
                st, scene, name, b.original, video_path, offset_s
            )
            loaders.attach_floor(st, scene, name, b.original)
    except HeavyBusyError as e:
        return json_error(str(e), 503)
    loaders.attach_bundle_media(st, scene, b)
    scene["mesh_version"] = st.clip_mtime(name)
    # Starting ("départ") metrics on open, computed+cached once if missing.
    if not (scene.get("metrics") or {}).get("ref"):
        from . import jobs

        scores = jobs.compute_and_cache_ref(st, name, b.original)
        if scores:
            scene.setdefault("metrics", {})["ref"] = scores
    return jsonify(scene)


@bp.post("/bundle/save")
def bundle_save():
    """Write/update a bundle (original kept, edited + meta updated)."""
    st = state()
    name, err = check_name(request.args.get("name"))
    if err:
        return json_error(err)
    payload = request.get_json(silent=True) or {}

    existing = loaders.load_bundle_for(st, name)
    raw = loaders.load_raw_motion(st, name)
    if existing is not None:
        original = existing.original
    elif raw is not None:
        original = raw
    else:
        return json_error(f"no original motion for bundle '{name}'", 404)

    edited = None
    if payload.get("joints_edited") is not None:
        try:
            joints = joints_from_payload(
                {
                    "N": payload["N"],
                    "T": payload["T"],
                    "J": payload["J"],
                    "joints": payload["joints_edited"],
                }
            )
        except (KeyError, ValueError, TypeError) as e:
            return json_error(f"malformed joints_edited: {e}")
        from motion_studio.smpl import refit as refit_mod

        pose_init = np.asarray(original.poses, dtype=np.float32)
        trans_init = np.asarray(original.trans, dtype=np.float32)
        try:
            with st.heavy_lock:
                res = refit_mod.refit(
                    st.config.smpl_dir,
                    joints,
                    pose_init=pose_init,
                    trans_init=trans_init,
                    frames=None,
                    iters=150,
                    want_verts=False,
                )
        except Exception as e:  # noqa: BLE001
            return json_error(f"/bundle/save refit failed: {e}", 500)
        edited = Motion(
            poses=np.asarray(res["poses"], dtype=np.float32),
            trans=np.asarray(res["trans"], dtype=np.float32),
            betas=original.betas,
            gender=original.gender,
            fps=original.fps,
            name=original.name,
        )
    elif existing is not None:
        edited = existing.edited

    video = existing.video if existing is not None else None
    music = existing.music if existing is not None else None
    music_ext = existing.music_ext if existing is not None else "wav"
    created = existing.manifest.get("created") if existing is not None else None

    path = st.bundle_path(name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bundle_mod.save_bundle(
        path,
        original=original,
        edited=edited,
        video=video,
        music=music,
        music_ext=music_ext,
        video_params=payload.get("video_params", {}),
        comments=payload.get("comments", []),
        metrics=payload.get("metrics", {}),
        source_clip=payload.get("source_clip", name),
        created=created,
    )
    st.invalidate_mesh(name)
    return jsonify({"ok": True, "path": path})


@bp.post("/export_pkl")
@bp.get("/export_pkl")
def export_pkl():
    """Refit edited joints and return a downloadable AIOZ ``.pkl``."""
    st = state()
    clip, err = check_name(request.args.get("clip"))
    if err:
        return json_error(err)
    payload = request.get_json(silent=True) or {}
    try:
        joints = joints_from_payload(payload)
    except (KeyError, ValueError, TypeError) as e:
        return json_error(f"malformed payload: {e}")
    iters = int(payload.get("iters", 150))
    motion, _ = loaders.resolve_motion(st, clip)
    if motion is None:
        return json_error(f"unknown clip: {clip}", 404)
    pose_init = np.asarray(motion.poses, dtype=np.float32)
    trans_init = np.asarray(motion.trans, dtype=np.float32)
    from motion_studio.smpl import refit as refit_mod

    try:
        with st.heavy_lock:
            res = refit_mod.refit(
                st.config.smpl_dir,
                joints,
                pose_init=pose_init,
                trans_init=trans_init,
                frames=None,
                iters=iters,
                want_verts=False,
            )
    except Exception as e:  # noqa: BLE001
        return json_error(f"/export_pkl failed: {e}", 500)
    poses_z = np.asarray(res["poses"], dtype=np.float32)
    trans_z = np.asarray(res["trans"], dtype=np.float32)
    poses_y, trans_y = refit_mod.zup2yup(poses_z, trans_z)
    n, t = poses_y.shape[:2]
    out = {
        "smpl_poses": poses_y.reshape(n, t, 72).astype(np.float64),
        "root_trans": trans_y.astype(np.float64),
    }
    body = pickle.dumps(out, protocol=pickle.HIGHEST_PROTOCOL)
    return binary(
        body,
        {
            "Content-Disposition": (
                f'attachment; filename="{clip}_corrected.pkl"'
            ),
        },
    )


@bp.get("/music")
def music():
    """Stream a bundle's music (supports HTTP Range)."""
    st = state()
    clip, err = check_name(request.args.get("clip"))
    if err:
        return json_error(err)
    b = loaders.load_bundle_for(st, clip)
    if b is None or b.music is None:
        return json_error(f"no music for {clip}", 404)
    data = b.music
    size = len(data)
    rng = request.headers.get("Range")
    start, end = 0, size - 1
    partial = False
    if rng and rng.startswith("bytes="):
        try:
            s, e = rng[len("bytes=") :].split("-", 1)
            if s.strip():
                start = int(s)
            if e.strip():
                end = int(e)
            if 0 <= start <= end < size:
                partial = True
            else:
                start, end = 0, size - 1
        except Exception:  # noqa: BLE001
            start, end = 0, size - 1
    chunk = data[start : end + 1]
    from flask import Response

    resp = Response(
        chunk,
        status=206 if partial else 200,
        mimetype="audio/%s" % (b.music_ext or "wav"),
    )
    resp.headers["Accept-Ranges"] = "bytes"
    if partial:
        resp.headers["Content-Range"] = "bytes %d-%d/%d" % (start, end, size)
    return resp


@bp.get("/comments")
def get_comments():
    """Return a clip's comments and the default user name."""
    st = state()
    clip, err = check_name(request.args.get("clip"))
    if err:
        return json_error(err)
    with _comments_lock:
        data = _load_comments(st)
        comments = data.get(clip, [])
    # Never echo the server's OS username to clients; the frontend shows a
    # "Your name" placeholder when this is empty.
    return jsonify({"comments": comments, "default_user": ""})


@bp.post("/comments")
def post_comment():
    """Append ``{user, text}`` to a clip's comments."""
    st = state()
    clip, err = check_name(request.args.get("clip"))
    if err:
        return json_error(err)
    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    if not text:
        return json_error("empty text")
    # Default author is empty (frontend shows a "Your name" placeholder); we
    # never fall back to the server's OS username.
    user = (payload.get("user") or "").strip()
    entry = {
        "user": user[:80],
        "text": text[:4000],
        "time": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    with _comments_lock:
        data = _load_comments(st)
        data.setdefault(clip, []).append(entry)
        _save_comments(st, data)
        comments = data.get(clip, [])
    return jsonify({"comments": comments, "default_user": ""})


@bp.post("/save_floor")
def save_floor():
    """Store a manual floor plane in a small workspace floors store."""
    st = state()
    clip, err = check_name(request.args.get("clip"))
    if err:
        return json_error(err)
    payload = request.get_json(silent=True) or {}
    try:
        plane = payload["plane"]
        a, b, c = float(plane[0]), float(plane[1]), float(plane[2])
    except (KeyError, ValueError, TypeError) as e:
        return json_error(f"expected {{plane:[a,b,c]}}: {e}")
    import math

    tilt = math.degrees(math.atan(math.hypot(a, b)))
    store = os.path.join(st.config.workspace, "floors_manual.json")
    with _comments_lock:
        data = {}
        if os.path.isfile(store):
            try:
                with open(store) as f:
                    data = json.load(f)
            except Exception:  # noqa: BLE001
                data = {}
        data[clip] = {"plane": [a, b, c], "tilt_deg": tilt, "source": "manual"}
        tmp = store + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, store)
    return jsonify(
        {
            "ok": True,
            "clip": clip,
            "plane": [a, b, c],
            "tilt_deg": round(tilt, 4),
        }
    )


# -- clip tags / lists ----------------------------------------------------
# Free-form, multi-label tags per clip (e.g. "à supprimer", "sol cassé",
# "parfait"), stored in a small workspace JSON so the projects browser can show
# and filter by them. Like comments, they are workspace-level, not in bundles.


def _tags_store(st) -> str:
    """Return the path of the workspace tags store."""
    return os.path.join(st.config.workspace, "tags.json")


def _load_tags(st) -> dict:
    """Return the ``{clip: [tag, ...]}`` map (``{}`` if missing/unreadable)."""
    path = _tags_store(st)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_tags(st, data: dict) -> None:
    """Atomically persist the tags map."""
    path = _tags_store(st)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def _all_tags(data: dict) -> list:
    """Return the sorted set of every tag used across clips."""
    seen: set = set()
    for tags in data.values():
        if isinstance(tags, list):
            seen.update(t for t in tags if isinstance(t, str))
    return sorted(seen)


@bp.get("/tags")
def get_tags():
    """Return ``{tags: {clip: [...]}, all_tags: [...]}`` for the workspace."""
    st = state()
    with _tags_lock:
        data = _load_tags(st)
    return jsonify({"tags": data, "all_tags": _all_tags(data)})


@bp.post("/tags")
def set_tags():
    """Replace a clip's tags. Body: ``{clip, tags: [str, ...]}``.

    An empty ``tags`` list removes the clip from the store. Tags are trimmed,
    de-duplicated, length-capped and count-capped. Returns the cleaned tags and
    the updated ``all_tags`` set.
    """
    st = state()
    p = request.get_json(silent=True) or {}
    clip, err = check_name(p.get("clip"))
    if err:
        return json_error(err)
    raw = p.get("tags")
    if not isinstance(raw, list):
        return json_error("expected {clip, tags: [...]}")
    clean: list = []
    for t in raw:
        if not isinstance(t, str):
            continue
        s = t.strip()[:_MAX_TAG_LEN]
        if s and s not in clean:
            clean.append(s)
        if len(clean) >= _MAX_TAGS_PER_CLIP:
            break
    with _tags_lock:
        data = _load_tags(st)
        if clean:
            data[clip] = clean
        else:
            data.pop(clip, None)
        _save_tags(st, data)
        all_tags = _all_tags(data)
    return jsonify(
        {"ok": True, "clip": clip, "tags": clean, "all_tags": all_tags}
    )


def _save_upload(upload, dest: str) -> bool:
    """Stream a single upload to ``dest``, enforcing the media size cap.

    Args:
      upload: A Werkzeug ``FileStorage`` from ``request.files``.
      dest: Absolute destination path inside the import temp dir.

    Returns:
      True on success; False if the upload exceeds ``_MAX_MEDIA_BYTES``.
    """
    data = _read_upload(upload)
    if data is None:
        return False
    with open(dest, "wb") as f:
        f.write(data)
    return True


@bp.post("/import")
def import_one():
    """Import a single uploaded pkl (+ optional video/music) as a bundle.

    The ``.pkl`` is loaded through the restricted unpickler in
    ``smpl_io.load_motion_pkl``; here we additionally cap each upload's size
    (before it is fully buffered), confine every written filename with
    ``secure_filename``, and allowlist the music extension that flows into the
    bundle's stored ``music_ext``.
    """
    st = state()
    if "pkl" not in request.files or not request.files["pkl"].filename:
        return json_error("missing 'pkl' file")
    import tempfile

    pkl_file = request.files["pkl"]
    raw_name = (
        request.form.get("name")
        or os.path.splitext(pkl_file.filename or "import")[0]
    )
    name, err = check_name(raw_name)
    if err:
        return json_error(err)
    tmp_dir = tempfile.mkdtemp(prefix="ms_import_")
    try:
        tmp_pkl = os.path.join(tmp_dir, secure_filename(name + ".pkl"))
        if not _save_upload(pkl_file, tmp_pkl):
            return json_error(
                "pkl too large (max %d bytes)" % _MAX_MEDIA_BYTES, 413
            )
        from motion_studio.smpl import io as smpl_io

        try:
            motion = smpl_io.load_motion_pkl(tmp_pkl)
        except Exception as e:  # noqa: BLE001
            return json_error(f"invalid pkl: {e}")
        video_path = music_path = None
        music_ext = _DEFAULT_MUSIC_EXT
        if "video" in request.files and request.files["video"].filename:
            video_path = os.path.join(tmp_dir, "video.mp4")
            if not _save_upload(request.files["video"], video_path):
                return json_error(
                    "video too large (max %d bytes)" % _MAX_MEDIA_BYTES, 413
                )
        if "music" in request.files and request.files["music"].filename:
            mf = request.files["music"]
            music_ext = _safe_music_ext(mf.filename)
            music_path = os.path.join(tmp_dir, "music." + music_ext)
            if not _save_upload(mf, music_path):
                return json_error(
                    "music too large (max %d bytes)" % _MAX_MEDIA_BYTES, 413
                )
        path = st.bundle_path(name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        bundle_mod.save_bundle(
            path,
            original=motion,
            edited=None,
            video=video_path,
            music=music_path,
            music_ext=music_ext,
            source_clip=name,
        )
        return jsonify(
            {
                "ok": True,
                "name": name,
                "N": motion.n_persons,
                "T": motion.n_frames,
                "has_video": video_path is not None,
                "has_music": music_path is not None,
            }
        )
    finally:
        import shutil

        shutil.rmtree(tmp_dir, ignore_errors=True)


def _ensure_bundle(st, name: str):
    """Return the loaded bundle for ``name``, creating it from a pkl if needed.

    When a clip was opened straight from a raw ``.pkl`` (no workspace bundle
    yet), this materializes a bundle from that source so there is always a
    ``.motion`` file to update.

    Args:
      st: The server state.
      name: Clip / bundle name.

    Returns:
      The loaded :class:`~motion_studio.bundle.Bundle`, or None if neither a
      bundle nor a raw motion exists for ``name``.
    """
    existing = loaders.load_bundle_for(st, name)
    if existing is not None:
        return existing
    raw = loaders.load_raw_motion(st, name)
    if raw is None:
        return None
    path = st.bundle_path(name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bundle_mod.save_bundle(path, original=raw, edited=None, source_clip=name)
    return loaders.load_bundle_for(st, name)


@bp.post("/bundle/set_media")
def bundle_set_media():
    """Import/replace the background video or music of a loaded clip.

    The uploaded ``file`` replaces the bundle's ``video`` (``kind=video``) or
    ``music`` (``kind=music``); the bundle is created from the raw source first
    if it does not exist yet. For a video the background frames are re-extracted
    and the response carries the same keys ``/bundle/load`` returns for video so
    the frontend can rebuild the billboard; for music the response just flags
    ``has_music``.
    """
    st = state()
    name, err = check_name(request.args.get("name"))
    if err:
        return json_error(err)
    kind = request.args.get("kind")
    if kind not in (_VIDEO_KIND, _MUSIC_KIND):
        return json_error("invalid 'kind' (expected 'video' or 'music')")
    if "file" not in request.files or not request.files["file"].filename:
        return json_error("missing 'file' upload")

    upload = request.files["file"]
    # Enforce the size cap while streaming so an oversized upload is never fully
    # buffered before the check (the previous upload.read() read it all first).
    data = _read_upload(upload)
    if data is None:
        return json_error(
            "file too large (max %d bytes)" % _MAX_MEDIA_BYTES, 413
        )
    if not data:
        return json_error("empty 'file' upload")

    b = _ensure_bundle(st, name)
    if b is None:
        return json_error(f"no motion for clip '{name}'", 404)

    if kind == _MUSIC_KIND:
        music_ext = _safe_music_ext(upload.filename)
        _save_media_bundle(st, name, b, music=data, music_ext=music_ext)
        return jsonify({"ok": True, "has_music": True})

    _save_media_bundle(st, name, b, video=data)
    try:
        with st.heavy_lock:
            meta = _reextract_after_video(st, name, b, data)
    except Exception as e:  # noqa: BLE001
        return json_error(f"/bundle/set_media re-extract failed: {e}", 500)
    if meta is None:
        return json_error("frame re-extraction produced no frames", 500)

    resp = {
        "ok": True,
        "_clip_dir": f"/cache/{name}",
        "bg_version": int(time.time() * 1000),
    }
    resp.update(meta)
    return jsonify(resp)


def _save_media_bundle(st, name, b, *, video=None, music=None, music_ext=None):
    """Rewrite ``name``'s bundle, replacing one media stream, keeping the rest.

    Args:
      st: The server state.
      name: Clip / bundle name.
      b: The currently loaded bundle (source of the preserved fields).
      video: New raw video bytes, or None to keep the bundle's current video.
      music: New raw music bytes, or None to keep the bundle's current music.
      music_ext: Extension for the new music, when ``music`` is given.
    """
    new_video = b.video if video is None else video
    new_music = b.music if music is None else music
    new_music_ext = b.music_ext if music is None else (music_ext or "wav")
    path = st.bundle_path(name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bundle_mod.save_bundle(
        path,
        original=b.original,
        edited=b.edited,
        video=new_video,
        music=new_music,
        music_ext=new_music_ext,
        video_params=b.video_params,
        comments=b.comments,
        metrics=b.metrics,
        source_clip=b.manifest.get("source_clip", name),
        created=b.manifest.get("created"),
    )
    st.invalidate_mesh(name)


def _reextract_after_video(st, name, b, video_bytes):
    """Force-extract billboard frames from new video bytes; drop stale masks.

    Must be called under ``heavy_lock``.

    Args:
      st: The server state.
      name: Clip / bundle name.
      b: The bundle (for the motion and its current bg offset).
      video_bytes: The freshly uploaded video bytes.

    Returns:
      The frame metadata dict from
      :func:`~motion_studio.server.video_cache.ensure_frames`, or None.
    """
    import shutil

    video_path = video_cache.bundle_video_path(st.config, name, video_bytes)
    offset_s = float(b.video_params.get("bg_offset", 0.0) or 0.0)
    meta = video_cache.ensure_frames(
        st.config, name, video_path, b.original, offset_s=offset_s, force=True
    )
    shutil.rmtree(video_cache.nobg_dir(st.config, name), ignore_errors=True)
    return meta


def _load_comments(st) -> dict:
    """Load the workspace comments store ``{clip: [...]}`` (best-effort)."""
    if not os.path.isfile(st.comments_store):
        return {}
    try:
        with open(st.comments_store) as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def _save_comments(st, data: dict) -> None:
    """Atomically write the workspace comments store."""
    tmp = st.comments_store + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
    os.replace(tmp, st.comments_store)
