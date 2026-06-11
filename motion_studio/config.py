"""Runtime configuration for a Motion Studio server instance.

Everything that ties the editor to a particular machine or dataset lives here:
the workspace where .motion bundles are stored, the three data directories
(SMPL ``.pkl`` motions, per-clip background videos, music), the SMPL body-model
directory, and the plugin specs for the auto-correction, metrics and floor
classes.

The data directories and plugin specs are persisted to ``workspace/config.json``
and configured from the UI, so the editor launches with at most a few CLI flags
(``--corrector`` / ``--metrics`` / ``--floor`` / ``--port``).
"""

from __future__ import annotations

import dataclasses
import json
import os

# Plugin specs are "<module-or-path>:<Class>" (see core.plugins).
DEFAULT_CORRECTOR = "motion_studio.plugins_builtin.corrector:Corrector"
DEFAULT_METRICS = "motion_studio.plugins_builtin.metrics:Metrics"
DEFAULT_FLOOR = "motion_studio.plugins_builtin.floor:Floor"

DEFAULT_SMPL_DIR = os.environ.get(
    "SMPL_DIR", os.path.expanduser("~/smpl/models")
)
DEFAULT_WORKSPACE = os.environ.get(
    "MOTION_STUDIO_HOME", os.path.expanduser("~/MotionStudio")
)

# Data-source settings persisted to ``workspace/config.json`` so the editor can
# be launched with no data flags and configured entirely from the UI.
CONFIG_FILE_NAME = "config.json"
_PERSIST_FIELDS = (
    "pkl_dir",
    "videos_dir",
    "audio_dir",
    "smpl_dir",
    "corrector_spec",
    "metrics_spec",
    "floor_spec",
    "floors_json",
)


@dataclasses.dataclass
class Config:
    """Resolved settings for one running server.

    Attributes:
      workspace: Root directory holding the saved .motion bundles.
      pkl_dir: Optional folder of raw SMPL ``.pkl`` motions (one ``<clip>.pkl``
        per clip); None if unset. This is the source for "load a file" and the
        per-clip / folder imports.
      videos_dir: Optional folder of pre-cut per-clip background videos named by
        the exact clip name (``<clip>.mp4``); matched as-is (no trimming).
      audio_dir: Optional folder of per-clip music named by the exact clip name
        (``<clip>.wav|mp3|...``); matched by name at import.
      smpl_dir: Directory containing the SMPL body model files.
      corrector_spec: Plugin spec for the auto-correction class.
      metrics_spec: Plugin spec for the metrics class.
      floor_spec: Plugin spec for the floor (ground-plane) estimator class.
      floors_json: Optional path to a floors.json reference used by the
        built-in corrector; None to let it estimate floors itself.
      host: Interface to bind.
      port: TCP port to serve on.
    """

    workspace: str = DEFAULT_WORKSPACE
    pkl_dir: str | None = None
    videos_dir: str | None = None
    audio_dir: str | None = None
    smpl_dir: str = DEFAULT_SMPL_DIR
    corrector_spec: str = DEFAULT_CORRECTOR
    metrics_spec: str = DEFAULT_METRICS
    floor_spec: str = DEFAULT_FLOOR
    floors_json: str | None = None
    host: str = "127.0.0.1"
    port: int = 8815

    def ensure_dirs(self) -> None:
        """Create the workspace directory tree if it does not exist."""
        os.makedirs(self.workspace, exist_ok=True)
        os.makedirs(os.path.join(self.workspace, "bundles"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace, "cache"), exist_ok=True)

    def save(self) -> None:
        """Persist the data-source fields to ``workspace/config.json``.

        A later bare launch (or the UI) then reuses them.
        """
        path = os.path.join(self.workspace, CONFIG_FILE_NAME)
        data = {f: getattr(self, f) for f in _PERSIST_FIELDS}
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
        except OSError:
            pass


def _migrate_legacy(data: dict) -> dict:
    """Map a pre-3-paths ``config.json`` onto the current field names.

    Older configs stored a single ``data_dir`` with ``motions_smpl/`` and
    ``musics/`` subfolders (plus a separate ``videos_dir``). Derive the new
    ``pkl_dir`` / ``audio_dir`` from it when the new keys are absent so an
    existing workspace keeps working after upgrade. The new keys always win.

    Args:
      data: The raw, parsed ``config.json`` mapping.

    Returns:
      The same mapping with ``pkl_dir`` / ``audio_dir`` filled in from a legacy
      ``data_dir`` when needed.
    """
    legacy = data.get("data_dir")
    if legacy:
        pkl = os.path.join(legacy, "motions_smpl")
        music = os.path.join(legacy, "musics")
        data.setdefault("pkl_dir", pkl if os.path.isdir(pkl) else legacy)
        if os.path.isdir(music):
            data.setdefault("audio_dir", music)
    return data


def load_persisted(workspace: str) -> dict:
    """Return the persisted data-source fields for ``workspace``.

    ``{}`` if the file is missing or unreadable. Only known, non-empty fields
    are returned.
    """
    path = os.path.join(workspace, CONFIG_FILE_NAME)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    data = _migrate_legacy(data)
    return {k: v for k, v in data.items() if k in _PERSIST_FIELDS and v}
