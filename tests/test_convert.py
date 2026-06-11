"""Tests for the ffmpeg/ffprobe helpers in ``motion_studio.smpl.convert``.

No real ffmpeg/ffprobe/librosa runs: ``subprocess.run`` is monkeypatched to
return stubbed tool output and the ``librosa`` calls inside ``audio_offset`` are
replaced with deterministic fakes, so the parsing/offset-search logic is tested
in isolation.
"""

from __future__ import annotations

import sys
import types

import numpy as np
import pytest

from motion_studio.smpl import convert


class _FakeCompleted:
    """Stand-in for ``subprocess.CompletedProcess`` carrying ``stdout``."""

    def __init__(self, stdout: bytes = b"") -> None:
        self.stdout = stdout
        self.returncode = 0


# -- video_duration ---------------------------------------------------------


def test_video_duration_parses_ffprobe_float(monkeypatch) -> None:
    """A clean ffprobe ``format=duration`` line parses to a float."""
    monkeypatch.setattr(convert.os.path, "isfile", lambda p: True)
    monkeypatch.setattr(
        convert.subprocess,
        "run",
        lambda *a, **k: _FakeCompleted(b"12.340000\n"),
    )
    assert convert.video_duration("any.mp4") == pytest.approx(12.34)


def test_video_duration_missing_file_is_none(monkeypatch) -> None:
    """A missing file short-circuits to None without invoking ffprobe."""
    monkeypatch.setattr(convert.os.path, "isfile", lambda p: False)

    def _boom(*a, **k):
        raise AssertionError("ffprobe must not run for a missing file")

    monkeypatch.setattr(convert.subprocess, "run", _boom)
    assert convert.video_duration("missing.mp4") is None


def test_video_duration_unparseable_output_is_none(monkeypatch) -> None:
    """Garbage on ffprobe stdout is swallowed and returns None."""
    monkeypatch.setattr(convert.os.path, "isfile", lambda p: True)
    monkeypatch.setattr(
        convert.subprocess, "run", lambda *a, **k: _FakeCompleted(b"N/A\n")
    )
    assert convert.video_duration("any.mp4") is None


def test_video_duration_ffprobe_failure_is_none(monkeypatch) -> None:
    """A non-zero ffprobe exit (raised) is caught and returns None."""
    monkeypatch.setattr(convert.os.path, "isfile", lambda p: True)

    def _raise(*a, **k):
        import subprocess

        raise subprocess.CalledProcessError(1, "ffprobe")

    monkeypatch.setattr(convert.subprocess, "run", _raise)
    assert convert.video_duration("any.mp4") is None


# -- audio_offset -----------------------------------------------------------


@pytest.fixture
def fake_librosa(monkeypatch):
    """Install a fake ``librosa`` module with deterministic MFCCs.

    The music MFCC is a short window; the video MFCC embeds that exact window at
    a known column lag, so the correlation search must recover that lag.
    """
    sr = 22050
    hop = 512
    n_mfcc = 4
    lag = 7  # the offset (in MFCC columns) we expect the search to find.

    rng = np.random.default_rng(0)
    music_mfcc = rng.standard_normal((n_mfcc, 15)).astype(np.float64)
    video_mfcc = rng.standard_normal((n_mfcc, 40)).astype(np.float64)
    # Plant the music sequence inside the video at column ``lag``.
    video_mfcc[:, lag : lag + 15] = music_mfcc

    fake = types.ModuleType("librosa")
    fake.feature = types.SimpleNamespace()

    def _load(path, sr=sr, mono=True):  # noqa: ANN001
        # Music wav -> short signal; the extracted video wav -> long signal.
        n = 15 if "music" in str(path) else 40
        return np.zeros(n * hop, dtype=np.float32), sr

    def _mfcc(y=None, sr=sr, n_mfcc=n_mfcc, hop_length=hop):  # noqa: ANN001
        return music_mfcc if len(y) // hop <= 15 else video_mfcc

    fake.load = _load
    fake.feature.mfcc = _mfcc
    monkeypatch.setitem(sys.modules, "librosa", fake)
    return types.SimpleNamespace(sr=sr, hop=hop, n_mfcc=n_mfcc, lag=lag)


def test_audio_offset_recovers_planted_lag(monkeypatch, fake_librosa) -> None:
    """``audio_offset`` recovers the planted music-in-video column lag."""
    # ffmpeg (audio extraction) is stubbed: it just "succeeds".
    monkeypatch.setattr(
        convert.subprocess, "run", lambda *a, **k: _FakeCompleted(b"")
    )
    # Avoid touching the real filesystem for the temp-wav cleanup.
    monkeypatch.setattr(convert.os.path, "exists", lambda p: False)

    offset, ratio, dur_music = convert.audio_offset(
        "music.wav",
        "video.mp4",
        hop=fake_librosa.hop,
        sr=fake_librosa.sr,
        n_mfcc=fake_librosa.n_mfcc,
    )

    expected = fake_librosa.lag * fake_librosa.hop / fake_librosa.sr
    assert offset == pytest.approx(expected, abs=1e-9)
    # A clean planted match scores well above the runner-up.
    assert ratio > 1.0
    assert dur_music == pytest.approx(15 * fake_librosa.hop / fake_librosa.sr)


def test_audio_offset_short_video_returns_zero(monkeypatch) -> None:
    """When video audio is shorter than the music, offset falls back to 0."""
    sr, hop, n_mfcc = 22050, 512, 4
    music_mfcc = np.zeros((n_mfcc, 30), dtype=np.float64)
    video_mfcc = np.zeros((n_mfcc, 10), dtype=np.float64)  # shorter than music

    fake = types.ModuleType("librosa")
    fake.feature = types.SimpleNamespace()
    fake.load = lambda path, sr=sr, mono=True: (
        np.zeros((30 if "music" in str(path) else 10) * hop, np.float32),
        sr,
    )
    fake.feature.mfcc = lambda y=None, sr=sr, n_mfcc=n_mfcc, hop_length=hop: (
        music_mfcc if len(y) // hop >= 30 else video_mfcc
    )
    monkeypatch.setitem(sys.modules, "librosa", fake)
    monkeypatch.setattr(
        convert.subprocess, "run", lambda *a, **k: _FakeCompleted(b"")
    )
    monkeypatch.setattr(convert.os.path, "exists", lambda p: False)

    offset, ratio, dur_music = convert.audio_offset(
        "music.wav", "video.mp4", hop=hop, sr=sr, n_mfcc=n_mfcc
    )
    assert offset == 0.0
    assert ratio == 0.0
