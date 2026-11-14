"""Bake a recipe's lights into an equirectangular HDRI (for KeyShot or any HDRI-lit renderer).

    python3 tools/bake_hdri.py <recipe_id> <model.glb> <out.exr> [options_json] [width]

The model only sets scale and the subject center; it is hidden while baking. Lights are made visible to
the panoramic camera, so each softbox/strip appears in the HDRI with its real brightness, size and color.
"""
import sys, os, json, math
import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, "skills/renderlight/catalog")
sys.path.insert(0, CAT)
from apply import apply_options, defaults  # noqa: E402

ns = {}
exec(open(os.path.join(ROOT, "skills/renderlight/scripts/lt_helpers.py")).read(), ns)
KIND = {"rect": "AREA", "spot": "SPOT", "point": "POINT", "sun": "SUN"}


def bake(rid, model, out, extra=None, width=2048):
    recipe_base = next(r for r in json.load(open(os.path.join(CAT, "recipes.json")))["recipes"] if r["id"] == rid)
    recipe = apply_options(recipe_base, {**defaults(recipe_base), **(extra or {})})
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=model)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    center = (lo + hi) / 2

    # a front camera defines the recipe's "camera side" (az 0), exactly like the real render
    size = (hi - lo).length
    cd = bpy.data.cameras.new("Front"); front = bpy.data.objects.new("Front", cd)
    front.location = center + Vector((0, -size * 2.9, size * 0.18))
    bpy.context.scene.collection.objects.link(front); bpy.context.scene.camera = front
    ctx = ns["lt_setup"](rid, subject=[o.name for o in meshes])
    for l in recipe["rig"]:
        sz = tuple(l["size"]) if isinstance(l.get("size"), list) else l.get("size", 0.5)
        o = ns["lt_light"](ctx, l["role"], kind=KIND[l["kind"]], az=l["az"], el=l["el"], dist=l.get("dist", 1.5),
                           ratio=l.get("ratio", 1.0), size=sz, kelvin=l.get("kelvin", 5600),
                           color=tuple(l["color"]) if l.get("color") else None,
                           spot_deg=l.get("spot_deg", 40), blend=l.get("blend", 0.15))
        o.visible_camera = True
    for m in meshes:
        m.hide_render = True

    # world: whatever the recipe's reflections would see (the reflection gradient, if any)
    w = recipe.get("world", {})
    ns["lt_world"](strength=w.get("strength", 0.0), color=tuple(w.get("color", (1, 1, 1))))
    if w.get("reflect"):
        nt = bpy.context.scene.world.node_tree
        bg = next(n for n in nt.nodes if n.type == 'BACKGROUND')
        tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.25; mr.inputs["From Max"].default_value = 1.0
        nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
        nt.links.new(mr.outputs["Result"], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = w["reflect"].get("strength", 0.6)

    # equirectangular camera at the subject center, oriented to the standard world mapping
    pc = bpy.data.cameras.new("Pano"); pc.type = 'PANO'
    pc.panorama_type = 'EQUIRECTANGULAR'
    pano = bpy.data.objects.new("Pano", pc)
    pano.location = center
    pano.rotation_euler = (math.radians(90), 0, math.radians(-90))
    bpy.context.scene.collection.objects.link(pano)
    sc = bpy.context.scene
    sc.camera = pano
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 64
    sc.cycles.use_denoising = False
    sc.render.resolution_x, sc.render.resolution_y = width, width // 2
    sc.view_settings.view_transform = 'Standard'   # keep linear radiance, no tone mapping
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print("baked", out)


if __name__ == "__main__":
    bake(sys.argv[1], sys.argv[2], sys.argv[3],
         json.loads(sys.argv[4]) if len(sys.argv) > 4 else {},
         int(sys.argv[5]) if len(sys.argv) > 5 else 2048)
