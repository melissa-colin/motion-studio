33# Motion Studio HTTP API

The frontend (in `motion_studio/static/`) talks to the server over these
endpoints. Endpoints marked **(kept)** preserve the exact path/params of the
legacy pose-editor so the migrated frontend keeps working; **(new)** endpoints
add the workspace / `.motion` bundle / folder-import features.

All responses send permissive CORS headers. `clip`/`name` params are rejected
if they contain `/`, `..`, or start with `.`.

## Session / motion (kept)

- `GET /clips` -> `{clips:[{name, has_video, converted, custom, mtime, metrics}], ...}`
- `GET /load?clip=&source=&mesh=0|1` -> scene JSON
  `{name, parents, fps, N, T, J, joints, floor, floors, floor_meta, has_music,
    frame_w, frame_h, frames, video_duration, clip_duration, bg_offset,
    bg_version, source}`
- `GET /mesh_faces?clip=&source=` -> binary int32 faces (header `X-Faces-Shape`)
- `GET /mesh_frame?clip=&source=&frame=` -> binary float32 verts (N,V,3)
  (headers `X-Mesh-Shape`, `X-Mesh-Time`)
- `GET /foot_masks` -> `{left:[...], right:[...]}`
- `GET /music?clip=&source=` -> audio, supports HTTP `Range`
- `GET /source_metrics?clip=&source=` -> `{ok, metrics:{...}}` (exact pkl metrics)
- `POST /refit` body `{N,T,J,joints,frames?,clip?,source?}` -> binary verts
  (headers `X-Refit-Shape`, `X-Refit-Frames`, `X-Refit-Err`)
- `POST /metrics` body `{N,T,J,joints,clip?,source?,plane?,fps?,want_verts?}`
  -> `{ok, frames, metrics:{...}}` (or binary verts + `X-Metrics`)

## Auto-correction & metrics (kept, now plugin-backed)

- `POST /correct_motion?clip=&mode=raw|edited` body (edited) `{N,T,J,joints,source?}`
  -> `{ok, N, T, J, joints, metrics:{...}, mode, time_s, log}`
  Runs the **corrector plugin** (`--corrector`) in a fresh import each call;
  returns FK joints + metrics as *pending* edits (does NOT save).
  Metrics come from the **metrics plugin** (`--metrics`).
- `POST /metrics_all` -> `{ok, started}`
  (Re)compute every bundle's reference metrics in the **background**.
- `GET /metrics_status` -> `{running, total, done, failed, current}`
  Background metrics warm-up progress.

## Floor (kept)

- `POST /save_floor?clip=` body `{plane:[a,b,c]}` -> `{ok, plane, tilt_deg}`
- `POST /recompute_floor?clip=&source=` body `{N,T,J,joints}` ->
  `{ok, plane, tilt_deg, ...}`

## Video background (kept)

- `GET /bg_nobg?clip=&source=&frame=&v=` -> PNG RGBA (person only, DeepLab)
- `POST /set_bg_offset?clip=&offset_s=` -> `{ok, frames, frame_w, frame_h, bg_version, ...}`
- `POST /prewarm_bg` body `{clip, source}` -> `{ok, total}`
  Pre-segment a clip's whole background crop into the cache in the background
  (avoids playback freezes).
- `GET /prewarm_status?clip=&source=` -> `{running, total, done}`

## Comments / import (kept)

- `GET /comments?clip=` -> `{comments:[{user,text,time}], default_user}`
- `POST /comments?clip=` body `{user,text}` -> `{comments:[...]}`
- `POST /import` multipart `{pkl, video?, music?, name?}` -> `{ok, name, N, T, ...}`

## Export (kept)

- `POST /export_pkl?clip=&source=` body `{N,T,J,joints,source?}` ->
  binary pickled AIOZ dict (`Content-Disposition: attachment`). Only here is an
  SMPL `.pkl` written out.

## Workspace & `.motion` bundles (new)

- `GET /workspace` -> `{workspace, bundles:[{name, mtime, source_clip,
    has_video, has_music, metrics}]}` (lists `*.motion` in the workspace)
- `POST /import_folder` body `{pkl_dir?, videos_dir?, audio_dir?}` (all
  optional; each falls back to the configured dir) -> `{ok, job:"import"}`.
  Scans the flat `pkl_dir/` (with videos/audio matched by exact clip name) and
  converts each clip into a `.motion` bundle in the workspace; starts a
  **background** job and returns immediately. Poll progress from
  `GET /import_status`. Uses `motion_studio.library`.
- `POST /import_clip` body `{name}` -> `{ok, name}`
  Convert one `pkl_dir/<name>.pkl` into a `.motion` bundle.
- `GET /import_status` -> `{running, total, done, failed, current,
    imported_names}` (folder-import job progress).
- `GET /bundle/load?name=` -> scene JSON (same shape as `/load`) plus
  `{edited, video_params, comments, metrics}` restored from the bundle.
- `POST /bundle/save?name=` body
  `{N,T,J,joints_edited, video_params, comments, metrics, source_clip?}`
  -> `{ok, path}`. Writes/updates the `.motion` bundle (original kept; edited +
  metadata updated). Does NOT export a `.pkl`.

## Static

- `GET /` and `GET /<path>` -> files under `motion_studio/static/`.
