"""Smoke test of rooms as polygons, coverings (Beläge) and shafts: HOUSE, BOM, ROOM_SAVE/DELETE, SHAFT_SAVE/DELETE,
WALLS_SAVE keeping the coverings, error cases.

Runs on a temp copy of catalog + house (WEINGAERTEN_HOME), the project data stays unchanged.
"""
import copy
import json
import os
import shutil
import sys
import tempfile

ROOT = r"c:\Development\weingaerten"
sys.path.insert(0, os.path.join(ROOT, "code"))
import weingaerten_core  # noqa: E402

failures = []


def ask(command):
    return json.loads(weingaerten_core.handle(json.dumps(command)))


def check(name, condition, detail=""):
    print(("ok   " if condition else "FAIL ") + name + ("" if condition else "  " + str(detail)))
    if not condition:
        failures.append(name)


def storey_out(storey_id):
    return next(s for s in ask({"command": "HOUSE"})["storeys"] if s["id"] == storey_id)


def room_out(storey_id, room_id):
    return next(r for r in storey_out(storey_id)["rooms"] if r["id"] == room_id)


def room_json(storey_id, room_id):
    with open(os.path.join(os.environ["WEINGAERTEN_HOME"], "house", "storeys", storey_id + ".json"), encoding="utf-8") as f:
        return next(r for r in json.load(f)["rooms"] if r["id"] == room_id)


def near(a, b, limit=1e-4):
    return a is not None and abs(a - b) <= limit


# --- project data: valid, Wohnzimmer is one polygon with the old area
os.environ["WEINGAERTEN_HOME"] = ROOT
validate = ask({"command": "VALIDATE"})
own = [e for e in validate["errors"] if "room" in e["where"] or "shaft" in e["where"] or e.get("kind") == "covering"]
check("project: no room / covering / shaft errors", not own, own)
wz = room_out("ground", "room-wohnzimmer")
check("Wohnzimmer polygon 8 points", len(wz["polygon"]) == 8, wz["polygon"])
check("Wohnzimmer area = old 3 rects", near(wz["area"], 2.792 * 1.52 + 3.767 * 4.622 + 2.697 * 2.992), wz["area"])
check("Wohnzimmer usage NUF1 + number", wz["usage"] == "NUF1" and wz["number"], (wz["usage"], wz["number"]))
check("Wohnzimmer height = storey - floor", wz["height"] and wz["height"] < 2.75 and near(wz["volume"], wz["area"] * wz["height"], 1e-3),
      (wz["height"], wz["volume"]))
house = ask({"command": "HOUSE"})
shaft = next(s for s in house["shafts"] if s["id"] == "schacht-kueche")
kinds = sorted((c["storey"], c["kind"]) for c in shaft["cuts"])
check("shaft cuts EG floor and EG ceiling, not KG floor", ("ground", "floor") in kinds and ("ground", "ceiling") in kinds
      and ("basement", "floor") not in kinds, kinds)
f_eg = next(f for f in storey_out("ground")["floors"] if f["id"] == "f-eg")
cut = next(c["area"] for c in shaft["cuts"] if c["kind"] == "floor" and c["storey"] == "ground")
check("EG floor area reduced by the shaft", near(sum(r["shaft_area"] for r in f_eg["rooms"]), cut), cut)

# --- temp copy for edits
home = tempfile.mkdtemp()
for folder in ("catalog", "house"):
    shutil.copytree(os.path.join(ROOT, folder), os.path.join(home, folder))
os.environ["WEINGAERTEN_HOME"] = home
try:
    room = room_json("ground", "room-wohnzimmer")
    room["coverings"] = [
        {"id": "bel-wz", "surface": "floor", "assembly": "assembly:covering-parkett-eiche", "area": "room"},
        {"id": "bel-wz-feld", "surface": "floor", "assembly": "assembly:covering-fliese-boden",
         "area": [[1.0, 6.0], [2.0, 6.0], [2.0, 7.0], [1.0, 7.0]]},
        {"id": "sockel-wz", "surface": "wall", "assembly": "assembly:covering-sockelleiste-kiefer", "walls": "all",
         "z": [0, 0.06]}]
    answer = ask({"command": "ROOM_SAVE", "storey": "ground", "room": room, "create": False})
    check("ROOM_SAVE coverings", "error" not in answer, answer)
    wz = room_out("ground", "room-wohnzimmer")
    by_id = {c["id"]: c for c in wz["coverings"]}
    check("whole-room covering = room minus zone", near(by_id["bel-wz"]["area"], wz["area"] - 1.0), by_id["bel-wz"]["area"])
    check("zone covering 1 m²", near(by_id["bel-wz-feld"]["area"], 1.0), by_id["bel-wz-feld"]["area"])
    skirting = by_id["sockel-wz"]
    check("skirting shorter than the perimeter (doors)", 0 < skirting["length"] < wz["perimeter"], skirting["length"])
    check("skirting area = length x 6 cm", near(skirting["area"], skirting["length"] * 0.06, 1e-3), skirting["area"])
    bom = ask({"command": "BOM"})
    check("BOM covering rows", len([r for r in bom["coverings"] if r["room"] == "room-wohnzimmer"]) == 3, bom["coverings"])
    check("BOM totals covering_floor_area", near(bom["totals"]["covering_floor_area"], wz["area"], 1e-3),
          bom["totals"]["covering_floor_area"])

    bad = copy.deepcopy(room)
    bad["coverings"].append({"id": "bel-x", "surface": "floor", "assembly": "assembly:covering-fliese-boden",
                             "area": [[1.5, 6.5], [2.5, 6.5], [2.5, 7.5], [1.5, 7.5]]})
    answer = ask({"command": "ROOM_SAVE", "storey": "ground", "room": bad, "create": False})
    check("overlapping zones rejected", "überlappen" in answer.get("error", ""), answer)
    bad = copy.deepcopy(room)
    bad["coverings"][1]["area"] = [[-1.0, 6.0], [2.0, 6.0], [2.0, 7.0], [-1.0, 7.0]]
    answer = ask({"command": "ROOM_SAVE", "storey": "ground", "room": bad, "create": False})
    check("zone outside the room rejected", "nicht im Raum" in answer.get("error", ""), answer)
    bad = copy.deepcopy(room)
    bad["polygon"] = [[0.328, 3.47], [3.12, 3.47], [3.5, 5.0], [0.328, 9.612]]
    answer = ask({"command": "ROOM_SAVE", "storey": "ground", "room": bad, "create": False})
    check("oblique polygon rejected", "90°" in answer.get("error", ""), answer)
    bad = dict(room, coverings=[{"id": "w", "surface": "floor", "assembly": "assembly:floor-eg-fbh"}])
    answer = ask({"command": "ROOM_SAVE", "storey": "ground", "room": bad, "create": False})
    check("non-covering assembly rejected", "kein Belag" in answer.get("error", ""), answer)

    # WALLS_SAVE from the plan editor only sends the shape: coverings and number stay
    shape = {"id": "room-wohnzimmer", "name": "Wohnzimmer", "polygon": room["polygon"]}
    answer = ask({"command": "WALLS_SAVE", "storey": "ground", "rooms": {"upsert": [shape]}})
    check("WALLS_SAVE room shape", "error" not in answer, answer)
    kept = room_json("ground", "room-wohnzimmer")
    check("WALLS_SAVE keeps coverings and number", len(kept.get("coverings", [])) == 3 and kept.get("number") == room["number"],
          kept)

    new_room = {"id": "room-test", "number": "9.99", "name": "Test", "polygon": [[0, 0], [1, 0], [1, 1], [0, 1]]}
    answer = ask({"command": "ROOM_SAVE", "storey": "ground", "room": new_room, "create": True})
    check("room outside the outline rejected", "error" in answer, answer)

    shaft = {"id": "schacht-test", "name": "Test", "polygon": [[2.0, 7.0], [2.3, 7.0], [2.3, 7.3], [2.0, 7.3]],
             "from_storey": "storey:ground", "to_storey": "storey:basement"}
    answer = ask({"command": "SHAFT_SAVE", "shaft": shaft, "create": True})
    check("SHAFT_SAVE", "error" not in answer, answer)
    wz = room_out("ground", "room-wohnzimmer")
    check("shaft cut out of the whole-room covering",
          near(next(c for c in wz["coverings"] if c["id"] == "bel-wz")["shaft_area"], 0.09), wz["coverings"][0])
    answer = ask({"command": "SHAFT_SAVE", "shaft": dict(shaft, from_storey="storey:basement",
                                                          to_storey="storey:ground"), "create": False})
    check("shaft upside down rejected", "error" in answer, answer)
    answer = ask({"command": "SHAFT_SAVE", "shaft": dict(shaft, penetrations=["tga-run:gibt-es-nicht"]), "create": False})
    check("unknown run rejected", "Leitung unbekannt" in answer.get("error", ""), answer)
    check("SHAFT_DELETE", ask({"command": "SHAFT_DELETE", "id": "schacht-test"}) == {"deleted": True})
    check("ROOM_DELETE unknown", "error" in ask({"command": "ROOM_DELETE", "storey": "ground", "id": "room-xyz"}))
finally:
    shutil.rmtree(home, ignore_errors=True)

print("%d failures" % len(failures))
sys.exit(1 if failures else 0)
