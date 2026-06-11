"""Video-background endpoints: person-only background and offset re-extract.

``/bg_nobg`` renders one cached background frame with the people kept and the
background made transparent (torchvision DeepLabV3 person segmentation), caching
the RGBA PNG under ``cache/<name>/nobg/``. ``/set_bg_offset`` re-extracts the
billboard frames at a new temporal offset into the source video and bumps a
``bg_version`` anti-cache token. Both serialize their GPU/ffmpeg work on the
server ``heavy_lock``; the segmentation model is lazy-loaded on first use. The
ffmpeg/frame helpers live in :mod:`motion_studio.smpl.convert` and
:mod:`motion_studio.server.video_cache`.
"""

from __future__ import annotations

import os
import time

from flask import Blueprint, Response, jsonify, request

from . import loaders, video_cache
from .common import check_name, json_error, state

bp = Blueprint("video", __name__)

# DeepLabV3 (VOC/COCO) class index of "person", and the keep threshold.
_SEG_PERSON_CLASS = 15
_SEG_PROB_THRESH = 0.5


def _seg_person_alpha(st, pil_img):
    """Return a uint8 person mask (255 person, 0 background) for ``pil_img``.

    Runs DeepLabV3 on the GPU; must be called under ``heavy_lock``.
    """
    import numpy as np
    import torch

    model, weights, device = st.seg_model()
    width, height = pil_img.size
    transform = weights.transforms()
    x = transform(pil_img).unsqueeze(0).to(device)
    with torch.no_grad():
        out = model(x)["out"][0]
        prob = torch.softmax(out, dim=0)[_SEG_PERSON_CLASS]
        prob = torch.nn.functional.interpolate(
            prob[None, None],
            size=(height, width),
            mode="bilinear",
            align_corners=False,
        )[0, 0]
        alpha = (prob >= _SEG_PROB_THRESH).to(torch.uint8) * 255
        alpha = alpha.cpu().numpy()
    try:
        from scipy.ndimage import gaussian_filter

        feathered = gaussian_filter(alpha.astype(np.float32), sigma=1.0)
        alpha = np.clip(feathered, 0, 255).astype(np.uint8)
    except Exception:  # noqa: BLE001 - feather is optional
        pass
    return alpha


def _nobg_make_png(st, src_png: str, dst_png: str, idle: bool = False) -> None:
    """Write ``dst_png`` (RGBA, transparent background) from ``src_png``.

    Serializes the GPU forward on the heavy lock; the file write is atomic.

    Args:
      st: The server state.
      src_png: Source RGB frame path.
      dst_png: Destination RGBA path.
      idle: When True, take the lock at background priority (yields to
        interactive requests) -- used by the whole-clip prewarm job so it
        cannot starve the editor.
    """
    import numpy as np
    from PIL import Image

    img = Image.open(src_png).convert("RGB")
    lock_cm = st.heavy_idle() if idle else st.heavy_lock
    with lock_cm:
        alpha = _seg_person_alpha(st, img)
    rgba = np.dstack([np.asarray(img, dtype=np.uint8), alpha])
    tmp = dst_png + ".tmp"
    Image.fromarray(rgba, mode="RGBA").save(tmp, "PNG")
    os.replace(tmp, dst_png)


def prewarm_frame(st, clip: str, source: str, frame: int) -> bool:
    """Ensure the background-crop mask for ``clip`` frame ``frame`` is cached.

    Used by the prewarm job (see :mod:`motion_studio.server.jobs`) to segment a
    clip's frames ahead of playback. The mask is independent of the SMPL
    ``source`` (it is computed from the billboard frame), so ``source`` is
    accepted for call-site parity but not part of the cache key. A no-op when
    the frame is already cached or has no extracted billboard frame.

    Args:
      st: The server state.
      clip: Clip / bundle name.
      source: Motion variant (accepted, unused -- masks are source-independent).
      frame: Frame index to warm.

    Returns:
      True if a mask now exists in the cache, False otherwise.
    """
    fdir = video_cache.frames_dir(st.config, clip)
    src_png = os.path.join(fdir, "%04d.png" % frame)
    if not os.path.isfile(src_png):
        return False
    nobg = video_cache.nobg_dir(st.config, clip)
    os.makedirs(nobg, exist_ok=True)
    dst_png = os.path.join(nobg, "%05d.png" % frame)
    if os.path.isfile(dst_png):
        return True
    try:
        _nobg_make_png(st, src_png, dst_png, idle=True)
    except Exception:  # noqa: BLE001 - best-effort warming
        return False
    return True


def _frame_count(st, name: str) -> int | None:
    """Return the number of cached background frames for ``name``, or None."""
    fdir = video_cache.frames_dir(st.config, name)
    if not os.path.isdir(fdir):
        return None
    return len([f for f in os.listdir(fdir) if f.endswith(".png")])


@bp.get("/bg_nobg")
def bg_nobg():
    """Person-only (transparent background) cached frame as an RGBA PNG."""
    st = state()
    clip, err = check_name(request.args.get("clip"))
    if err:
        return json_error(err)
    try:
        frame = int(request.args.get("frame", "0"))
    except ValueError:
        return json_error("invalid 'frame'")
    if frame < 0:
        return json_error("negative frame")
    fdir = video_cache.frames_dir(st.config, clip)
    src_png = os.path.join(fdir, "%04d.png" % frame)
    if not os.path.isfile(src_png):
        n = _frame_count(st, clip)
        if n is None:
            return json_error(f"clip has no extracted frames: {clip}", 404)
        return json_error(
            "frame %d out of range (max %d)" % (frame, n - 1), 404
        )
    nobg = video_cache.nobg_dir(st.config, clip)
    os.makedirs(nobg, exist_ok=True)
    dst_png = os.path.join(nobg, "%05d.png" % frame)
    try:
        if not os.path.isfile(dst_png):
            _nobg_make_png(st, src_png, dst_png)
    except Exception as e:  # noqa: BLE001
        return json_error(f"/bg_nobg failed: {e}", 500)
    with open(dst_png, "rb") as f:
        body = f.read()
    resp = Response(body, mimetype="image/png")
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@bp.post("/prewarm_bg")
def prewarm_bg():
    """Start segmenting a clip's whole background crop ahead of playback.

    Body: ``{clip, source}``. Kicks a background job that fills the ``/bg_nobg``
    cache for every extracted frame so playback never freezes waiting on a
    per-frame mask. Returns immediately; poll ``/prewarm_status``.
    """
    from . import jobs

    st = state()
    p = request.get_json(silent=True) or {}
    clip, err = check_name(p.get("clip"))
    if err:
        return json_error(err)
    source = str(p.get("source") or "")
    n = _frame_count(st, clip)
    if not n:
        return json_error(f"clip has no extracted frames: {clip}", 404)
    jobs.start_prewarm(st, clip, source, list(range(n)))
    return jsonify({"ok": True, "total": n})


@bp.get("/prewarm_status")
def prewarm_status():
    """Return a clip's background-crop prewarm progress."""
    from . import jobs

    clip, err = check_name(request.args.get("clip"))
    if err:
        return json_error(err)
    source = str(request.args.get("source") or "")
    return jsonify(jobs.prewarm_status(clip, source))


@bp.post("/set_bg_offset")
@bp.get("/set_bg_offset")
def set_bg_offset():
    """Re-extract billboard frames at ``offset_s`` and bump ``bg_version``."""
    st = state()
    clip, err = check_name(request.args.get("clip"))
    if err:
        return json_error(err)
    offset_s = request.args.get("offset_s")
    if offset_s is None:
        payload = request.get_json(silent=True) or {}
        offset_s = payload.get("offset_s")
    try:
        offset_s = float(offset_s)
    except (TypeError, ValueError):
        return json_error("missing or invalid 'offset_s'")

    motion, where = loaders.resolve_motion(st, clip)
    if motion is None:
        return json_error(f"unknown clip: {clip}", 404)
    if where == "bundle":
        bundle = loaders.load_bundle_for(st, clip)
        video_path = loaders.bundle_video_file(st, clip, bundle)
    else:
        video_path = loaders.raw_video_path(st, clip)
    if not video_path or not os.path.isfile(video_path):
        return json_error(f"no video for clip: {clip}", 404)

    try:
        with st.heavy_lock:
            meta = video_cache.ensure_frames(
                st.config,
                clip,
                video_path,
                motion,
                offset_s=offset_s,
                force=True,
            )
    except Exception as e:  # noqa: BLE001
        return json_error(f"/set_bg_offset failed: {e}", 500)
    if meta is None:
        return json_error("frame re-extraction produced no frames", 500)

    # The background frames changed -> stale nobg masks; drop them.
    import shutil

    shutil.rmtree(video_cache.nobg_dir(st.config, clip), ignore_errors=True)

    return _bg_offset_response(clip, meta)


def _bg_offset_response(clip: str, meta) -> Response:
    """Build the ``/set_bg_offset`` JSON the frontend reads."""
    from flask import jsonify

    return jsonify(
        {
            "ok": True,
            "clip": clip,
            "offset_sec": meta["bg_offset"],
            "frames": meta["frames"],
            "n_frames": len(meta["frames"]),
            "frame_w": meta["frame_w"],
            "frame_h": meta["frame_h"],
            "video_duration": meta["video_duration"],
            "clip_duration": meta["clip_duration"],
            "bg_version": int(time.time() * 1000),
        }
    )
