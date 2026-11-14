# Lighting catalog

- `recipes.json`: lighting recipes. Each one has a look, a light rig, checks, things to avoid, and **options**: questions the user answers.
- `materials.json`: how each material shows itself (glass by its edges, metal by what it reflects).
- `search.py`: find recipes for a request (`python3 catalog/search.py "luxury perfume"`).
- `apply.py`: apply the user's chosen options to a recipe. A choice may only change these keys: `backdrop`, `kelvin`, `ratio_scale`, `size_scale`, `exposure`, `world_strength`.

## How the AI uses options

Never pick an option for the user. For each option group, ask the group's `ask` question with its choices: as a multiple-choice question where the client has one, otherwise as a numbered list. Show a preview sheet when you can render:

```bash
python3 tools/render_options.py luxury_glass_darkfield public/models/perfume.glb tone sheet.png
python3 tools/render_recipe.py luxury_glass_darkfield public/models/perfume.glb out.png 960 128 '{"tone":"gold","floor":"acrylic"}'
```

Unanswered groups use their `default`. Recipes marked `verified` have been rendered and checked; treat the others as drafts.
