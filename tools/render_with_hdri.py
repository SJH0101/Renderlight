"""Render a model lit ONLY by an HDRI (simulates KeyShot: environment image + solid background color).

    python3 tools/render_with_hdri.py <model.glb> <hdri.exr> <out.png> [bg_gray 0-1] [rotation_deg] [res] [floor: matte|glossy]
"""
import sys, math
import bpy
from mathutils import Vector

model, hdri, out = sys.argv[1:4]
bg = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
rot = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
res = int(sys.argv[6]) if len(sys.argv) > 6 else 480
floor = sys.argv[7] if len(sys.argv) > 7 else "matte"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=model)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
center, size = (lo + hi) / 2, (hi - lo).length
cd = bpy.data.cameras.new("Cam"); cd.lens = 85
cam = bpy.data.objects.new("Cam", cd)
cam.location = center + Vector((0, -size * 2.9, size * 0.18))
cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.collection.objects.link(cam); bpy.context.scene.camera = cam
# KeyShot-style ground: large plane catching shadows/reflections
bpy.ops.mesh.primitive_plane_add(size=size * 40, location=(center.x, center.y, lo.z))
gm = bpy.data.materials.new("Ground"); gm.use_nodes = True
b = gm.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (bg * 0.5 + 0.004,) * 3 + (1,)
b.inputs["Roughness"].default_value = 0.05 if floor == "glossy" else 1.0
if floor != "glossy":
    b.inputs["Specular IOR Level"].default_value = 0.0
else:
    b.inputs["Coat Weight"].default_value = 1.0
bpy.context.active_object.data.materials.append(gm)
w = bpy.data.worlds.new("W"); bpy.context.scene.world = w
try: w.use_nodes = True
except Exception: pass
nt = w.node_tree; nodes, links = nt.nodes, nt.links
out_ = next(n for n in nodes if n.type == 'OUTPUT_WORLD'); bgn = next(n for n in nodes if n.type == 'BACKGROUND')
env = nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(hdri)
tc = nodes.new("ShaderNodeTexCoord"); mp = nodes.new("ShaderNodeMapping")
mp.inputs["Rotation"].default_value[2] = math.radians(rot)
links.new(tc.outputs["Generated"], mp.inputs["Vector"]); links.new(mp.outputs["Vector"], env.inputs["Vector"])
links.new(env.outputs["Color"], bgn.inputs["Color"])
solid = nodes.new("ShaderNodeBackground"); solid.inputs["Color"].default_value = (bg, bg, bg, 1)
lp = nodes.new("ShaderNodeLightPath"); mix = nodes.new("ShaderNodeMixShader")
links.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); links.new(bgn.outputs[0], mix.inputs[1]); links.new(solid.outputs[0], mix.inputs[2])
links.new(mix.outputs[0], out_.inputs["Surface"])
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.samples = 128; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 16; sc.cycles.transmission_bounces = 16
sc.render.resolution_x = sc.render.resolution_y = res
sc.view_settings.view_transform = 'AgX'
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("rendered", out)
