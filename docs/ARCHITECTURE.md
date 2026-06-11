# Architecture

A one-page map of Motion Studio: the modules, the data model, how an HTTP
request flows through the server, the concurrency model, and the on-disk
`.motion` format. The package is layered so the **library** (data model, bundle
I/O, dataset scan, plugin contract) imports with **only numpy + flask** — torch
is pulled in lazily, and only by the SMPL/refit and built-in plugin code paths.

## Module map

```
motion_studio/
├── __init__.py            Public API re-exports + __all__ (Motion, Floor,
│                          load_bundle, save_bundle, load_corrector,
│                          load_metrics, scan_dataset, Config, __version__).
├── cli.py                 Argparse entry point. Bare/`serve` start the server;
│                          `correct`/`metrics` run headless; `--version`.
├── __main__.py            `python -m motion_studio` → cli.main().
├── config.py              Config dataclass (workspace, pkl_dir, videos_dir,
│                          audio_dir, smpl_dir, corrector_spec, metrics_spec,
│                          floors_json, host, port) + the
│                          DEFAULT_* constants and SMPL_DIR/MOTION_STUDIO_HOME
│                          environment overrides.
│
├── core/                  The contract layer (no torch).
│   ├── types.py           The data model: Motion and Floor dataclasses.
│   └── plugins.py         The plugin Protocols (MotionCorrector, MotionMetrics),
│                          the spec loader (load_corrector / load_metrics) with
│                          class validation, and PluginLoadError.
│
├── smpl/                  SMPL geometry + raw dataset I/O.
│   ├── io.py              Load a raw SMPL `.pkl` into a Motion (torch-free entry).
│   ├── refit.py           Joint→SMPL pose refit (torch; lazy).
│   └── convert.py         Coordinate / format conversions (torch; lazy).
│
├── bundle.py              The `.motion` save format: save_bundle / load_bundle /
│                          load_bundle_meta, Bundle & BundleMeta, npz (de)ser.
│
├── library.py             Dataset scanning + import: scan_dataset,
│                          import_entry, import_dataset, DatasetEntry.
│
├── plugins_builtin/       Simple reference plugins (heavy; opt-in via extras).
│   ├── corrector.py       Reference Corrector (floor grounding).
│   ├── metrics.py         Reference Metrics (geometric).
│   ├── _convert.py        Pure-numpy zup2yup / yup2zup (no torch).
│   └── utils/             FK, floor, motion helpers (torch lazy).
│
├── server/                The Flask app, split into focused blueprints.
│   ├── app.py             create_app() factory + run(); Host/Origin guard,
│                          MAX_CONTENT_LENGTH, static serving, /health /version
│                          /info, /cache.
│   ├── state.py           ServerState: the per-process shared state and the
│                          heavy_lock that serializes GPU/refit work.
│   ├── api_motion.py      /load /refit /metrics /mesh_frame /source_metrics …
│   ├── api_bundle.py      /workspace /save /import /set_media …
│   ├── api_video.py       background-removal / per-clip video routes.
│   ├── loaders.py         resolve a clip name → Motion (cache-aware).
│   ├── common.py          shared helpers (CORS/response helpers, validation).
│   └── video_cache.py     per-clip background-frame cache.
│
└── static/                The browser front-end (index.html, app.js, Three.js
                           editor, i18n) served at `/`.
```

## Data model

Two dataclasses are the only things plugins and the bundle exchange
(`core/types.py`):

- **`Motion`** — a multi-person SMPL clip.
  - `poses: np.ndarray` `(N, T, 24, 3)` axis-angle, **z-up**.
  - `trans: np.ndarray` `(N, T, 3)` root translation.
  - `betas: np.ndarray | None` shape parameters.
  - `gender: str`, `fps: float`, `name: str`.
  - `n_persons` / `n_frames` properties.
- **`Floor`** — the ground plane.
  - `plane: tuple[float, float, float]` for `z = a·x + b·y + c`.
  - `normal` property (the up vector).

## Request flow

1. The browser front-end (`static/`) issues a JSON/HTTP request.
2. `app.before_request` runs the **Host/Origin guard**: non-loopback `Host`
   (or a cross-origin `Origin`) is rejected `403` unless `--allow-remote`.
   `MAX_CONTENT_LENGTH` caps the body size before any read.
3. The matching **blueprint** handler validates the payload (clip-name safety,
   shape ceilings `N/T/J/iters`, NaN/Inf check) and returns `400` early on bad
   input — *before* any heavy work.
4. For SMPL work the handler resolves the clip → `Motion` (`loaders.py`,
   cache-aware) and acquires `state.heavy_lock`.
5. The plugin spec is resolved through `load_corrector` / `load_metrics`
   (`core/plugins.py`), re-imported each call so edits to a user plugin take
   effect on the next request.
6. The result is serialized back to JSON. Errors return generic messages with
   the right status; details are logged server-side, never leaked to the client.

## The heavy-lock model

The Flask dev/prod server is threaded, but the torch/SMPL forward-kinematics and
refit paths are **not** safe to run concurrently (shared CUDA/CPU model state,
large allocations). `ServerState.heavy_lock` serializes them: a handler acquires
it only after all cheap validation has passed, does the GPU/refit work, and
releases it. Cheap, read-only routes (`/health`, `/version`, `/info`,
`/workspace`, static files) never touch the lock, so the UI stays responsive
while a correction runs.

## The `.motion` format

A `.motion` file is a single **ZIP** archive bundling one editing session
(`bundle.py`):

```
manifest.json        format/version, name, source_clip, comments,
                     video placement params, metrics snapshot, timestamps
motion_original.npz  the original SMPL motion (poses, trans, betas, fps, gender)
motion_edited.npz    your edited motion (omitted if you never edited)
video.mp4            the source video (optional)
music.<ext>          the music track (optional)
thumbnail.*          optional preview image
```

- `save_bundle(path, *, original, edited=None, video=None, music=None, …)`
  writes it; `load_bundle(path)` reads the whole thing back (media included);
  `load_bundle_meta(path)` reads only the manifest + motions with lazy media
  accessors for the playback hot path.
- Motions are stored as `.npz` (`motion_to_npz_dict` / `motion_from_npz`), so
  loading never unpickles arbitrary objects. The `/import` route uses a
  restricted unpickler for legacy raw `.pkl` inputs (see `SECURITY.md`).
