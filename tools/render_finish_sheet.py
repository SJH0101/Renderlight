"""One sheet per finishing question: python3 tools/render_finish_sheet.py <recipe> <model> <group> <out> [res] [samples] [base_choices_json]"""
import sys, os, json, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rid, model, group, out = sys.argv[1:5]
res = int(sys.argv[5]) if len(sys.argv) > 5 else 320
samples = sys.argv[6] if len(sys.argv) > 6 else "64"
base = json.loads(sys.argv[7]) if len(sys.argv) > 7 else {}
g = next(x for x in json.load(open(os.path.join(ROOT, "catalog/finishing.json")))["options"] if x["id"] == group)
font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 18)
tiles = []
with tempfile.TemporaryDirectory() as tmp:
    for c in g["choices"]:
        p = os.path.join(tmp, c["id"] + ".png")
        subprocess.run([sys.executable, os.path.join(ROOT, "tools/render_recipe.py"), rid, model, p, str(res), samples,
                        json.dumps({**base, group: c["id"]})], check=True, capture_output=True)
        tiles.append((c, Image.open(p).convert("RGB")))
L = 34
sheet = Image.new("RGB", (res * len(tiles), res + L), (38, 38, 38)); d = ImageDraw.Draw(sheet)
for i, (c, im) in enumerate(tiles):
    sheet.paste(im, (i * res, 0)); d.text((i * res + 10, res + 7), f"{i+1}. {c['label']['ko']}", fill=(235, 235, 235), font=font)
sheet.save(out); print("wrote", out)
