"""Structural checks in a second Blender process, after loading the saved .blend."""

import json
import sys
from pathlib import Path

import bpy

output = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
expected = {"Lamp base", "Lower arm", "Upper arm", "Lamp shade", "Diffuser", "Product camera"}
assert expected <= set(bpy.data.objects.keys()), "Missing expected objects in saved scene"
scene = bpy.context.scene
assert scene.camera.name == "Product camera"
assert (scene.render.resolution_x, scene.render.resolution_y) == (960, 720)
assert scene.render.resolution_percentage == 100
assert abs(bpy.data.objects["Lamp base"].dimensions.x - 1.32) < 0.01
assert (output / "lamp.blend").stat().st_size > 10000
assert (output / "lamp.png").stat().st_size > 1000
image = bpy.data.images.load(str(output / "lamp.png"), check_existing=False)
assert tuple(image.size) == (960, 720), "Saved PNG has wrong dimensions"
report = {
    "blender_version": bpy.app.version_string,
    "reopened_scene": True,
    "expected_objects": sorted(expected),
    "render_dimensions": list(image.size),
    "visual_review": "pending: inspect lamp.png in an image viewer",
}
(output / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report))
