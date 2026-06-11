#!/usr/bin/env python3
"""Pre-cut per-clip background videos aligned to each clip's music.

For each AIOZ-GDANCE clip this finds where the clip's music starts inside the
full youtube source video (the 11-char ytid prefix of the clip name), then
cuts a frame-accurate, playable segment of exactly the motion's duration and
saves it under the clip's name (``<out>/<clip>.mp4``). The result is what the
motion-studio tool loads as the clip's background: it is already aligned, so
the tool embeds it as-is with no further trimming.

The audio alignment uses the same MFCC sliding-correlation as the tool
(:func:`motion_studio.smpl.convert.audio_offset`).

Example:
  python scripts/precut_videos.py \\
    --motions /path/to/GDance/motions_smpl \\
    --musics  /path/to/GDance/musics \\
    --src-videos /path/to/GDance_src/videos \\
    --out /path/to/GDance_src/clip_videos \\
    -4yoUMiBwXg_01_0_960 GSKxQcb1PTU_03_0_137

  python scripts/precut_videos.py ... --all
"""
from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
from typing import List, Optional, Sequence

from motion_studio import library
from motion_studio.smpl import convert
from motion_studio.smpl import io as smpl_io

_VIDEO_EXTS = (".mp4", ".mov", ".webm", ".mkv")
_MUSIC_EXTS = (".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac")


def _match(stem: str, folder: str, exts: Sequence[str]) -> Optional[str]:
    """Return ``folder/<stem><ext>`` for the first existing ext, or None."""
    for ext in exts:
        candidate = os.path.join(folder, stem + ext)
        if os.path.isfile(candidate):
            return candidate
    return None


def _video_fps(video_path: str) -> float:
    """Return the native frame rate of ``video_path`` via ffprobe.

    Args:
      video_path: Path to a video file.

    Returns:
      Frames per second; falls back to :data:`convert.DEFAULT_FPS` on failure.
    """
    try:
        out = subprocess.run(
            [convert.FFPROBE, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=r_frame_rate",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        text = out.stdout.decode().strip()
        if "/" in text:
            num, den = text.split("/")
            den_f = float(den)
            if den_f:
                return float(num) / den_f
        return float(text)
    except Exception:  # noqa: BLE001 - probe failure -> default fps
        return float(convert.DEFAULT_FPS)


def _frame_count(video_path: str) -> Optional[int]:
    """Return the number of decoded video frames via ffprobe, or None."""
    try:
        out = subprocess.run(
            [convert.FFPROBE, "-v", "error", "-select_streams", "v:0",
             "-count_frames", "-show_entries", "stream=nb_read_frames",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return int(out.stdout.decode().strip())
    except Exception:  # noqa: BLE001 - probe failure
        return None


def _cut(src: str, start_sec: float, duration_sec: float, dst: str) -> None:
    """Cut a frame-accurate, playable ``[start, start+dur]`` segment of ``src``.

    Re-encodes (accurate seek, not nearest-keyframe) so the output's frames
    advance from the exact start. Audio is dropped; the segment is muxed with
    ``+faststart`` so players can seek it.

    Args:
      src: Full source video path.
      start_sec: Start offset into ``src``, in seconds.
      duration_sec: Length of the cut, in seconds.
      dst: Destination .mp4 path (overwritten).

    Raises:
      subprocess.CalledProcessError: If ffmpeg fails.
    """
    subprocess.run(
        [convert.FFMPEG, "-y", "-ss", "%.4f" % max(0.0, start_sec), "-i", src,
         "-t", "%.4f" % max(0.0, duration_sec),
         "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
         "-an", "-movflags", "+faststart", dst],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def precut_clip(clip: str, motions_dir: str, musics_dir: str,
                src_videos_dir: str, out_dir: str) -> bool:
    """Pre-cut one clip's aligned background video into ``out_dir``.

    Args:
      clip: Clip name (motion .pkl stem).
      motions_dir: Folder of ``<clip>.pkl`` motion files.
      musics_dir: Folder of ``<clip>.wav`` music files.
      src_videos_dir: Folder of full ``<ytid>.mp4`` source videos.
      out_dir: Output folder; the cut is written to ``<out_dir>/<clip>.mp4``.

    Returns:
      True if a video was written, False if the clip was skipped.
    """
    motion_path = _match(clip, motions_dir, (".pkl",))
    if motion_path is None:
        print("[skip] %s: no motion pkl in %s" % (clip, motions_dir))
        return False

    ytid = library.clip_ytid(clip)
    src_video = _match(ytid, src_videos_dir, _VIDEO_EXTS)
    if src_video is None:
        print("[skip] %s: no source video %s.* in %s"
              % (clip, ytid, src_videos_dir))
        return False

    motion = smpl_io.load_motion_pkl(motion_path)
    n_frames = motion.n_frames
    fps = float(motion.fps or convert.DEFAULT_FPS)
    dur = n_frames / fps

    music_path = _match(clip, musics_dir, _MUSIC_EXTS)
    offset = 0.0
    if music_path is None:
        print("[warn] %s: no music; using offset 0.0 (head of video)" % clip)
    else:
        try:
            vid_dur = convert.video_duration(src_video)
            res = convert.audio_offset(
                music_path, src_video, clip_duration=dur, vid_duration=vid_dur)
            offset = float(res[0]) if res and res[0] is not None else 0.0
        except Exception as exc:  # noqa: BLE001 - never crash the batch
            print("[warn] %s: audio_offset failed (%s); using offset 0.0"
                  % (clip, exc))
            offset = 0.0

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, clip + ".mp4")
    try:
        _cut(src_video, offset, dur, out_path)
    except subprocess.CalledProcessError as exc:
        print("[skip] %s: ffmpeg cut failed (%s)" % (clip, exc))
        return False

    n_out = _frame_count(out_path)
    size = os.path.getsize(out_path) if os.path.isfile(out_path) else 0
    print("[ok]   %s: offset=%.3fs dur=%.3fs (T=%d @ %.2ffps) "
          "out_frames=%s size=%.2fMB -> %s"
          % (clip, offset, dur, n_frames, fps,
             n_out, size / 1e6, out_path))
    return True


def _all_clips(motions_dir: str) -> List[str]:
    """Return every clip name (``.pkl`` stem) in ``motions_dir``, sorted."""
    return sorted(
        os.path.splitext(os.path.basename(p))[0]
        for p in glob.glob(os.path.join(motions_dir, "*.pkl")))


def _build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for the precut CLI."""
    p = argparse.ArgumentParser(
        prog="precut_videos",
        description="Pre-cut per-clip background videos aligned to the music.")
    p.add_argument("--motions", required=True,
                   help="Folder of <clip>.pkl motion files (motions_smpl).")
    p.add_argument("--musics", required=True,
                   help="Folder of <clip>.wav music files (musics).")
    p.add_argument("--src-videos", dest="src_videos", required=True,
                   help="Folder of full <ytid>.mp4 source videos.")
    p.add_argument("--out", required=True,
                   help="Output folder for the cut <clip>.mp4 videos.")
    p.add_argument("--all", action="store_true",
                   help="Process every clip found under --motions.")
    p.add_argument("clips", nargs="*",
                   help="Clip names to process (ignored when --all is given).")
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse arguments and pre-cut the requested clips.

    Args:
      argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
      Process exit code (0 if at least one clip was written, else 1).
    """
    args = _build_parser().parse_args(argv)
    if args.all:
        clips = _all_clips(args.motions)
    else:
        clips = list(args.clips)
    if not clips:
        print("no clips to process (pass clip names or --all)")
        return 1

    n_done = 0
    for clip in clips:
        if precut_clip(clip, args.motions, args.musics,
                       args.src_videos, args.out):
            n_done += 1
    print("done: %d/%d clips written to %s" % (n_done, len(clips), args.out))
    return 0 if n_done else 1


if __name__ == "__main__":
    sys.exit(main())
