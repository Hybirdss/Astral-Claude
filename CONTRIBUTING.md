# Contributing

Start with a real task that fails or takes unnecessary steps. Explain the app, version, OS,
desired artifact, actual behavior, and a small reproducible example. Do not attach private
desktop screenshots, credentials, or proprietary documents to public issues. Issue templates
ask for exactly this information.

For an app skill, include a precise trigger, a useful control-surface choice, one tested
procedure, context/focus traps, and artifact verification. Put detailed variants in linked
references. Label untested platforms. Avoid broad guarantees or a list of memorized pixels.

For runtime changes, run the checks in README and add behavioral coverage where errors can
misdirect input or break transport. Use an isolated desktop for integration tests:

```sh
env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE xvfb-run -a -s '-screen 0 1280x800x24' \
  env ASTRAL_TEST_DESKTOP=1 uv run --frozen python tests/desktop_smoke.py
```

Cross-platform claims need actual OS/session/permission evidence, not only import success or
mocks. `tests/test_repo.py` enforces resolvable links, matching versions, valid skill
frontmatter, and the absence of machine-specific paths; keep it green rather than weakening it.
`pre-commit install` runs ruff and basic file checks before each commit.

Update `docs/validation.md` when you run meaningful end-to-end checks, and add a line to
`CHANGELOG.md` under Unreleased. Keep performance comparisons reproducible: same task, model,
environment, time/tool budget, and scoring rubric.

The Blender server is pinned in `.mcp.json`. To move to a newer blender-mcp release, update the
pin, the install command in `docs/platforms.md`, rerun the live-session check from the
validation record against the matching addon, and note behavior changes in the Blender skill.

For releases, bump `pyproject.toml` and `.claude-plugin/plugin.json`, run `uv lock`, move the
Unreleased notes into a dated section, validate the plugin, and rerun the relevant tests.
Do not publish generated private artifacts.
