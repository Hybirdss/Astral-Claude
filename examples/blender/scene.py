"""Run only in a fresh Blender process; see run.py. No external assets required."""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

output = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"


def material(name, color, metallic=0.0, roughness=0.4):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return mat


enamel = material("Ochre enamel", (0.82, 0.34, 0.055), 0.3, 0.27)
metal = material("Dark brushed metal", (0.055, 0.075, 0.085), 0.75, 0.32)
rubber = material("Rubber", (0.025, 0.032, 0.03), 0, 0.7)
floor_mat = material("Warm studio", (0.26, 0.32, 0.30), 0, 0.8)


def finish(obj, name, mat, bevel=0.025):
    obj.name = name
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new("Soft manufactured edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def cylinder(name, radius, depth, location, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=radius, depth=depth, location=location)
    return finish(bpy.context.object, name, mat)


def rod(name, start, end, radius):
    a, b = Vector(start), Vector(end)
    obj = cylinder(name, radius, (b - a).length, (a + b) / 2, metal)
    obj.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    return obj


cylinder("Rubber foot", 0.61, 0.06, (0, 0, 0.035), rubber)
cylinder("Lamp base", 0.66, 0.13, (0, 0, 0.125), enamel)
cylinder("Base inset", 0.39, 0.04, (0, 0, 0.21), metal)
rod("Lower arm", (0, 0, 0.23), (-0.36, 0, 1.42), 0.055)
rod("Upper arm", (-0.36, 0, 1.42), (0.43, 0, 2.12), 0.05)
for index, point in enumerate([(0, 0, 0.26), (-0.36, 0, 1.42), (0.43, 0, 2.12)]):
    joint = cylinder(f"Joint {index}", 0.115, 0.17, point, enamel)
    joint.rotation_euler.x = math.pi / 2

bpy.ops.mesh.primitive_cone_add(
    vertices=96, radius1=0.43, radius2=0.17, depth=0.43, location=(0.43, 0, 1.87)
)
finish(bpy.context.object, "Lamp shade", enamel)
bulb_mat = material("Warm diffuser", (1.0, 0.82, 0.47), 0, 0.3)
shader = bulb_mat.node_tree.nodes.get("Principled BSDF")
shader.inputs["Emission Color"].default_value = (1, 0.68, 0.3, 1)
shader.inputs["Emission Strength"].default_value = 2
cylinder("Diffuser", 0.395, 0.018, (0.43, 0, 1.648), bulb_mat)
cylinder("Power switch", 0.07, 0.05, (0.32, -0.24, 0.225), rubber)
bpy.ops.mesh.primitive_plane_add(size=200)
finish(bpy.context.object, "Studio floor", floor_mat, bevel=0)


def area(name, location, energy, size, target, color=(1, 1, 1)):
    light = bpy.data.lights.new(name, "AREA")
    light.energy = energy
    light.shape = "DISK"
    light.size = size
    light.color = color
    obj = bpy.data.objects.new(name, light)
    scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


area("Key", (0, -3, 5), 500, 4, (0, 0, 1))
area("Rim", (2, 2, 4), 650, 3, (0, 0, 1), (0.75, 0.86, 1))
area("Practical", (0.43, 0, 1.62), 25, 0.5, (0.43, 0, 0), (1, 0.65, 0.3))
camera_data = bpy.data.cameras.new("Product camera")
camera = bpy.data.objects.new("Product camera", camera_data)
scene.collection.objects.link(camera)
camera.location = (3.6, -6, 3.3)
camera.rotation_euler = (
    (Vector((0.05, 0, 1.05)) - camera.location).to_track_quat("-Z", "Y").to_euler()
)
camera_data.type = "ORTHO"
camera_data.ortho_scale = 3.75
scene.camera = camera
scene.world.color = (0.18, 0.18, 0.18)
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x = 960
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(output / "lamp.png")
bpy.ops.wm.save_as_mainfile(filepath=str(output / "lamp.blend"))
bpy.ops.render.render(write_still=True)
