"""Smoke test of the DG roof covering (Dachdeckung): faces, layers, openings, edges, items, BOM, error cases."""
import json
import math
import os
import shutil
import sys
import tempfile

ROOT = r"c:\Development\weingaerten"
sys.path.insert(0, os.path.join(ROOT, "code"))
import weingaerten_core  # noqa: E402

COS = math.cos(math.radians(30))
failures = []


def check(label, condition, detail=""):
    print(("ok   " if condition else "FAIL ") + label + ("" if condition else "  " + str(detail)))
    if not condition:
        failures.append(label)


def ask(command):
    return json.loads(weingaerten_core.handle(json.dumps(command)))


def near(a, b, eps=2e-3):
    return abs(a - b) < eps


def upper_of(house):
    return next(s for s in house["storeys"] if s["id"] == "upper")


os.environ["WEINGAERTEN_HOME"] = ROOT
validate = ask({"command": "VALIDATE"})
check("VALIDATE ok", validate["ok"], validate["errors"][:3])
check("count roof_covering 3", validate["counts"].get("roof_covering") == 3, validate["counts"])
house = ask({"command": "HOUSE"})
rc = upper_of(house)["roof_covering"]
faces = {f["id"]: f for f in rc["faces"]}
e, v = rc["eaves_overhang"], rc["verge_overhang"]
check("face west", faces["west"]["across"] == [-e, 3.56] and near(faces["west"]["along"][0], 2.08 - v)
      and near(faces["west"]["along"][1], 9.94), faces["west"]["along"])
check("face west-kammer (to the ridge)", near(faces["west-kammer"]["across"][1], 3.56)
      and near(faces["west-kammer"]["along"][1], 13.13 + v), faces["west-kammer"])
check("face east", near(faces["east"]["across"][1], 7.12 + e) and near(faces["east"]["along"][1], 9.94 + v))
area = sum((f["across"][1] - f["across"][0]) * (f["along"][1] - f["along"][0]) for f in faces.values()) / COS
check("area", near(rc["area"], area), (rc["area"], area))
check("thickness 0.2305", near(rc["thickness"], 0.2305))
west = faces["west"]
top, bottom = west["layers"][0]["top_plane"], west["layers"][-1]["bottom_plane"]
check("layer stack perpendicular", near(top[2] - bottom[2], 0.2305 / COS), (top, bottom))
check("base = rafter top", near(west["base_plane"][2] - (2.95 + 1.25), 0.16 / COS), west["base_plane"])
check("tile on top", west["layers"][0]["material"] == "material:clay-tile-rubin")
openings = {o["id"]: o for o in rc["openings"]}
check("3 openings", set(openings) == {"dfe-schlaf", "dfe-durchgang", "kamin"}, list(openings))
check("FK06 area", near(openings["dfe-schlaf"]["area"], 0.66 * 1.18))
check("net area", near(rc["area_net"], rc["area"] - sum(o["area"] for o in rc["openings"])))
edges = rc["edges"]
check("eaves", near(edges["eaves"], sum(f["along"][1] - f["along"][0] for f in faces.values())), edges)
east_along = faces["east"]["along"]
ridge = sum(max(0.0, min(f["along"][1], east_along[1]) - max(f["along"][0], east_along[0]))
            for f in faces.values() if f["side"] == "west")
check("ridge", near(edges["ridge"], ridge), (edges, ridge))
items = {i["component"]: i for i in rc["items"]}
check("gutter = eaves", near(items["component:roof-gutter"]["quantity"], edges["eaves"]))
check("brackets per m", items["component:roof-gutter-bracket"]["quantity"] == math.ceil(edges["eaves"] * 1.5 - 1e-9))
check("trimmer invoice", items["component:roof-trimmer"]["quantity"] == 3)

bom = ask({"command": "BOM"})
row = bom["roof_covering"][0]
check("BOM row", near(row["area_net"], rc["area_net"], 2e-3) and near(row["volume"], rc["volume"], 2e-3))
check("BOM totals", near(bom["totals"]["roof_area"], rc["area_net"], 2e-3))
comps = {c["component"]: c for c in bom["components"]}
check("BOM window + flashing", comps.get("component:roof-window-velux-fk06", {}).get("count") == 1
      and comps.get("component:roof-flashing-velux-ck04", {}).get("unit_price") == 140.0)
tile = next(m for m in bom["materials"] if m["material"] == "material:clay-tile-rubin")
check("tile volume", tile["volume"] >= row["layers"][0]["volume"] - 1e-3, tile)


def with_change(label, change, expected):
    tmp = tempfile.mkdtemp()
    try:
        for name in ("catalog", "house"):
            shutil.copytree(os.path.join(ROOT, name), os.path.join(tmp, name))
        path = os.path.join(tmp, "house", "storeys", "upper.json")
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        change(data)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
        os.environ["WEINGAERTEN_HOME"] = tmp
        result = ask({"command": "VALIDATE"})
        messages = [x["message"] for x in result["errors"]]
        check(label, any(expected in m for m in messages), messages[:4])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


with_change("error no roof", lambda d: d.pop("roof"), "Dachdeckung ohne Dach")
with_change("error assembly", lambda d: d["roof_covering"].update(assembly="assembly:exterior-wall-ew1"),
            "kein Dachaufbau")
with_change("error overhang", lambda d: d["roof_covering"].update(eaves_overhang=-1), "Überstand ungültig")
with_change("error sill", lambda d: d["roof_covering"]["openings"][0].update(sill=1.0), "Unterkante unter dem Kniestock")
with_change("error outside", lambda d: d["roof_covering"]["openings"][0].update(y=30), "außerhalb der Dachfläche")
os.environ["WEINGAERTEN_HOME"] = ROOT
print("FAILED: %s" % failures if failures else "all ok")
sys.exit(1 if failures else 0)
