"""Fit SMPL poses to hand-edited target joints (the refit optimizer).

Vendored from the legacy pose-editor ``refit_smpl.py`` and adapted to Motion
Studio: imports are package-relative (the FK / yup2zup / pkl helpers come from
:mod:`motion_studio.plugins_builtin.utils.motion_utils`) and the SMPL model
directory is passed in instead of hard-coded.

The browser lets the user drag 3D joints; this module turns those edited joints
back into a consistent SMPL body (axis-angle poses + translation, plus the mesh
vertices). It powers ``/refit``, ``/export_pkl`` and ``/recompute_floor``.

Optimization (per dancer, all frames batched on GPU): variables are the
axis-angle pose ``(T, 24, 3)`` and the global translation ``(T, 3)``; betas are
fixed to zero (neutral). The loss is the L2 fit of the SMPL joints ``Jtr`` to
the target joints, plus a small temporal-acceleration smoothness term and a
weak anchor to the init pose. Init from the source pkl (yup2zup) so a
non-edited dancer starts near zero error.
"""

from __future__ import annotations

import collections
import threading
from typing import Callable

import numpy as np
import torch

from motion_studio.plugins_builtin import _convert
from motion_studio.plugins_builtin.utils.motion_utils import (
    load_raw_gdance_pkl,
    yup2zup,
)

NUM_J = 24

# SMPL models are frozen to a batch_size at build time; cache one per
# (smpl_dir, device, batch_size) so successive refits of the same length are
# cheap. The cache is LRU-bounded so distinct clip lengths cannot accumulate an
# unbounded pile of GPU-resident models; the evicted model is moved off the GPU
# so its VRAM is reclaimed.
_SMPL_CACHE_CAP = 6
_SMPL_CACHE: collections.OrderedDict[tuple, object] = collections.OrderedDict()
_SMPL_LOCK = threading.Lock()


def _free_smpl(model) -> None:
    """Release a cached SMPL model's GPU memory on eviction (best-effort)."""
    try:
        model.to("cpu")
    except Exception:  # noqa: BLE001 - eviction must never raise
        pass
    if torch.cuda.is_available():
        try:
            torch.cuda.empty_cache()
        except Exception:  # noqa: BLE001
            pass


def get_smpl(smpl_dir: str, device: torch.device, batch_size: int):
    """Return a cached ``smplx.SMPL`` NEUTRAL model for ``batch_size`` frames.

    The cache is LRU with a small cap (:data:`_SMPL_CACHE_CAP`); evicting the
    least-recently-used model frees its GPU memory. This is the single SMPL
    construction seam: every model build in the package routes through here so
    the bound is global.

    Args:
      smpl_dir: Directory containing the SMPL body model files.
      device: Torch device to place the model on.
      batch_size: Frame batch size the model is frozen to.

    Returns:
      The (possibly cached) SMPL model on ``device``.
    """
    from smplx import SMPL

    key = (smpl_dir, str(device), batch_size)
    with _SMPL_LOCK:
        model = _SMPL_CACHE.get(key)
        if model is not None:
            _SMPL_CACHE.move_to_end(key)
            return model
        model = SMPL(
            model_path=smpl_dir, gender="NEUTRAL", batch_size=batch_size
        ).to(device)
        _SMPL_CACHE[key] = model
        while len(_SMPL_CACHE) > _SMPL_CACHE_CAP:
            _evicted_key, evicted = _SMPL_CACHE.popitem(last=False)
            _free_smpl(evicted)
        return model


def _smpl_jtr_verts(
    smpl, pose_aa: torch.Tensor, transl: torch.Tensor, want_verts: bool = False
):
    """Differentiable SMPL forward in the editor z-up frame.

    Args:
      smpl: A built ``smplx.SMPL`` model.
      pose_aa: Axis-angle poses, shape ``(B, 24, 3)``.
      transl: Root translations, shape ``(B, 3)``.
      want_verts: Whether to also return the mesh vertices.

    Returns:
      A tuple ``(jtr, verts)`` where ``jtr`` is ``(B, 24, 3)`` and ``verts`` is
      ``(B, 6890, 3)`` or None.
    """
    global_orient = pose_aa[:, 0, :]
    body_pose = pose_aa[:, 1:, :].reshape(pose_aa.shape[0], -1)
    out = smpl(global_orient=global_orient, body_pose=body_pose, transl=transl)
    jtr = out.joints[:, :NUM_J]
    verts = out.vertices if want_verts else None
    return jtr, verts


def init_from_pkl(pkl_path: str):
    """Return z-up ``(poses, trans)`` to seed the refit, from a GDance pkl.

    Args:
      pkl_path: Path to the AIOZ-GDANCE pkl (y-up).

    Returns:
      ``(poses_init, trans_init)`` numpy arrays of shape ``(N, T, 24, 3)`` and
      ``(N, T, 3)`` in the z-up editor frame.
    """
    poses, trans, _ = load_raw_gdance_pkl(pkl_path)
    trans_z, poses_z, _ = yup2zup(trans, poses)
    return poses_z.float().numpy(), trans_z.float().numpy()


def zup2yup(poses_z, trans_z):
    """Rotate a z-up SMPL motion back to the y-up AIOZ-GDANCE convention.

    Thin wrapper over :func:`motion_studio.plugins_builtin._convert.zup2yup` so
    callers of this module have a single import surface.

    Args:
      poses_z: ``(N, T, 24, 3)`` axis-angle poses in the z-up world.
      trans_z: ``(N, T, 3)`` root translations in the z-up world.

    Returns:
      ``(poses_y, trans_y)`` numpy float32 arrays in the y-up convention.
    """
    return _convert.zup2yup(poses_z, trans_z)


def detect_rigid(target_joints_n, orig_joints_n, eps: float = 1e-4):
    """Detect a whole-body rigid translation of one dancer.

    When the tool drags a dancer bodily, all 24 joints shift by the same
    per-frame vector; the exact solution is then "pose unchanged, trans +=
    offset" (error 0), and refitting would only drift the feet. This compares
    the edited joints to the original FK joints and reports rigidity.

    Args:
      target_joints_n: ``(T, 24, 3)`` edited joints for this dancer (z-up).
      orig_joints_n: ``(T, 24, 3)`` original FK joints for this dancer (z-up).
      eps: Tolerance in metres on the per-joint residual to the common shift.

    Returns:
      A tuple ``(is_rigid, offset)`` where ``offset`` is the common per-frame
      shift ``(T, 3)`` (meaningful only when ``is_rigid`` is True).
    """
    tj = np.asarray(target_joints_n, dtype=np.float64)
    oj = np.asarray(orig_joints_n, dtype=np.float64)
    if tj.shape != oj.shape:
        return False, np.zeros((tj.shape[0], 3), np.float32)
    delta = tj - oj
    offset = delta.mean(axis=1)
    resid = delta - offset[:, None, :]
    max_resid = float(np.abs(resid).max()) if resid.size else 0.0
    return bool(max_resid <= eps), offset.astype(np.float32)


def fit_one_dancer(
    smpl_dir: str,
    target_joints: np.ndarray,
    pose_init: np.ndarray,
    trans_init: np.ndarray,
    device: torch.device,
    iters: int = 150,
    lr: float = 0.05,
    w_smooth: float = 1e-3,
    w_reg: float = 1e-4,
    want_verts: bool = True,
    progress: Callable[[int, float], None] | None = None,
) -> dict[str, np.ndarray]:
    """Fit one dancer's SMPL pose/trans to its target joints (all frames).

    Args:
      smpl_dir: Directory containing the SMPL body model files.
      target_joints: ``(T, 24, 3)`` target joints for this dancer (z-up).
      pose_init: ``(T, 24, 3)`` initial axis-angle poses.
      trans_init: ``(T, 3)`` initial root translations.
      device: Torch device to optimize on.
      iters: Number of Adam iterations.
      lr: Adam learning rate.
      w_smooth: Weight of the temporal-acceleration smoothness term.
      w_reg: Weight of the anchor-to-init term.
      want_verts: Whether to also return the fitted mesh vertices.
      progress: Optional ``callback(iteration, data_loss)``.

    Returns:
      A dict with ``pose`` ``(T, 24, 3)``, ``trans`` ``(T, 3)``,
      ``err_before``/``err_after`` (RMS metres) and ``verts`` if requested.
    """
    T = target_joints.shape[0]
    smpl = get_smpl(smpl_dir, device, batch_size=T)

    tgt = torch.from_numpy(target_joints.astype(np.float32)).to(device)
    pose = (
        torch.from_numpy(pose_init.astype(np.float32))
        .to(device)
        .clone()
        .requires_grad_(True)
    )
    trans = (
        torch.from_numpy(trans_init.astype(np.float32))
        .to(device)
        .clone()
        .requires_grad_(True)
    )
    pose0 = torch.from_numpy(pose_init.astype(np.float32)).to(device)

    opt = torch.optim.Adam([pose, trans], lr=lr)

    def data_loss():
        jtr, _ = _smpl_jtr_verts(smpl, pose, trans, want_verts=False)
        return ((jtr - tgt) ** 2).sum(-1).mean()

    with torch.no_grad():
        err0 = float(torch.sqrt(data_loss()).item())

    for it in range(iters):
        opt.zero_grad()
        jtr, _ = _smpl_jtr_verts(smpl, pose, trans, want_verts=False)
        l_data = ((jtr - tgt) ** 2).sum(-1).mean()
        if T > 2:
            accel = pose[2:] - 2 * pose[1:-1] + pose[:-2]
            l_smooth = (accel**2).sum(-1).mean()
        else:
            l_smooth = torch.zeros((), device=device)
        l_reg = ((pose - pose0) ** 2).sum(-1).mean()
        loss = l_data + w_smooth * l_smooth + w_reg * l_reg
        loss.backward()
        opt.step()
        if progress is not None and (it % 10 == 0 or it == iters - 1):
            progress(it, float(l_data.item()))

    with torch.no_grad():
        jtr, verts = _smpl_jtr_verts(smpl, pose, trans, want_verts=want_verts)
        errf = float(torch.sqrt(((jtr - tgt) ** 2).sum(-1).mean()).item())
        out: dict[str, np.ndarray] = {
            "pose": pose.detach().cpu().numpy(),
            "trans": trans.detach().cpu().numpy(),
            "err_before": err0,
            "err_after": errf,
        }
        if want_verts:
            out["verts"] = verts.detach().cpu().numpy()
    return out


def refit(
    smpl_dir: str,
    target_joints: np.ndarray,
    pose_init: np.ndarray | None = None,
    trans_init: np.ndarray | None = None,
    frames: list[int] | None = None,
    device: torch.device | None = None,
    iters: int = 150,
    want_verts: bool = True,
    progress: Callable[[int, int, float], None] | None = None,
    init_pkl: str | None = None,
    rigid_eps: float = 1e-4,
) -> dict[str, np.ndarray]:
    """Fit N dancers' SMPL bodies to edited target joints.

    Args:
      smpl_dir: Directory containing the SMPL body model files.
      target_joints: ``(N, T, 24, 3)`` edited target joints (z-up).
      pose_init: Optional ``(N, T, 24, 3)`` init poses; loaded from ``init_pkl``
        if None.
      trans_init: Optional ``(N, T, 3)`` init translations; loaded likewise.
      frames: Optional iterable of frame indices to fit (None fits all frames).
      device: Torch device; defaults to cuda if available.
      iters: Number of Adam iterations per dancer.
      want_verts: Whether to also return fitted mesh vertices.
      progress: Optional ``callback(dancer, iteration, data_loss)``.
      init_pkl: Path of the GDance pkl used to seed poses when ``pose_init`` is
        None; pass the clip's own pkl for a good start.
      rigid_eps: Tolerance (metres) for the pure-translation shortcut.

    Returns:
      A dict with ``verts`` ``(N, Tsel, 6890, 3)`` or None, ``poses``
      ``(N, Tsel, 24, 3)``, ``trans`` ``(N, Tsel, 3)``, ``frames`` (selected
      indices), ``err_before``/``err_after`` ``(N,)`` and ``rigid`` ``(N,)``.

    Raises:
      ValueError: If neither ``pose_init``/``trans_init`` nor ``init_pkl`` is
        supplied (no way to seed the optimization).
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    N, T, J, _ = target_joints.shape
    if pose_init is None or trans_init is None:
        if not init_pkl:
            raise ValueError("refit needs pose_init/trans_init or init_pkl")
        pi, ti = init_from_pkl(init_pkl)
        if pose_init is None:
            pose_init = pi
        if trans_init is None:
            trans_init = ti

    sel = (
        list(range(T))
        if frames is None
        else sorted(set(int(f) for f in frames))
    )
    Tsel = len(sel)

    verts_out = np.zeros((N, Tsel, 6890, 3), np.float32) if want_verts else None
    poses_out = np.zeros((N, Tsel, J, 3), np.float32)
    trans_out = np.zeros((N, Tsel, 3), np.float32)
    eb = np.zeros(N, np.float32)
    ea = np.zeros(N, np.float32)
    rigid_flags = np.zeros(N, bool)

    smpl_sel = get_smpl(smpl_dir, device, batch_size=Tsel)
    for n in range(N):
        pose_n = pose_init[n, sel]
        trans_n = trans_init[n, sel]
        with torch.no_grad():
            jtr0, _ = _smpl_jtr_verts(
                smpl_sel,
                torch.from_numpy(pose_n.astype(np.float32)).to(device),
                torch.from_numpy(trans_n.astype(np.float32)).to(device),
                want_verts=False,
            )
            orig_joints_n = jtr0.cpu().numpy()
        is_rigid, offset = detect_rigid(
            target_joints[n, sel], orig_joints_n, eps=rigid_eps
        )
        if is_rigid:
            pose_r = pose_n.copy()
            trans_r = (trans_n + offset).astype(np.float32)
            poses_out[n] = pose_r
            trans_out[n] = trans_r
            rigid_flags[n] = True
            with torch.no_grad():
                jtr_r, verts_r = _smpl_jtr_verts(
                    smpl_sel,
                    torch.from_numpy(pose_r.astype(np.float32)).to(device),
                    torch.from_numpy(trans_r).to(device),
                    want_verts=want_verts,
                )
                err = float(
                    torch.sqrt(
                        (
                            (
                                jtr_r
                                - torch.from_numpy(
                                    target_joints[n, sel].astype(np.float32)
                                ).to(device)
                            )
                            ** 2
                        )
                        .sum(-1)
                        .mean()
                    ).item()
                )
            eb[n] = err
            ea[n] = err
            if want_verts:
                verts_out[n] = verts_r.cpu().numpy()
            if progress is not None:
                progress(n, iters - 1, err * err)
            continue
        cb = (lambda it, loss, n=n: progress(n, it, loss)) if progress else None
        res = fit_one_dancer(
            smpl_dir,
            target_joints[n, sel],
            pose_n,
            trans_n,
            device,
            iters=iters,
            want_verts=want_verts,
            progress=cb,
        )
        poses_out[n] = res["pose"]
        trans_out[n] = res["trans"]
        eb[n] = res["err_before"]
        ea[n] = res["err_after"]
        if want_verts:
            verts_out[n] = res["verts"]

    return {
        "verts": verts_out,
        "poses": poses_out,
        "trans": trans_out,
        "frames": sel,
        "err_before": eb,
        "err_after": ea,
        "rigid": rigid_flags,
    }
