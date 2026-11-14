"""34 named lighting presets built on lt_helpers.

Usage inside Blender (after lt_helpers is loaded into the same namespace):
    apply_preset("rembrandt", subject="Head")
    apply_preset(["rembrandt", "golden_hour", "rim"], subject="Head")   # stacked

Each preset is a function (ctx) -> None. Values are starting points; render and tune.
"""
import bpy
import math

try:  # when exec'd after lt_helpers in the same namespace, the names already exist
    lt_light  # noqa: B018
except NameError:
    from lt_helpers import *  # noqa: F401,F403


def _key_light(ctx):
    return bpy.data.objects.get(ctx.get("key_name", ""))


# ---------- A. Face key patterns ----------
def p_rembrandt(ctx):
    k = lt_light(ctx, "Key", az=45, el=40, ratio=1.0, size=0.5)
    lt_light(ctx, "Fill", az=-45, el=10, ratio=0.15, size=1.0)
    lt_world(strength=0.02)
    return k


def p_butterfly(ctx):
    k = lt_light(ctx, "Key", az=0, el=50, dist=1.3, ratio=1.0, size=0.5)
    lt_light(ctx, "Reflector", az=0, el=-25, dist=1.0, ratio=0.25, size=0.8)
    lt_world(strength=0.02)
    return k


def p_split(ctx):
    k = lt_light(ctx, "Key", az=90, el=5, dist=1.3, ratio=1.0, size=0.4)
    lt_world(strength=0.005)
    return k


def p_loop(ctx):
    k = lt_light(ctx, "Key", az=35, el=30, ratio=1.0, size=0.5)
    lt_light(ctx, "Fill", az=-40, el=5, ratio=0.25, size=1.0)
    lt_world(strength=0.02)
    return k


def _face_side(ctx):
    # +1 if the face is turned toward camera-right, -1 toward camera-left.
    return ctx.get("face_turn", 1)


def p_broad(ctx):
    s = -_face_side(ctx)  # key on the side the face is turned AWAY from
    k = lt_light(ctx, "Key", az=45 * s, el=30, ratio=1.0, size=0.5)
    lt_light(ctx, "Fill", az=-45 * s, el=10, ratio=0.2, size=1.0)
    lt_world(strength=0.02)
    return k


def p_short(ctx):
    s = _face_side(ctx)  # key on the side the face is turned TOWARD
    k = lt_light(ctx, "Key", az=45 * s, el=30, ratio=1.0, size=0.5)
    lt_light(ctx, "Fill", az=-45 * s, el=10, ratio=0.15, size=1.0)
    lt_world(strength=0.02)
    return k


# ---------- B. Contrast / mood ----------
def p_high_key(ctx):
    k = lt_light(ctx, "Key", az=20, el=25, ratio=1.0, size=1.0)
    lt_light(ctx, "Fill", az=-40, el=10, ratio=0.7, size=1.2)
    lt_world(strength=1.0, color=(1, 1, 1), exposure=0.5)
    return k


def p_low_key(ctx):
    k = lt_light(ctx, "Key", az=50, el=35, ratio=1.0, size=0.4, kelvin=4500)
    lt_light(ctx, "Rim", az=150, el=25, ratio=0.6, size=0.3)
    lt_world(strength=0.002)
    return k


def p_chiaroscuro(ctx):
    k = lt_light(ctx, "Key", kind="SPOT", az=70, el=25, dist=2, ratio=1.5, size=0.1,
                 spot_deg=35, blend=0.3, kelvin=3800)
    lt_world(strength=0.0)
    return k


def p_silhouette(ctx):
    # glowing card behind the subject, nothing in front
    s = ctx["size"]
    me = bpy.data.meshes.new("LT_BackGlowMesh")
    me.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)])
    o = bpy.data.objects.new("LT_BackGlow", me)
    o.location = ctx["center"] + lt_dir(ctx, 180, 0) * s * 1.2
    o.scale = (s * 1.5, s * 1.5, 1)
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (ctx["center"] - o.location).to_track_quat('Z', 'Y')
    ctx["col"].objects.link(o)
    m = bpy.data.materials.new("LT_BackGlow")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 8.0
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    me.materials.append(m)
    lt_world(strength=0.0)
    return None


def p_flat(ctx):
    k = lt_light(ctx, "Key", az=0, el=10, dist=1.2, ratio=1.0, size=2.0)
    lt_light(ctx, "FillR", az=60, el=10, dist=1.2, ratio=0.8, size=2.0)
    lt_light(ctx, "FillL", az=-60, el=10, dist=1.2, ratio=0.8, size=2.0)
    lt_world(strength=0.5, color=(0.5, 0.5, 0.5))
    return k


# ---------- C. Quality ----------
def p_hard(ctx):
    k = lt_light(ctx, "Key", az=40, el=35, dist=2.5, ratio=1.0, size=0.03)
    lt_world(strength=0.02)
    return k


def p_soft(ctx):
    k = lt_light(ctx, "Key", az=40, el=30, dist=1.0, ratio=1.0, size=1.5)
    lt_light(ctx, "Fill", az=-50, el=10, dist=1.0, ratio=0.4, size=1.5)
    lt_world(strength=0.05)
    return k


def p_bounce(ctx):
    s = ctx["size"]
    me = bpy.data.meshes.new("LT_BounceCardMesh")
    me.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)])
    card = bpy.data.objects.new("LT_BounceCard", me)
    card.location = ctx["center"] + lt_dir(ctx, -60, 20) * s * 1.2
    card.scale = (s * 0.6, s * 0.6, 1)
    card.rotation_mode = 'QUATERNION'
    card.rotation_quaternion = (ctx["center"] - card.location).to_track_quat('Z', 'Y')
    ctx["col"].objects.link(card)
    card.visible_camera = False
    k = lt_light(ctx, "Key", az=60, el=60, ratio=2.0, size=0.5, aim=card)
    lt_world(strength=0.02)
    return k


# ---------- D. Direction ----------
def p_rim(ctx):
    k = lt_light(ctx, "RimR", az=140, el=25, dist=1.2, ratio=1.2, size=0.3)
    lt_light(ctx, "RimL", az=-140, el=25, dist=1.2, ratio=1.2, size=0.3)
    return k


def p_top(ctx):
    k = lt_light(ctx, "Key", az=0, el=85, dist=1.2, ratio=1.2, size=0.5)
    lt_world(strength=0.005)
    return k


def p_under(ctx):
    k = lt_light(ctx, "Key", az=0, el=-45, dist=1.0, ratio=1.0, size=0.3)
    lt_world(strength=0.005)
    return k


# ---------- E. Time of day / natural ----------
def p_golden_hour(ctx):
    k = lt_light(ctx, "Sun", kind="SUN", az=60, el=6, ratio=1.2, size=2.0, kelvin=3000)
    lt_world(strength=0.3, kelvin=4500)
    return k


def p_blue_hour(ctx):
    k = lt_light(ctx, "Fill", az=0, el=30, ratio=0.2, size=2.0, kelvin=10000)
    lt_world(strength=0.5, kelvin=12000, exposure=-0.5)
    return k


def p_day_for_night(ctx):
    k = lt_light(ctx, "Sun", kind="SUN", az=60, el=35, ratio=1.0, size=0.5, kelvin=9000)
    lt_world(strength=0.1, kelvin=12000, exposure=-0.8)
    return k


def p_moonlight(ctx):
    k = lt_light(ctx, "Moon", kind="SUN", az=100, el=40, ratio=1.0, size=0.5, kelvin=7500)
    lt_world(strength=0.15, color=(0.02, 0.03, 0.08))
    return k


def p_window(ctx):
    k = lt_light(ctx, "Window", az=80, el=20, ratio=1.2, size=(1.2, 1.6), kelvin=6000)
    lt_light(ctx, "Fill", az=-60, el=10, ratio=0.15, size=1.0)
    lt_world(strength=0.05)
    return k


def p_dappled(ctx):
    k = lt_light(ctx, "Sun", kind="SUN", az=40, el=55, ratio=1.5, size=0.5, kelvin=5200)
    lt_gobo(ctx, k, mode="dapple", n=14, open_frac=0.55)
    lt_world(strength=0.1, kelvin=6500)
    return k


def p_firelight(ctx):
    k = lt_light(ctx, "Fire", kind="POINT", az=30, el=-20, dist=1.0, ratio=1.0, size=0.15, kelvin=1900)
    lt_flicker(k, amount=0.35)
    lt_world(strength=0.003)
    return k


# ---------- F. Color ----------
def p_neon(ctx):
    k = lt_light(ctx, "NeonPink", az=70, el=10, ratio=2.0, size=(0.05, 1.0), color=(1, 0.05, 0.6))
    lt_light(ctx, "NeonCyan", az=-70, el=10, ratio=2.0, size=(0.05, 1.0), color=(0, 0.8, 1))
    lt_world(strength=0.01, color=(0.02, 0.02, 0.08))
    return k


def p_teal_orange(ctx):
    k = lt_light(ctx, "Key", az=40, el=25, ratio=1.0, size=0.5, kelvin=3000)
    lt_light(ctx, "Teal", az=-120, el=20, ratio=0.6, size=0.5, color=(0, 0.5, 0.55))
    lt_world(strength=0.5, color=(0, 0.08, 0.1))
    return k


def p_mono_red(ctx):
    k = lt_light(ctx, "Key", az=45, el=30, ratio=1.2, size=0.5, color=(1, 0.02, 0.02))
    lt_world(strength=0.3, color=(0.05, 0, 0))
    return k


# ---------- G. Practical / effects ----------
def p_practical(ctx, lamp_names=()):
    """Pass lamp object names via ctx['practicals']; a light is placed at each."""
    names = list(lamp_names) or ctx.get("practicals", [])
    if not names:
        raise ValueError("practical: set ctx['practicals'] = ['LampObj', ...] (light sources must be in frame)")
    k = None
    for n in names:
        src = bpy.data.objects[n]
        src.visible_shadow = False  # the lamp body must not block its own bulb
        data = bpy.data.lights.new("LT_Practical_" + n, 'POINT')
        data.color = kelvin_rgb(2700)
        data.shadow_soft_size = 0.05 * ctx["size"]
        d = (src.matrix_world.translation - ctx["center"]).length
        data.energy = 3 * math.pi * 0.5 * d * d * 4
        o = bpy.data.objects.new("LT_Practical_" + n, data)
        o.location = src.matrix_world.translation
        ctx["col"].objects.link(o)
        k = k or o
    lt_world(strength=0.01)
    return k


def p_venetian_blinds(ctx):
    k = lt_light(ctx, "Sun", kind="SUN", az=70, el=25, ratio=1.5, size=0.3, kelvin=5000)
    lt_gobo(ctx, k, mode="blinds", n=14, open_frac=0.5)
    lt_world(strength=0.03)
    return k


def p_volumetric(ctx):
    lt_volume(ctx, density=0.05)
    k = lt_light(ctx, "Back", kind="SPOT", az=160, el=40, ratio=3.0, size=0.05, spot_deg=30)
    lt_world(strength=0.0)
    return k


def p_screen_glow(ctx):
    k = lt_light(ctx, "Screen", az=0, el=-10, dist=0.5, ratio=0.6, size=(0.4, 0.25), color=(0.6, 0.75, 1))
    lt_flicker(k, amount=0.08, speed=0.5)
    lt_world(strength=0.003)
    return k


def p_passing(ctx):
    k = lt_light(ctx, "Pass", kind="SPOT", az=60, el=15, dist=2, ratio=2.0, size=0.05, spot_deg=25, kelvin=4000)
    lt_pass(ctx, k, start=1, end=48)
    lt_world(strength=0.01)
    return k


def p_strobe(ctx):
    k = lt_light(ctx, "Strobe", az=30, el=20, ratio=3.0, size=0.5, kelvin=6500)
    lt_strobe(k, period=6, on=1)
    lt_world(strength=0.0)
    return k


def p_theatrical(ctx):
    k = lt_light(ctx, "Spot", kind="SPOT", az=15, el=55, dist=2.5, ratio=3.0, size=0.05,
                 spot_deg=22, blend=0.08, kelvin=3200)
    lt_world(strength=0.0)
    return k


PRESETS = {
    # id: (number, Korean, function)
    "high_key":        (1,  "하이키", p_high_key),
    "low_key":         (2,  "로우키", p_low_key),
    "rembrandt":       (3,  "렘브란트", p_rembrandt),
    "butterfly":       (4,  "버터플라이", p_butterfly),
    "split":           (5,  "스플릿", p_split),
    "loop":            (6,  "루프", p_loop),
    "broad":           (7,  "브로드", p_broad),
    "short":           (8,  "숏", p_short),
    "chiaroscuro":     (9,  "키아로스쿠로", p_chiaroscuro),
    "silhouette":      (10, "실루엣", p_silhouette),
    "rim":             (11, "림 라이트", p_rim),
    "hard":            (12, "하드 라이트", p_hard),
    "soft":            (13, "소프트 라이트", p_soft),
    "bounce":          (14, "바운스", p_bounce),
    "top":             (15, "탑 라이트", p_top),
    "under":           (16, "언더 라이트", p_under),
    "golden_hour":     (17, "골든 아워", p_golden_hour),
    "blue_hour":       (18, "블루 아워", p_blue_hour),
    "day_for_night":   (19, "데이 포 나이트", p_day_for_night),
    "moonlight":       (20, "문라이트", p_moonlight),
    "window":          (21, "윈도우 라이트", p_window),
    "practical":       (22, "프랙티컬", p_practical),
    "firelight":       (23, "파이어라이트", p_firelight),
    "venetian_blinds": (24, "베니션 블라인드", p_venetian_blinds),
    "dappled":         (25, "대플드", p_dappled),
    "volumetric":      (26, "볼류메트릭", p_volumetric),
    "flat":            (27, "플랫 라이트", p_flat),
    "neon":            (28, "네온", p_neon),
    "teal_orange":     (29, "틸 앤 오렌지", p_teal_orange),
    "mono_red":        (30, "모노크롬 레드", p_mono_red),
    "screen_glow":     (31, "스크린 글로우", p_screen_glow),
    "passing":         (32, "패싱 라이트", p_passing),
    "strobe":          (33, "스트로브", p_strobe),
    "theatrical":      (34, "시어트리컬 라이트", p_theatrical),
}

# Stacking order: pattern -> mood/time/color -> direction -> effects
_STAGE = {
    **{k: 0 for k in ("rembrandt", "butterfly", "split", "loop", "broad", "short",
                      "hard", "soft", "bounce", "flat")},
    **{k: 1 for k in ("high_key", "low_key", "chiaroscuro", "silhouette", "golden_hour",
                      "blue_hour", "day_for_night", "moonlight", "window", "neon",
                      "teal_orange", "mono_red", "theatrical", "top", "under")},
    **{k: 2 for k in ("rim",)},
    **{k: 3 for k in ("practical", "firelight", "venetian_blinds", "dappled",
                      "volumetric", "screen_glow", "passing", "strobe")},
}


def _resolve(name):
    key = str(name).strip().lower().replace(" ", "_").replace("-", "_").replace("&", "")
    if key in PRESETS:
        return key
    for k, (num, ko, _) in PRESETS.items():
        if key in (str(num), f"{num:02d}") or str(name).replace(" ", "") == ko.replace(" ", ""):
            return k
    raise KeyError(f"Unknown preset: {name}. Options: {', '.join(PRESETS)}")


def apply_preset(names, subject=None, face_turn=1, practicals=(), hide_existing=True):
    """Build one preset or a stack of them in a single LT_ collection.

    names: id ('rembrandt'), number (3 / '03'), Korean name ('렘브란트'), or a list of these.
    face_turn: +1 if the subject's face is turned toward camera-right, -1 toward camera-left (broad/short).
    """
    if isinstance(names, (str, int)):
        names = [names]
    keys = sorted((_resolve(n) for n in names), key=lambda k: _STAGE.get(k, 1))
    ctx = lt_setup("+".join(f"{PRESETS[k][0]:02d}" for k in keys), subject, hide_existing)
    ctx["face_turn"] = face_turn
    ctx["practicals"] = list(practicals)
    key_light = None
    for i, k in enumerate(keys):
        fn = PRESETS[k][2]
        if i > 0 and key_light is not None and _STAGE.get(k) == 1 and k in _RECOLOR:
            _RECOLOR[k](ctx, key_light)   # keep the pattern's geometry, change mood
        else:
            out = fn(ctx)
            key_light = key_light or out
    return ctx


# When a mood preset is stacked on a key pattern, recolor/reshape the existing key
# instead of adding a second competing key light.
def _recolor(kelvin=None, color=None, world=None, ratio=None):
    def f(ctx, key):
        if color or kelvin:
            key.data.color = color or kelvin_rgb(kelvin)
        if ratio:
            key.data.energy *= ratio
        if world:
            lt_world(**world)
    return f


_RECOLOR = {
    "golden_hour":   _recolor(kelvin=3000, world=dict(strength=0.3, kelvin=4500)),
    "blue_hour":     _recolor(kelvin=10000, ratio=0.4, world=dict(strength=0.5, kelvin=12000, exposure=-0.5)),
    "day_for_night": _recolor(kelvin=9000, ratio=0.6, world=dict(strength=0.1, kelvin=12000, exposure=-0.8)),
    "moonlight":     _recolor(kelvin=7500, ratio=0.4, world=dict(strength=0.15, color=(0.02, 0.03, 0.08))),
    "teal_orange":   _recolor(kelvin=3000, world=dict(strength=0.5, color=(0, 0.08, 0.1))),
    "mono_red":      _recolor(color=(1, 0.02, 0.02), world=dict(strength=0.3, color=(0.05, 0, 0))),
    "low_key":       _recolor(world=dict(strength=0.002)),
    "high_key":      _recolor(world=dict(strength=1.0, color=(1, 1, 1), exposure=0.5)),
}


# ---------- Choice support: lets an AI ask the user instead of guessing ----------
# group -> preset ids. Used to build a 2-step question: group, then 3-4 presets.
GROUPS = {
    "portrait": ("인물 정석", "Classic portrait",
                 ["rembrandt", "loop", "butterfly", "split", "broad", "short", "soft", "hard", "flat", "bounce"]),
    "natural":  ("자연광·시간대", "Natural light / time of day",
                 ["golden_hour", "window", "blue_hour", "moonlight", "day_for_night", "dappled", "firelight"]),
    "mood":     ("무드·대비", "Mood / contrast",
                 ["low_key", "chiaroscuro", "high_key", "silhouette", "rim", "top", "under", "theatrical"]),
    "color_fx": ("컬러·효과", "Color / effects",
                 ["neon", "teal_orange", "venetian_blinds", "volumetric", "mono_red", "screen_glow",
                  "practical", "passing", "strobe"]),
}

# id -> (Korean one-liner, English one-liner) shown as option descriptions
INFO = {
    "high_key": ("밝고 그림자 거의 없음, 깨끗한 광고 느낌", "Bright, nearly shadowless, clean commercial look"),
    "low_key": ("대부분 어둡고 한쪽만 빛, 진지한 분위기", "Mostly dark, one-sided light, serious mood"),
    "rembrandt": ("그늘진 뺨에 빛 삼각형, 고전 초상화", "Lit triangle on the shadow cheek, painterly portrait"),
    "butterfly": ("정면 위에서, 코 밑 나비 그림자, 뷰티샷", "High front light, butterfly nose shadow, beauty shot"),
    "split": ("얼굴 절반만 빛, 강렬·이중성", "Half the face lit, intense and dual"),
    "loop": ("가장 무난한 인물 조명, 자연스러운 입체감", "Safest portrait pattern, natural depth"),
    "broad": ("카메라 쪽 넓은 면을 밝힘, 얼굴이 넓어 보임", "Lights the wide side, face looks fuller"),
    "short": ("안쪽 좁은 면을 밝힘, 얼굴이 갸름해 보임", "Lights the narrow side, slimming"),
    "chiaroscuro": ("극단적 명암, 카라바조 그림 같은", "Extreme light/dark, Caravaggio-like"),
    "silhouette": ("밝은 배경에 피사체는 검은 실루엣", "Black subject against a glowing background"),
    "rim": ("윤곽선만 빛나게, 배경과 분리 (추가용)", "Glowing outline, separates from background (add-on)"),
    "hard": ("칼같이 선명한 그림자, 한낮·강렬", "Razor-sharp shadows, midday, punchy"),
    "soft": ("부드럽게 번지는 그림자, 편안함", "Gentle wrap-around shadows, calm"),
    "bounce": ("벽·반사판에 튕긴 은은한 빛", "Light bounced off a card, subtle"),
    "top": ("머리 위에서, 눈이 그늘져 미스터리", "From above, shadowed eyes, mysterious"),
    "under": ("아래에서, 공포·괴담 느낌", "From below, horror"),
    "golden_hour": ("해질녘 낮고 따뜻한 빛, 감성", "Low warm sunset light, nostalgic"),
    "blue_hour": ("해 진 직후 푸르고 고요함", "Cool calm just after sunset"),
    "day_for_night": ("선명한 그림자인데 푸르고 어두운 밤", "Daylight shadows graded to blue night"),
    "moonlight": ("차가운 달빛, 어두운 밤 장면", "Cold moonlight, dark night scene"),
    "window": ("창가의 큰 부드러운 옆빛, 일상·감성", "Big soft window side light, everyday mood"),
    "practical": ("화면 속 스탠드·전구가 실제 광원", "In-frame lamps are the light source"),
    "firelight": ("모닥불·촛불, 따뜻하게 일렁임 (애니)", "Campfire/candle, warm flicker (animated)"),
    "venetian_blinds": ("블라인드 줄무늬 그림자, 누아르", "Blind-stripe shadows, noir"),
    "dappled": ("나뭇잎 사이로 얼룩진 햇빛", "Sunlight through leaves"),
    "volumetric": ("안개 속 빛줄기, 신비·영화적", "Light beams in haze, cinematic"),
    "flat": ("그림자 없이 균일, 증명사진·제품", "Even and shadowless, ID photo/product"),
    "neon": ("핑크·시안 네온, 사이버펑크", "Pink/cyan neon, cyberpunk"),
    "teal_orange": ("따뜻한 피부 vs 청록 그림자, 할리우드", "Warm skin vs teal shadows, blockbuster"),
    "mono_red": ("전부 빨간빛, 긴장·위험", "All red, tension/danger"),
    "screen_glow": ("모니터·폰 화면 불빛, 밤샘 작업", "Monitor/phone glow, late night"),
    "passing": ("빛이 지나가며 훑음, 차 안·밤길 (애니)", "Light sweeps past, car/night street (animated)"),
    "strobe": ("번쩍번쩍 점멸, 클럽·긴박함 (애니)", "Flashing, club/urgency (animated)"),
    "theatrical": ("무대 스포트라이트, 바닥에 원형 빛", "Stage spotlight, circular pool on floor"),
}

# free-form mood words -> 3-4 candidate presets to offer
MOODS = {
    "horror|공포|무서운|괴담": ["under", "top", "chiaroscuro", "low_key"],
    "warm|감성|따뜻|노스탤지어|nostalgic": ["golden_hour", "window", "firelight", "practical"],
    "cyberpunk|사이버펑크|네온|미래": ["neon", "teal_orange", "screen_glow", "volumetric"],
    "noir|누아르|탐정|범죄": ["venetian_blinds", "chiaroscuro", "low_key", "top"],
    "product|제품|광고|commercial": ["soft", "high_key", "rim", "flat"],
    "dreamy|몽환|꿈|신비": ["volumetric", "high_key", "dappled", "blue_hour"],
    "cinematic|영화|시네마틱|blockbuster": ["teal_orange", "rembrandt", "volumetric", "rim"],
    "night|밤|야경": ["moonlight", "blue_hour", "day_for_night", "practical"],
    "stage|무대|공연|concert|클럽|club": ["theatrical", "strobe", "rim", "neon"],
    "clean|깔끔|증명|profile|프로필": ["flat", "butterfly", "loop", "high_key"],
    "portrait|인물|초상": ["rembrandt", "loop", "butterfly", "short"],
    "dramatic|드라마틱|강렬|intense": ["chiaroscuro", "split", "low_key", "hard"],
}


def choices(group=None, mood=None, lang="ko", limit=4):
    """Return [(id, label, description)] for building a multiple-choice question.

    group: key of GROUPS, or None for the 4 groups themselves.
    mood: free text; matched against MOODS keywords.
    """
    i = 0 if lang == "ko" else 1
    if mood:
        text = mood.lower()
        for keys, ids in MOODS.items():
            if any(k in text for k in keys.split("|")):
                return [(k, PRESETS[k][1] if i == 0 else k, INFO[k][i]) for k in ids[:limit]]
        return []
    if group is None:
        return [(g, v[i], ", ".join(PRESETS[k][1] if i == 0 else k for k in v[2][:4]))
                for g, v in GROUPS.items()]
    return [(k, PRESETS[k][1] if i == 0 else k, INFO[k][i]) for k in GROUPS[group][2][:limit]]


def _remove_collection(col):
    lights = {o.data for o in col.objects if o.type == 'LIGHT'}
    for o in list(col.all_objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(col)
    for d in lights:
        if d.users == 0:
            bpy.data.lights.remove(d)


def lt_preview(candidates, subject=None, out_dir="//lt_preview", res=320, samples=24, **kw):
    """Render each candidate preset to a small image so the user can compare and pick.

    Restores the scene and render settings afterwards. Returns {id: filepath}.
    """
    import os
    scn = bpy.context.scene
    r = scn.render
    saved = (r.resolution_x, r.resolution_y, r.resolution_percentage, r.filepath,
             r.image_settings.file_format)
    cyc = getattr(scn, "cycles", None)
    saved_samples = cyc.samples if cyc and r.engine == 'CYCLES' else None
    out = bpy.path.abspath(out_dir)
    os.makedirs(out, exist_ok=True)
    aspect = saved[1] / saved[0]
    paths = {}
    try:
        r.resolution_x, r.resolution_y, r.resolution_percentage = res, max(int(res * aspect), 1), 100
        r.image_settings.file_format = 'PNG'
        if saved_samples is not None:
            cyc.samples = samples
        for name in candidates:
            key = _resolve(name)
            ctx = apply_preset(key, subject=subject, **kw)
            r.filepath = os.path.join(out, f"{PRESETS[key][0]:02d}_{key}.png")
            bpy.ops.render.render(write_still=True)
            paths[key] = r.filepath
            lt_restore()
            _remove_collection(ctx["col"])  # previews leave nothing behind
    finally:
        r.resolution_x, r.resolution_y, r.resolution_percentage, r.filepath, r.image_settings.file_format = saved
        if saved_samples is not None:
            cyc.samples = saved_samples
    return paths
