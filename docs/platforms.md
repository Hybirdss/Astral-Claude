# Platform setup

Install uv and Claude Code first. The Python dependencies are portable; OS access to the
desktop still needs the setup below. Run `uv run --frozen astral-desktop doctor` from a clone
for diagnostics, or call `desktop_status` inside Claude. Neither captures the screen.

## Linux: X11

Run Claude Code from the graphical session with the same `DISPLAY` and X authority as the
target apps. On Debian/Ubuntu, install build prerequisites if missing:

```sh
sudo apt-get install python3-tk python3-dev build-essential xclip
```

MSS captures screens without `scrot`. `xclip` supplies Unicode clipboard paste on X11.
Other distributions have equivalent packages. The process needs access to the X server;
do not use `xhost +` to disable access controls.

## Linux: Wayland and isolated desktops

The native backend intentionally rejects Wayland. XWayland visibility/input is not a reliable
substitute for access to every native Wayland window. Use an X11 login session, or run target
apps and Claude Code together on a separate Xvfb desktop. This leaves your main desktop alone.

Example for Debian/Ubuntu, starting a fresh display on an automatically chosen free number:

```sh
sudo apt-get install xvfb xauth openbox xterm python3-tk xclip
env -u WAYLAND_DISPLAY -u XDG_SESSION_TYPE xvfb-run -a -s '-screen 0 1280x800x24' sh
```

In the resulting shell:

```sh
openbox &
xterm &
claude --plugin-dir /absolute/path/to/Astral-Claude
```

Launch the target application from this same shell/display. Claude sees it through screenshots.
For interactive human viewing, attach a properly secured VNC viewer/server or use an X11
desktop session. The repository does not install or expose a remote desktop server.

## Windows

Use native Windows Claude Code and uv from the interactive user's session. Keep the target
app on the primary monitor. Start with an ordinary, non-elevated app and a single display.
The backend requests DPI awareness before loading input/capture libraries.

UAC secure desktop, lock screens, services, and apps at higher integrity levels are outside
this workflow. Do not elevate the agent just to bypass these boundaries. A disconnected RDP
session may stop capture/input. WSL's Linux backend is not a bridge to native Windows apps;
run this plugin natively on Windows when those are the targets.

If Blender is not on PATH, examples accept its executable explicitly:

```powershell
uv run python examples/blender/run.py --blender "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --output artifacts/lamp
```

Use the path to your installed version; the version in this example is not required.

## macOS

Allow the launching app/process under **System Settings → Privacy & Security → Screen
Recording** (or Screen & System Audio Recording) and **Accessibility**. Depending on how
Claude Code is launched, macOS may attribute access to Terminal, iTerm, Claude Code, or its
Python child. Quit and reopen the launcher after changing permissions.

Keep the target window on the primary display. Run `desktop_observe` and confirm that it shows
the correct screen. Test a harmless click in a scratch document before real work; Retina
capture pixels and logical mouse coordinates can differ. Use `command` for ordinary macOS
application shortcuts, not `ctrl`. Screenshots being available does not prove input permission.

```sh
uv run python examples/blender/run.py --blender /Applications/Blender.app/Contents/MacOS/Blender --output artifacts/lamp
```

## Troubleshooting

| Symptom | Next step |
| --- | --- |
| `uv` not found / MCP disconnected | Ensure the launcher sees uv on PATH; restart it; inspect `/mcp` errors |
| Missing Python or dependency | Run `uv sync --frozen --python 3.12` in the clone; check network/build prerequisites |
| Missing tool names | Verify plugin installed/enabled and restart; skills alone do not create tools |
| Another server owns this display | Close the other Claude session or duplicate project MCP; do not delete a live lock |
| Black/empty screenshot | Check screen permission, desktop session, lock state, and display selection |
| Correct image, wrong click | Stop input; use one primary display; verify scale/focus with a scratch target |
| Stale/expired ID | Observe again and inspect; never guess or reuse an old ID |
| Tool failed after a click | Input may already have happened; observe before deciding whether to retry |
| Fail-safe exception | Stop and inspect why the pointer reached a corner; reposition manually before resuming |
| Wrong characters | Check keyboard layout; use explicit Unicode paste if clipboard changes are acceptable |
| Wayland rejected | Use X11 or the isolated Xvfb procedure above; do not just unset variables on the live session |

## Uninstall

Inside Claude Code: `/plugin uninstall astral-claude@astral-claude`, then restart the session.
Remove the marketplace separately if desired. This stops the plugin; it does not delete your
created documents. A local clone and uv caches can be removed independently. No startup daemon,
system service, external socket, or global skill-copy installer is installed by this repository.
