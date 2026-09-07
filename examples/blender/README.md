# Blender: build, render, reopen

From the repository root, with Blender installed:

```text
uv run python examples/blender/run.py --output artifacts/lamp
```

If Blender is not on PATH, pass `--blender` with the executable path (see
[platform setup](../../docs/platforms.md)). The wrapper uses argument arrays and resolves paths
without shell-specific quoting logic. It refuses an existing output directory.

The script starts a **new factory-default background process**, creates a small desk-lamp
product scene, saves `lamp.blend`, and renders `lamp.png` with CPU Cycles. A second process
opens the saved scene and writes `verification.json` with structural checks. No external
textures, downloads, GUI access, or model API calls are needed. Allow a few minutes on slower CPUs.

Open `lamp.png` with Claude Code's image-reading capability or an image viewer, evaluate
appearance, and revise if needed. The verification script checks objects, dimensions, camera,
and image size; it cannot tell whether a render looks good. To inspect the native scene in
Blender's GUI, open the saved `.blend` on the desktop controlled by the MCP server.

This example demonstrates the native scripting half of a hybrid workflow. It does not pretend
to be a GUI-driven modeling benchmark. `scene.py` deletes the fresh startup scene; do not run
it inside a user's existing document. Read the [Blender skill](../../skills/blender/SKILL.md)
for adapting the workflow to existing projects.
