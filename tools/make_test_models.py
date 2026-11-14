"""Build test models for lighting recipes (glass bottle, chrome watch, glossy device).

    python3 tools/make_test_models.py public/models
Needs the `bpy` module (pip install bpy). Each model rests on z=0 (y=0 in glTF), faces -Y (the camera).
"""
import sys, os, math
import bpy

OUT = sys.argv[1] if len(sys.argv) > 1 else "public/models"
os.makedirs(OUT, exist_ok=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, base=(0.8, 0.8, 0.8), metallic=0.0, rough=0.5, transmission=0.0, ior=1.45, coat=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    b.inputs["IOR"].default_value = ior
    b.inputs["Transmission Weight"].default_value = transmission
    b.inputs["Coat Weight"].default_value = coat
    return m


def smooth(angle=35):
    # smooth curved parts but keep flat faces flat (a smooth-shaded flat cap bends light like a lens)
    try:
        bpy.ops.object.shade_auto_smooth(angle=math.radians(angle))
    except Exception:
        bpy.ops.object.shade_smooth()


def rounded_box(name, size, bevel, segs=6, loc=(0, 0, 0), material=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    m = o.modifiers.new("bevel", 'BEVEL')
    m.width = bevel
    m.segments = segs
    m.limit_method = 'NONE'
    bpy.ops.object.modifier_apply(modifier="bevel")
    smooth()
    if material:
        o.data.materials.append(material)
    return o


def cyl(name, r, h, loc, material=None, verts=64, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=verts, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    smooth()
    if material:
        o.data.materials.append(material)
    return o


def export(name):
    path = os.path.join(OUT, f"{name}.glb")
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_apply=True, export_yup=True)
    print("wrote", path)


# ---------- 1. perfume bottle: hollow thick glass, heavy base, amber liquid, gold foil logo, grooved cap ----------
def smudge_texture(path, res=512, seed=3):
    """Roughness map: clean glass (low) with faint fingerprints/smudges (higher)."""
    import numpy as np
    from PIL import Image, ImageFilter
    rng = np.random.default_rng(seed)
    img = np.full((res, res), 10, np.float32)          # ~0.04 roughness
    for _ in range(14):                                 # smudges
        x, y, r = rng.integers(0, res, 2).tolist() + [int(rng.integers(20, 70))]
        yy, xx = np.ogrid[:res, :res]
        img += 30 * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * r * r))
    for _ in range(4):                                  # fingerprint-ish ridges
        x, y = rng.integers(60, res - 60, 2)
        yy, xx = np.ogrid[:res, :res]
        d = np.sqrt((xx - x) ** 2 + ((yy - y) * 1.3) ** 2)
        img += np.where(d < 45, 18 * (0.5 + 0.5 * np.sin(d * 0.9)), 0)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    rgb = Image.merge("RGB", (im, im, im))
    rgb.save(path)
    return path


def boolean(target, cutter):
    m = target.modifiers.new("bool", 'BOOLEAN')
    m.operation = 'DIFFERENCE'; m.solver = 'EXACT'; m.object = cutter
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier="bool")
    bpy.data.objects.remove(cutter, do_unlink=True)


reset()
tex_path = smudge_texture(os.path.join(OUT, "_glass_rough.png"))
glass = mat("Glass", base=(1, 1, 1), rough=0.03, transmission=1.0, ior=1.5)
img = bpy.data.images.load(tex_path); img.colorspace_settings.name = "Non-Color"
nt = glass.node_tree
ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = img
sep = nt.nodes.new("ShaderNodeSeparateColor")
nt.links.new(ti.outputs["Color"], sep.inputs["Color"])
nt.links.new(sep.outputs["Green"], nt.nodes["Principled BSDF"].inputs["Roughness"])
liquid = mat("Perfume", base=(0.95, 0.6, 0.22), rough=0.0, transmission=1.0, ior=1.33)
gold = mat("Gold", base=(1.0, 0.77, 0.4), metallic=1.0, rough=0.16)
foil = mat("GoldFoil", base=(1.0, 0.78, 0.42), metallic=1.0, rough=0.28)
cap = mat("CapBlack", base=(0.012, 0.012, 0.012), rough=0.12, coat=1.0)

W, D, H = 0.62, 0.30, 0.78
WALL, BASE = 0.05, 0.13
outer = rounded_box("Bottle", (W, D, H), 0.11, segs=10, loc=(0, 0, H / 2), material=glass)
iw, idp, ih = W - 2 * WALL, D - 2 * WALL, H - BASE - WALL
inner = rounded_box("Cavity", (iw, idp, ih + 0.2), 0.07, segs=8, loc=(0, 0, BASE + (ih + 0.2) / 2))
boolean(outer, inner)
# simple box UVs so the smudge map lands on the glass
bpy.context.view_layer.objects.active = outer
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.cube_project(cube_size=1.0); bpy.ops.object.mode_set(mode='OBJECT')
smooth(30)
lh = ih * 0.75
rounded_box("Liquid", (iw - 0.006, idp - 0.006, lh), 0.065, segs=8, loc=(0, 0, BASE + lh / 2 + 0.002), material=liquid)
cyl("Neck", 0.06, 0.06, (0, 0, H + 0.03), glass)
cyl("Collar", 0.085, 0.04, (0, 0, H + 0.07), gold)
capo = rounded_box("Cap", (0.32, 0.32, 0.26), 0.035, loc=(0, 0, H + 0.09 + 0.13), material=cap)
groove = rounded_box("CapGroove", (0.34, 0.34, 0.012), 0.004, loc=(0, 0, H + 0.09 + 0.06))
boolean(capo, groove)
# gold foil wordmark on the front (invented brand)
bpy.ops.object.text_add(location=(0, -D / 2 - 0.0015, H * 0.62), rotation=(math.radians(90), 0, 0))
t = bpy.context.active_object
t.data.body = "LUMEN"
t.data.align_x = 'CENTER'; t.data.align_y = 'CENTER'
t.data.size = 0.085; t.data.extrude = 0.0008; t.data.space_character = 1.35
bpy.ops.object.convert(target='MESH')
t.name = "Wordmark"; t.data.materials.append(foil)
bpy.ops.object.text_add(location=(0, -D / 2 - 0.0015, H * 0.52), rotation=(math.radians(90), 0, 0))
t2 = bpy.context.active_object
t2.data.body = "EAU DE PARFUM"; t2.data.align_x = 'CENTER'; t2.data.align_y = 'CENTER'
t2.data.size = 0.028; t2.data.extrude = 0.0006; t2.data.space_character = 1.6
bpy.ops.object.convert(target='MESH')
t2.name = "Subline"; t2.data.materials.append(foil)
export("perfume")
os.remove(tex_path)

# ---------- 2. chrome watch: polished case, sapphire glass, dark dial, leather strap ----------
reset()
chrome = mat("Chrome", base=(0.95, 0.95, 0.95), metallic=1.0, rough=0.08)
brushed = mat("Bezel", base=(0.95, 0.95, 0.95), metallic=1.0, rough=0.07)  # polished bezel
sapphire = mat("Sapphire", base=(1, 1, 1), rough=0.0, transmission=1.0, ior=1.77)
dial = mat("Dial", base=(0.02, 0.03, 0.06), rough=0.35)
hands = mat("Hands", base=(0.95, 0.95, 0.95), metallic=1.0, rough=0.1)
leather = mat("Leather", base=(0.12, 0.06, 0.03), rough=0.7)
R, T = 0.42, 0.14
cz = R + 0.05  # watch stands on its edge, dial facing -Y
rot = (math.radians(90), 0, 0)
cyl("Case", R, T, (0, 0, cz), chrome, rot=rot)
bpy.ops.mesh.primitive_torus_add(major_radius=R - 0.02, minor_radius=0.035, location=(0, -T / 2, cz), rotation=rot, major_segments=96, minor_segments=24)
bz = bpy.context.active_object; bz.name = "Bezel"; bpy.ops.object.shade_smooth(); bz.data.materials.append(brushed)
cyl("Dial", R - 0.05, 0.006, (0, -T / 2 - 0.004, cz), dial, rot=rot)
cyl("Crystal", R - 0.04, 0.012, (0, -T / 2 - 0.022, cz), sapphire, rot=rot)
for i in range(12):  # hour markers
    a = i * math.pi / 6
    rounded_box(f"Marker{i}", (0.018, 0.01, 0.07 if i % 3 == 0 else 0.045), 0.004,
                loc=(math.sin(a) * (R - 0.11), -T / 2 - 0.009, cz + math.cos(a) * (R - 0.11)), material=hands).rotation_euler = (0, a, 0)
rounded_box("HourHand", (0.025, 0.008, 0.2), 0.006, loc=(0.05, -T / 2 - 0.012, cz + 0.07), material=hands).rotation_euler = (0, math.radians(-40), 0)
rounded_box("MinuteHand", (0.018, 0.008, 0.3), 0.005, loc=(-0.09, -T / 2 - 0.014, cz + 0.11), material=hands).rotation_euler = (0, math.radians(35), 0)
cyl("Crown", 0.04, 0.06, (R + 0.02, 0, cz), chrome, rot=(0, math.radians(90), 0))
rounded_box("StrapTop", (0.26, 0.06, 0.5), 0.02, loc=(0, 0.02, cz + R + 0.22), material=leather)
rounded_box("StrapBottom", (0.26, 0.06, 0.1), 0.02, loc=(0, 0.02, cz - R - 0.03), material=leather)
export("watch")

# ---------- 3. glossy device: white earbud-style charging case with a seam and LED ----------
reset()
plastic = mat("GlossWhite", base=(0.92, 0.92, 0.9), rough=0.12, coat=1.0)
seam = mat("Seam", base=(0.05, 0.05, 0.05), rough=0.6)
led = mat("LED", base=(0.2, 0.9, 0.4), rough=0.3)
cw, cd, ch = 0.62, 0.26, 0.5
rounded_box("Case", (cw, cd, ch), 0.12, segs=10, loc=(0, 0, ch / 2), material=plastic)
rounded_box("Seam", (cw + 0.004, cd + 0.004, 0.008), 0.003, loc=(0, 0, ch * 0.72), material=seam)
cyl("Led", 0.012, 0.01, (0, -cd / 2 - 0.002, ch * 0.45), led, rot=(math.radians(90), 0, 0))
export("device")
