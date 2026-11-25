"""Smoke test of the Dachgeschoss: roof walls (gables following the storey roof), upper storey, WALLS_SAVE keeps the
shape; error cases on a temp copy."""
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

TAN = math.tan(math.radians(30))
RIDGE = 1.25 + 3.56 * TAN
failures = []


def check(label, condition, detail=""):
    print(("ok   " if condition else "FAIL ") + label + ("" if condition else "  " + str(detail)))
    if not condition:
        failures.append(label)


def ask(command):
    return json.loads(weingaerten_core.handle(json.dumps(command)))


def near(a, b, eps=1e-3):
    return abs(a - b) < eps


def area(profile):
    return sum((q[0] - p[0]) * (p[1] + q[1]) / 2 for p, q in zip(profile, profile[1:]))


os.environ["WEINGAERTEN_HOME"] = ROOT
validate = ask({"command": "VALIDATE"})
check("VALIDATE ok", validate["ok"], validate["errors"][:3])
check("3 storeys (EG, DG, KG)", validate["counts"]["storeys"] == 3, validate["counts"])

house = ask({"command": "HOUSE"})
upper = next(s for s in house["storeys"] if s["id"] == "upper")
walls = {w["id"]: w for w in upper["walls"]}
roof = upper["roof"]
check("roof ridge 3.305 at x 3.56", near(roof["ridge"], 3.56) and near(roof["ridge_height"], RIDGE), roof)

north = walls["w-dg-north"]
check("north gable 1.25 -> ridge -> 1.25", [round(p[1], 4) for p in north["profile"]] == [1.25, round(RIDGE, 4), 1.25]
      and near(north["profile"][1][0], 3.571), north["profile"])  # wall starts at x -0.011 (paint + board facade)
check("north height = ridge, z1 = 2.95 + ridge", near(north["height"], RIDGE) and near(north["z1"], 2.95 + RIDGE))
volume = sum(l["volume"] for l in north["layers"])
check("north volume ~ gable area x thickness (corners mitred)", 0.95 < volume / (area(north["profile"]) * north["thickness"]) < 1.0,
      (volume, area(north["profile"]) * north["thickness"]))
check("north pieces have top planes", all(p["top_plane"] for l in north["layers"] for p in l["pieces"]))
balkon = walls["w-dg-south-balkon"]
check("balcony wall 1.25 at east, ~2.82 at west", near(balkon["profile"][0][1], 1.25) and
      near(balkon["profile"][-1][1], 1.25 + 2.72 * TAN), balkon["profile"])
kammer = walls["w-dg-kammer-ost"]
check("Kammer 2 east wall level 2.82", all(near(p[1], 1.25 + 2.72 * TAN) for p in kammer["profile"]), kammer["profile"])
check("knee walls 1.25", all(near(walls[w]["height"], 1.25) for w in ("w-dg-east", "w-dg-west")))
check("interior wall up to the roof", near(walls["iw-dg-durchgang-schlaf"]["height"], RIDGE))
face = north["faces"]["inside"]
check("north inside face area < length x ridge", 0 < face["area"] < face["length"] * RIDGE)
check("EG walls rectangular", all(p["top_plane"] is None for w in house["storeys"][0]["walls"]
                                  for l in w["layers"] for p in l["pieces"]))

temp = tempfile.mkdtemp(prefix="weingaerten-dg-")
try:
    for folder in ("catalog", "house"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(temp, folder))
    path = os.path.join(temp, "house", "storeys", "upper.json")
    original = json.load(open(path, encoding="utf-8"))
    os.environ["WEINGAERTEN_HOME"] = temp

    broken = copy.deepcopy(original)
    west = next(w for w in broken["walls"] if w["id"] == "w-dg-west")
    west["openings"] = [{"id": "o-y", "component": "component:door-dg-durchgang", "offset": 1.0, "sill": 0,
                         "joint": 0.01, "inset": 0.03, "reveal_material": "material:interior-plaster"}]
    north_wall = next(w for w in broken["walls"] if w["id"] == "w-dg-north")
    north_wall["openings"] = [dict(west["openings"][0], id="o-z", offset=0.4)]
    json.dump(broken, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    errors = {(e["where"], e["message"]) for e in ask({"command": "VALIDATE"})["errors"]}
    check("door in knee wall -> Öffnung höher als die Wand",
          ("storey:upper.w-dg-west.o-y", "Öffnung höher als die Wand") in errors, sorted(errors))
    check("door under the slope near the eaves -> Öffnung höher als die Wand",
          ("storey:upper.w-dg-north.o-z", "Öffnung höher als die Wand") in errors, sorted(errors))
    check("no foundation check on upper storey", not any("Bodenplatte" in m for w, m in errors if "upper" in w))

    no_roof = copy.deepcopy(original)
    del no_roof["roof"]
    json.dump(no_roof, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    errors = {(e["where"], e["message"]) for e in ask({"command": "VALIDATE"})["errors"]}
    check("roof wall without roof -> Dach fehlt", ("storey:upper.w-dg-north", "Dach fehlt für Dachwand") in errors,
          sorted(errors)[:3])
    bad_roof = dict(copy.deepcopy(original), roof={"pitch": 95, "knee_wall_height": 1.25, "eaves": [0, 7.12]})
    json.dump(bad_roof, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    errors = {(e["where"], e["message"]) for e in ask({"command": "VALIDATE"})["errors"]}
    check("pitch 95 -> Dach ungültig", ("storey:upper.roof", "Dach ungültig") in errors, sorted(errors)[:3])

    json.dump(original, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    wall = {k: v for k, v in next(w for w in original["walls"] if w["id"] == "w-dg-west").items() if k != "openings"}
    wall["name"] = "Kniestock West (geändert)"
    answer = ask({"command": "WALLS_SAVE", "storey": "upper", "upsert": [wall]})
    check("WALLS_SAVE ok", "error" not in answer, answer.get("errors") or answer.get("error"))
    saved = next(w for w in json.load(open(path, encoding="utf-8"))["walls"] if w["id"] == "w-dg-west")
    check("WALLS_SAVE keeps shape roof", saved.get("shape") == {"kind": "roof"}, saved)
finally:
    os.environ["WEINGAERTEN_HOME"] = ROOT
    shutil.rmtree(temp, ignore_errors=True)

print("%d failures" % len(failures))
sys.exit(1 if failures else 0)
