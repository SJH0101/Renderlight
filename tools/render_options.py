"""Fast previews of one question's choices, so the user can pick by eye.

    python3 tools/render_options.py <recipe_id> <model.glb> <group> <out_dir> [base_choices_json]

Works for recipe option groups (floor, tone, ...) and finishing groups (angle, dof, grade).
Renders in one Blender process at preview quality (320 px, 16 samples + denoise; ~1-2 s each on a GPU)
and writes each tile the moment it's done: out_dir/1.png, 2.png, ... plus out_dir/sheet.png updated after
every tile. Show tile 1 immediately; don't wait for the whole sheet.
"""
import sys, os, json, time
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from render_recipe import render  # noqa: E402

RES, SAMPLES = 320, 16


def choices_for(rid, group):
    recipe = next(r for r in json.load(open(os.path.join(ROOT, "skills/renderlight/catalog/recipes.json")))["recipes"] if r["id"] == rid)
    for g in recipe.get("options", []) + json.load(open(os.path.join(ROOT, "skills/renderlight/catalog/finishing.json")))["options"]:
        if g["id"] == group:
            return g
    raise KeyError(f"{rid}: no question '{group}'")


def font(size=18):
    for f in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/System/Library/Fonts/AppleSDGothicNeo.ttc",
              "C:/Windows/Fonts/malgun.ttf"]:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def main():
    rid, model, group, out_dir = sys.argv[1:5]
    base = json.loads(sys.argv[5]) if len(sys.argv) > 5 else {}
    os.makedirs(out_dir, exist_ok=True)
    g = choices_for(rid, group)
    n, L, f = len(g["choices"]), 34, font()
    sheet = Image.new("RGB", (RES * n, RES + L), (38, 38, 38))
    d = ImageDraw.Draw(sheet)
    t0 = time.time()
    for i, c in enumerate(g["choices"]):
        tile = os.path.join(out_dir, f"{i + 1}.png")
        render(rid, model, tile, RES, SAMPLES, {**base, group: c["id"]})
        sheet.paste(Image.open(tile).convert("RGB"), (i * RES, 0))
        d.text((i * RES + 10, RES + 7), f"{i + 1}. {c['label']['ko']}", fill=(235, 235, 235), font=f)
        sheet.save(os.path.join(out_dir, "sheet.png"))
        print(f"tile {i + 1}/{n} ready ({c['id']}) at {time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
