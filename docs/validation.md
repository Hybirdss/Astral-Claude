# Validation evidence

Validation record for 0.2.0: **2026-09-07**. Environment: Linux, uv-managed Python 3.12,
Claude Code 2.1.x, Blender 5.2 LTS, blender-mcp 1.9.1 (addon protocol 5). Desktop input and
the Blender live session were confined to fresh Xvfb displays and a scratch Blender profile;
the operator's live desktop (a Wayland session) and Blender configuration were not touched.

| Check | Observed result |
| --- | --- |
| `uv run --frozen pytest -q` | 48 tests passed: coordinate mapping, bounds, expiry, consumed IDs, resolution persistence, numeric rounding, validation, backend dispatch and per-platform key checks, clipboard paste and restore, primary display selection, Linux session checks, MCP image content, numeric coordinates through the tool layer, stdio discovery/status/errors, server lock exclusivity, repository hygiene (links, versions, skill frontmatter, manifests, no machine-specific paths) |
| `uv run --frozen ruff check .` and `ruff format --check` | Passed |
| `uv build` | Source distribution and wheel built |
| `claude plugin validate .` | Marketplace passed, including with an empty `CLAUDE_CONFIG_DIR` (no login) |
| `claude plugin validate .claude-plugin/plugin.json` | Plugin passed; informational warning that root CLAUDE.md is not consumer context, as documented |
| `tests/desktop_smoke.py` in Xvfb | Real MCP PNGs at the requested resolution; click, type_text, key (`home`, `shift+end`, `delete`), Unicode `paste_text`, drag on a slider, scroll in a text box, wait, move; the saved widget state matched |
| Blender MCP live session in Xvfb | Scratch Blender 5.2 GUI with the bundled 1.9.1 addon on an isolated display: `get_addon_status` (up to date, protocol 5, telemetry consent off), `get_scene_info`, `execute_blender_code` (inspection JSON; collection and object with a custom property; `save_as_mainfile(copy=True)` left the working file unsaved; 320×240 Workbench render written), `get_object_info` (bounding box, mesh counts), `get_viewport_screenshot` before and after the edit showed the new object |
| Blender addon disconnected | Blender tools returned "Could not connect to Blender. Make sure the Blender addon is running."; the desktop server and skills were unaffected |
| `uvx --from blender-mcp==1.9.1 blender-mcp --help` | Console script present with `install-addon` and `addon-paths` subcommands |
| Blender example (0.1.0 record) | Fresh scene generated, `.blend` saved, 960×720 PNG rendered; second process reopened scene and checked objects, camera, dimensions, and PNG |
| Render inspection (0.1.0 record) | Actual PNG viewed: complete lamp silhouette, legible joints/switch, grounded base, no frame clipping |
| Public marketplace installation (0.1.0 record) | Installed from GitHub in temporary Claude settings; four skills and one MCP server discovered |
| Cached plugin runtime (0.1.0 record) | Locked runtime launched from a cached public install with an unrelated working directory |
| GitHub OS matrix (0.1.0 record) | Unit/protocol tests, lint, and doctor passed on ubuntu-latest, windows-latest, and macos-latest; the 0.2.0 workflow adds `ruff format --check`, `uv build`, and plugin validation |

The render shown in README is the inspected output. It is a basic reproducible scene, not a
claim of expert modeling or autonomous aesthetic performance.

## Unreleased runtime fixes verified on 2026-09-07

- `uv run --frozen pytest`: 73 passed, including macOS keycode zero, failed-input cleanup,
  clipboard changes during paste, cleanup-error preservation, strict screenshot limits,
  and lock contention between X11 screen aliases in separate MCP processes.
- `uv run --frozen ruff check .` and `uv run --frozen ruff format --check src tests examples`:
  passed. `uv build` produced both distributions; headless `astral-desktop doctor` passed.
- The isolated Xvfb smoke test passed all eight actions, then deliberately dragged to a
  fail-safe corner. The tool returned an error, the X server reported the left button
  released, and replaying the consumed observation returned a stale-ID error.
- macOS and Windows behavior is covered by mocks here; physical GUI validation remains
  outstanding. The earlier Blender and plugin evidence above was not rerun for these fixes.

## Reproduce the desktop check on Linux

Install Xvfb, xauth, xclip, and Tk, then run from the repository root:

```sh
env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE xvfb-run -a -s '-screen 0 1280x800x24' \
  env ASTRAL_TEST_DESKTOP=1 uv run --frozen python tests/desktop_smoke.py
```

This creates its own Tk scratch window, drives it through a separate MCP server process with an
isolated lock directory, checks the saved widget state, and shuts down the test processes. It
uses known target geometry to test execution/coordinate mapping; it does not measure a model's
visual reasoning.

## Reproduce the Blender live-session check on Linux

Run a scratch Blender GUI with the bundled addon on an isolated display, without touching your
Blender profile. Replace `5.2` with your installed Blender version:

```sh
SCRATCH=$(mktemp -d)
mkdir -p "$SCRATCH/cfg/blender/5.2/scripts/addons" "$SCRATCH/cache"
uv run --no-project --with blender-mcp==1.9.1 python -c "import blender_mcp, pathlib, shutil, sys; \
  shutil.copy(pathlib.Path(blender_mcp.__file__).parent / 'bundled' / 'addon.py', sys.argv[1])" \
  "$SCRATCH/cfg/blender/5.2/scripts/addons/blender_mcp.py"
cat > "$SCRATCH/start.py" <<'PY'
import bpy
bpy.ops.preferences.addon_enable(module="blender_mcp")
bpy.context.preferences.addons["blender_mcp"].preferences.telemetry_consent = False
bpy.ops.blendermcp.start_server()
PY
env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE XDG_CONFIG_HOME="$SCRATCH/cfg" XDG_CACHE_HOME="$SCRATCH/cache" \
  xvfb-run -a -s '-screen 0 1280x800x24' blender --python "$SCRATCH/start.py"
```

With that process running, ask Claude Code for `get_addon_status`, then exercise the snippets in
`skills/blender/references/live-session.md`. Stop the scratch Blender and delete `$SCRATCH`
afterwards. The addon listens on localhost only; make sure no other Blender addon server is
using the same port.

## Remaining validation

- Windows and macOS physical GUI input, permissions, keyboard layouts, and high-DPI behavior.
- The Blender live-session route on Windows and macOS, and with a user's own profile rather
  than a scratch profile.
- Native Wayland desktop control is not implemented and is not a pending claim of support.
- Secondary-display control is not implemented.
- End-to-end model/skill evaluation and comparisons against an unmodified Claude Code session.
- Application workflows beyond the included Blender example and scratch desktop test.

The [GitHub Actions workflow](../.github/workflows/ci.yml) covers headless unit/protocol/
repository checks on all three OS families, real input on a Linux virtual desktop, and plugin
validation. Consult the actual workflow run for its outcome; a configured CI job is not
evidence that it passed. Use the [manual scenarios](../evals/scenarios.md) for future
model-level testing.
