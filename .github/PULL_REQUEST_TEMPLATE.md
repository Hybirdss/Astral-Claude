## What changed and why

<!-- Link the issue or describe the task that motivated this change. -->

## Checks

- [ ] `uv run --frozen pytest` and `uv run --frozen ruff check .` pass
- [ ] `claude plugin validate .` passes after manifest or skill changes
- [ ] `uv.lock` updated when dependencies or the version changed
- [ ] Documentation updated; no personal paths, machine settings, or untested platform claims
- [ ] Desktop input changes were exercised on an isolated Xvfb or scratch desktop, and
      `docs/validation.md` records what was actually run
