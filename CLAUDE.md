# Working on Astral-Claude

This is a portable Claude Code plugin: skills supply procedures, the local MCP server supplies
desktop input/capture, and application scripts supply precise native operations.

- Keep README and public documentation in English. Avoid personal paths and machine settings.
- Keep plugin runtime files inside this repository so cached installs are self-contained.
- Do not claim native Wayland, secondary-monitor, or real OS GUI coverage that is not tested.
- Keep desktop imports lazy. `doctor`, schema discovery, and unit tests must work headlessly.
- Preserve image-coordinate mapping, one-use observations, serialization, and the fail-safe.
- Verify meaningful changes with `uv run --frozen pytest` and `uv run --frozen ruff check .`.
- Run `claude plugin validate .` after manifest/skill changes. Update `uv.lock` with dependency
  changes. Test real desktop input only on an explicitly selected scratch/virtual desktop.
- For skill changes, evaluate concrete tasks from `evals/scenarios.md`; report actual results.

Plugin consumers receive instructions through skills. This file guides repository development;
it is not automatically loaded into unrelated projects when the plugin is installed.
