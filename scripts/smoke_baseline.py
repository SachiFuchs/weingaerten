# Runs smoke_core.py on a temp copy of the data with only the four sample openings (user-added openings removed).
import json, os, shutil, subprocess, sys, tempfile
SRC = r"c:\Development\weingaerten"
SAMPLE = {"o-door", "o-small", "o-win1", "o-win2"}
tmp = tempfile.mkdtemp()
for d in ("catalog", "house"):
    shutil.copytree(os.path.join(SRC, d), os.path.join(tmp, d))
p = os.path.join(tmp, "house", "storeys", "ground.json")
st = json.load(open(p, encoding="utf-8"))
for w in st["walls"]:
    w["openings"] = [o for o in w.get("openings", []) if o["id"] in SAMPLE]
json.dump(st, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
env = dict(os.environ, WEINGAERTEN_SMOKE_HOME=tmp)
r = subprocess.run([sys.executable, os.path.join(SRC, "scripts", "smoke_core.py")], env=env)
shutil.rmtree(tmp)
sys.exit(r.returncode)
