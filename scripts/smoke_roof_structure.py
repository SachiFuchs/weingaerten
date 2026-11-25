"""Smoke test of the DG roof structure (Dachstuhl, Pfettendach): members, geometry, BOM, error cases on a temp copy."""
import copy
import json
import math
import os
import shutil
import sys
import tempfile

ROOT = r"c:\Development\weingaerten"
sys.path.insert(0, os.path.join(ROOT, "code"))
import weingaerten_core  # noqa: E402

COS, TAN = math.cos(math.radians(30)), math.tan(math.radians(30))
failures = []


def check(label, condition, detail=""):
    print(("ok   " if condition else "FAIL ") + label + ("" if condition else "  " + str(detail)))
    if not condition:
        failures.append(label)


def ask(command):
    return json.loads(weingaerten_core.handle(json.dumps(command)))


def near(a, b, eps=2e-3):
    return abs(a - b) < eps


os.environ["WEINGAERTEN_HOME"] = ROOT
validate = ask({"command": "VALIDATE"})
check("VALIDATE ok", validate["ok"], validate["errors"][:3])
check("count roof_structure 39", validate["counts"].get("roof_structure") == 39, validate["counts"])

house = ask({"command": "HOUSE"})
upper = next(s for s in house["storeys"] if s["id"] == "upper")
rs = upper["roof_structure"]
check("counts per kind", rs["counts"] == {"rafter": 24, "purlin": 2, "foot_purlin": 2, "collar": 10, "ridge_purlin": 1}, rs["counts"])
members = {m["id"]: m for m in rs["members"]}
main = [m for m in rs["members"] if m["id"].startswith("west-s")]
kammer = [m for m in rs["members"] if m["id"].startswith("west-kammer-s")]
check("10 / 4 / 10 rafters", (len(main), len(kammer), len([m for m in rs["members"] if m["id"].startswith("east-s")]))
      == (10, 4, 10))
check("main rafter length 3.56 / cos30", all(near(m["length"], 3.56 / COS) for m in main), main[0]["length"])
check("Kammer rafter length 3.56 / cos30 (to the ridge)", all(near(m["length"], 3.56 / COS) for m in kammer), kammer[0]["length"])
ridge_purlin = next(m for m in rs["members"] if m["kind"] == "ridge_purlin")
check("ridge purlin top = ridge underside, 9.94..13.13", near(ridge_purlin["z1"], 2.95 + 1.25 + 3.56 * TAN)
      and near(ridge_purlin["length"], 3.19), (ridge_purlin["z1"], ridge_purlin["length"]))
r = main[0]
check("rafter bottom on roof line (z at x 0 = 2.95 + 1.25)", near(r["bottom_plane"][2], 4.2) and near(r["bottom_plane"][0], TAN),
      r["bottom_plane"])
check("rafter top = bottom + 0.16 / cos30", near(r["top_plane"][2] - r["bottom_plane"][2], 0.16 / COS))
check("rafter volume = b h l", near(r["volume"], 0.08 * 0.16 * r["length"], 1e-4))
purlin = members["purlin-west"]
xs = [p[0] for p in purlin["footprint"]]
check("west purlin centre x 1.472, z 4.85..5.05", near(sum(xs) / 4, 0.85 / TAN) and near(purlin["z0"], 4.85)
      and near(purlin["z1"], 5.05), (sum(xs) / 4, purlin["z0"], purlin["z1"]))
check("west purlin runs 2.08..13.13", near(purlin["length"], 11.05))
check("east purlin runs 2.08..9.94", near(members["purlin-east"]["length"], 7.86))
foot = members["foot-purlin-west"]
check("foot purlin on knee wall centre 0.159, z 4.20..4.32", near(sum(p[0] for p in foot["footprint"]) / 4, 0.159)
      and near(foot["z0"], 4.2) and near(foot["z1"], 4.32))
collar = members["collar-1"]
check("collar z 5.35..5.51", near(collar["z0"], 5.35) and near(collar["z1"], 5.51), (collar["z0"], collar["z1"]))
check("collar length between slopes", near(collar["length"], 7.12 - 2 * (1.23 / TAN)), collar["length"])

bom = ask({"command": "BOM"})
rows = {row["kind"]: row for row in bom["roof_structure"]}
check("BOM 5 rows", sorted(rows) == ["collar", "foot_purlin", "purlin", "rafter", "ridge_purlin"], sorted(rows))
total = sum(m["volume"] for m in rs["members"])
check("BOM total roof_structure_volume", near(bom["totals"]["roof_structure_volume"], total), bom["totals"])
spruce = next(m for m in bom["materials"] if m["material"] == "material:spruce-wood")
check("spruce volume includes the roof structure", spruce["volume"] >= total - 1e-3)

temp = tempfile.mkdtemp(prefix="weingaerten-rs-")
try:
    for folder in ("catalog", "house"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(temp, folder))
    path = os.path.join(temp, "house", "storeys", "upper.json")
    original = json.load(open(path, encoding="utf-8"))
    os.environ["WEINGAERTEN_HOME"] = temp
    cases = [("Dachstuhl ohne Dach", lambda s: s.pop("roof")),
             ("unbekannt: material:nope", lambda s: s["roof_structure"].update(material="material:nope")),
             ("Maße ungültig", lambda s: s["roof_structure"]["rafters"].update(spacing=0)),
             ("Dachfläche ungültig", lambda s: s["roof_structure"]["slopes"].append({"side": "north", "range": [0, 1]}))]
    for message, change in cases:
        broken = copy.deepcopy(original)
        change(broken)
        json.dump(broken, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        errors = {(e["where"], e["message"]) for e in ask({"command": "VALIDATE"})["errors"]}
        check("error " + message, ("storey:upper.roof_structure", message) in errors, sorted(errors)[:3])
finally:
    os.environ["WEINGAERTEN_HOME"] = ROOT
    shutil.rmtree(temp, ignore_errors=True)

print("%d failures" % len(failures))
sys.exit(1 if failures else 0)
