---
name: renderlight
description: Light a product in the user's own Blender scene from a plain-language intent ("luxury perfume ad", "clean skincare shot"). Picks a verified studio recipe, asks the user each choice with instant Cycles preview tiles, then renders. Use for Blender product/still-life lighting requests.
---

# Renderlight

The user says what the shot should feel like. You pick a recipe, set it up in their Blender, and ask them
the recipe's questions, each with preview tiles. You never choose an option for them, and you never ask
them for a number (angles, watts, Kelvin). The recipes hold the numbers; the user judges the pictures.

The users are designers who know lighting. Speak to them as peers: name the technique ("dark-field",
"bright-field", "acrylic floor"), skip basics, and take their correction seriously when they say a
preview is wrong.

## Files

- `catalog/recipes.json`: recipes. Each has `look` (what the result must look like), `rig`, `checks`
  (measurable), `avoid`, `needs` (what the model must have), and `options` (the questions).
- `catalog/finishing.json`: questions every shot gets: `angle`, `dof`, `grade`.
- `catalog/materials.json`: how each material reads (glass by its edges, metal by what it reflects).
- `catalog/search.py`: `python3 catalog/search.py "고급 향수 광고"` ranks recipes for a request.
- `scripts/renderlight.py`: runs inside Blender. `rl_apply`, `rl_preview_choices`, `rl_sheet`, `rl_show`,
  `rl_render`, `rl_stats`, `rl_remove`. Read its docstring once.
- `scripts/make_install.py`: prints one snippet that installs the above into the user's Blender.
- `scripts/rl_cli.py`: the same thing headless on a `.blend` copy, when there is no live Blender connection.

## Connecting to Blender

1. **Live Blender (preferred).** A Blender MCP tool that runs Python (e.g. `execute_blender_code`).
   - If the skill folder is on the same computer as Blender, run
     `import sys; sys.path.insert(0, "<skill>/scripts"); import renderlight as rl`.
   - Otherwise run `python3 scripts/make_install.py` where you are, and send its whole output as the code
     once per session. It writes into Blender's user scripts folder. After that, every call starts with
     `import renderlight as rl`.
2. **Headless.** `blender -b their.blend -P scripts/rl_cli.py -- '<json>'` (see the script's docstring).
   It saves to a new `.blend`; never overwrite the user's file.
3. Neither available: say so, and say which one would let you do it.

## Workflow

1. **Read the scene.** List meshes, lights, camera, world, and selection. Find the product:
   - If it is selected, use the selection.
   - If not, propose the objects you think are the product by name, and confirm.
   - Note any floor, walls, props, or the user's own lights.
2. **Pick the recipe.** Run `search.py` with the user's words. Say which recipe you picked in one line,
   using its `look`.
   - If two recipes fit, ask, for example "dark-field or bright-field?". Show one preview of each.
   - Read the recipe's `needs`. If the model fails it, say so before lighting. For example, bright-field
     needs thick, rounded glass; a solid square block will not get outlines.
3. **Ask about the scene once.** These answers become `rl_apply` arguments:
   - **Backdrop.** The recipe sweep (`backdrop="recipe"`), or their own floor/wall
     (`backdrop=["Floor", ...]`). Their own backdrop keeps its material; the recipe's backdrop lights now
     hit it.
   - **Other objects.** If notes list "also in the shot", ask whether to hide them (`isolate=True`).
   - **Camera.** Keep theirs (default), or a recipe angle (the `angle` question).
4. **Apply:** `rl.rl_apply(recipe_id, answers, subject=[...], backdrop=..., isolate=...)`.
   - Report any `notes` it returns. For example, a light that was moved closer because a wall blocked it.
5. **Ask each question with previews.** Ask the recipe's option groups in order, then `angle`, `dof`, and
   `grade`. For each group:
   - Render the tiles:
     `tiles = rl.rl_preview_choices(recipe_id, group, out_dir)`
     (320 px short side, 16 samples + denoise, Cycles). It keeps the answers given so far.
   - Make the sheet and show it in Blender:
     `rl.rl_sheet([t["file"] for t in tiles], sheet)` then `rl.rl_show(sheet)`. `rl_show` puts it in
     any open Image Editor.
   - If the client can display images, show the sheet in the chat too.
   - Ask the group's `ask` with the choices numbered left to right as in the sheet. Use a
     multiple-choice question where the client has one.
   - Previews must come fast. Show tile 1 as soon as it exists if rendering is slow. Never switch
     previews to EEVEE.
6. **Final render:** `rl.rl_render(path, res=..., samples=..., grade=answers["grade"])`.
   - Measure with `rl.rl_stats(path)` and compare to the recipe's `checks`.
   - If a check fails, say which one and what you changed. Don't silently ship a failed check.
7. **Undo:** `rl.rl_remove()` restores everything: the user's world, camera and DOF, lights,
   visibility, and render and view settings. Applying again (another recipe or different answers) does
   this first automatically.

## What makes these look right

These are the reasons recipes look like product photography rather than "3D render". Keep them when you
adjust anything:

- **Light by what the material shows.** Glass shows its edges, so outline it (dark-field: bright edges on
  black; bright-field: dark edges on white) and never light its face. Metal shows what it reflects, so
  give it large shapes to reflect: the recipe's reflection-only gradient (`world.reflect`) lights
  reflections without lighting the background.
- **Scope every light.**
  - `subject_only` lights must not spill on the floor.
  - `backdrop_only` lights must not touch the product.
  - Black flags are invisible to the camera. Glass edges refract them into outlines.
  - The `mirror` flag sits where the front face reflects the camera, so metal print stays readable
    from any angle.
- **The floor is a choice.**
  - Matte black has zero specular, so it can't glow.
  - Acrylic is a clean mirror.
  - Glass casts weak shadows, so a "shadow" answer usually means a glossy floor reflection.
- **Previews and finals are Cycles.** Glass and metal are wrong in EEVEE.

## Tells to avoid

These read as an untrained or AI-made render:

- Even, frontal fill on everything.
- Several random highlights.
- A bright blob in the middle of a glass body.
- Light leaking onto the floor.
- A visible light shape seen through glass.
- Gray "white" products (raise exposure).
- A faceted, striped sweep.
- Stacked warmth. A gold `tone` plus the `warm_film` grade goes orange; say so when the user picks both.
- DOF that blurs the label.

## Limits

- **Scene scale.** Recipes scale to the product's bounding box. Huge scene scales still work, but say so
  if the product is tiny next to its surroundings.
- **Your own lights.** The user's lights are hidden while a recipe is applied. Pass `keep_lights=True`
  only if they ask.
- **Emissive objects.** Emissive meshes in the scene still emit. Mention them if you see them.
- **Missing recipe.** If no recipe fits the request, say that the catalog has nothing for it rather than
  improvising a rig as if it were verified.
