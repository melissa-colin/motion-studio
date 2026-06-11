# Third-Party Notices

Motion Studio is released under the **MIT License**, Copyright © 2026
Melissa Colin (see `LICENSE`).

This file lists the third-party components that Motion Studio **bundles** (ships
in the repository), **loads at runtime**, or **depends on** at install time,
together with their licenses and sources. It is provided for attribution and
convenience; each component remains governed by its own license. This is a
research tool, not legal advice — when in doubt, consult the upstream license.

The SPDX identifier is given where it is well established. SMPL / SMPL-X body
models are **not** redistributed by this project and carry a separate
non-commercial license that users must accept upstream (see below).

---

## Vendored JavaScript

These files are copied into the repository under
`motion_studio/static/vendor/` and served to the browser as-is.

### Three.js (r160)

- **Role:** 3D rendering engine for the in-browser editor (scene, camera,
  meshes, skeletons).
- **File:** `motion_studio/static/vendor/three.module.js`
  (the bundled `REVISION` constant is `'160'`).
- **License:** MIT (SPDX: `MIT`).
- **Copyright:** Copyright © 2010-2023 three.js authors.
- **Source:** https://github.com/mrdoob/three.js

### OrbitControls.js and TransformControls.js

- **Role:** camera orbit/zoom controls and interactive translate/rotate gizmos
  used in the 3D editor.
- **Files:** `motion_studio/static/vendor/OrbitControls.js`,
  `motion_studio/static/vendor/TransformControls.js`.
- **Origin:** the Three.js examples/addons (`examples/jsm/controls/`),
  same project and version family as the vendored Three.js above.
- **License:** MIT (SPDX: `MIT`).
- **Copyright:** Copyright © 2010-2023 three.js authors.
- **Source:** https://github.com/mrdoob/three.js

---

## Runtime model & ML

These are not vendored in the repository; they are loaded at runtime — either
downloaded as Python packages / model weights, or fetched client-side from a
CDN.

### torchvision — DeepLabV3-ResNet101 (server-side person segmentation)

- **Role:** server-side background removal. The video pipeline runs
  `torchvision.models.segmentation.deeplabv3_resnet101` with
  `DeepLabV3_ResNet101_Weights.DEFAULT` to produce a "person" mask on the GPU
  (see `motion_studio/server/state.py` and `motion_studio/server/api_video.py`).
- **License:** BSD-3-Clause (SPDX: `BSD-3-Clause`).
- **Copyright:** Copyright © Soumith Chintala 2016; PyTorch / torchvision
  contributors.
- **Source:** https://github.com/pytorch/vision
- **Pretrained weights:** `DeepLabV3_ResNet101_Weights.DEFAULT`, trained on a
  COCO/VOC subset of classes. The weights are downloaded by torchvision on
  first use and are subject to torchvision's terms; refer to the torchvision
  model documentation for the weights' provenance.

### MediaPipe Tasks-Vision — Image Segmenter (client-side fallback)

- **Role:** client-side fallback for background removal when the server path is
  unavailable. `motion_studio/static/app.js` dynamically `import()`s
  `@mediapipe/tasks-vision` (version `0.10.14`) from the jsDelivr CDN and runs
  its image segmenter (`selfie_segmenter_landscape.tflite`) in the browser.
- **License:** Apache License 2.0 (SPDX: `Apache-2.0`).
- **Copyright:** Copyright © Google LLC.
- **Source:** https://github.com/google-ai-edge/mediapipe
  (package: https://www.npmjs.com/package/@mediapipe/tasks-vision)
- **Note:** loaded from a third-party CDN
  (`https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14`); it is not
  redistributed in this repository.

### SMPL / SMPL-X body models and the `smplx` loader

- **Role:** parametric human body models used to build meshes from SMPL motion
  parameters. The body-model files themselves are **not shipped** with this
  tool; the user supplies them via the SMPL models directory (`--smpl-dir`).
- **Models license:** licensed separately by the Max Planck Institute for
  Intelligent Systems (MPI-IS) for **non-commercial / research use only**.
  Users must obtain the models from the official sites and accept that license
  before use:
  - SMPL: https://smpl.is.tue.mpg.de
  - SMPL-X: https://smpl-x.is.tue.mpg.de
- **`smplx` Python loader:** the package used to build meshes from the model
  files, by MPI-IS. Its use is governed by the SMPL-X license terms.
  - **Source:** https://github.com/vchoutas/smplx
- **Important:** because the models are non-commercial / research-licensed,
  they are intentionally excluded from this repository and from any
  redistribution of it.

---

## Python dependencies

Declared in `pyproject.toml` (core dependencies plus the `smpl`, `video` and
`all` optional extras). Each is downloaded by `pip` at install time and remains
under its own license.

| Package | SPDX / license | Role in Motion Studio | Source |
| --- | --- | --- | --- |
| numpy | `BSD-3-Clause` | numerical arrays; the data model and core math | https://github.com/numpy/numpy |
| Flask | `BSD-3-Clause` | the editor's HTTP server | https://github.com/pallets/flask |
| torch (PyTorch) | `BSD-3-Clause` (BSD-3-style) | tensors and SMPL forward kinematics / pose refit | https://github.com/pytorch/pytorch |
| smplx | non-commercial / research (MPI-IS SMPL-X license) | build SMPL/SMPL-X meshes — see "Runtime model & ML" above | https://github.com/vchoutas/smplx |
| Pillow | `HPND` (historically MIT-CMU) | image I/O for the video pipeline | https://github.com/python-pillow/Pillow |
| torchvision | `BSD-3-Clause` | DeepLabV3 segmentation — see "Runtime model & ML" above | https://github.com/pytorch/vision |
| librosa | `ISC` | audio loading for the music background | https://github.com/librosa/librosa |
| scipy | `BSD-3-Clause` | scientific routines used by the video / motion pipeline | https://github.com/scipy/scipy |

Core install (`numpy`, `flask`) is required; `torch` and `smplx` come with the
`[smpl]` extra, and `pillow`, `torchvision`, `librosa`, `scipy` with the
`[video]` extra (`[all]` installs every optional dependency). The `[dev]` extra
adds `pytest` and is not redistributed with the tool at runtime.
