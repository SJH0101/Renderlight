"""Render every preset on a test scene -> gallery images + smoke test."""
import sys, os, math, time
import bpy
from mathutils import Vector

SCRIPTS = sys.argv[1]
OUT = sys.argv[2]
RES = int(sys.argv[3]) if len(sys.argv) > 3 else 256
SAMPLES = int(sys.argv[4]) if len(sys.argv) > 4 else 32
ONLY = sys.argv[5].split(",") if len(sys.argv) > 5 and sys.argv[5] else None
os.makedirs(OUT, exist_ok=True)

ns = {}
exec(open(os.path.join(SCRIPTS, "lt_helpers.py")).read(), ns)
exec(open(os.path.join(SCRIPTS, "lt_presets.py")).read(), ns)


def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    # subject: head-ish sphere with a nose so face patterns read
    bpy.ops.mesh.primitive_monkey_add(size=1.0, location=(0, 0, 1.0))
    head = bpy.context.active_object
    head.name = "Head"
    head.rotation_euler = (0, 0, 0)  # suzanne faces -Y
    m = bpy.ops.object.modifier_add(type='SUBSURF')
    head.modifiers[-1].levels = 2
    head.modifiers[-1].render_levels = 2
    bpy.ops.object.shade_smooth()
    mat = bpy.data.materials.new("Skin")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1)
    mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.5
    head.data.materials.append(mat)
    # floor + back wall
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0.3))
    floor = bpy.context.active_object
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 3, 0.3), rotation=(math.radians(90), 0, 0))
    wall = bpy.context.active_object
    gm = bpy.data.materials.new("Grey")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.35, 0.35, 0.35, 1)
    floor.data.materials.append(gm)
    wall.data.materials.append(gm)
    # an existing light (should be hidden by presets)
    ld = bpy.data.lights.new("UserLight", 'POINT')
    lo = bpy.data.objects.new("UserLight", ld)
    lo.location = (0, -3, 4)
    scn.collection.objects.link(lo)
    # camera
    cd = bpy.data.cameras.new("Cam")
    cd.lens = 70
    cam = bpy.data.objects.new("Cam", cd)
    cam.location = (0, -5.2, 1.15)
    cam.rotation_euler = (math.radians(89), 0, 0)
    scn.collection.objects.link(cam)
    scn.camera = cam
    w = bpy.data.worlds.new("World")
    scn.world = w
    scn.render.engine = 'CYCLES'
    scn.cycles.samples = SAMPLES
    scn.cycles.use_denoising = True
    scn.cycles.device = 'CPU'
    scn.render.resolution_x = scn.render.resolution_y = RES
    scn.render.film_transparent = False
    try:
        scn.view_settings.view_transform = 'AgX'
    except Exception:
        pass
    scn.frame_set(24)
    return scn


results = []
keys = ONLY or list(ns["PRESETS"].keys())
for key in keys:
    num, ko, _ = ns["PRESETS"][key]
    scn = build_scene()
    kw = {}
    if key == "practical":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15, location=(1.1, -0.3, 1.5))
        bpy.context.active_object.name = "Lamp"
        kw["practicals"] = ["Lamp"]
    t = time.time()
    try:
        ns["apply_preset"](key, subject="Head", **kw)
        assert bpy.data.objects["UserLight"].hide_render, "existing light not hidden"
        scn.render.filepath = os.path.join(OUT, f"{num:02d}_{key}.png")
        bpy.ops.render.render(write_still=True)
        # restore check
        ns["lt_restore"]()
        assert not bpy.data.objects["UserLight"].hide_render, "restore failed"
        results.append((key, "ok", round(time.time() - t, 1)))
    except Exception as e:
        import traceback; traceback.print_exc()
        results.append((key, f"FAIL {type(e).__name__}: {e}", 0))
    print("RESULT", results[-1], flush=True)

# stacked combo test
scn = build_scene()
try:
    ns["apply_preset"](["rembrandt", "golden_hour", "rim"], subject="Head")
    scn.render.filepath = os.path.join(OUT, "combo_rembrandt_golden_rim.png")
    bpy.ops.render.render(write_still=True)
    ns["apply_preset"]("렘브란트", subject="Head")
    ns["apply_preset"]("03", subject="Head")
    results.append(("combo+aliases", "ok", 0))
except Exception as e:
    import traceback; traceback.print_exc()
    results.append(("combo+aliases", f"FAIL {e}", 0))

print("SUMMARY")
for r in results:
    print(r)
