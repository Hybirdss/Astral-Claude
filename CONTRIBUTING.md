# Contributing

Start with a real task that fails or takes unnecessary steps. Explain the app, version, OS,
desired artifact, actual behavior, and a small reproducible example. Do not attach private
desktop screenshots, credentials, or proprietary documents to public issues.

For an app skill, include a precise trigger, a useful control-surface choice, one tested
procedure, context/focus traps, and artifact verification. Put detailed variants in linked
references. Label untested platforms. Avoid broad guarantees or a list of memorized pixels.

For runtime changes, run the checks in README and add behavioral coverage where errors can
misdirect input or break transport. Use an isolated desktop for integration tests. Cross-platform
claims need actual OS/session/permission evidence, not only import success or mocks.

Update the validation record when you run meaningful end-to-end checks. Keep performance
comparisons reproducible: same task, model, environment, time/tool budget, and scoring rubric.

For releases, bump both `pyproject.toml` and `.claude-plugin/plugin.json`, update `uv.lock`,
validate the plugin, and rerun the relevant tests. Do not publish generated private artifacts.
