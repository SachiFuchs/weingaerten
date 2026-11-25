"""Smoke test of the basement (Kellergeschoss): ground detection, heights, solid stair, light wells, slab cutout, BOM."""
import json
import os
import shutil
import sys
import tempfile

ROOT = r"c:\Development\weingaerten"
sys.path.insert(0, os.path.join(ROOT, "code"))
import weingaerten_core  # noqa: E402

failures = []


def check(label, condition, detail=""):
    print(("ok   " if condition else "FAIL ") + label + ("" if condition else "  " + str(detail)))
    if not condition:
        failures.append(label)


def ask(command):
    return json.loads(weingaerten_core.handle(json.dumps(command)))


def near(a, b, eps=2e-3):
    return abs(a - b) < eps


def area(points):
    return abs(sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(points, points[1:] + points[:1]))) / 2


def temp_home(change):
    # a fresh copy per variant (the core caches the model per WEINGAERTEN_HOME)
    home = tempfile.mkdtemp(prefix="wg-kg-")
    for folder in ("catalog", "house"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(home, folder))
    change(home)
    return home


def edit_json(path, change):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    change(data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


os.environ["WEINGAERTEN_HOME"] = ROOT
validate = ask({"command": "VALIDATE"})
check("VALIDATE ok", validate["ok"], validate["errors"][:3])
check("count light_wells 2", validate["counts"].get("light_wells") == 2, validate["counts"])
house = ask({"command": "HOUSE"})
kg = next(s for s in house["storeys"] if s["id"] == "basement")
check("elevation -2.25", near(kg["elevation"], -2.25))
wall = next(w for w in kg["walls"] if w["id"] == "w-kg-ost")
check("wall z -2.25..-0.25", near(wall["z0"], -2.25) and near(wall["z1"], -0.25), (wall["z0"], wall["z1"]))
floor = kg["floors"][0]
check("floor -2.45..-2.25", near(floor["z_bottom"], -2.45) and near(floor["z_top"], -2.25), floor)
window = wall["openings"][0]
check("window bottom -0.85", near(wall["z0"] + window["rough"]["zb"], -0.85), window["rough"])
stair = kg["stairs"][0]
check("solid stair", stair.get("construction") == "solid" and stair["counts"] == {"step": 11}, stair["counts"])
check("rise 2.25/12", near(stair["rise"], 2.25 / 12), stair["rise"])
check("top step at the door (west)", min(p[0] for p in stair["parts"][-1]["footprint"]) < 0.31)
check("steps stand on the floor", all(near(p["z0"], -2.25) for p in stair["parts"]))
wells = {w["id"]: w for w in kg["light_wells"]}
east, west = wells["ls-ost"], wells["ls-west"]
check("z_floor -0.95", near(east["z_floor"], -0.95), east["z_floor"])
check("east well outside x 7.12", min(p[0] for q in east["parts"] for p in q["footprint"]) >= 7.12 - 1e-6)
check("west well outside x 0", max(p[0] for q in west["parts"] for p in q["footprint"]) <= 1e-6)
grating = next(p for p in east["parts"] if p["kind"] == "grating")
check("grating 0.8 x 0.5", near(area(grating["footprint"]), 0.4), area(grating["footprint"]))
check("well centred on window y 3.73",
      near(sum(p[1] for p in grating["footprint"]) / 4, 3.73, 0.02), grating["footprint"])
foundation = house["foundation"]
check("foundation cutout", len(foundation.get("cutouts") or []) == 1)
check("ground storey still on foundation", not any("Bodenplatte" in e["message"] for e in validate["errors"]))
bom = ask({"command": "BOM"})
check("BOM light wells", len(bom["light_wells"]) == 2 and bom["totals"]["light_well_volume"] > 0, bom["totals"])
check("BOM grating area", any(m["material"] == "material:steel-grating" and near(m["area_outside"], 0.8)
                              for m in bom["materials"]))

# basement listed first: ground detection by elevation keeps the foundation on the EG
os.environ["WEINGAERTEN_HOME"] = temp_home(lambda h: edit_json(
    os.path.join(h, "house", "house.json"),
    lambda d: d.update(storeys=["storey:basement", "storey:ground", "storey:upper"])))
v = ask({"command": "VALIDATE"})
check("order independent ok", v["ok"], v["errors"][:3])
h = ask({"command": "HOUSE"})
check("order independent foundation area", near(h["foundation"]["area"], foundation["area"]))


def shallow(home):
    edit_json(os.path.join(home, "house", "storeys", "basement.json"),
              lambda d: d["light_wells"][0].update(depth=0.5))


os.environ["WEINGAERTEN_HOME"] = temp_home(shallow)
v = ask({"command": "VALIDATE"})
check("shallow well error", any(e["message"] == "Lichtschacht zu flach" for e in v["errors"]), v["errors"][:3])

print("\n%d failures" % len(failures))
sys.exit(1 if failures else 0)
