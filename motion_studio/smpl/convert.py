"""Build editor scenes from a :class:`Motion`, and handle video/music.

Vendored and adapted from the legacy pose-editor ``convert_clip.py``. The old
module was wired to a raw GDance directory layout; this version is built around
the Motion Studio data model: it works on a :class:`~motion_studio.core.types.
Motion` (already z-up) plus optional raw video/music bytes from a ``.motion``
bundle.

It provides:
  * :func:`fk_joints` / :func:`build_scene` -- SMPL forward kinematics to the
    z-up joints the frontend draws, and the ``scene.json``-shaped dict.
  * :class:`MeshState` / :func:`verts_for_frame` -- lazy per-frame SMPL mesh.
  * :func:`extract_frames` / :func:`audio_offset` / :func:`video_duration` --
    ffmpeg/ffprobe-backed background-video helpers (used by ``/set_bg_offset``).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import torch

from motion_studio.core.types import Motion
from motion_studio.plugins_builtin.utils.motion_utils import (
    smpl_forward_one_person,
)

# SMPL kinematic tree (parent of each of the 24 joints; root = -1).
SMPL_PARENTS = [
    -1,
    0,
    0,
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    9,
    9,
    12,
    13,
    14,
    16,
    17,
    18,
    19,
    20,
    21,
]
DEFAULT_FPS = 30


def _find_tool(name: str) -> str:
    """Return a path to ``name`` (ffmpeg/ffprobe).

    Resolution order: the ``MOTION_STUDIO_FFMPEG`` environment variable (only
    honored for ``ffmpeg``), then ``$PATH`` via :func:`shutil.which`, then the
    bare name as a last resort.

    Args:
      name: Executable base name, e.g. ``"ffmpeg"``.

    Returns:
      An absolute path to the tool, or just ``name`` to rely on ``$PATH``.
    """
    if name == "ffmpeg":
        override = os.environ.get("MOTION_STUDIO_FFMPEG")
        if override:
            return override
    found = shutil.which(name)
    return found or name


FFMPEG = _find_tool("ffmpeg")
FFPROBE = _find_tool("ffprobe")
OUTRO_MARGIN = 4.0


def _build_smpl(smpl_dir: str, batch_size: int, device: torch.device):
    """Return a freshly built ``smplx.SMPL`` NEUTRAL model on ``device``."""
    from smplx import SMPL

    return SMPL(
        model_path=smpl_dir, gender="NEUTRAL", batch_size=batch_size
    ).to(device)


def fk_joints(
    motion: Motion,
    smpl_dir: str,
    device: torch.device | None = None,
    want_mesh: bool = False,
):
    """Run SMPL forward kinematics on a z-up :class:`Motion`.

    Args:
      motion: The motion, poses ``(N, T, 24, 3)`` and trans ``(N, T, 3)`` z-up.
      smpl_dir: Directory containing the SMPL body model files.
      device: Torch device; defaults to cuda if available.
      want_mesh: Whether to also return vertices and faces.

    Returns:
      ``(joints, fps, verts, faces)`` where ``joints`` is ``(N, T, 24, 3)``,
      ``verts`` is ``(N, T, 6890, 3)`` or None and ``faces`` is ``(F, 3)`` or
      None.
    """
    import torch

    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    poses = np.asarray(motion.poses, dtype=np.float32)
    trans = np.asarray(motion.trans, dtype=np.float32)
    n_persons, n_frames = poses.shape[:2]
    smpl = _build_smpl(smpl_dir, n_frames, device)
    pz = poses.reshape(n_persons, n_frames, 72)
    jlist, vlist = [], []
    for n in range(n_persons):
        out = smpl_forward_one_person(pz[n], trans[n], smpl, device=device)
        jlist.append(out["Jtr"].numpy())
        if want_mesh:
            vlist.append(out["v"].numpy())
    joints = np.stack(jlist, 0).astype(np.float32)
    verts = faces = None
    if want_mesh:
        verts = np.stack(vlist, 0).astype(np.float32)
        faces = smpl.faces.astype(np.int32)
    return joints, float(motion.fps or DEFAULT_FPS), verts, faces


def build_scene(
    motion: Motion,
    smpl_dir: str,
    *,
    source: str = "original",
    device: torch.device | None = None,
) -> dict:
    """Build the ``scene.json``-shaped dict the frontend consumes.

    Args:
      motion: The z-up motion to render.
      smpl_dir: Directory containing the SMPL body model files.
      source: Label echoed back in the scene (e.g. ``"original"``).
      device: Torch device; defaults to cuda if available.

    Returns:
      A dict with ``name, source, fps, N, T, J, parents, joints`` (flat list)
      and placeholder video/music fields the server fills in.
    """
    joints, fps, _verts, _faces = fk_joints(
        motion, smpl_dir, device=device, want_mesh=False
    )
    n_persons, n_frames, n_joints, _ = joints.shape
    clip_dur = n_frames / float(fps)
    return {
        "name": motion.name,
        "source": source,
        "fps": int(fps),
        "N": int(n_persons),
        "T": int(n_frames),
        "J": int(n_joints),
        "parents": SMPL_PARENTS,
        "frame_w": 640,
        "frame_h": 360,
        "frames": [],
        "has_video": False,
        "has_music": False,
        "video_duration": None,
        "clip_duration": round(clip_dur, 3),
        "bg_offset": None,
        "joints": np.round(joints, 5).reshape(-1).tolist(),
    }


class MeshState:
    """Reusable SMPL state for per-frame mesh forward kinematics.

    Loads the pkl-equivalent poses and the SMPL model once; each
    :func:`verts_for_frame` call is then a single one-frame forward.

    Attributes:
      pz: ``(N, T, 72)`` z-up axis-angle poses.
      tz: ``(N, T, 3)`` z-up root translations.
      smpl: A ``smplx.SMPL`` model with ``batch_size=1``.
      faces: ``(F, 3)`` int32 mesh faces.
      device: The torch device the model lives on.
      n_persons: Number of dancers.
      n_frames: Number of frames.
    """

    def __init__(
        self,
        motion: Motion,
        smpl_dir: str,
        device: torch.device | None = None,
    ) -> None:
        import torch

        if device is None:
            device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu"
            )
        poses = np.asarray(motion.poses, dtype=np.float32)
        trans = np.asarray(motion.trans, dtype=np.float32)
        self.n_persons, self.n_frames = poses.shape[:2]
        self.pz = poses.reshape(self.n_persons, self.n_frames, 72)
        self.tz = trans
        self.smpl = _build_smpl(smpl_dir, 1, device)
        self.faces = self.smpl.faces.astype(np.int32)
        self.device = device


def verts_for_frame(state: MeshState, t: int) -> np.ndarray:
    """Return the SMPL vertices of one frame, ``(N, 6890, 3)`` z-up.

    Args:
      state: A :class:`MeshState` built for the clip.
      t: Frame index.

    Returns:
      ``(N, 6890, 3)`` float32 vertices.

    Raises:
      IndexError: If ``t`` is out of range.
    """
    if not (0 <= t < state.n_frames):
        raise IndexError("frame %d out of range [0,%d)" % (t, state.n_frames))
    vlist = []
    for n in range(state.n_persons):
        out = smpl_forward_one_person(
            state.pz[n][t : t + 1],
            state.tz[n][t : t + 1],
            state.smpl,
            device=state.device,
        )
        vlist.append(out["v"].numpy()[0])
    return np.stack(vlist, 0).astype(np.float32)


def video_duration(video_path: str) -> float | None:
    """Return the duration (seconds) of a video via ffprobe, or None.

    Args:
      video_path: Path to a video file.

    Returns:
      The duration in seconds, or None on failure / missing file.
    """
    if not os.path.isfile(video_path):
        return None
    try:
        out = subprocess.run(
            [
                FFPROBE,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                video_path,
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        return float(out.stdout.decode().strip())
    except Exception:
        return None


def trim_video(
    src: str, start_sec: float, duration_sec: float, dst: str
) -> None:
    """Re-encode a frame-accurate ``[start, start+duration]`` cut of ``src``.

    Unlike a stream copy, this re-encodes so the cut starts exactly at
    ``start_sec`` (no nearest-keyframe rounding). Audio is kept (AAC); it is
    tiny and lets a caller re-derive the music sync if needed.

    Args:
      src: Source video path (a full youtube video).
      start_sec: Start offset into ``src``, in seconds.
      duration_sec: Length of the cut, in seconds.
      dst: Destination .mp4 path (overwritten).

    Returns:
      None.

    Raises:
      subprocess.CalledProcessError: If ffmpeg fails.
    """
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-ss",
            f"{max(0.0, start_sec):.4f}",
            "-i",
            src,
            "-t",
            f"{max(0.0, duration_sec):.4f}",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            dst,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def audio_offset(
    music_wav: str,
    video_mp4: str,
    hop: int = 512,
    sr: int = 22050,
    n_mfcc: int = 20,
    clip_duration: float | None = None,
    vid_duration: float | None = None,
) -> tuple[float, float, float]:
    """Find the offset (s) of the clip music inside the video's audio.

    Slides the short MFCC sequence (music) over the long one (video audio) and
    picks the lag maximizing correlation; MFCCs disambiguate looped
    choreography that fools a plain RMS envelope.

    Args:
      music_wav: Path to the clip music wav.
      video_mp4: Path to the source video.
      hop: MFCC hop length in samples.
      sr: Resampling rate.
      n_mfcc: Number of MFCC coefficients.
      clip_duration: Clip duration (s), to skip end-of-video outro matches.
      vid_duration: Video duration (s), used with ``clip_duration``.

    Returns:
      ``(offset_sec, score_ratio, music_duration)``.
    """
    import librosa

    ym, _ = librosa.load(music_wav, sr=sr, mono=True)
    dur_music = len(ym) / sr
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        tmp_wav = tf.name
    try:
        subprocess.run(
            [
                FFMPEG,
                "-y",
                "-i",
                video_mp4,
                "-ac",
                "1",
                "-ar",
                str(sr),
                "-vn",
                tmp_wav,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        yv, _ = librosa.load(tmp_wav, sr=sr, mono=True)
    finally:
        if os.path.exists(tmp_wav):
            os.remove(tmp_wav)

    mm = librosa.feature.mfcc(y=ym, sr=sr, n_mfcc=n_mfcc, hop_length=hop)
    mv = librosa.feature.mfcc(y=yv, sr=sr, n_mfcc=n_mfcc, hop_length=hop)
    mm = mm - mm.mean(axis=1, keepdims=True)
    mv = mv - mv.mean(axis=1, keepdims=True)
    length = mm.shape[1]
    if mv.shape[1] < length:
        return 0.0, 0.0, dur_music
    n_off = mv.shape[1] - length + 1
    scores = np.zeros(n_off, dtype=np.float64)
    for c in range(n_mfcc):
        scores += np.correlate(mv[c], mm[c], mode="valid")[:n_off]

    def _sec(o):
        return o * hop / sr

    off = int(np.argmax(scores))
    if clip_duration is not None and vid_duration is not None and n_off > 1:
        outro_start = vid_duration - clip_duration - OUTRO_MARGIN
        if _sec(off) > outro_start:
            order = np.argsort(scores)[::-1]
            best_peak = float(scores[off])
            for cand in order:
                if _sec(int(cand)) <= outro_start:
                    if scores[cand] >= 0.70 * best_peak:
                        off = int(cand)
                    break

    if n_off > 1:
        second = np.partition(scores, -2)[-2]
        ratio = float(scores[off] / (second + 1e-9))
    else:
        ratio = 1.0
    return _sec(off), ratio, dur_music


def extract_frames(
    video_mp4: str,
    start_sec: float,
    n_frames: int,
    fps: float,
    out_dir: str,
    width: int | None = None,
):
    """Extract ``n_frames`` PNGs from ``start_sec`` at ``fps`` into ``out_dir``.

    Args:
      video_mp4: Source video path.
      start_sec: Start offset in seconds.
      n_frames: Number of frames to keep.
      fps: Sampling rate for extraction.
      out_dir: Destination directory (created/cleaned).
      width: Optional output width (height auto, keeps aspect).

    Returns:
      ``(w, h, n_extracted)`` or None if nothing was extracted.
    """
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.lower().endswith((".png", ".jpg", ".jpeg")):
            os.remove(os.path.join(out_dir, f))
    dur = n_frames / float(fps)
    vf = f"fps={fps}"
    if width:
        vf += ",scale=%d:-2" % width
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-ss",
            f"{start_sec:.4f}",
            "-i",
            video_mp4,
            "-t",
            "%.4f" % (dur + 0.5),
            "-vf",
            vf,
            "-start_number",
            "0",
            os.path.join(out_dir, "%04d.png"),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    pngs = sorted(f for f in os.listdir(out_dir) if f.endswith(".png"))
    for f in pngs[n_frames:]:
        os.remove(os.path.join(out_dir, f))
    pngs = pngs[:n_frames]
    if not pngs:
        return None
    try:
        from PIL import Image

        with Image.open(os.path.join(out_dir, pngs[0])) as im:
            w, h = im.size
    except Exception:
        w, h = (width or 640), 360
    return w, h, len(pngs)
