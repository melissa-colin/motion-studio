# Contributing

Thanks for your interest in Motion Studio. This guide covers a local dev setup,
running the tests, the lint/format tooling, and where to look to write a plugin.

## Dev install

Use a fresh virtual environment (conda or venv), then install the package
editable with the `dev` extra:

```bash
pip install -e ".[dev]"
```

That gives you the torch-free core (numpy + flask) plus the dev tools (pytest,
ruff, black, pre-commit). The heavy SMPL/video paths are opt-in:

```bash
pip install -e ".[all]"    # + torch, smplx, torchvision, pillow, librosa, scipy
pip install -e ".[smpl]"   # + torch, smplx only
pip install -e ".[video]"  # + pillow, torchvision, librosa, scipy only
```

The SMPL body models are **not** shipped. For SMPL-marked tests or to run the
editor end to end, point the tool at your local copy via `--smpl-dir` or the
`SMPL_DIR` environment variable.

## Running the tests

```bash
pytest -m "not torch and not smpl" -q   # the fast, torch-free core lane (CI)
pytest -q                               # everything available locally
```

Two pytest **markers** split the heavy lanes from the core (see `conftest.py`):

- `torch` — the test needs PyTorch. Skip it on the torch-free lane.
- `smpl` — the test needs a local SMPL model directory. Auto-skipped unless
  `SMPL_DIR` points at a directory of model files.

The torch-free lane (`-m "not torch and not smpl"`) is what CI runs across
Python 3.9 / 3.11 / 3.12, and it must never import torch. When you add a test
that needs torch or SMPL, mark it so the core lane stays green for contributors
without the heavy stack.

## Lint & format

The code follows the Google Python style (module imports, 80 columns, Google
docstrings). Linting and formatting are enforced with **ruff**; **black** is
configured to the same 80-column width and is compatible if you prefer it.

```bash
ruff check .            # lint
ruff format --check .   # formatting check (what CI runs)
ruff format .           # apply formatting
black .                 # equivalent formatter (optional, same line length)
```

## Pre-commit

Install the hooks once so lint/format run automatically on each commit:

```bash
pip install pre-commit   # included in the [dev] extra
pre-commit install
pre-commit run --all-files   # run on the whole tree once
```

The hooks (see `.pre-commit-config.yaml`) run `ruff --fix`, `ruff-format`, a
large-file guard, and an end-of-file fixer.

## Writing a plugin

Motion Studio depends on a small **contract**, not on any concrete corrector or
metrics implementation. A plugin is any class matching one of the Protocols in
`motion_studio/core/plugins.py` (`MotionCorrector` / `MotionMetrics`); the only
types exchanged are `Motion` and `Floor` from `motion_studio/core/types.py`.

Point the tool at your class with a `--corrector`/`--metrics` spec
(`<module-or-path>:<Class>`). The full authoring guide, with runnable
dependency-light examples, is in [`docs/PLUGINS.md`](docs/PLUGINS.md); see also
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the module map and data flow.

## Pull requests

- Keep changes small and focused; one logical change per PR.
- Add or update tests for behavior you change; keep the torch-free lane green.
- Run `ruff check .`, `ruff format --check .`, and `pytest -m "not torch and not
  smpl" -q` before pushing.
- Update `CHANGELOG.md` under the `Unreleased` section.
