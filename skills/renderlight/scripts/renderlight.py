"""Renderlight: apply a catalog lighting recipe to the user's OWN Blender scene, without breaking it.

Run inside Blender (Blender MCP "execute code", the Python console, or `blender -b file.blend -P rl_cli.py`):

    exec(open("/path/to/skills/renderlight/scripts/renderlight.py").read())
    rl_apply("luxury_glass_darkfield", {"tone": "gold"}, subject=["Bottle", "Cap"])
    rl_preview("/tmp/rl/preview.png")            # 320 px, 16 samples, user's settings untouched
    rl_preview_choices("luxury_glass_darkfield", "floor", "/tmp/rl/floor")   # one tile per choice
    rl_render("/tmp/rl/final.png", res=1600, samples=256, grade="warm_film")
    rl_remove()                                    # scene is exactly as before

What rl_apply touches, and how rl_remove undoes it:
  * new objects   -> all live in the "RL_Lighting" collection; removed with their data.
  * user's lights -> hidden (tagged RL_hidden), shown again on remove. keep_lights=True leaves them on.
  * world         -> a new "RL_World" is swapped in; the user's world is never edited.
  * camera        -> the user's camera is kept. angle="hero" etc. adds RL_Camera instead.
                     DOF values on the user's camera are saved and restored.
  * render/view   -> engine, samples, bounces, caustics, view transform, look, exposure saved and restored.
Calling rl_apply again first calls rl_remove, so switching recipes/options is always clean.
"""
import bpy, json, math, os, sys, copy
from mathutils import Vector

RL_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else None
PREFIX = "RL_"
KIND = {"rect": "AREA", "spot": "SPOT", "point": "POINT", "sun": "SUN"}
BACKDROP = {"gray": 0.18, "white_glossy": 0.85, "black_glossy": 0.004, "black": 0.008, "white": 0.85,
            "dark_gradient": 0.03, "light_gradient": 0.6}

# settings rl_apply may change; saved before and restored by rl_remove
_SAVED = [
    "render.engine", "cycles.samples", "cycles.preview_samples", "cycles.use_denoising",
    "cycles.max_bounces", "cycles.transmission_bounces", "cycles.glossy_bounces",
    "cycles.caustics_refractive", "cycles.caustics_reflective",
    "view_settings.view_transform", "view_settings.look", "view_settings.exposure",
]
_DOF = ["use_dof", "focus_distance", "aperture_fstop"]


# ---------------------------------------------------------------- catalog
def _catalog_dir():
    for d in [os.environ.get("RENDERLIGHT_CATALOG"), RL_DIR and os.path.join(RL_DIR, "..", "catalog")]:
        if d and os.path.exists(os.path.join(d, "recipes.json")):
            return os.path.abspath(d)
    raise FileNotFoundError("catalog not found: set RENDERLIGHT_CATALOG or RL_DIR to skills/renderlight/scripts")


def rl_catalog():
    d = _catalog_dir()
    recipes = {r["id"]: r for r in json.load(open(os.path.join(d, "recipes.json"), encoding="utf-8"))["recipes"]}
    finishing = {g["id"]: g for g in json.load(open(os.path.join(d, "finishing.json"), encoding="utf-8"))["options"]}
    return recipes, finishing


def _resolve(recipe_id, options):
    d = _catalog_dir()
    if d not in sys.path:
        sys.path.insert(0, d)
    from apply import apply_options, defaults
    recipes, finishing = rl_catalog()
    options = dict(options or {})
    fin = {}
    for gid, g in finishing.items():
        cid = options.pop(gid, None)
        if cid is not None:
            fin[gid] = next(c for c in g["choices"] if c["id"] == cid)
    base = recipes[recipe_id]
    return apply_options(base, {**defaults(base), **options}), fin


# ---------------------------------------------------------------- small helpers
def kelvin_rgb(k):
    t = k / 100.0
    r = 255 if t <= 66 else 329.698727446 * ((t - 60) ** -0.1332047592)
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * ((t - 60) ** -0.0755148492)
    b = 255 if t >= 66 else (0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    c = [min(max(v, 0), 255) / 255 for v in (r, g, b)]
    return tuple(x ** 2.2 for x in c)


def _get(obj, path):
    for p in path.split(".")[:-1]:
        obj = getattr(obj, p)
    return getattr(obj, path.split(".")[-1])


def _set(obj, path, v):
    for p in path.split(".")[:-1]:
        obj = getattr(obj, p)
    setattr(obj, path.split(".")[-1], v)


def _state():
    s = bpy.context.scene.get("RL_state")
    return json.loads(s) if s else None


def _col():
    scn = bpy.context.scene
    col = bpy.data.collections.get(PREFIX + "Lighting")
    if col is None:
        col = bpy.data.collections.new(PREFIX + "Lighting")
    if col.name not in scn.collection.children:
        scn.collection.children.link(col)
    return col


def _bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return lo, hi


def _subject(subject):
    scn = bpy.context.scene
    if subject:
        names = [subject] if isinstance(subject, str) else list(subject)
        objs = [bpy.data.objects[n] for n in names]
    else:
        objs = [o for o in bpy.context.selected_objects if not o.name.startswith(PREFIX)]
    meshes = []
    for o in objs:
        meshes += [o] if o.type == 'MESH' else [c for c in o.children_recursive if c.type == 'MESH']
    if not meshes:
        cands = [o.name for o in scn.objects if o.type == 'MESH' and not o.name.startswith(PREFIX) and o.visible_get()]
        raise ValueError("No subject. Select the product or pass subject=[names]. Visible meshes: " + ", ".join(cands[:40]))
    return meshes


def _dir(ctx, az, el):
    a, e = math.radians(az), math.radians(el)
    h = ctx["f"] * math.cos(a) + ctx["right"] * math.sin(a)
    return (h * math.cos(e) + Vector((0, 0, 1)) * math.sin(e)).normalized()


def _clear_distance(ctx, direction, d, name):
    """Move a light closer if a wall/ceiling/floor of the user's scene is in the way."""
    scn = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    origin, travelled = ctx["center"].copy(), 0.0
    for _ in range(32):
        hit, loc, _n, _i, obj, _m = scn.ray_cast(dg, origin, direction, distance=d - travelled)
        if not hit:
            return d
        travelled += (loc - origin).length + 1e-4
        if obj.name in ctx["subject_names"] or obj.name.startswith(PREFIX) or obj.name in ctx["backdrop_names"]:
            origin = loc + direction * 1e-4
            continue
        new_d = max(travelled * 0.9, ctx["size"] * 0.2)
        ctx["notes"].append(f"{name}: blocked by '{obj.name}', moved closer ({d:.2f} -> {new_d:.2f})")
        return new_d
    return d


def _light(ctx, l):
    s = ctx["size"]
    kind = KIND[l["kind"]]
    d = l.get("dist", 1.5) * s
    direction = _dir(ctx, l["az"], l["el"])
    if kind != 'SUN':
        d = _clear_distance(ctx, direction, d, l["role"])
    data = bpy.data.lights.new(PREFIX + l["role"], kind)
    data.color = tuple(l["color"]) if l.get("color") else kelvin_rgb(l.get("kelvin", 5600))
    size = tuple(l["size"]) if isinstance(l.get("size"), list) else l.get("size", 0.5)
    ratio = l.get("ratio", 1.0)
    if kind == 'SUN':
        data.energy = 3.0 * ratio
        data.angle = math.radians(size)
    else:
        # calibrated: AREA needs 3*pi*d^2 W to match SUN strength 3 on the subject; POINT/SPOT 4x that
        data.energy = 3 * math.pi * ratio * d * d * (4 if kind in ('POINT', 'SPOT') else 1)
        if kind == 'AREA':
            if isinstance(size, tuple):
                data.shape = 'RECTANGLE'
                data.size, data.size_y = size[0] * s, size[1] * s
            else:
                data.size = size * s
            if l.get("spread") is not None:
                data.spread = math.radians(l["spread"])
        else:
            data.shadow_soft_size = size * s
        if kind == 'SPOT':
            data.spot_size = math.radians(l.get("spot_deg", 40))
            data.spot_blend = l.get("blend", 0.15)
    o = bpy.data.objects.new(PREFIX + l["role"], data)
    o.location = ctx["center"] + direction * d
    ctx["col"].objects.link(o)
    con = o.constraints.new('TRACK_TO')
    con.target = ctx["tgt"]
    con.track_axis, con.up_axis = 'TRACK_NEGATIVE_Z', 'UP_Y'
    if l.get("subject_only"):
        o.light_linking.receiver_collection = ctx["subject_col"]
    if l.get("backdrop_only"):
        if ctx["backdrop_col"] is None:
            ctx["notes"].append(f"{l['role']}: backdrop-only light, but there is no backdrop (backdrop='none')")
        o.light_linking.receiver_collection = ctx["backdrop_col"]
    return o


def _mat(name, color, rough, spec=None, coat=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if spec is not None:
        b.inputs["Specular IOR Level"].default_value = spec
    if coat is not None:
        b.inputs["Coat Weight"].default_value = coat
    return m


def _sweep(ctx, kind):
    """Seamless curved backdrop behind and under the subject (48 smooth segments: no stripes in glossy floors)."""
    size, lo = ctx["size"], ctx["lo"]
    S, N = size * 6, 48
    prof = [(-S, 0)] + [(S * 0.3 * math.sin(t / N * math.pi / 2), S * 0.3 * (1 - math.cos(t / N * math.pi / 2)))
                        for t in range(N + 1)] + [(S * 0.3, S)]
    f, r, up = ctx["f"], ctx["right"], Vector((0, 0, 1))
    base = Vector((ctx["center"].x, ctx["center"].y, lo.z))
    verts, faces = [], []
    for i, (y, z) in enumerate(prof):
        for side in (-S, S):
            # y runs away from the camera (-f), x along the camera's right
            verts.append(base + r * side - f * (y + size * 1.2) + up * z)
        if i:
            faces.append((2 * i - 2, 2 * i - 1, 2 * i + 1, 2 * i))
    me = bpy.data.meshes.new(PREFIX + "Sweep")
    me.from_pydata([tuple(v) for v in verts], [], faces)
    for p in me.polygons:
        p.use_smooth = True
    alb = BACKDROP.get(kind, 0.05)
    if kind in ("black_glossy", "white_glossy"):
        m = _mat(PREFIX + "Backdrop", (alb,) * 3, 0.04 if kind == "black_glossy" else 0.08, coat=1.0)  # acrylic
    elif kind == "black":
        m = _mat(PREFIX + "Backdrop", (alb,) * 3, 0.95, spec=0.0)  # truly matte
    else:
        m = _mat(PREFIX + "Backdrop", (alb,) * 3, 0.8)
    me.materials.append(m)
    o = bpy.data.objects.new(PREFIX + "Sweep", me)
    ctx["col"].objects.link(o)
    return o


def _flag(ctx, i, f):
    """Camera-invisible black card: glass edges refract it into a dark outline; also darkens metal logos."""
    me = bpy.data.meshes.new(f"{PREFIX}Flag{i}")
    me.from_pydata([(-.5, -.5, 0), (.5, -.5, 0), (.5, .5, 0), (-.5, .5, 0)], [], [(0, 1, 2, 3)])
    me.materials.append(_mat(f"{PREFIX}Flag", (0, 0, 0), 1.0, spec=0.0))
    o = bpy.data.objects.new(f"{PREFIX}Flag{i}", me)
    s = ctx["size"]
    if f.get("mirror"):
        # where the product's front face reflects the camera: the logo/foil sees this spot,
        # so a black card here makes metallic print read dark from any camera angle
        c = (ctx["cam_pos"] - ctx["center"]).normalized()
        n = ctx["front"]
        d = (2 * c.dot(n) * n - c).normalized()
    else:
        d = _dir(ctx, f["az"], f.get("el", 0))
    o.location = ctx["center"] + d * f.get("dist", 1.0) * s
    w, h = f.get("size", [0.8, 2.0])
    o.scale = (w * s, h * s, 1)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (ctx["center"] - o.location).to_track_quat('Z', 'Y')
    o.visible_camera = False
    o.visible_shadow = False
    ctx["col"].objects.link(o)


def _world(recipe):
    """A fresh RL_World. The camera sees the recipe background; reflections may see a soft studio gradient."""
    w = recipe.get("world", {})
    world = bpy.data.worlds.new(PREFIX + "World")
    try:
        world.use_nodes = True
    except Exception:
        pass
    nt = world.node_tree
    nodes, links = nt.nodes, nt.links
    out = next(n for n in nodes if n.type == 'OUTPUT_WORLD')
    bg = next(n for n in nodes if n.type == 'BACKGROUND')
    bg.inputs["Color"].default_value = (*w.get("color", (1, 1, 1)), 1)
    bg.inputs["Strength"].default_value = w.get("strength", 0.0)
    env = w.get("reflect")
    if env:
        tc = nodes.new("ShaderNodeTexCoord")
        sep = nodes.new("ShaderNodeSeparateXYZ")
        mr = nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.25  # dark near the horizon so glossy floors stay clean
        mr.inputs["From Max"].default_value = 1.0
        ref = nodes.new("ShaderNodeBackground")
        ref.inputs["Strength"].default_value = env.get("strength", 0.6)
        lp = nodes.new("ShaderNodeLightPath")
        mix = nodes.new("ShaderNodeMixShader")
        links.new(tc.outputs["Generated"], sep.inputs[0])
        links.new(sep.outputs["Z"], mr.inputs["Value"])
        links.new(mr.outputs["Result"], ref.inputs["Color"])
        links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
        links.new(ref.outputs[0], mix.inputs[1])
        links.new(bg.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], out.inputs["Surface"])
    return world


def _camera(ctx, spec):
    cd = bpy.data.cameras.new(PREFIX + "Camera")
    cd.lens = spec["lens"]
    cam = bpy.data.objects.new(PREFIX + "Camera", cd)
    r = bpy.context.scene.render
    rx, ry = r.resolution_x * r.pixel_aspect_x, r.resolution_y * r.pixel_aspect_y
    k = min(rx, ry) / max(rx, ry)  # the narrow side of the frame must still fit the product
    dist = ctx["size"] * 2.9 * spec["lens"] / 85 / k
    d = _dir(ctx, -spec["az"], spec["el"])  # positive angle = camera swings to the product's left side
    cam.location = ctx["center"] + d * dist
    cam.rotation_euler = (ctx["center"] - cam.location).to_track_quat('-Z', 'Y').to_euler()
    ctx["col"].objects.link(cam)
    return cam


# ---------------------------------------------------------------- public API
def rl_apply(recipe_id, options=None, subject=None, backdrop="recipe", keep_lights=False, isolate=False, samples=128):
    """Light the user's scene with a recipe.

    options:  the user's answers, e.g. {"floor": "acrylic", "tone": "gold"}. Finishing answers may be
              mixed in: {"angle": "hero", "dof": "soft"} ("grade" is applied by rl_render).
    subject:  object names of the product (default: selected objects). Children of empties are included.
    backdrop: "recipe" = build the recipe's sweep | ["Floor", ...] = use the user's own objects as the
              backdrop (backdrop-only lights hit them; their materials are not changed) | "none".
    isolate:  hide every other visible mesh from the render (restored by rl_remove). Without it,
              meshes the recipe doesn't know about are listed in notes as "also in the shot".
    Returns a summary dict (lights, notes, needs) for the AI to report.
    """
    if _state():
        rl_remove()
    scn = bpy.context.scene
    recipe, fin = _resolve(recipe_id, options)
    meshes = _subject(subject)
    lo, hi = _bounds(meshes)
    center, size = (lo + hi) / 2, max((hi - lo).length, 1e-3)

    state = {"recipe": recipe_id, "options": options or {}, "settings": {}, "world": scn.world.name if scn.world else None,
             "camera": scn.camera.name if scn.camera else None, "dof": None, "hidden": [],
             "subject": sorted(o.name for o in meshes), "backdrop": backdrop,
             "isolate": isolate, "keep_lights": keep_lights}
    for p in _SAVED:
        state["settings"][p] = _get(scn, p) if not isinstance(_get(scn, p), float) else float(_get(scn, p))

    col = _col()
    ctx = {"center": center, "size": size, "lo": lo, "col": col, "notes": [],
           "subject_names": {o.name for o in meshes}, "backdrop_names": set()}

    # camera: keep the user's, unless an angle was chosen (or there is none)
    if "angle" in fin or scn.camera is None:
        f = Vector((0, -1, 0))  # temporary frame to place the new camera
        ctx.update(f=f, right=(-f).cross(Vector((0, 0, 1))).normalized())
        spec = fin["angle"]["camera"] if "angle" in fin else {"az": 0, "el": 4, "lens": 85}
        if scn.camera is not None:
            ref = scn.camera.matrix_world.translation - center
            ref.z = 0
            if ref.length > 1e-6:  # keep the user's viewing side; angle is relative to it
                ctx.update(f=ref.normalized(), right=(-ref.normalized()).cross(Vector((0, 0, 1))).normalized())
        scn.camera = _camera(ctx, spec)
        bpy.context.view_layer.update()  # matrix_world of a new object is stale until the depsgraph updates
    front = ctx.get("f")  # the product's front: the side the angle choice was measured from
    f = scn.camera.matrix_world.translation - center
    f.z = 0
    f = f.normalized() if f.length > 1e-6 else Vector((0, -1, 0))
    ctx.update(f=f, right=(-f).cross(Vector((0, 0, 1))).normalized(),
               front=front or f, cam_pos=scn.camera.matrix_world.translation.copy())

    tgt = bpy.data.objects.new(PREFIX + "Target", None)
    tgt.location = center
    col.objects.link(tgt)
    ctx["tgt"] = tgt

    # who receives what (Cycles light linking)
    sc = bpy.data.collections.new(PREFIX + "SubjectOnly")
    for o in meshes:
        sc.objects.link(o)
    ctx["subject_col"] = sc
    ctx["backdrop_col"] = None
    if backdrop == "recipe":
        sweep = _sweep(ctx, recipe.get("backdrop", "black"))
        bc = bpy.data.collections.new(PREFIX + "BackdropOnly")
        bc.objects.link(sweep)
        ctx["backdrop_col"], ctx["backdrop_names"] = bc, {sweep.name}
    elif isinstance(backdrop, (list, tuple)):
        bc = bpy.data.collections.new(PREFIX + "BackdropOnly")
        for n in backdrop:
            bc.objects.link(bpy.data.objects[n])
        ctx["backdrop_col"], ctx["backdrop_names"] = bc, set(backdrop)
        ctx["notes"].append(f"using your backdrop {list(backdrop)}; the recipe expects '{recipe.get('backdrop')}'")

    # hide the user's own lights (restored by rl_remove)
    if not keep_lights:
        for o in scn.objects:
            if o.type == 'LIGHT' and not o.name.startswith(PREFIX) and not o.hide_render:
                o["RL_hidden"] = [o.hide_render, o.hide_viewport]
                o.hide_render = o.hide_viewport = True
                state["hidden"].append(o.name)

    others = [o for o in scn.objects if o.type == 'MESH' and not o.name.startswith(PREFIX) and not o.hide_render
              and o.name not in ctx["subject_names"] and o.name not in ctx["backdrop_names"]]
    if isolate:
        for o in others:
            o["RL_hidden"] = [o.hide_render, o.hide_viewport]
            o.hide_render = True
            state["hidden"].append(o.name)
    elif others:
        ctx["notes"].append("also in the shot (not part of the recipe): " + ", ".join(o.name for o in others[:20]))

    lights = [_light(ctx, l).name for l in recipe["rig"]]
    for i, fl in enumerate(recipe.get("flags", [])):
        _flag(ctx, i, fl)

    if scn.world is not None:  # keep the user's world alive in the .blend while RL_World is active
        state["world_fake_user"] = scn.world.use_fake_user
        scn.world.use_fake_user = True
    scn.world = _world(recipe)

    # depth of field in "real product photo" terms (f/8-f/16 equivalent), focused on the camera-facing face
    if "dof" in fin and fin["dof"].get("dof"):
        cd = scn.camera.data
        if not scn.camera.name.startswith(PREFIX):
            state["dof"] = {k: getattr(cd.dof, k) for k in _DOF}
        view = (center - scn.camera.matrix_world.translation).normalized()
        half = max(abs(view.x) * (hi.x - lo.x), abs(view.y) * (hi.y - lo.y), abs(view.z) * (hi.z - lo.z)) / 2
        cd.dof.use_dof = True
        cd.dof.focus_distance = (scn.camera.matrix_world.translation - center).length - half
        cd.dof.aperture_fstop = fin["dof"]["dof"]["fstop_rel"] * 0.15 / size

    scn.render.engine = 'CYCLES'
    scn.cycles.samples = samples
    scn.cycles.use_denoising = True
    scn.cycles.max_bounces = max(scn.cycles.max_bounces, 16)
    scn.cycles.transmission_bounces = max(scn.cycles.transmission_bounces, 16)
    scn.cycles.glossy_bounces = max(scn.cycles.glossy_bounces, 8)
    if recipe.get("no_caustics"):
        scn.cycles.caustics_refractive = scn.cycles.caustics_reflective = False
    scn.view_settings.view_transform = 'AgX'
    scn.view_settings.look = 'None'
    scn.view_settings.exposure = recipe.get("exposure") or 0.0

    scn["RL_state"] = json.dumps(state)
    return {"recipe": recipe_id, "lights": lights, "subject": sorted(ctx["subject_names"]),
            "needs": recipe.get("needs"), "notes": ctx["notes"], "checks": recipe.get("checks", [])}


def rl_remove():
    """Undo rl_apply completely."""
    scn = bpy.context.scene
    st = _state()
    col = bpy.data.collections.get(PREFIX + "Lighting")
    if st:
        for p, v in st["settings"].items():
            try:
                _set(scn, p, v)
            except Exception as e:
                print("[RL] could not restore", p, e)
        scn.world = bpy.data.worlds.get(st["world"]) if st["world"] else None
        if scn.world is not None and "world_fake_user" in st:
            scn.world.use_fake_user = st["world_fake_user"]
        if st["camera"] and st["camera"] in bpy.data.objects:
            scn.camera = bpy.data.objects[st["camera"]]
            if st.get("dof"):
                for k, v in st["dof"].items():
                    setattr(scn.camera.data.dof, k, v)
        for n in st["hidden"]:
            o = bpy.data.objects.get(n)
            if o and "RL_hidden" in o:
                o.hide_render, o.hide_viewport = o["RL_hidden"]
                del o["RL_hidden"]
        del scn["RL_state"]
    if col:
        datas = [(o.type, o.data.name) for o in col.all_objects if o.data is not None]
        for n in [o.name for o in col.all_objects]:
            bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
        pools = {'LIGHT': bpy.data.lights, 'MESH': bpy.data.meshes, 'CAMERA': bpy.data.cameras}
        for t, n in datas:
            d = pools.get(t, {}).get(n)
            if d is not None and d.users == 0:
                pools[t].remove(d)
        bpy.data.collections.remove(col)
    for n in (PREFIX + "SubjectOnly", PREFIX + "BackdropOnly"):
        c = bpy.data.collections.get(n)
        if c:
            bpy.data.collections.remove(c)
    for coll in (bpy.data.worlds, bpy.data.materials):
        for d in list(coll):
            if d.name.startswith(PREFIX) and d.users == 0:
                coll.remove(d)


def _render_to(path, res, samples, grade=None):
    scn = bpy.context.scene
    keep = {p: _get(scn, p) for p in ["render.resolution_x", "render.resolution_y", "render.resolution_percentage",
                                      "render.filepath", "cycles.samples", "render.image_settings.file_format"]}
    try:
        if res:
            ax, ay = scn.render.resolution_x, scn.render.resolution_y
            k = res / min(ax, ay)  # res = the short side, so wide frames don't shrink the product
            scn.render.resolution_x, scn.render.resolution_y = max(1, round(ax * k)), max(1, round(ay * k))
        scn.render.resolution_percentage = 100
        scn.cycles.samples = samples
        scn.render.image_settings.file_format = 'PNG'
        scn.render.filepath = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        bpy.ops.render.render(write_still=True)
    finally:
        for p, v in keep.items():
            _set(scn, p, v)
    if grade:
        _, finishing = rl_catalog()
        post = next(c for c in finishing["grade"]["choices"] if c["id"] == grade)["post"]
        if post:
            rl_grade(path, post)
    return path


def rl_preview(path, res=320, samples=16):
    """Fast look (seconds). The user's resolution/samples/output path are restored afterwards."""
    return _render_to(path, res, samples)


def rl_render(path, res=None, samples=None, grade=None):
    """Final render. res=None keeps the scene's resolution. grade: finishing 'grade' choice id."""
    return _render_to(path, res, samples or bpy.context.scene.cycles.samples, grade)


def rl_preview_choices(recipe_id, group, out_dir, base=None, res=320, samples=16, **apply_kw):
    """One preview tile per choice of an option group: out_dir/1.png, 2.png, ... (written as each finishes).
    Show tile 1 to the user as soon as it exists. subject/backdrop/isolate/keep_lights default to the
    current rl_apply call. Leaves the scene lit with `base` (the answers so far)."""
    recipes, finishing = rl_catalog()
    groups = {g["id"]: g for g in recipes[recipe_id].get("options", [])}
    groups.update(finishing)
    g = groups[group]
    st = _state() or {}
    kw = {k: st[k] for k in ("subject", "backdrop", "isolate", "keep_lights") if k in st}
    kw.update(apply_kw)
    if base is None:  # keep the answers already given (angle, tone, ...)
        base = dict(st.get("options") or {}) if st.get("recipe") == recipe_id else {}
    tiles = []
    for i, c in enumerate(g["choices"]):
        opts = {**(base or {}), group: c["id"]}
        grade = opts.pop("grade", None)
        rl_apply(recipe_id, opts, **kw)
        tiles.append(_render_to(os.path.join(out_dir, f"{i + 1}.png"), res, samples, grade))
        print(f"[RL] tile {i + 1}/{len(g['choices'])}: {c['id']}", flush=True)
    rl_apply(recipe_id, {k: v for k, v in (base or {}).items() if k != "grade"}, **kw)
    return [{"n": i + 1, "id": c["id"], "label": c["label"], "file": t} for i, (c, t) in enumerate(zip(g["choices"], tiles))]


# ---------------------------------------------------------------- post (numpy only: runs in Blender's Python)
def _blur(a, r):
    import numpy as np
    r = max(1, int(r))
    for axis in (0, 1):
        for _ in range(3):  # 3 box blurs ~ gaussian
            c = np.cumsum(np.pad(a, [(r + 1, r) if i == axis else (0, 0) for i in range(a.ndim)], mode="edge"), axis=axis)
            a = (np.take(c, range(2 * r + 1, c.shape[axis]), axis=axis) - np.take(c, range(0, c.shape[axis] - 2 * r - 1), axis=axis)) / (2 * r + 1)
    return a


def rl_grade(path, p):
    """Finishing grade on a rendered PNG, in place (bloom, contrast, lift/gain, vignette, sharpen, grain)."""
    import numpy as np
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    a = px.reshape(h, w, 4)[..., :3].copy()  # sRGB-encoded PNG values
    if p.get("bloom"):
        bright = np.clip((a - 0.7) / 0.3, 0, 1) * a
        b = _blur(bright, max(w, h) * 0.02 / 1.7)
        a = 1 - (1 - a) * (1 - b * p["bloom"])
    if p.get("contrast"):
        a = (a - 0.5) * p["contrast"] + 0.5
    if p.get("lift") or p.get("gain"):
        lift = np.array(p.get("lift", [0, 0, 0]), np.float32)
        gain = np.array(p.get("gain", [1, 1, 1]), np.float32)
        a = lift + a * (gain - lift)
    if p.get("vignette"):
        yy, xx = np.mgrid[0:h, 0:w]
        r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / np.sqrt(2)
        a = a * (1 - p["vignette"] * np.clip((r - 0.35) / 0.65, 0, 1) ** 1.6)[..., None]
    if p.get("sharpen"):
        a = a + (a - _blur(a, 1)) * 1.2 * p["sharpen"]
    if p.get("grain"):
        a = a + np.random.default_rng(7).normal(0, p["grain"], (h, w, 1)).astype(np.float32)
    out = px.reshape(h, w, 4)
    out[..., :3] = np.clip(a, 0, 1)
    img.pixels.foreach_set(out.ravel())
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)


def rl_stats(path):
    """Numbers for the recipe's checks: background brightness, clipped %, darkest/brightest (0-255)."""
    import numpy as np
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    lum = (px.reshape(h, w, 4)[::-1, :, :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)) * 255
    return {"top_band_mean": round(float(lum[: h // 8].mean()), 1), "mean": round(float(lum.mean()), 1),
            "clipped_pct": round(float((lum >= 250).mean() * 100), 2), "crushed_pct": round(float((lum <= 3).mean() * 100), 2)}


# ---------------------------------------------------------------- showing previews inside Blender
def _load_px(path):
    import numpy as np
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)


def rl_sheet(files, out, gap=6):
    """Put preview tiles side by side (tile 1 on the left) into one PNG. Numbering is left to right."""
    import numpy as np
    tiles = [_load_px(f) for f in files]
    h = max(t.shape[0] for t in tiles)
    w = sum(t.shape[1] for t in tiles) + gap * (len(tiles) - 1)
    sheet = np.zeros((h, w, 4), np.float32)
    sheet[..., :3], sheet[..., 3] = 0.15, 1.0
    x = 0
    for t in tiles:
        sheet[h - t.shape[0]:, x:x + t.shape[1]] = t  # Blender pixel rows start at the bottom
        x += t.shape[1] + gap
    img = bpy.data.images.new(PREFIX + "sheet", w, h, alpha=True)
    img.pixels.foreach_set(sheet.ravel())
    img.filepath_raw, img.file_format = out, 'PNG'
    img.save()
    bpy.data.images.remove(img)
    return out


def rl_show(path):
    """Open a preview in an Image Editor inside Blender (if the window has one), so the user sees it at once."""
    name = PREFIX + "Preview"
    old = bpy.data.images.get(name)
    if old:
        old.filepath = path
        old.reload()
        img = old
    else:
        img = bpy.data.images.load(path)
        img.name = name
    shown = False
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                area.spaces.active.image = img
                area.tag_redraw()
                shown = True
    return shown
