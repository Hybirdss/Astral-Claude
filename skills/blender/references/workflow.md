# Blender workflow notes

## A useful order

1. Inspect scene, units, frame range, engine, camera, output paths, dependencies, and version.
2. Block out scale, silhouettes, and camera with simple materials.
3. Add the few forms that determine recognition. Preview and inspect.
4. Tune material roughness, light size/direction, background separation, and color management.
5. Add supporting detail only when it helps at delivery resolution.
6. Save, render/export, reopen, and inspect. Package assets or document required external paths.

## Context-sensitive operations

`bpy.ops` can depend on active object, selection, mode, view layer, region, and editor area.
Headless execution has no interactive 3D viewport. Use the data API when there is no suitable
UI context. If an operator is required, inspect its installed-version documentation and set
the actual prerequisites; do not assume a successful call changed the intended object.

## Structural evidence

Use assertions tied to the user's task: expected object names and types, dimension tolerance,
active render camera, frame range, export format, and existence of linked images. Reopen the
saved file in another Blender process to detect failures hidden by in-memory state.
Use `blender --background file.blend --python-exit-code 1 --python verify.py`.

## Visual evidence

Inspect the saved render, including full-frame composition and details at final resolution.
Watch for clipped silhouettes, floating objects, excessively dark materials, distracting
highlights, unreadable text, missing textures, and camera changes that invalidate the brief.
For animation, sample representative frames and transitions; one still is not animation QA.

Primary references: [Python API](https://docs.blender.org/api/current/),
[operator context](https://developer.blender.org/docs/features/interface/operators/), and
[command line](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html).
