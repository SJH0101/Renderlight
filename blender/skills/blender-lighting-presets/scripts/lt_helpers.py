"""Blender lighting preset helpers (LT_*).

Lights are placed relative to a subject and the active camera, so the same
preset looks the same regardless of scene scale or camera position.

Coordinates
  az   azimuth in degrees. 0 = camera side, +90 = camera right, -90 = camera left, 180 = behind subject
  el   elevation in degrees from subject center. 0 = eye level, 90 = straight above, negative = below
  dist distance as a multiple of the subject's bounding-box diagonal
  size AREA/POINT/SPOT: multiple of the bbox diagonal (AREA accepts (w, h)). SUN: angle in degrees
  ratio brightness relative to the key light (distance falloff and light type are compensated)

Everything is non-destructive: new lights live in an `LT_<preset>` collection,
existing lights are hidden (not deleted), and lt_restore() undoes it all.
"""
import bpy
import math
import random
from mathutils import Vector

__all__ = [
    "kelvin_rgb", "lt_setup", "lt_dir", "lt_light", "lt_world", "lt_volume",
    "lt_gobo", "lt_flicker", "lt_strobe", "lt_pass", "lt_restore",
]


def kelvin_rgb(k):
    """Approximate linear RGB for a color temperature in Kelvin (1000-40000)."""
    t = k / 100.0
    r = 255 if t <= 66 else 329.698727446 * ((t - 60) ** -0.1332047592)
    g = (99.4708025861 * math.log(t) - 161.1195681661 if t <= 66
         else 288.1221695283 * ((t - 60) ** -0.0755148492))
    if t >= 66:
        b = 255
    elif t <= 19:
        b = 0
    else:
        b = 138.5177312231 * math.log(t - 10) - 305.0447927307
    return tuple((min(max(x, 0), 255) / 255) ** 2.2 for x in (r, g, b))


def _subject_bounds(objs):
    pts = []
    for o in objs:
        if o.type == 'MESH' or o.bound_box:
            pts += [o.matrix_world @ Vector(c) for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)])
    hi = Vector([max(p[i] for p in pts) for i in range(3)])
    return (lo + hi) / 2, max((hi - lo).length, 0.1)


def lt_setup(preset, subject=None, hide_existing=True):
    """Start a preset. `subject` is an object name (or list of names); defaults to the active object."""
    scn = bpy.context.scene
    if subject is None:
        objs = [bpy.context.active_object]
    elif isinstance(subject, str):
        objs = [bpy.data.objects[subject]]
    else:
        objs = [bpy.data.objects[n] for n in subject]
    if not objs or objs[0] is None:
        raise ValueError("No subject: pass subject='ObjectName' or select an object")
    # Use child meshes if the subject is an empty/armature root
    meshes = [o for o in objs if o.type == 'MESH']
    for o in objs:
        if o.type != 'MESH':
            meshes += [c for c in o.children_recursive if c.type == 'MESH']
    center, size = _subject_bounds(meshes or objs)

    f = (scn.camera.matrix_world.translation - center) if scn.camera else Vector((0, -1, 0))
    f.z = 0
    f = f.normalized() if f.length > 1e-6 else Vector((0, -1, 0))
    right = (-f).cross(Vector((0, 0, 1))).normalized()

    for c in scn.collection.children:
        if c.name.startswith("LT_"):
            c.hide_render = c.hide_viewport = True
    if hide_existing:
        for o in scn.objects:
            if o.type == 'LIGHT' and not o.name.startswith("LT_") and not o.hide_render:
                o["LT_hidden"] = True
                o.hide_render = True
                o.hide_viewport = True

    col = bpy.data.collections.new("LT_" + preset)
    scn.collection.children.link(col)
    tgt = bpy.data.objects.new("LT_Target", None)
    tgt.location = center
    col.objects.link(tgt)
    return dict(center=center, size=size, f=f, right=right, col=col, tgt=tgt,
                subject_names={o.name for o in (meshes or objs)})


def lt_dir(ctx, az, el):
    a, e = math.radians(az), math.radians(el)
    h = ctx["f"] * math.cos(a) + ctx["right"] * math.sin(a)
    return (h * math.cos(e) + Vector((0, 0, 1)) * math.sin(e)).normalized()


def _clear_distance(ctx, direction, d, name):
    """Shorten d if something other than the subject (floor, wall, ceiling) blocks the path."""
    scn = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    origin, travelled = ctx["center"].copy(), 0.0
    skip = ctx.get("subject_names", set())
    for _ in range(32):
        hit, loc, _n, _i, obj, _m = scn.ray_cast(dg, origin, direction, distance=d - travelled)
        if not hit:
            return d
        travelled += (loc - origin).length + 1e-4
        if obj.name in skip or obj.name.startswith("LT_"):
            origin = loc + direction * 1e-4
            continue
        new_d = max(travelled * 0.9, ctx["size"] * 0.2)
        print(f"[LT] {name}: path blocked by '{obj.name}', moved light closer ({d:.2f} -> {new_d:.2f})")
        return new_d
    return d


def lt_light(ctx, name, kind="AREA", az=45, el=30, dist=1.5, ratio=1.0, kelvin=5600,
             size=0.5, color=None, spot_deg=40, blend=0.15, aim=None, base=3 * math.pi, spread=None):
    """Add one light. Returns the light object.

    ratio=1 gives the same irradiance on the subject as a SUN of strength 3 (calibrated in Cycles).
    """
    s = ctx["size"]
    d = dist * s
    direction = lt_dir(ctx, az, el)
    if kind != 'SUN':
        d = _clear_distance(ctx, direction, d, name)
    data = bpy.data.lights.new("LT_" + name, kind)
    data.color = color or kelvin_rgb(kelvin)
    if kind == 'SUN':
        data.energy = 3.0 * ratio
        data.angle = math.radians(size)
    else:
        # measured: AREA needs 3*pi*d^2 W to match SUN 3; POINT/SPOT need 4x that
        data.energy = base * ratio * d * d * (4 if kind in ('POINT', 'SPOT') else 1)
        if kind == 'AREA':
            if isinstance(size, (tuple, list)):
                data.shape = 'RECTANGLE'
                data.size, data.size_y = size[0] * s, size[1] * s
            else:
                data.size = size * s
            if spread is not None:  # degrees; narrower = less spill (e.g. onto the floor)
                data.spread = math.radians(spread)
        else:
            data.shadow_soft_size = size * s
        if kind == 'SPOT':
            data.spot_size = math.radians(spot_deg)
            data.spot_blend = blend
    o = bpy.data.objects.new("LT_" + name, data)
    o.location = ctx["center"] + direction * d
    ctx["col"].objects.link(o)
    con = o.constraints.new('TRACK_TO')
    con.target = aim or ctx["tgt"]
    con.track_axis, con.up_axis = 'TRACK_NEGATIVE_Z', 'UP_Y'
    return o


def _background_node(world):
    try:
        world.use_nodes = True
    except Exception:
        pass
    nt = world.node_tree
    bg = next((n for n in nt.nodes if n.type == 'BACKGROUND'), None)
    if bg is None:
        out = next((n for n in nt.nodes if n.type == 'OUTPUT_WORLD'), None) or nt.nodes.new("ShaderNodeOutputWorld")
        bg = nt.nodes.new("ShaderNodeBackground")
        nt.links.new(bg.outputs[0], out.inputs["Surface"])
    return bg


def lt_world(strength=0.05, color=(1, 1, 1), kelvin=None, exposure=None):
    """Set world background color/strength and view exposure. Originals are saved for lt_restore()."""
    scn = bpy.context.scene
    w = scn.world or bpy.data.worlds.new("World")
    scn.world = w
    bg = _background_node(w)
    if "LT_orig" not in w:
        w["LT_orig"] = [bg.inputs[1].default_value, *bg.inputs[0].default_value]
    if not bg.inputs[0].is_linked:  # leave an HDRI alone, only change strength
        bg.inputs[0].default_value = (*(kelvin_rgb(kelvin) if kelvin else color), 1)
    bg.inputs[1].default_value = strength
    if exposure is not None:
        if "LT_orig_exposure" not in scn:
            scn["LT_orig_exposure"] = scn.view_settings.exposure
        scn.view_settings.exposure = exposure


def lt_volume(ctx, density=0.03, anisotropy=0.3, color=(1, 1, 1)):
    """Fog box around subject and camera (for visible light beams)."""
    scn = bpy.context.scene
    s = ctx["size"] * 8
    if scn.camera:
        s = max(s, 2.2 * (scn.camera.matrix_world.translation - ctx["center"]).length)
    me = bpy.data.meshes.new("LT_VolumeMesh")
    v = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    me.from_pydata(v, [], [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
                           (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    o = bpy.data.objects.new("LT_Volume", me)
    o.location, o.scale = ctx["center"], (s / 2,) * 3
    ctx["col"].objects.link(o)
    m = bpy.data.materials.new("LT_Volume")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = density
    pv.inputs["Anisotropy"].default_value = anisotropy
    pv.inputs["Color"].default_value = (*color, 1)
    nt.links.new(pv.outputs["Volume"], out.inputs["Volume"])
    me.materials.append(m)
    return o


def lt_gobo(ctx, light, mode="blinds", n=14, open_frac=0.5, t=0.7, seed=0):
    """Camera-invisible cutout between `light` and subject. mode: 'blinds' or 'dapple'."""
    bpy.context.view_layer.update()
    lpos = light.matrix_world.translation.copy()
    p = lpos.lerp(ctx["center"], t)
    parent = bpy.data.objects.new("LT_Gobo", None)
    parent.location = p
    parent.rotation_mode = 'QUATERNION'
    parent.rotation_quaternion = (lpos - p).to_track_quat('Z', 'Y')
    ctx["col"].objects.link(parent)
    w, rng = ctx["size"] * 2.0, random.Random(seed)
    pitch = w / n
    verts, faces = [], []

    def quad(cx, cy, hx, hy):
        i = len(verts)
        verts.extend([(cx - hx, cy - hy, 0), (cx + hx, cy - hy, 0),
                      (cx + hx, cy + hy, 0), (cx - hx, cy + hy, 0)])
        faces.append((i, i + 1, i + 2, i + 3))

    if mode == "blinds":
        for k in range(n):
            quad(0, -w / 2 + (k + 0.5) * pitch, w / 2, pitch * (1 - open_frac) / 2)
    else:
        for i in range(n):
            for j in range(n):
                if rng.random() > open_frac:
                    quad(-w / 2 + (i + 0.5 + rng.uniform(-.3, .3)) * pitch,
                         -w / 2 + (j + 0.5 + rng.uniform(-.3, .3)) * pitch,
                         pitch * rng.uniform(.4, .9), pitch * rng.uniform(.4, .9))
    me = bpy.data.meshes.new("LT_GoboMesh")
    me.from_pydata(verts, [], faces)
    o = bpy.data.objects.new("LT_GoboShape", me)
    o.parent = parent
    ctx["col"].objects.link(o)
    o.visible_camera = False
    return parent


def _drive_energy(light, expr):
    fc = light.data.driver_add("energy")
    fc.driver.type = 'SCRIPTED'
    fc.driver.expression = expr
    return fc


def lt_flicker(light, amount=0.3, speed=1.0):
    """Organic flicker (fire, screens). Uses a simple driver expression, no auto-run scripts needed."""
    e = light.data.energy
    return _drive_energy(light, (
        f"{e:.4f}*(1+{amount}*(0.5*sin(frame*{1.7 * speed:.4f})"
        f"+0.3*sin(frame*{4.3 * speed:.4f}+1)+0.2*sin(frame*{9.1 * speed:.4f}+2)))"))


def lt_strobe(light, period=6, on=1):
    """On for `on` frames out of every `period` frames."""
    e = light.data.energy
    return _drive_energy(light, (
        f"{e:.4f}*(cos(frame*{2 * math.pi / period:.6f})>{math.cos(math.pi * on / period):.6f})"))


def lt_pass(ctx, light, start=1, end=48, span=3.0):
    """Freeze aim, then slide the light sideways so its beam sweeps across the subject."""
    base = light.location.copy()
    light.rotation_euler = (ctx["center"] - base).to_track_quat('-Z', 'Y').to_euler()
    light.constraints.clear()
    r = ctx["right"] * span * ctx["size"]
    light.location = base - r
    light.keyframe_insert("location", frame=start)
    light.location = base + r
    light.keyframe_insert("location", frame=end)


def lt_restore():
    """Hide all LT_ collections and bring back the original lights, world and exposure."""
    scn = bpy.context.scene
    for c in scn.collection.children:
        if c.name.startswith("LT_"):
            c.hide_render = c.hide_viewport = True
    for o in scn.objects:
        if o.get("LT_hidden"):
            o.hide_render = o.hide_viewport = False
            del o["LT_hidden"]
    w = scn.world
    if w and "LT_orig" in w:
        bg = _background_node(w)
        st, *col = w["LT_orig"]
        bg.inputs[1].default_value = st
        if not bg.inputs[0].is_linked:
            bg.inputs[0].default_value = col
        del w["LT_orig"]
    if "LT_orig_exposure" in scn:
        scn.view_settings.exposure = scn["LT_orig_exposure"]
        del scn["LT_orig_exposure"]
