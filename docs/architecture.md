# Architecture and computer-use mechanics

## Model, host, and environment

Computer use needs a model that interprets observations, a host that executes its requested
actions, and an environment containing the target application. A screenshot does not itself
grant input capability, and a prompt cannot add a tool to a host that does not expose it.

OpenAI documents both code-driven UI operations and structured computer actions. The host
executes them and supplies new observations. This project adopts that feedback loop, not any
private Codex runtime or hidden tool. [OpenAI computer use](https://developers.openai.com/api/docs/guides/tools-computer-use).

Anthropic's native computer-use API similarly requires a client-side implementation. Its
provider-defined tool schemas and model support are separate from this plugin. Astral-Claude
exposes ordinary MCP tools to the model already selected in Claude Code; it does not inject a
native computer tool or promise the same performance as a provider's dedicated harness.
[Anthropic computer use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool).

Claude Code plugins package skills and MCP servers. Skills hold task-specific procedures,
while servers give the host callable operations. Plugin-root `CLAUDE.md` is for repository
work, not automatically loaded consumer context. Runtime paths use `CLAUDE_PLUGIN_ROOT` so
cached installs are self-contained. Plugin tool names carry a `mcp__plugin_<plugin>_<server>__`
prefix. [Plugin reference](https://code.claude.com/docs/en/plugins-reference),
[skills](https://code.claude.com/docs/en/skills),
[marketplaces](https://code.claude.com/docs/en/plugin-marketplaces).

## Two servers

| Server | Origin | Purpose |
| --- | --- | --- |
| `astral-desktop` | This repository | Primary-display screenshots and observation-bound mouse/keyboard input for any application |
| `blender` | [blender-mcp](https://github.com/ahujasid/blender-mcp) (MIT), pinned release started with `uvx` | Scene queries, `bpy` execution, and viewport screenshots inside the user's open Blender session, plus optional asset tools |

They are independent processes. The desktop server needs an X11, Windows, or macOS session;
the Blender server needs its addon connected inside a running Blender and works anywhere Blender
runs, including Wayland desktops, because Blender captures its own viewport. The `blender`
skill chooses between background `bpy` scripts, the live session, and desktop input per task.

## Desktop tool contract

| Tool | Input | Output / effect |
| --- | --- | --- |
| `desktop_status` | None | Session/prerequisite report with plugin version and `primary_modifier`; no capture or input |
| `desktop_observe` | Optional `max_dimension` (640–2400) | PNG image content plus JSON text with image size, desktop size, and ID |
| `desktop_act` | Latest `observation_id`, structured `action` | One input operation, then a new PNG (same `max_dimension`) and ID |

Supported actions: `click` (one/two clicks; left/middle/right), `move`, `drag`, `scroll`
(moves the pointer to `x, y`, then vertical signed notches), `key` (simultaneous hotkey),
`type_text` (ASCII), `paste_text` (Unicode through the clipboard; restores the previous text
after `duration` seconds if the clipboard still contains the pasted text), `wait` (0.1–10
seconds). Paths and shell commands are not part of
this MCP. Use Claude Code's existing execution tools for authorized native scripts.

Images use the display anchored at desktop origin `(0,0)`. Their longest side is at most 1600
pixels by default. Actions use the image's coordinates; numeric values round to whole pixels,
and the server maps them proportionally to logical input coordinates. Aspect-ratio mismatches
and changed logical dimensions reject input. Key names are checked against the OS backend's
real key map, so a name PyAutoGUI would silently ignore (for example `command` on X11) is
rejected with a hint. Use one primary display; arbitrary monitor selection and crop-coordinate
input are not implemented.

The controller serializes calls with a lock. Each action consumes the current ID before
executing, including when execution raises, because a failure may follow partial input.
Failed hotkeys and drags attempt to release their keys/buttons, even at a fail-safe corner;
cleanup failures retain the original input error. The fail-safe remains enabled.
IDs expire after 120 seconds. A process-level file lock, keyed by the X11 server identity
(screen suffixes such as `:0.0` share `:0`) or a fixed native identity on Windows/macOS, prevents multiple
Astral servers on the same user's display; `ASTRAL_CLAUDE_LOCK_DIR` relocates the lock files
for tests or unusual home directories. These checks do not detect changed page content, moved
windows, stolen focus, another automation system, or all physical monitor configuration changes.

Images stay in process memory and are returned as MCP image content, so a capable host/model
can inspect them directly. No screenshot-file permission or path trick is required. The host
may retain tool results according to its own settings. The implementation keeps only the
latest observation; it does not write screen recordings or text input logs.

## Blender MCP boundaries

The bundled server connects to the addon's localhost socket only when a Blender tool is called;
without Blender it starts, logs a warning, and every Blender tool returns a connection error.
`execute_blender_code` runs arbitrary Python on Blender's main thread with the user's
privileges, so the skill treats scene text and tool results as data, saves versioned copies
before destructive edits, and keeps snippets short. The plugin starts the server with
`DISABLE_TELEMETRY=true`, which upstream documents as turning off its telemetry for that
process; the addon keeps its own consent setting in Blender's preferences. See
[platform setup](platforms.md#blender-mcp) for installation and version matching.

## Choosing a surface

For app state available through a native API, use exact operations with explicit targets.
For UI state, inspect screenshots or existing accessibility/DOM tools. For visual quality,
inspect the render/export. For durable completion, reopen the native artifact. These forms
of evidence answer different questions and can be combined within one task.

Blender is the first application with both a runnable background example and a live-session
route. Other application classes have discovery guidance, not advertised adapters. The
extension point is a narrowly triggered skill plus tested helpers when needed, rather than a
universal prompt full of every application's shortcuts.

Backend references: [PyAutoGUI](https://pyautogui.readthedocs.io/en/latest/),
[MSS](https://python-mss.readthedocs.io/),
[official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk).
