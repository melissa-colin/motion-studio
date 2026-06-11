## Summary

What does this PR change, and why? Link any related issue (`Fixes #123`).

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] Docs only
- [ ] Refactor / cleanup (no behavior change)
- [ ] Build / CI / packaging

## Checklist

- [ ] The change is small and focused (one logical change).
- [ ] `ruff check .` passes.
- [ ] `ruff format --check .` passes.
- [ ] `pytest -m "not torch and not smpl" -q` passes (the torch-free lane).
- [ ] Added / updated tests for the changed behavior.
- [ ] Heavy paths that need torch or SMPL are marked `@pytest.mark.torch` /
      `@pytest.mark.smpl` so the core lane stays green.
- [ ] Updated `CHANGELOG.md` (under `Unreleased`).
- [ ] Updated the docs (README / `docs/`) if behavior or the public API changed.

## Notes for reviewers

Anything that needs context: trade-offs, follow-ups, things you are unsure about.
