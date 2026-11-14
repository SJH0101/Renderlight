"""Run Renderlight on a .blend from the command line (when no live Blender connection is available).

    blender -b scene.blend -P rl_cli.py -- '{"recipe": "luxury_glass_darkfield",
        "options": {"tone": "gold"}, "subject": ["Bottle"], "isolate": true,
        "choices": {"group": "floor", "out_dir": "/tmp/rl/floor"},
        "preview": "/tmp/rl/p.png", "render": {"path": "/tmp/rl/final.png", "res": 1600, "samples": 256, "grade": "warm_film"},
        "save": "scene_lit.blend"}'

Every key except "recipe" is optional. The original .blend is never overwritten: "save" must be a new path.
Prints one JSON line starting with RL_RESULT for the AI to read.
"""
import bpy, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ns = {"__file__": os.path.join(HERE, "renderlight.py"), "__name__": "renderlight"}
exec(open(ns["__file__"], encoding="utf-8").read(), ns)

args = json.loads(sys.argv[sys.argv.index("--") + 1])
out = {}
kw = {k: args[k] for k in ("subject", "backdrop", "isolate", "keep_lights") if k in args}
out["apply"] = ns["rl_apply"](args["recipe"], args.get("options"), **kw)
if "choices" in args:
    c = args["choices"]
    out["tiles"] = ns["rl_preview_choices"](args["recipe"], c["group"], c["out_dir"], base=args.get("options"))
if "preview" in args:
    out["preview"] = ns["rl_preview"](args["preview"])
    out["preview_stats"] = ns["rl_stats"](args["preview"])
if "render" in args:
    r = args["render"]
    out["render"] = ns["rl_render"](r["path"], r.get("res"), r.get("samples"), r.get("grade"))
    out["render_stats"] = ns["rl_stats"](r["path"])
if "save" in args:
    dst = os.path.abspath(args["save"])
    if bpy.data.filepath and os.path.abspath(bpy.data.filepath) == dst:
        raise SystemExit("refusing to overwrite the original .blend; pass a new path in 'save'")
    bpy.ops.wm.save_as_mainfile(filepath=dst, copy=True)
    out["saved"] = dst
print("RL_RESULT " + json.dumps(out, ensure_ascii=False, default=str))
