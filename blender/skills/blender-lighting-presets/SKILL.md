---
name: blender-lighting-presets
description: Blender에서 하이키·렘브란트·골든아워·네온 등 34가지 이름 있는 조명 셋업을 피사체·카메라 기준으로 만들거나 조합·조정할 때 사용. Build, stack, and tune 34 named cinematic lighting setups (Rembrandt, golden hour, neon, venetian blinds...) in Blender.
---

# Blender Lighting Presets (34)

Builds named lighting setups in Blender **relative to the subject and the active camera**, so a preset looks the same at any scene scale or camera position. Needs a Blender connection that can run Python (e.g. a Blender MCP server with an `execute_blender_code`-style tool).

## Workflow

1. **Inspect the scene**: list meshes, camera, existing lights, render engine.
2. **Pick the subject**: the mesh the light should be built around (head mesh for portraits, body for full shots). If it's ambiguous (floors and walls make the bounding box useless), ask. For `broad`/`short`, also find out which way the face is turned relative to the camera (`face_turn=+1` toward camera-right, `-1` toward camera-left).
3. **Load the helpers** into Blender once per session. Read `scripts/lt_helpers.py` and `scripts/lt_presets.py` from this skill folder and store them as Blender Text datablocks:
   ```python
   import bpy
   for name, src in (("lt_helpers.py", HELPERS_SRC), ("lt_presets.py", PRESETS_SRC)):
       t = bpy.data.texts.get(name) or bpy.data.texts.new(name)
       t.clear(); t.write(src)
   ```
   Start every later call with:
   ```python
   import bpy
   exec(bpy.data.texts["lt_helpers.py"].as_string(), globals())
   exec(bpy.data.texts["lt_presets.py"].as_string(), globals())
   ```
4. **Let the user choose** (see *Asking the user* below) unless they already named a preset.
5. **Apply**:
   ```python
   apply_preset("rembrandt", subject="Head")
   apply_preset(["rembrandt", "golden_hour", "rim"], subject="Head")  # stack
   apply_preset("렘브란트", subject="Head")                            # Korean name or number ("03") works too
   ```
6. **Look at it**: render a viewport/thumbnail and check the checkpoint in the table below. The values are starting points. Tune with `bpy.data.objects["LT_Key"]` (energy, size, location) or rebuild with custom `lt_light(...)` calls. Never say it's done without looking.
7. **Report** briefly: what was built and what knobs to turn, then offer one follow-up choice (e.g. "add a rim light?", "warmer or cooler?").

Non-destructive by design: new lights go in an `LT_<preset>` collection, existing lights are hidden (not deleted), the previous `LT_` collection is hidden, and the original world color and exposure are saved. `lt_restore()` brings the original scene back. Delete `LT_` collections only if the user asks.

## Asking the user

Lighting is taste. Don't pick for the user. Offer choices and let them decide. Skip the questions only when they already named a preset ("Rembrandt", "03", "골든아워") or told you to just pick.

**How to ask**: if your environment has a multiple-choice question tool (e.g. `AskUserQuestion` in Claude), use it, with 2–4 options per question, the preset name as the label and its one-liner as the description. Otherwise (ChatGPT, other agents) ask in plain text as a short numbered list and accept a number or a name. Always say they can type any of the 34 names instead. Ask in the user's language (`choices(..., lang="ko"|"en")`).

**Which questions**: get the labels and one-liners from `choices()` in `lt_presets.py`, either by running it in Blender or by reading `GROUPS`, `INFO` and `MOODS` straight from the file. Don't invent descriptions.
1. **They described a mood** ("무서운 느낌", "cyberpunk", "warm and nostalgic"): `choices(mood=text)` returns 4 matching presets. Ask one question. If nothing matches, fall back to 2.
2. **They gave no direction** ("조명 잡아줘"): ask two steps. First the group, from `choices()`: 인물 정석 / 자연광·시간대 / 무드·대비 / 컬러·효과. Then the preset: take `choices(group, limit=10)` and offer the 4 most fitting in that group for the scene (a product shot → soft/flat over split).
3. **Add-ons (optional, one question, multi-select)**: after the main pick, offer things that stack: rim light, volumetric haze, venetian blinds, or "none". Skip it if the user seems to want speed.

**Show, don't describe (recommended when Blender can render)**: after narrowing to 2–4 candidates, run `lt_preview([...], subject=...)`. It renders a small image of each candidate, then restores the scene and leaves nothing behind. Show the images side by side and ask which one. Use low res and samples so it takes seconds. Skip it on slow machines or when the user wants to move fast.

Example (Claude, mood given):
> Q: 어떤 조명으로 할까? — 언더 라이트 (아래에서, 공포·괴담 느낌) / 탑 라이트 (머리 위에서, 눈이 그늘져 미스터리) / 키아로스쿠로 (극단적 명암) / 로우키 (대부분 어둡고 한쪽만 빛)

Example (plain text, no direction):
> 어떤 쪽 느낌이 좋아?
> 1. 인물 정석 (렘브란트, 루프, 버터플라이…)
> 2. 자연광·시간대 (골든아워, 창가빛, 달빛…)
> 3. 무드·대비 (로우키, 실루엣, 스포트라이트…)
> 4. 컬러·효과 (네온, 틸앤오렌지, 블라인드, 안개…)
> 번호나 조명 이름으로 답해줘. 34개 중 아무거나 직접 말해도 돼.

## Engine notes

- **Cycles** is recommended for gobos (blinds, dappled), volumetrics and bounce.
- On **EEVEE**, turn on Raytracing, Volumetrics and soft shadows, or those presets will look weak.
- AgX view transform. Adjust overall brightness with `scene.view_settings.exposure` before touching light energy.
- `ratio=1` on any light ≈ irradiance of a SUN at strength 3 (calibrated in Cycles).
- `lt_light` raycasts from the subject; if a floor or wall blocks the path, it moves the light closer and prints `[LT] ... moved light closer`. Mention that to the user if it happens.

## Building custom setups

`lt_light(ctx, name, kind, az, el, dist, ratio, kelvin, size, color, spot_deg, blend, aim)`
- `az`: 0 = camera side, +90 = camera right, −90 = camera left, 180 = behind the subject
- `el`: elevation from subject center (0 = eye level, 90 = overhead, negative = below)
- `dist`, `size`: multiples of the subject bbox diagonal. AREA `size` may be `(w, h)`. For SUN, `size` is the angle in degrees
- Extras: `lt_world`, `lt_volume`, `lt_gobo(mode="blinds"|"dapple")`, `lt_flicker`, `lt_strobe`, `lt_pass`

```python
ctx = lt_setup("custom", subject="Head")
lt_light(ctx, "Key", az=50, el=35, ratio=1.0, size=0.4, kelvin=4300)
lt_light(ctx, "Rim", az=-150, el=30, ratio=1.5, size=0.2, color=(0.3, 0.6, 1.0))
lt_world(strength=0.01)
```

## Presets and what to check

| # | id | 이름 | Check in the render |
|---|---|---|---|
| 01 | `high_key` | 하이키 | Bright, low contrast, almost no dark areas |
| 02 | `low_key` | 로우키 | Mostly dark, one-sided key, rim separates from background |
| 03 | `rembrandt` | 렘브란트 | Small lit triangle on the shadow-side cheek. If missing, raise az to 50–60 or el to 45 |
| 04 | `butterfly` | 버터플라이 | Butterfly-shaped shadow under the nose, symmetric |
| 05 | `split` | 스플릿 | Face divided exactly in half |
| 06 | `loop` | 루프 | Small nose shadow toward the cheek, not touching the lip line |
| 07 | `broad` | 브로드 | Key lights the wide side of the face (the side facing the camera). Needs `face_turn` |
| 08 | `short` | 숏 | Key lights the narrow side (turned away from camera), slimming. Needs `face_turn` |
| 09 | `chiaroscuro` | 키아로스쿠로 | Extreme light/dark split, black background |
| 10 | `silhouette` | 실루엣 | Subject pure black against a glowing background |
| 11 | `rim` | 림 라이트 | Bright edges outlining the subject. Usually stacked |
| 12 | `hard` | 하드 라이트 | Razor-sharp shadow edges |
| 13 | `soft` | 소프트 라이트 | Wide, gradual shadow falloff |
| 14 | `bounce` | 바운스 | Light arrives from an invisible white card. Cycles |
| 15 | `top` | 탑 라이트 | Dark eye sockets, light from straight above |
| 16 | `under` | 언더 라이트 | Lit from below, horror look |
| 17 | `golden_hour` | 골든 아워 | Low, warm, long shadows |
| 18 | `blue_hour` | 블루 아워 | Soft cool ambient, no direct sun |
| 19 | `day_for_night` | 데이 포 나이트 | Crisp daylight shadows, but blue and underexposed |
| 20 | `moonlight` | 문라이트 | Cool side light on a dark scene |
| 21 | `window` | 윈도우 라이트 | Large soft rectangular side source |
| 22 | `practical` | 프랙티컬 | Lamps visible in frame light the scene. Pass `practicals=["LampObj"]` |
| 23 | `firelight` | 파이어라이트 | Low, very warm, flickering (animated) |
| 24 | `venetian_blinds` | 베니션 블라인드 | Hard parallel stripes across the subject |
| 25 | `dappled` | 대플드 | Irregular leaf-shadow patches |
| 26 | `volumetric` | 볼류메트릭 | Visible light beam in haze. Needs backlight |
| 27 | `flat` | 플랫 라이트 | Almost shadowless, even |
| 28 | `neon` | 네온 | Saturated pink/cyan from two sides, dark scene |
| 29 | `teal_orange` | 틸 앤 오렌지 | Warm skin key against cool teal shadows |
| 30 | `mono_red` | 모노크롬 레드 | Everything red |
| 31 | `screen_glow` | 스크린 글로우 | Cool glow from below-front, slight flicker |
| 32 | `passing` | 패싱 라이트 | Light patch sweeps across the subject (frames 1–48) |
| 33 | `strobe` | 스트로브 | On 1 frame of every 6 (animated) |
| 34 | `theatrical` | 시어트리컬 라이트 | Narrow hard spotlight from above-front, circular pool on the floor |

## Stacking

`apply_preset([...])` sorts presets into **pattern → mood/time/color → direction → effects**. When a mood preset (golden hour, teal & orange, moonlight...) is stacked on a key pattern, it **recolors the existing key** instead of adding a competing one: geometry comes from the pattern, color and world from the mood. Effects (blinds, volumetric, flicker...) are added on top.

## Gotchas

- If the subject is an Empty or armature root, its child meshes are used automatically. Still prefer naming the actual mesh.
- If the world uses an HDRI (texture linked into Background color), `lt_world` changes only its strength. Ask before disabling an HDRI.
- Animated presets (`firelight`, `screen_glow`, `strobe`, `passing`) use simple driver expressions or keyframes, so they work without enabling Python auto-run.
