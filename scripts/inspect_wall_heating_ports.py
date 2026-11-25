"""Read-only: per DG wall heating field the panels (type, u, z), the links (direct or via the strip below) and every
link that touches a pipe end of a panel it does not join (branch), plus the core's "Abzweig" warnings.

python scripts/inspect_wall_heating_ports.py   (sets WEINGAERTEN_HOME to the project)
"""
import json
import math
import os
import sys

ROOT = r"c:\Development\weingaerten"
os.environ.setdefault("WEINGAERTEN_HOME", ROOT)
sys.path.insert(0, os.path.join(ROOT, "code"))
import weingaerten_core  # noqa: E402


def find(node):
    if isinstance(node, dict):
        if isinstance(node.get("wall_heating"), dict) and "fields" in node["wall_heating"]:
            return node["wall_heating"]
        for v in node.values():
            r = find(v)
            if r:
                return r
    elif isinstance(node, list):
        for v in node:
            r = find(v)
            if r:
                return r
    return None


def on_segment(point, p, q, tol=0.005):
    seg = [q[i] - p[i] for i in range(3)]
    n2 = sum(v * v for v in seg)
    t = 0.0 if n2 < 1e-12 else max(0.0, min(1.0, sum((point[i] - p[i]) * seg[i] for i in range(3)) / n2))
    return math.dist(point, [p[i] + t * seg[i] for i in range(3)]) < tol


house = json.loads(weingaerten_core.handle(json.dumps({"command": "HOUSE"})))
heating = find(house)
if not heating:
    print("keine Wandheizung:", str(house)[:200])
    sys.exit(1)
branches = 0
for field in heating["fields"]:
    print("==", field["id"], field["name"])
    print("   Platten:", ", ".join("%d %s (u %.3f, z %.3f)" % (p["index"], p["type"], p["u0"], p["z0"]) for p in field["panels"]))
    for link in field["links"]:
        kind = "direkt" if len(link["points"]) == 2 else "über Streifen"
        hits = [("%d %s" % (p["index"], ("Anfang", "Ende")[e])) for p in field["panels"] for e in (0, 1)
                if (p["index"], e) not in {(link["from"], 1), (link["to"], 0)}
                and any(on_segment(p["pipe"][-e if e else 0] if e == 0 else p["pipe"][-1], a, b)
                        for a, b in zip(link["points"], link["points"][1:]))]
        branches += len(hits)
        print("   Verbindung %d -> %d %s%s" % (link["from"], link["to"], kind, ("  ABZWEIG an " + ", ".join(hits)) if hits else ""))
warnings = [w for w in json.loads(weingaerten_core.handle(json.dumps({"command": "VALIDATE"}))).get("warnings", [])
            if "Abzweig" in json.dumps(w, ensure_ascii=False)]
print("Abzweige:", branches, "| Core-Warnungen Abzweig:", len(warnings))
for w in warnings:
    print("  ", w)
