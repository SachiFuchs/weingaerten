"""Read-only: print the computed waste water runs, penetrations, parts and related issues."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ.setdefault("WEINGAERTEN_HOME", ROOT)
from weingaerten_core.command_handler import handle  # noqa: E402

house = json.loads(handle(json.dumps({"command": "HOUSE"})))
ww = house.get("waste_water") or {}
for r in ww.get("runs", []):
    print("run %-18s %-4s DN%-4s %.2f m slopes %s" % (r["id"], r["line"], r["dn"], r["length"],
          [None if s["slope"] is None else round(s["slope"] * 100, 1) for s in r["segments"]]))
for p in ww.get("penetrations", []):
    print("pen %-9s %-34s %-18s #%s drill %.2f %s %s" % (p["kind"], p["element"], p["run"], p.get("index"),
          p["core_drill"], [round(v, 3) for v in p["position"]], p["direction"]))
for s in ww.get("stock", []):
    print("stock", s)
print("parts", len(ww.get("parts", [])))
validate = json.loads(handle(json.dumps({"command": "VALIDATE"})))
for kind in ("errors", "warnings"):
    for issue in validate.get(kind, []):
        if any(k in issue["where"] for k in ("tga", "penetr", "aw-", "waste")):
            print(kind[:-1], issue)
print("total errors", len(validate.get("errors", [])))
