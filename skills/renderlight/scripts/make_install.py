"""Print ONE Python snippet that installs Renderlight into the user's Blender.

    python3 make_install.py > /tmp/rl_install.py   # then send the file's text to Blender's "execute code" tool

Use this when the skill files are not on the same computer as Blender (e.g. the AI runs in a cloud sandbox).
The snippet writes scripts + catalog into Blender's user scripts folder (renderlight/) and imports it.
Afterwards every call can start with:  import renderlight as rl
"""
import base64, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
files = {}
for sub, names in (("scripts", ["renderlight.py"]), ("catalog", ["recipes.json", "finishing.json", "materials.json", "apply.py"])):
    for n in names:
        files[f"{sub}/{n}"] = base64.b64encode(open(os.path.join(SKILL, sub, n), "rb").read()).decode()
print(f'''import base64, os, sys, importlib, bpy
FILES = {json.dumps(files)}
root = os.path.join(bpy.utils.user_resource('SCRIPTS', path='renderlight', create=True))
for rel, b in FILES.items():
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(base64.b64decode(b))
d = os.path.join(root, 'scripts')
if d not in sys.path: sys.path.insert(0, d)
import renderlight; importlib.reload(renderlight)
result = {{"installed": root, "recipes": sorted(renderlight.rl_catalog()[0])}}''')
