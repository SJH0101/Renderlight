"""Render a catalog recipe on a test model (Blender / Cycles).

    python3 tools/render_recipe.py <recipe_id> <model.glb> <out.png> [res] [samples] [overrides.json]
"""
import sys, os, json, math
import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "blender/skills/blender-lighting-presets/scripts")
ns = {}
exec(open(os.path.join(SCRIPTS, "lt_helpers.py")).read(), ns)

rid, model, out = sys.argv[1], sys.argv[2], sys.argv[3]
RES = int(sys.argv[4]) if len(sys.argv) > 4 else 480
SAMPLES = int(sys.argv[5]) if len(sys.argv) > 5 else 128
override = json.loads(sys.argv[6]) if len(sys.argv) > 6 else None

recipes = {r["id"]: r for r in json.load(open(os.path.join(ROOT, "catalog/recipes.json")))["recipes"]}
recipe = override or recipes[rid]

KIND = {"rect": "AREA", "spot": "SPOT", "point": "POINT", "sun": "SUN"}
BACKDROP = {"black": 0.008, "white": 0.85, "dark_gradient": 0.03, "light_gradient": 0.6}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=model)
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)])
hi = Vector([max(p[i] for p in pts) for i in range(3)])
center, size = (lo + hi) / 2, (hi - lo).length

# camera: front, slightly above, framed to the subject
cd = bpy.data.cameras.new("Cam"); cd.lens = 85
cam = bpy.data.objects.new("Cam", cd)
dist = size * 2.9
cam.location = center + Vector((0, -dist, size * 0.18))
cam.rotation_euler = (center - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

# seamless backdrop (sweep) behind and under the subject
bd = recipe.get("backdrop", "black")
alb = BACKDROP.get(bd, 0.05)
S = size * 6
me = bpy.data.meshes.new("Sweep")
prof = [(-S, 0)] + [(S * 0.3 * math.sin(t / 12 * math.pi / 2), S * 0.3 * (1 - math.cos(t / 12 * math.pi / 2))) for t in range(13)] + [(S * 0.3, S)]
verts, faces = [], []
for i, (y, z) in enumerate(prof):
    verts += [(-S, y + size * 1.2, z + lo.z), (S, y + size * 1.2, z + lo.z)]
    if i: faces.append((2 * i - 2, 2 * i - 1, 2 * i + 1, 2 * i))
me.from_pydata(verts, [], faces)
sweep = bpy.data.objects.new("LT_Sweep", me)
bpy.context.scene.collection.objects.link(sweep)
m = bpy.data.materials.new("Backdrop"); m.use_nodes = True
b = m.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (alb, alb, alb, 1)
b.inputs["Roughness"].default_value = 0.95 if bd == "black" else 0.8
me.materials.append(m)

# lights from the recipe, in subject/camera coordinates
ctx = ns["lt_setup"](rid, subject=[o.name for o in meshes])
for l in recipe["rig"]:
    size_v = tuple(l["size"]) if isinstance(l.get("size"), list) else l.get("size", 0.5)
    ns["lt_light"](ctx, l["role"], kind=KIND[l["kind"]], az=l["az"], el=l["el"], dist=l.get("dist", 1.5),
                   ratio=l.get("ratio", 1.0), size=size_v, kelvin=l.get("kelvin", 5600),
                   color=tuple(l["color"]) if l.get("color") else None, spread=l.get("spread"))
w = recipe.get("world", {})
ns["lt_world"](strength=w.get("strength", 0.0), color=tuple(w.get("color", (1, 1, 1))), exposure=recipe.get("exposure"))

sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 16
sc.cycles.transmission_bounces = 16
sc.cycles.glossy_bounces = 8
sc.render.resolution_x = sc.render.resolution_y = RES
sc.view_settings.view_transform = 'AgX'
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("rendered", out)
