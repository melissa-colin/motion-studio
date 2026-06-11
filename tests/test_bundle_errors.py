"""Error-path tests for the ``.motion`` bundle loader.

Complements ``test_bundle.py`` (happy-path round trips) with the malformed-input
contract: a bundle missing its manifest, a bundle with no edited motion, and a
file that is not a valid zip at all. These are written against the post-Phase-3
behavior in which :func:`load_bundle` raises ``ValueError`` on a missing or
non-Motion-Studio manifest rather than leaking a bare ``KeyError``.
"""

from __future__ import annotations

import io
import zipfile

import numpy as np
import pytest

from motion_studio import bundle as bundle_mod
from motion_studio.bundle import load_bundle, save_bundle
from motion_studio.core.types import Motion


def _make_motion(seed: int = 0) -> Motion:
    """Build a tiny synthetic 1-person, 3-frame motion."""
    rng = np.random.default_rng(seed)
    return Motion(
        poses=rng.standard_normal((1, 3, 24, 3)).astype(np.float32),
        trans=rng.standard_normal((1, 3, 3)).astype(np.float32),
        name="clip",
    )


def _motion_npz_bytes(motion: Motion) -> bytes:
    """Serialize ``motion`` to the .npz bytes the loader expects."""
    buffer = io.BytesIO()
    np.savez(buffer, **bundle_mod.motion_to_npz_dict(motion))
    return buffer.getvalue()


def test_missing_manifest_raises_value_error(tmp_path) -> None:
    """A bundle whose archive omits ``manifest.json`` raises ValueError."""
    path = tmp_path / "no_manifest.motion"
    # A zip with a valid original motion member but no manifest.
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("motion_original.npz", _motion_npz_bytes(_make_motion()))
    with pytest.raises(ValueError):
        load_bundle(str(path))


def test_wrong_format_manifest_raises_value_error(tmp_path) -> None:
    """A manifest that is not a Motion Studio bundle raises ValueError."""
    path = tmp_path / "wrong_format.motion"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", '{"format": "something-else"}')
        zf.writestr("motion_original.npz", _motion_npz_bytes(_make_motion()))
    with pytest.raises(ValueError):
        load_bundle(str(path))


def test_no_edited_bundle_loads_edited_none(tmp_path) -> None:
    """A bundle saved without an edited motion loads ``edited is None``."""
    original = _make_motion(seed=5)
    path = tmp_path / "noedit.motion"
    save_bundle(str(path), original=original, edited=None)

    loaded = load_bundle(str(path))
    assert loaded.edited is None
    assert loaded.manifest["format"] == "motion-studio"
    assert np.allclose(loaded.original.poses, original.poses)


def test_corrupt_zip_errors_cleanly(tmp_path) -> None:
    """A file that is not a zip raises ``zipfile.BadZipFile`` (no crash)."""
    path = tmp_path / "garbage.motion"
    path.write_bytes(b"this is definitely not a zip archive")
    with pytest.raises(zipfile.BadZipFile):
        load_bundle(str(path))


def test_truncated_zip_errors_cleanly(tmp_path) -> None:
    """A bundle truncated mid-archive raises a clean exception, not a hang."""
    good = tmp_path / "good.motion"
    save_bundle(str(good), original=_make_motion(seed=6))
    blob = good.read_bytes()
    truncated = tmp_path / "truncated.motion"
    truncated.write_bytes(blob[: len(blob) // 2])
    # A truncated bundle may fail in several low-level ways (zip/json/struct);
    # the contract here is only that loading a corrupt file raises, not how.
    with pytest.raises(Exception):  # noqa: B017
        load_bundle(str(truncated))
