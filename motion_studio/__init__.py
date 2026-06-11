"""Motion Studio: a clean, installable multi-person SMPL motion editor.

The names re-exported here are the package's stable public API. Everything in
this top-level namespace is torch-free and safe to import in a numpy+flask-only
("core") install: the heavy server stack and the built-in torch/SMPL plugins
are imported lazily, never at package import time.

Typical use::

    import motion_studio as ms

    bundle = ms.load_bundle("session.motion")
    motion = bundle.original                       # ms.Motion
    corrector = ms.load_corrector(ms.Config().corrector_spec,
                                  smpl_dir="~/smpl/models")
    fixed = corrector.correct(motion)
    ms.save_motion_pkl(fixed, "fixed.pkl")
"""

from __future__ import annotations

from .bundle import load_bundle, save_bundle
from .config import Config
from .core.plugins import (
    MotionCorrector,
    MotionMetrics,
    load_corrector,
    load_metrics,
)
from .core.types import Floor, Motion
from .library import import_dataset, scan_dataset
from .smpl.io import load_motion_pkl, save_motion_pkl

__version__ = "0.1.3"

__all__ = [
    # Core data types.
    "Motion",
    "Floor",
    # Plugin contracts + loaders.
    "MotionCorrector",
    "MotionMetrics",
    "load_corrector",
    "load_metrics",
    # SMPL pkl I/O.
    "load_motion_pkl",
    "save_motion_pkl",
    # .motion bundle I/O.
    "save_bundle",
    "load_bundle",
    # Dataset discovery / import.
    "scan_dataset",
    "import_dataset",
    # Configuration.
    "Config",
    "__version__",
]
