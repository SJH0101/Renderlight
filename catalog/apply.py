"""Apply a recipe's user-chosen options. Shared by the Blender renderer and (mirrored) the web app.

A choice's `patch` may only use these keys:
  backdrop        "black" | "black_glossy" | "white" | "dark_gradient" | "light_gradient"
  kelvin          color temperature for every light (or {"role": K, ...} per light)
  ratio_scale     multiply every light's brightness
  size_scale      multiply every light's size (bigger = softer)
  exposure        overall exposure in stops
  world_strength  ambient light level
"""
import copy

ALLOWED = {"backdrop", "kelvin", "ratio_scale", "size_scale", "exposure", "world_strength"}


def apply_options(recipe, chosen):
    """chosen: {"floor": "acrylic", "tone": "gold"}. Unknown groups/choices raise."""
    r = copy.deepcopy(recipe)
    groups = {g["id"]: g for g in r.get("options", [])}
    for gid, cid in chosen.items():
        if gid not in groups:
            raise KeyError(f"{r['id']}: no option group '{gid}'. Groups: {list(groups)}")
        choice = next((c for c in groups[gid]["choices"] if c["id"] == cid), None)
        if choice is None:
            raise KeyError(f"{r['id']}.{gid}: no choice '{cid}'. Choices: {[c['id'] for c in groups[gid]['choices']]}")
        patch = choice.get("patch", {})
        bad = set(patch) - ALLOWED
        if bad:
            raise KeyError(f"{r['id']}.{gid}.{cid}: unsupported patch keys {bad}")
        if "backdrop" in patch:
            r["backdrop"] = patch["backdrop"]
        if "exposure" in patch:
            r["exposure"] = patch["exposure"]
        if "world_strength" in patch:
            r.setdefault("world", {})["strength"] = patch["world_strength"]
        for l in r["rig"]:
            if "kelvin" in patch:
                k = patch["kelvin"]
                l["kelvin"] = k.get(l["role"], l.get("kelvin", 5600)) if isinstance(k, dict) else k
                l.pop("color", None) if not isinstance(k, dict) or l["role"] in k else None
            if "ratio_scale" in patch:
                l["ratio"] = l.get("ratio", 1.0) * patch["ratio_scale"]
            if "size_scale" in patch:
                s = l.get("size", 0.5)
                l["size"] = [v * patch["size_scale"] for v in s] if isinstance(s, list) else s * patch["size_scale"]
    return r


def defaults(recipe):
    return {g["id"]: g["default"] for g in recipe.get("options", [])}
