#!/usr/bin/env python3
"""Find lighting recipes for a request.

    python3 catalog/search.py "고급 향수 광고"
    python3 catalog/search.py "chrome watch, dark and luxurious" -n 2 --json
"""
import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).parent


def load():
    recipes = json.loads((HERE / "recipes.json").read_text(encoding="utf-8"))["recipes"]
    materials = json.loads((HERE / "materials.json").read_text(encoding="utf-8"))["materials"]
    return recipes, materials


def score(recipe, query):
    q = query.lower()
    tokens = set(re.findall(r"[\w가-힣]+", q))
    s = 0.0
    for kw in recipe["keywords"]:
        k = kw.lower()
        if k in tokens:
            s += 2.0
        elif k in q:
            s += 1.5  # substring, e.g. Korean particles: "향수를"
    for m in recipe.get("mood", []):
        if m in q:
            s += 1.0
    return s


def search(query, n=3):
    recipes, materials = load()
    ranked = sorted(((score(r, query), r) for r in recipes), key=lambda x: -x[0])
    hits = [r for s, r in ranked if s > 0][:n]
    for r in hits:
        r["material_notes"] = {m: materials[m] for m in r.get("materials", []) if m in materials}
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("-n", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    hits = search(a.query, a.n)
    if a.json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
        return
    if not hits:
        print("맞는 레시피가 없음. 가장 가까운 장르를 사용자에게 물어볼 것.")
        return
    for r in hits:
        print(f"■ {r['name']['ko']}  ({r['id']})")
        print(f"  모습: {r['look']}")
        for l in r["rig"]:
            print(f"  - {l['role']}: {l['kind']} az {l['az']} el {l['el']} ratio {l['ratio']}")
        print(f"  확인: {' / '.join(r['checks'])}")
        print(f"  금지: {' / '.join(r['avoid'])}")
        for m, note in r["material_notes"].items():
            print(f"  [{note['ko']}] {note['show_by']}")
        print()


if __name__ == "__main__":
    main()
