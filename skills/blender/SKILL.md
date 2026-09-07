---
name: blender
description: Create, edit, render, and verify Blender scenes with bpy scripting and GUI inspection. Use for modeling, materials, lighting, cameras, animation, and Blender deliverables.
---

# Blender

Start by identifying the deliverable: editable `.blend`, render, animation, or interchange
export. Establish scale/units, visual target, resolution, and relevant budget from the request.
Inspect the existing scene before changing it. Do not reset a user's scene to run an example.

## Build precisely; inspect visually

- Discover the installed Blender executable and version. Blender's embedded Python provides
  `bpy`; the MCP server's Python does not. Run scripts with Blender or its Text Editor.
- Prefer `bpy.data` for explicit objects, materials, collections, and properties. Use operators
  when useful, with the correct mode, active object, selection, and area. A failed `poll()` is
  a context problem; inspect it instead of retrying unchanged or fabricating an override.
- In existing files, work in a named collection and use stable names/custom properties to
  update only task-owned content. Preserve unrelated objects. Make a versioned save before
  changing topology, applying modifiers, or replacing materials.
- For scripted background work, put `--python-exit-code 1` before `--python`. Use an argument
  array when launching from Python so paths with spaces work on every OS. Check exit status.
- Choose camera and silhouette early. Make a cheap preview before detail work. Inspect actual
  pixels for framing, clipping, intersections, material response, shadows, and readability.
  Fix the largest visible defect, render again, and compare. Data assertions cannot judge art.
- Check object transforms, dimensions, normals, missing assets, and engine/version support.
  Export into a new output directory. Reopen the `.blend` and verify the expected objects,
  camera, render settings, and external assets. Deliver native source as well as requested media.

## GUI work

Use [computer use](../computer-use/SKILL.md) for screenshot/input mechanics. Blender shortcuts
depend on the editor under the mouse and Object/Edit mode. Observe both before sending keys.
Identify the relevant viewport, Outliner, Properties tab, or editor explicitly. Inspect a
rendered camera view as well as structural state. Opening a file is not proof it rendered well.

For a complete runnable seed, read [the example](../../examples/blender/README.md). The example
uses a fresh process with factory startup and creates a new scene; adapt its approach, not its
destructive initialization, when the user has an existing project. Read
[Blender references](references/workflow.md) for context and verification details.
