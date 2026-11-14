"""Render a catalog recipe on a test model (test harness: starts from an EMPTY scene every call).

    python3 tools/render_recipe.py <recipe_id> <model.glb> <out.png> [res] [samples] ['{"floor":"acrylic"}']
The lighting itself is done by skills/renderlight/scripts/renderlight.py, the same code the skill runs
inside the user's own scene.
"""
import sys, os, json
import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RL = os.path.join(ROOT, "skills/renderlight/scripts/renderlight.py")
ns = {"__file__": RL, "__name__": "renderlight"}
exec(open(RL).read(), ns)


def render(rid, model, out, RES=480, SAMPLES=128, extra=None):
    extra = dict(extra or {})
    grade = extra.pop("grade", None)
    _, finishing = ns["rl_catalog"]()
    extra.setdefault("angle", finishing["angle"]["default"])
    extra.setdefault("dof", finishing["dof"]["default"])
    grade = grade or finishing["grade"]["default"]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=model)
    meshes = [o.name for o in bpy.context.scene.objects if o.type == 'MESH']
    sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = RES
    info = ns["rl_apply"](rid, extra, subject=meshes, samples=SAMPLES)
    for n in info["notes"]:
        print("[RL]", n)
    ns["rl_render"](out, grade=None if grade == "none" else grade)
    print("rendered", out)


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], sys.argv[3],
           int(sys.argv[4]) if len(sys.argv) > 4 else 480,
           int(sys.argv[5]) if len(sys.argv) > 5 else 128,
           json.loads(sys.argv[6]) if len(sys.argv) > 6 else {})
