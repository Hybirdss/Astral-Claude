# Working on Astral-Claude

This is a portable Claude Code plugin: skills supply procedures, the local MCP server supplies
desktop input/capture, the bundled Blender MCP server supplies live-session access, and
application scripts supply precise native operations.

- Keep README and public documentation in English. Never hardcode personal paths, user names,
  hosts, ports, or machine settings; `tests/test_repo.py` rejects home-directory paths.
- Keep plugin runtime files inside this repository so cached installs are self-contained.
  The Blender server is a pinned upstream release in `.mcp.json`; keep the pin, the install
  command in `docs/platforms.md`, and the skill notes in step.
- Do not claim native Wayland, secondary-monitor, or real OS GUI coverage that is not tested.
- Keep desktop imports lazy. `doctor`, schema discovery, and unit tests must work headlessly.
- Preserve image-coordinate mapping, one-use observations, serialization, the fail-safe, the
  per-display lock, and telemetry-off defaults for bundled third-party servers.
- Verify meaningful changes with `uv run --frozen pytest` and `uv run --frozen ruff check .`.
  Backend changes also need the Xvfb smoke test from CONTRIBUTING on an isolated display.
- Run `claude plugin validate .` after manifest/skill changes. Update `uv.lock` with dependency
  or version changes. Test real desktop input only on an explicitly selected scratch/virtual
  desktop; test Blender live-session changes against a scratch Blender, never a user's document.
- For skill changes, evaluate concrete tasks from `evals/scenarios.md`; report actual results
  and record them in `docs/validation.md` and `CHANGELOG.md`.

Plugin consumers receive instructions through skills. This file guides repository development;
it is not automatically loaded into unrelated projects when the plugin is installed.
