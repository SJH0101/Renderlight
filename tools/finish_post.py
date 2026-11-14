"""Post-processing for finishing grades (works on any rendered PNG; the web app mirrors these steps).

    python3 tools/finish_post.py in.png out.png '{"contrast":1.1,"vignette":0.25}'
"""
import sys, json
import numpy as np
from PIL import Image, ImageFilter


def apply_post(img, p):
    if not p:
        return img
    a = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
    h, w, _ = a.shape
    if p.get("bloom"):
        bright = np.clip((a - 0.7) / 0.3, 0, 1) * a
        b = Image.fromarray((bright * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(w, h) * 0.02))
        a = 1 - (1 - a) * (1 - np.asarray(b).astype(np.float32) / 255.0 * p["bloom"])  # screen blend
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
    a = np.clip(a, 0, 1)
    out = Image.fromarray((a * 255).astype(np.uint8))
    if p.get("sharpen"):
        out = out.filter(ImageFilter.UnsharpMask(radius=1.4, percent=int(120 * p["sharpen"]), threshold=2))
    if p.get("grain"):
        rng = np.random.default_rng(7)
        g = np.asarray(out).astype(np.float32) / 255.0 + rng.normal(0, p["grain"], (h, w, 1)).astype(np.float32)
        out = Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8))
    return out


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    params = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    apply_post(Image.open(src), params).save(dst)
