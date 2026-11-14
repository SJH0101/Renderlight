"""Render every choice of one option group side by side, so the user can pick by eye.

    python3 tools/render_options.py <recipe_id> <model.glb> <group> <out.png> [res] [samples]
"""
import sys, os, json, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rid, model, group, out = sys.argv[1:5]
res = int(sys.argv[5]) if len(sys.argv) > 5 else 320
samples = sys.argv[6] if len(sys.argv) > 6 else "64"
recipe = next(r for r in json.load(open(os.path.join(ROOT, "catalog/recipes.json")))["recipes"] if r["id"] == rid)
g = next(x for x in recipe["options"] if x["id"] == group)
tiles = []
with tempfile.TemporaryDirectory() as tmp:
    for c in g["choices"]:
        p = os.path.join(tmp, c["id"] + ".png")
        subprocess.run([sys.executable, os.path.join(ROOT, "tools/render_recipe.py"), rid, model, p, str(res), samples,
                        json.dumps({group: c["id"]})], check=True, capture_output=True)
        tiles.append((c, Image.open(p).convert("RGB")))
    font = None
    for f in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"]:
        if os.path.exists(f): font = ImageFont.truetype(f, 18); break
    font = font or ImageFont.load_default()
    L = 34
    sheet = Image.new("RGB", (res * len(tiles), res + L), (38, 38, 38))
    d = ImageDraw.Draw(sheet)
    for i, (c, im) in enumerate(tiles):
        sheet.paste(im, (i * res, 0))
        d.text((i * res + 10, res + 7), f"{i + 1}. {c['label']['ko']}", fill=(235, 235, 235), font=font)
    sheet.save(out)
print("wrote", out)
