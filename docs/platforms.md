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
The Blender MCP route below does not depend on the display server.

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
application shortcuts, not `ctrl`; `desktop_status` reports the right one as `primary_modifier`.
Screenshots being available does not prove input permission.

```sh
uv run python examples/blender/run.py --blender /Applications/Blender.app/Contents/MacOS/Blender --output artifacts/lamp
```

## Blender MCP

The plugin also starts the open-source [blender-mcp](https://github.com/ahujasid/blender-mcp)
server through `uvx`, pinned to the release named in `.mcp.json`. Background scripts such as the
included example never need it. The live-session tools need its addon inside a running Blender:

1. Install the addon that matches the pinned server. From a terminal:

   ```sh
   uvx --from blender-mcp==1.9.1 blender-mcp install-addon
   ```

   This writes `blender_mcp.py` into your Blender user add-ons folder (`addon-paths` instead of
   `install-addon` shows the folder). Alternatively download `addon.py` from the matching
   upstream release and use **Edit → Preferences → Add-ons → Install**.
2. In Blender, enable **Interface: MCP for Blender** under **Edit → Preferences → Add-ons**.
3. In the 3D Viewport press `N`, open the **MCP for Blender** tab, and click **Connect to
   Claude**. The addon listens on `localhost:9876` by default.
4. In Claude Code, `/mcp` should list the plugin's `blender` server. Ask for `get_addon_status`;
   it reports the addon version, capabilities, and whether an update is needed.

If you changed the addon's port, set `BLENDER_HOST`/`BLENDER_PORT` in the environment that
launches Claude Code. If you previously registered blender-mcp yourself (for example with
`claude mcp add blender uvx blender-mcp`), remove that entry or the plugin's copy: upstream
supports one server per addon. Without Blender running, the bundled server idles and Blender
tools return a connection error; nothing else is affected.

Upstream enables anonymous telemetry by default and states it may be used for research and to
train AI models. The plugin starts its server with `DISABLE_TELEMETRY=true`. The addon has its
own consent checkbox under **Edit → Preferences → Add-ons → MCP for Blender**; review it. To
opt in on the server side, edit the `env` entry in a local checkout's `.mcp.json`.

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
| Key rejected as not available | Use the OS's names: `ctrl`/`alt`/`win` on Linux and Windows, `command`/`option` on macOS |
| Wrong characters | Check keyboard layout; use explicit Unicode paste if clipboard changes are acceptable |
| Wayland rejected | Use X11 or the isolated Xvfb procedure above; do not just unset variables on the live session |
| `Could not connect to Blender` | Open Blender, enable the addon, click Connect to Claude; check the port; background Blender processes do not run the addon |
| Two `blender` servers in `/mcp` | Remove your own `blender` entry or the plugin's; one server per addon |
| Blender tool times out | Shorten the snippet; long renders freeze the interface, so run them in a background process |

## Uninstall

Inside Claude Code: `/plugin uninstall astral-claude@astral-claude`, then restart the session.
Remove the marketplace separately if desired. This stops the plugin; it does not delete your
created documents or the Blender addon. A local clone and uv caches can be removed
independently. No startup daemon, system service, external socket, or global skill-copy
installer is installed by this repository.
