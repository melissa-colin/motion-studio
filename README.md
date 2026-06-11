# Motion Studio

[![PyPI version](https://img.shields.io/pypi/v/motion-studio.svg)](https://pypi.org/project/motion-studio/)
[![Python versions](https://img.shields.io/pypi/pyversions/motion-studio.svg)](https://pypi.org/project/motion-studio/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/melissa-colin/motion-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/melissa-colin/motion-studio/actions/workflows/ci.yml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-261230.svg)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A clean, installable **multi-person SMPL motion editor** for the browser, with
a 3D view (Three.js), a video/music background, frame-by-frame pose editing,
and **pluggable** auto-correction and metrics.

It started as an internal pose editor for the AIOZ-GDANCE dataset and was
rewritten as a small, modular, self-contained tool: no dependency on any
external research repo, a single save-file format, and a plugin contract so you
can drop in **your own** correction / metrics classes without touching the app.

![Motion Studio — playing a clip over its source video while orbiting the camera](https://raw.githubusercontent.com/melissa-colin/motion-studio/main/docs/img/demo.gif)

*Editing a multi-person clip: the SMPL motion and the source video play in sync while you orbit the camera.*

---

## Features

- **3D editor**: skeleton + SMPL mesh, per-joint and whole-body editing, undo/redo.
- **Video & music background**: place the source video in the scene (position,
  scale, opacity, time offset), server-side background removal, audio playback
  synced to the timeline.
- **Floor**: estimate / edit / recompute the ground plane.
- **Auto-correction & metrics**: run a corrector and score the motion; both are
  **plugins**. The built-ins are simple, generic reference implementations
  (floor grounding + geometric metrics) — swap in your own for anything more.
- **One save file**: a `.motion` bundle holds the original motion, your edits,
  the video, the music, placement parameters, comments and a metrics snapshot.
- **Two ways to load**: open a single SMPL `.pkl` (with optional video/music),
  or point at your data directories (a flat `pkl_dir/`, plus optional
  `videos_dir/` and `audio_dir/` matched by clip name) and convert them into the
  workspace.

---

## Screenshots

![The 3D editor](https://raw.githubusercontent.com/melissa-colin/motion-studio/main/docs/img/editor.png)
*The 3D editor: multiple SMPL dancers (mesh + skeleton), per-joint and
whole-body editing, the automatic corrector (a plugin), and the live metrics
panel. One **Save (.motion)** button and an **Export (.pkl)** button.*

![Video background](https://raw.githubusercontent.com/melissa-colin/motion-studio/main/docs/img/video.png)
*The source video as a placeable background — position, scale, opacity, time
offset and server-side background removal — to check the motion against the
real footage.*

![Estimated floor](https://raw.githubusercontent.com/melissa-colin/motion-studio/main/docs/img/floor.png)
*The ground plane is estimated on load (RANSAC on foot contacts) and can be
edited or recomputed.*

![Empty start](https://raw.githubusercontent.com/melissa-colin/motion-studio/main/docs/img/empty.png)
*On startup the editor is empty (no clip auto-loaded, no pop-up). From the
**Clip** tab you choose: browse loaded clips, open a folder, or import a .pkl.*

---

## Install

```bash
pip install "motion-studio[all]"   # recommended: full feature set
```

`[all]` pulls in torch, smplx, torchvision, pillow, librosa and scipy — the SMPL
forward kinematics, pose refit, built-in corrector/metrics, server-side
background removal and music import. Narrower extras are available:

```bash
pip install motion-studio            # core only (numpy + flask): no SMPL/video
pip install "motion-studio[smpl]"    # + torch, smplx
pip install "motion-studio[video]"   # + pillow, torchvision, librosa, scipy
pip install "motion-studio[dev]"     # + pytest, ruff, black, pre-commit
```

Requires Python >= 3.9. The SMPL body models are **not** shipped; point the tool
at your local copy with `--smpl-dir`.

## Run

```bash
motion-studio --port 8815
# optional: point at your own plugins
motion-studio --corrector ./my.py:MyCorrector --metrics ./my.py:MyMetrics
```

Then open <http://127.0.0.1:8815>.

The data directories (SMPL `.pkl` motions, background videos, music) and the
SMPL model directory are configured from the UI ("Data source" / settings) and
persisted to `workspace/config.json`, so a bare relaunch reuses them. The
**workspace** is the root folder that holds your saved `.motion` bundles,
like any desktop app keeps its documents.

When a real (non-default) **metrics** plugin is configured, the server computes
and caches each bundle's reference metrics in the background after launch, so
the library becomes sortable by metric.

---

## Command line

The bare command (or `motion-studio serve`) starts the editor server. Two
headless subcommands run the same plugins from a terminal, no browser:

```bash
motion-studio                                       # start the editor (default)
motion-studio --port 8815                           # on a chosen port

# Run the auto-corrector on a .motion and write the corrected bundle:
motion-studio correct in.motion -o out.motion
motion-studio correct in.motion -o out.motion --corrector ./my.py:MyCorrector

# Compute metrics on a .motion and print them:
motion-studio metrics in.motion
motion-studio metrics in.motion --metrics ./my.py:MyMetrics

motion-studio --version
```

`--corrector` / `--metrics` take a plugin spec (`<module-or-path>:<Class>`),
the same as the server flags; omit them to use the built-in plugins.

---

## Docker

A `Dockerfile` is included. Build the image, then run it with your SMPL models
mounted in and the port published:

```bash
docker build -t motion-studio .
docker run -p 8815:8815 -v ~/smpl/models:/models -e SMPL_DIR=/models motion-studio
```

Then open <http://127.0.0.1:8815>. Mount a host folder to `/workspace` (and set
`MOTION_STUDIO_HOME=/workspace`) to persist your `.motion` bundles across runs.

---

## Python API

Motion Studio is also a library — import it and use the data model, bundle I/O
and plugin loaders directly, headless:

```python
import motion_studio as ms

bundle = ms.load_bundle("session.motion")     # -> Bundle (original/edited + media)
motion = bundle.original                       # -> Motion(poses, trans, betas, …)

corrector = ms.load_corrector(
    "motion_studio.plugins_builtin.corrector:Corrector",
    smpl_dir="~/smpl/models",
)
fixed = corrector.correct(motion)

ms.save_bundle("fixed.motion", original=motion, edited=fixed)
```

The top-level surface (`__all__`) is: `Motion`, `Floor`, `load_bundle`,
`save_bundle`, `load_corrector`, `load_metrics`, `scan_dataset`, `Config`,
`__version__`. The library core imports with only numpy + flask (no torch).

---

## The `.motion` save file

A `.motion` file is a single ZIP archive bundling an entire editing session:

```
manifest.json        format/version, comments, video placement params,
                     metrics snapshot, timestamps
motion_original.npz  the original SMPL motion (poses, trans, betas, fps, gender)
motion_edited.npz    your edited motion (omitted if you have not edited)
video.mp4            the source video (optional)
music.<ext>          the music track (optional)
```

Open a `.motion` to **continue** where you left off; the SMPL `.pkl` is written
out only when you click **Export**.

---

## Plugins: bring your own correction / metrics

Motion Studio depends only on a small contract, not on any concrete
implementation. A plugin is any class matching one of these protocols
(`motion_studio/core/plugins.py`):

```python
class MotionCorrector(Protocol):
    def __init__(self, *, smpl_dir, floor=None): ...
    def correct(self, motion: Motion, log=print) -> Motion: ...

class MotionMetrics(Protocol):
    def __init__(self, *, smpl_dir): ...
    def compute(self, motion: Motion, floor: Floor) -> dict[str, float]: ...
```

`Motion` and `Floor` are the only types exchanged
(`motion_studio/core/types.py`):

```python
@dataclass
class Motion:
    poses: np.ndarray   # (N, T, 24, 3) axis-angle, z-up
    trans: np.ndarray   # (N, T, 3)
    betas: np.ndarray | None
    gender: str
    fps: float
    name: str

@dataclass
class Floor:
    plane: tuple[float, float, float]   # z = a*x + b*y + c
```

Point the tool at your own classes (a dotted module **or** a file path,
followed by the class name); they are re-imported on every run, so edits take
effect on the next click:

```bash
motion-studio --corrector ./my_corrector.py:MyCorrector \
              --metrics   ./my_metrics.py:MyMetrics
```

The built-in plugins live in `motion_studio/plugins_builtin/`. They are
deliberately simple reference implementations — a floor-grounding corrector and
a handful of geometric metrics — there to make the editor work out of the box,
not a research-grade physics pipeline. Point `--corrector`/`--metrics` at your
own classes for anything more.

**New to plugins?** See the full authoring guide in
[`docs/PLUGINS.md`](docs/PLUGINS.md) and the runnable, dependency-light
examples in [`examples/`](examples). For instance, the pure-numpy metrics
example (no torch / no SMPL needed) shows custom keys rendering end to end:

```bash
motion-studio --metrics ./examples/simple_metrics.py:SimpleMetrics
```

---

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — module map, data model,
  request flow, the heavy-lock model, the `.motion` format.
- [`docs/PLUGINS.md`](docs/PLUGINS.md) — the plugin authoring guide.
- [`docs/USAGE.md`](docs/USAGE.md) — day-to-day editor usage.
- [`docs/API.md`](docs/API.md) — the HTTP API.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — dev install, tests, lint/format.
- [`SECURITY.md`](SECURITY.md) — the threat model and `--allow-remote` risk.

---

## Third-party components & attribution

The in-browser 3D view is built on **Three.js** (r160, MIT), vendored under
`motion_studio/static/vendor/` along with its `OrbitControls` / `TransformControls`
addons. Background removal uses **torchvision DeepLabV3-ResNet101** server-side
(BSD-3-Clause) with a client-side **MediaPipe** Image Segmenter fallback
(Apache-2.0). The **SMPL / SMPL-X** body models are **not** shipped — you provide
them yourself under the Max Planck Institute (MPI-IS) non-commercial / research
license. See [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for the full list
of bundled and depended-on components with their licenses and sources.

---

## License

Released under the **MIT License** (see the `LICENSE` file in the repository).
