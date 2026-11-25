"""Shows the exterior wall faces of the ground storey that border the Wohnzimmer (room segments of the inside face)."""
import json
import os
import sys

ROOT = r"c:\Development\weingaerten"
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["WEINGAERTEN_HOME"] = ROOT
import weingaerten_core  # noqa: E402

house = json.loads(weingaerten_core.handle(json.dumps({"command": "HOUSE"})))
ground = next(s for s in house["storeys"] if s["id"] == "ground")
print([(r["id"], r["name"], r["rect"]) for r in ground["rooms"] if r["name"] == "Wohnzimmer"])
for w in ground["walls"]:
    if w["category"] == "exterior_wall":
        print(w["id"], w["u_range"]["inside"], json.dumps(w["faces"]["inside"].get("rooms") or w["faces"]["inside"], ensure_ascii=False)[:400])
