"""Read-only: print the computed electrical runs, penetrations, stock, cuts and related issues."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ.setdefault("WEINGAERTEN_HOME", ROOT)
from weingaerten_core.command_handler import handle  # noqa: E402

house = json.loads(handle(json.dumps({"command": "HOUSE"})))
el = house.get("electrical") or {}
for r in el.get("runs", []):
    print("run %-16s %-14s %s rohr %.2f m kabel %.2f m" % (r["id"], r["label"], r["line"], r["length"],
                                                        r["cable_length"]))
for p in el.get("penetrations", []):
    print("pen %-9s %-34s %-16s drill %.2f %s" % (p["kind"], p["element"], p["run"], p["core_drill"], p["direction"]))
for s in el.get("stock", []):
    print("stock %-7s %-70s count %3s packs %s len %s price %s" % (s["kind"], s["name"][:70], s["count"], s["packs"],
                                                                 s["length"] and round(s["length"], 2), s["price"]))
for c in el.get("cuts", []):
    print("cut", c["run"], c["segment"], c["net_length"], c["pieces"])
bom = json.loads(handle(json.dumps({"command": "BOM"})))
print("totals", {k: v for k, v in bom["totals"].items() if k.startswith("electrical")})
validate = json.loads(handle(json.dumps({"command": "VALIDATE"})))
for kind in ("errors", "warnings"):
    for issue in validate.get(kind, []):
        if any(k in issue["where"] for k in ("el-", "schacht", "electr")):
            print(kind[:-1], issue)
print("total errors", len(validate.get("errors", [])))
