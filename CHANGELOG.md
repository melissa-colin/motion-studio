# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.3] - 2026-06-11

### Changed

- **Floor estimation is now a plugin** (`MotionFloor`, `--floor`), like the
  corrector and metrics. The bundled default is a generic reference estimator
  (lowest foot-sole points + textbook RANSAC plane fit); point `--floor` at your
  own class for anything more sophisticated. This removes the previous bundled
  floor heuristic in favour of a clean, swappable contract.

## [0.1.2] - 2026-06-10

### Added

- **Three independent data directories** (`pkl_dir` / `videos_dir` / `audio_dir`,
  matched by exact clip name) replacing the single `data_dir` + `motions_smpl/
  musics/smpl_videos` convention. Configured from the UI and persisted to
  `workspace/config.json`; a legacy `data_dir` config is migrated automatically.
- **Three loading entry points** (in the Fichier menu): load a single `.pkl`,
  load an existing `.motion` project, or load a whole folder (background import
  with progress).
- **Unified projects browser** sortable by name, source, media and **per-metric**
  columns, with prev/next navigation.
- **Background jobs** (`server/jobs.py`): folder import (`/import_status`),
  reference-metrics warm-up that caches each bundle's metrics in its manifest so
  the library is sortable by metric (`/metrics_status`, `/metrics_all`; runs at
  boot when a non-default metrics plugin is configured), and whole-clip
  background-crop prewarm (`/prewarm_bg`, `/prewarm_status`).
- New endpoints `/import_clip`, plus client-side background-crop prefetch and a
  three-resource loading indicator to stop playback freezes.
- `THIRD_PARTY_NOTICES.md` documenting third-party components (Three.js,
  torchvision DeepLabV3, MediaPipe, SMPL/SMPL-X, …).
- **Remote-friendly playback**: mesh frames are streamed as float16 (half the
  bytes) with immutable, versioned caching, and a clip is pre-buffered behind
  the loading screen so playback and scrubbing are smooth once it is cached.
- **Background jobs yield to the editor**: the metrics warm-up / segmentation
  prewarm run at background priority and pause while you interact, so a
  full-library pass never stalls playback.

### Changed

- **Real-software UI shell**: a top menu bar (Fichier / Édition / Affichage /
  Outils / Paramètres / Aide), a collapsible right panel, and a decluttered
  canvas (only the camera-orientation cross and the playback bar stay on screen;
  explanatory text moved to hover tooltips).
- **Simplified CLI**: the server launch takes only `--corrector` / `--metrics` /
  `--port`; data and SMPL directories are configured from the UI. Networking and
  workspace flags remain available but hidden.

## [0.1.1] - 2026-06-10

### Changed

- Removed the bundled correction algorithm and PhysDiff metrics; built-in
  plugins are now simple generic reference implementations (floor grounding +
  geometric metrics). Bring your own via `--corrector`/`--metrics`.

## [0.1.0] - 2026-06-09

The first public release: a clean, installable multi-person SMPL motion editor.

### Added

- **3D browser editor** (Three.js): SMPL mesh + skeleton, per-joint and
  whole-body editing, undo/redo, trilingual i18n.
- **Video & music background**: placeable source video (position, scale,
  opacity, time offset), server-side background removal, audio synced to the
  timeline.
- **Floor estimation**: RANSAC ground-plane estimate on foot contacts, editable
  and recomputable.
- **Pluggable auto-correction & metrics**: the `MotionCorrector` /
  `MotionMetrics` Protocols (`core/plugins.py`); built-in plugins by default,
  swappable for your own via a `<module-or-path>:<Class>` spec.
- **`.motion` save format**: a single ZIP bundling the original motion, your
  edits, the video, the music, placement params, comments and a metrics
  snapshot (`save_bundle` / `load_bundle`).
- **Public library API**: top-level re-exports (`Motion`, `Floor`,
  `load_bundle`, `save_bundle`, `load_corrector`, `load_metrics`,
  `scan_dataset`, `Config`, `__version__`) with `__all__` — importable with
  only numpy + flask (no torch).
- **Headless CLI subcommands**: `motion-studio correct <input> [-o out]
  [--corrector SPEC]` and `motion-studio metrics <input> [--metrics SPEC]`,
  plus `motion-studio --version`; the bare/`serve` form still starts the server.
- **Server info routes**: `/health`, `/version`, `/info` (active
  corrector/metrics specs and workspace).
- **Docs**: README, `docs/USAGE.md`, `docs/API.md`, `docs/PLUGINS.md`,
  `docs/ARCHITECTURE.md`, `CONTRIBUTING.md`, `SECURITY.md`.
- **Packaging & CI**: `pyproject.toml` with core / `[smpl]` / `[video]` /
  `[all]` / `[dev]` extras, a Dockerfile, a torch-free test lane across Python
  3.9 / 3.11 / 3.12, and a build/wheel-smoke job.

### Security

- Loopback-only bind by default; non-loopback `--host` requires the explicit
  `--allow-remote` opt-in with a warning.
- Host/Origin guard against DNS-rebinding; dropped wildcard CORS.
- `MAX_CONTENT_LENGTH` upload cap and `N`/`T`/`J`/`iters` shape ceilings,
  enforced before any heavy work.
- Restricted unpickler for legacy raw `.pkl` import (numpy reconstruct/ndarray
  /dtype + safe scalars only).

[Unreleased]: https://github.com/melissa-colin/motion-studio/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/melissa-colin/motion-studio/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/melissa-colin/motion-studio/releases/tag/v0.1.0
