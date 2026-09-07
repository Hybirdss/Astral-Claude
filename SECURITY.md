# Security policy

## What this project controls

The desktop MCP server sends real mouse and keyboard input to the logged-in desktop with that
user's privileges and returns screenshots of the primary display to Claude Code. The bundled
Blender MCP server executes Python inside a running Blender session when its addon is connected.
Neither server opens a network port; Claude Code starts them over stdio. The Blender addon
listens on localhost only.

Treat any Claude Code session using this plugin like an operator at the keyboard: run it on a
scratch desktop or VM for unfamiliar workflows, keep sensitive windows off the primary display,
and remember that screenshots and typed text pass through Claude Code to its model provider.

## Reporting a vulnerability

Report vulnerabilities privately through
[GitHub security advisories](https://github.com/Hybirdss/Astral-Claude/security/advisories/new).
Include the OS and session type, plugin version, a minimal reproduction, and the impact.
Do not attach screenshots containing private data. Reports are handled on a best-effort basis
by the maintainers; you will receive an acknowledgement and, once fixed, credit in the changelog
unless you prefer otherwise.

In scope: input delivered to the wrong target, observation or lock bypasses, clipboard or
screenshot data leaks caused by this code, unsafe defaults in the bundled server configuration.
Out of scope: model behavior in general, third-party servers' own vulnerabilities (report those
upstream), and setups that intentionally disable the PyAutoGUI fail-safe.

## Supported versions

Only the latest release on the `main` branch receives fixes.
