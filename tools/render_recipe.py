"""Render a catalog recipe on a test model (Blender / Cycles).

    python3 tools/render_recipe.py <recipe_id> <model.glb> <out.png> [res] [samples] ['{"floor":"acrylic"}']
The last argument is the user's chosen options (or a full recipe JSON with a "rig" key, for tuning).
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
extra = json.loads(sys.argv[6]) if len(sys.argv) > 6 else {}

sys.path.insert(0, os.path.join(ROOT, "catalog"))
from apply import apply_options, defaults
recipes = {r["id"]: r for r in json.load(open(os.path.join(ROOT, "catalog/recipes.json")))["recipes"]}
if "rig" in extra:
    recipe = extra
else:
    base = recipes[rid]
    recipe = apply_options(base, {**defaults(base), **extra})

KIND = {"rect": "AREA", "spot": "SPOT", "point": "POINT", "sun": "SUN"}
BACKDROP = {"white_glossy": 0.85, "black_glossy": 0.004, "black": 0.008, "white": 0.85, "dark_gradient": 0.03, "light_gradient": 0.6}

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
b.inputs["Roughness"].default_value = {"black": 0.95, "black_glossy": 0.04}.get(bd, 0.8)
if bd in ("black_glossy", "white_glossy"):
    b.inputs["Roughness"].default_value = 0.04 if bd == "black_glossy" else 0.08
    b.inputs["Coat Weight"].default_value = 1.0  # acrylic: clean mirror reflection
elif bd == "black":
    b.inputs["Specular IOR Level"].default_value = 0.0  # truly matte: no blurry reflection of the bright subject
me.materials.append(m)

# lights from the recipe, in subject/camera coordinates
ctx = ns["lt_setup"](rid, subject=[o.name for o in meshes])
backdrop_col = bpy.data.collections.new("LT_BackdropOnly")
backdrop_col.objects.link(sweep)
subject_col = bpy.data.collections.new("LT_SubjectOnly")
for o in meshes:
    subject_col.objects.link(o)
for l in recipe["rig"]:
    size_v = tuple(l["size"]) if isinstance(l.get("size"), list) else l.get("size", 0.5)
    ns["lt_light"](ctx, l["role"], kind=KIND[l["kind"]], az=l["az"], el=l["el"], dist=l.get("dist", 1.5),
                   ratio=l.get("ratio", 1.0), size=size_v, kelvin=l.get("kelvin", 5600),
                   color=tuple(l["color"]) if l.get("color") else None, spread=l.get("spread"),
                   spot_deg=l.get("spot_deg", 40), blend=l.get("blend", 0.15))
    if l.get("subject_only"):  # light linking: this light does not touch the floor/backdrop
        lo_ = bpy.data.objects["LT_" + l["role"]]
        lo_.light_linking.receiver_collection = subject_col
    if l.get("backdrop_only"):  # lights the backdrop evenly without touching the subject
        bpy.data.objects["LT_" + l["role"]].light_linking.receiver_collection = backdrop_col
# black flags: camera-invisible black cards beside the subject. Glass edges refract them into dark outlines.
for i, f in enumerate(recipe.get("flags", [])):
    fm = bpy.data.meshes.new(f"Flag{i}")
    fm.from_pydata([(-.5, -.5, 0), (.5, -.5, 0), (.5, .5, 0), (-.5, .5, 0)], [], [(0, 1, 2, 3)])
    fo = bpy.data.objects.new(f"LT_Flag{i}", fm)
    d = ns["lt_dir"](ctx, f["az"], f.get("el", 0))
    fo.location = ctx["center"] + d * f.get("dist", 1.0) * size
    w_, h_ = f.get("size", [0.8, 2.0])
    fo.scale = (w_ * size, h_ * size, 1)
    fo.rotation_mode = 'QUATERNION'
    fo.rotation_quaternion = (ctx["center"] - fo.location).to_track_quat('Z', 'Y')
    bpy.context.scene.collection.objects.link(fo)
    fmat = bpy.data.materials.new("Flag"); fmat.use_nodes = True
    fb = fmat.node_tree.nodes["Principled BSDF"]
    fb.inputs["Base Color"].default_value = (0, 0, 0, 1)
    fb.inputs["Roughness"].default_value = 1.0
    fb.inputs["Specular IOR Level"].default_value = 0.0
    fm.materials.append(fmat)
    fo.visible_camera = False
    fo.visible_shadow = False

w = recipe.get("world", {})
ns["lt_world"](strength=w.get("strength", 0.0), color=tuple(w.get("color", (1, 1, 1))), exposure=recipe.get("exposure"))

# Reflection-only studio: the camera sees a dark background, but reflective surfaces see a
# soft gradient (bright above, dark below). This is how metal gets shape without lighting the background.
env = w.get("reflect")
if env:
    wt = bpy.context.scene.world.node_tree
    nodes, links = wt.nodes, wt.links
    out_ = next(n for n in nodes if n.type == 'OUTPUT_WORLD')
    bg_cam = next(n for n in nodes if n.type == 'BACKGROUND')
    tc = nodes.new("ShaderNodeTexCoord"); sep = nodes.new("ShaderNodeSeparateXYZ")
    mr = nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -0.1; mr.inputs["From Max"].default_value = 0.9
    bg_ref = nodes.new("ShaderNodeBackground")
    bg_ref.inputs["Strength"].default_value = env.get("strength", 0.6)
    lp = nodes.new("ShaderNodeLightPath"); mix = nodes.new("ShaderNodeMixShader")
    links.new(tc.outputs["Generated"], sep.inputs[0])
    links.new(sep.outputs["Z"], mr.inputs["Value"])
    links.new(mr.outputs["Result"], bg_ref.inputs["Color"])
    links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
    links.new(bg_ref.outputs[0], mix.inputs[1])
    links.new(bg_cam.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out_.inputs["Surface"])

sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 16
sc.cycles.transmission_bounces = 16
sc.cycles.glossy_bounces = 8
if recipe.get("no_caustics"):  # glass refracting light onto the floor
    sc.cycles.caustics_refractive = False
    sc.cycles.caustics_reflective = False
sc.render.resolution_x = sc.render.resolution_y = RES
sc.view_settings.view_transform = 'AgX'
sc.render.filepath = out
bpy.ops.render.render(write_still=True)
print("rendered", out)
