# Writing a Motion Studio plugin

Motion Studio's auto-correction and live metrics are both **plugins**. The
editor never imports a concrete implementation directly: it loads whatever
class you point it at, as long as that class matches one of two tiny protocols.
This guide shows the data shapes, the protocols, how to select a plugin, the
hot-reload boundary, how metric keys map onto the panel, and what the editor
expects on error.

Runnable, dependency-light examples live in [`../examples/`](../examples):

- [`examples/identity_corrector.py`](../examples/identity_corrector.py) — a
  corrector that returns the motion unchanged.
- [`examples/simple_metrics.py`](../examples/simple_metrics.py) — a metrics
  plugin in pure numpy (no torch / no SMPL) that emits custom keys.

---

## The data you exchange: `Motion` and `Floor`

These two dataclasses (`motion_studio/core/types.py`) are the **only** types a
plugin sees. You never touch the editor's on-disk formats.

```python
@dataclass
class Motion:
    poses: np.ndarray            # (n_persons, n_frames, 24, 3) axis-angle, z-up
    trans: np.ndarray            # (n_persons, n_frames, 3) root translation
    betas: np.ndarray | None     # (n_persons, 10) SMPL shape, or None
    gender: str = "neutral"      # "neutral" | "male" | "female"
    fps: float = 30.0
    name: str = ""               # clip name, no path, no extension
    # convenience: motion.n_persons, motion.n_frames, motion.copy()

@dataclass
class Floor:
    plane: tuple[float, float, float]   # z = a*x + b*y + c, in the z-up world
    # convenience: floor.normal -> unit up-normal np.ndarray
```

Key facts:

- The world frame is **z-up**. `poses` are axis-angle (24 SMPL body joints,
  including the root orientation at joint 0), *not* rotation matrices.
- `betas` may be `None`. Don't assume it's present.
- `Motion.copy()` returns a deep copy (arrays included) — use it as the basis
  for the corrected motion you return.

---

## The two protocols

Both are `runtime_checkable` protocols in `motion_studio/core/plugins.py`. Your
class does **not** need to subclass anything; it just needs matching methods.

### `MotionCorrector`

```python
class MotionCorrector(Protocol):
    def __init__(self, *, smpl_dir: str, floor: Optional[Floor] = None) -> None: ...
    def correct(self, motion: Motion, log: Callable[[str], None] = print) -> Motion: ...
```

- `smpl_dir` is the directory of SMPL model files (from `--smpl-dir`). Accept
  it even if you don't use it — it's part of the constructor signature.
- `floor` is the current ground plane, or `None` when none is set.
- `correct(...)` must return a **new** `Motion` with the **same array shapes**
  as the input (`poses` `(N, T, 24, 3)`, `trans` `(N, T, 3)`). Start from
  `motion.copy()`.
- `log` is a callback whose lines are surfaced in the editor; default `print`.

### `MotionMetrics`

```python
class MotionMetrics(Protocol):
    def __init__(self, *, smpl_dir: str) -> None: ...
    def compute(self, motion: Motion, floor: Floor) -> Dict[str, float]: ...
```

- `compute(...)` returns a mapping `{metric_name: float}` with **arbitrary
  string keys**. Keys are displayed by the editor's metrics panel (see the
  mapping below). Coerce values to `float`; omit a key entirely when it can't
  be computed (don't return `None`).

### `MotionFloor`

```python
class MotionFloor(Protocol):
    def __init__(self, *, smpl_dir: str) -> None: ...
    def estimate(self, motion: Motion) -> Floor: ...
```

- `estimate(...)` returns the clip's single shared ground plane as a `Floor`
  (`plane = (a, b, c)` for `z = a*x + b*y + c`, z-up). Used on clip load and by
  the "Recompute floor" action. The bundled default
  (`motion_studio.plugins_builtin.floor:Floor`) is a generic reference (lowest
  foot-sole points + RANSAC); bring your own for anything more sophisticated.

---

## Pointing the tool at your plugin

Pass a **spec** of the form `<module-or-path>:<Class>` to `--corrector`,
`--metrics` or `--floor`:

```bash
# file-path spec (relative or absolute path ending in .py, or any path with a "/")
motion-studio --corrector ./examples/identity_corrector.py:IdentityCorrector \
              --metrics   ./examples/simple_metrics.py:SimpleMetrics

# dotted-module spec (must be importable, i.e. on PYTHONPATH / installed)
motion-studio --corrector my_pkg.correctors:MyCorrector \
              --metrics   my_pkg.metrics:MyMetrics
```

How the spec is resolved (`_import_class` in `core/plugins.py`):

- **File-path spec** — the target ends in `.py` **or** contains a path
  separator. It is loaded directly from that file (no import machinery, so it
  does not need to be on `PYTHONPATH`).
- **Dotted-module spec** — anything else. It is imported by name and must be
  resolvable through the normal Python import path.
- The part after the **last** colon is the class name. (A Windows drive letter
  in a path would be ambiguous; on Linux this is a non-issue.)

The built-in defaults are dotted specs into
`motion_studio.plugins_builtin.*`; your own plugins are usually file-path specs
during development.

---

## Hot-reload boundary

Your plugin source is **re-imported on every call** — every "Correct" or
metrics request reloads the module and re-instantiates the class. So:

- Editing your plugin `.py` takes effect on the **next click**; no server
  restart needed. This is the single most useful property when iterating.
- Do **not** rely on instance state surviving between calls; each call gets a
  fresh instance. Cache expensive, immutable resources (e.g. a loaded SMPL
  model) at *module* scope if you must, keyed so a stale cache can't leak.
- The reload reruns module-top code each time, so keep import-time work cheap
  and side-effect-free. Heavy imports (torch, smplx) belong inside methods or
  guarded so a numpy-only metrics plugin stays numpy-only.

---

## Metric key → panel mapping

The frontend metrics panel renders **whatever keys** your `compute(...)`
returns. Known keys are shown first in a preferred order, with friendly,
localized labels and per-metric decimal precision:

```
float, penetrate, skate, pfc, jitter, self_pen, inter_pen
```

Any **extra** keys you emit (e.g. the example's `root_height`, `bbox_volume`,
`travel`) are appended after the known ones, in the order returned, labeled by
their **raw key** (no translation). So custom metrics render correctly without
any frontend change — they just won't be localized. To get a friendly label
and a fixed slot, a key has to be one of the known names above.

Practical guidance:

- Prefer the standard keys when your metric is one of them; you inherit labels,
  ordering, and decimals.
- Use short, stable `snake_case` keys for custom metrics — the raw key *is* the
  label users see.

---

## Errors, validation, and expectations

- **Shape contract (corrector).** Return a `Motion` with unchanged array
  shapes. Returning mismatched shapes will break the editor's diff/reload.
- **Types (metrics).** Return JSON-serializable `float` values. Cast numpy
  scalars with `float(x)`. Omit uncomputable keys instead of returning `None`.
- **Raised exceptions** propagate to the server, which logs them and returns an
  error to the client rather than crashing. Fail loudly and early (clear
  `ValueError`/`RuntimeError` messages) rather than returning garbage.
- **A bad spec** (no colon, missing class, unimportable module) raises at load
  time: `ValueError` for a malformed spec, `AttributeError` for a missing
  class, the underlying `ImportError`/`FileNotFoundError` otherwise.
- **Don't block forever.** The editor serializes heavy plugin calls; a hung
  call stalls correction/metrics for everyone. Keep work bounded.

---

## Minimal copy-paste corrector

```python
"""my_corrector.py — point the tool at it with
   motion-studio --corrector ./my_corrector.py:MyCorrector
"""
from __future__ import annotations

from typing import Callable, Optional

from motion_studio.core.types import Floor, Motion


class MyCorrector:
    def __init__(self, *, smpl_dir: str,
                 floor: Optional[Floor] = None) -> None:
        self._smpl_dir = smpl_dir
        self._floor = floor

    def correct(self, motion: Motion,
                log: Callable[[str], None] = print) -> Motion:
        out = motion.copy()
        # ... edit out.poses / out.trans in place, same shapes ...
        log("MyCorrector: done.")
        return out
```

## Minimal copy-paste metrics

```python
"""my_metrics.py — point the tool at it with
   motion-studio --metrics ./my_metrics.py:MyMetrics
"""
from __future__ import annotations

from typing import Dict

import numpy as np

from motion_studio.core.types import Floor, Motion


class MyMetrics:
    def __init__(self, *, smpl_dir: str) -> None:
        self._smpl_dir = smpl_dir

    def compute(self, motion: Motion, floor: Floor) -> Dict[str, float]:
        del floor
        return {"root_height": float(np.mean(motion.trans[..., 2]))}
```

For complete, runnable versions of both, see
[`examples/identity_corrector.py`](../examples/identity_corrector.py) and
[`examples/simple_metrics.py`](../examples/simple_metrics.py).
