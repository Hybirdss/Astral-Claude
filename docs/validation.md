# Validation evidence

Initial local validation: **2026-09-07**. Environment: Linux, uv-managed Python 3.12.12,
Claude Code 2.1.258, Blender 5.2.1 LTS. GUI input was confined to a fresh Xvfb display;
the operator's live Wayland desktop was not controlled.

| Check | Observed result |
| --- | --- |
| `uv run --frozen pytest -q` | 21 tests passed: mapping, bounds, expiry, consumed IDs, resize, concurrency, validation, MCP image content, and stdio discovery/status/errors |
| `uv run --frozen ruff check .` | Passed |
| `uv build` | Source distribution and wheel built |
| `claude plugin validate .` | Marketplace passed |
| `claude plugin validate .claude-plugin/plugin.json` | Plugin passed; informational warning that root CLAUDE.md is not consumer context, as documented |
| Skill frontmatter validation | All four skills passed the skill-creator validator |
| `tests/desktop_smoke.py` in Xvfb | Actual MCP PNG → scaled click → text entry → button click → saved text verified |
| Blender example | Fresh scene generated, `.blend` saved, 960×720 PNG rendered; second process reopened scene and checked objects, camera, dimensions, and PNG |
| Render inspection | Actual PNG viewed: complete lamp silhouette, legible joints/switch, grounded base, no frame clipping |

The render shown in README is the inspected output. It is a basic reproducible scene, not a
claim of expert modeling or autonomous aesthetic performance.

## Reproduce the desktop check on Linux

Install Xvfb and xauth, then run from the repository root:

```sh
env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE xvfb-run -a -s '-screen 0 1280x800x24' \
  env ASTRAL_TEST_DESKTOP=1 uv run --frozen python tests/desktop_smoke.py
```

This creates its own Tk scratch window, drives it through a separate MCP server process,
checks the saved file, and shuts down the test processes. It uses known target geometry to
test execution/coordinate mapping; it does not measure a model's visual reasoning.

## Remaining validation

- Windows and macOS physical GUI input, permissions, keyboard layouts, and high-DPI behavior.
- Native Wayland is not implemented and is not a pending claim of support.
- Secondary-display control is not implemented.
- End-to-end model/skill evaluation and comparisons against an unmodified Claude Code session.
- Application workflows beyond the included Blender example and scratch desktop test.

The [GitHub Actions workflow](../.github/workflows/ci.yml) covers headless unit/protocol checks
on all three OS families and real input on a Linux virtual desktop. Consult the actual workflow
run for its outcome; a configured CI job is not evidence that it passed. Use the
[manual scenarios](../evals/scenarios.md) for future model-level testing.
