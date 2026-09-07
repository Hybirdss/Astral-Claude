# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Accept macOS hardware keycode zero so shortcuts such as Command+A work.
- Release keys and drag buttons after input errors, including a corner fail-safe abort,
  without disabling the fail-safe. Preserve the original error if cleanup also fails.
- Keep clipboard text changed during paste settling instead of overwriting it with the
  previous value; restore the previous text on input failure when it is still safe to do so.
- Use one server lock for X11 screen suffixes such as `:0` and `:0.0`; Windows and macOS
  locks no longer depend on an unrelated `DISPLAY` environment variable.
- Reject non-integer screenshot limits before capture and publish the allowed range in
  the MCP input schema.

### Validation

- 73 unit/protocol/repository tests passed, along with lint, formatting, package build,
  and headless doctor. The isolated Xvfb smoke test passed all eight actions and verified
  that an aborted corner drag releases the actual X11 button and consumes its observation.

## [0.2.0] - 2026-09-07

### Added

- Bundled the open-source [blender-mcp](https://github.com/ahujasid/blender-mcp) server
  (pinned release) as a second plugin MCP server, with its telemetry disabled by default.
- Blender skill: a live-session route through the Blender MCP tools, with tested snippets in
  `skills/blender/references/live-session.md`, alongside the background-script route.
- `desktop_status` reports the plugin version and the platform's primary shortcut modifier.
- `ASTRAL_CLAUDE_LOCK_DIR` overrides the per-display server lock location for tests and CI.
- Unit tests for the native backend (dispatch, key validation, clipboard paste, primary
  display selection, Linux session checks), a server lock exclusivity test, and repository
  hygiene tests (links, versions, skill frontmatter, manifests, no machine-specific paths).
- The Xvfb smoke test now exercises all eight actions and checks widget state.
- Security policy, code of conduct, issue and pull request templates, Dependabot, pre-commit,
  editorconfig, and a plugin validation job in CI.

### Changed

- `desktop_act` screenshots keep the `max_dimension` of the observation they consume.
- `paste_text` waits `duration` seconds before restoring the previous clipboard text.
- Coordinates accept numeric values and round to whole pixels; other strict checks remain.
- The package version is read from installed metadata instead of a duplicated constant.

### Fixed

- Key names that the current OS backend cannot press (for example `command` on X11) are
  rejected with a hint instead of being silently dropped by PyAutoGUI.
- Protocol tests use an isolated lock directory, so they no longer collide with a running
  server on Windows or macOS.

## [0.1.0] - 2026-09-07

### Added

- Desktop MCP server with `desktop_status`, `desktop_observe`, and `desktop_act`.
- Skills: `computer-use`, `blender`, `learn-app`, `verify-artifact`.
- Blender background example with structural verification, evaluation scenarios, and
  cross-platform CI with a Linux virtual-desktop smoke test.
