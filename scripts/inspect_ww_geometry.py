"""Read-only: print wall, ceiling, floor and foundation geometry relevant for the waste water runs."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ.setdefault("WEINGAERTEN_HOME", ROOT)
from weingaerten_core.command_handler import handle  # noqa: E402

house = json.loads(handle(json.dumps({"command": "HOUSE"})))
f = house.get("foundation") or {}
print("foundation top", f.get("top"), "thick", f.get("thickness"), "rect", f.get("rect"),
      [(l["material"], l["z0"], l["z1"]) for l in f.get("layers", [])])
for s in house["storeys"]:
    print("== storey", s["id"], "elev", s.get("elevation"), "h", s.get("height"))
    for w in s.get("walls", []):
        print("  wall %-24s %s -> %s t=%.3f z %.2f..%.2f" % (w["id"], w["start"], w["end"], w["thickness"], w["z0"], w["z1"]))
    for c in s.get("ceilings", []) or []:
        print("  ceil", c["id"], c["z_bottom"], c["z_top"], c["polygon"])
    for fl in s.get("floors", []) or []:
        print("  floor", fl.get("id"), fl.get("z_bottom"), fl.get("z_top"), [r.get("name") for r in fl.get("rooms", [])] if isinstance(fl.get("rooms"), list) else fl.get("rooms"))
    print("  keys", sorted(s.keys()))
print("errors", len(house.get("errors", [])))
