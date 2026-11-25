"""Smoke test of the DG board facade (Stülpschalung): HOUSE, VALIDATE, BOM and error cases."""
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

failures = []


def ask(command):
    return json.loads(weingaerten_core.handle(json.dumps(command)))


def check(name, condition, detail=""):
    print(("ok   " if condition else "FAIL ") + name + ("" if condition else "  " + str(detail)))
    if not condition:
        failures.append(name)


def with_change(change, expected):
    temp = tempfile.mkdtemp()
    try:
        for folder in ("catalog", "house"):
            shutil.copytree(os.path.join(ROOT, folder), os.path.join(temp, folder))
        path = os.path.join(temp, "catalog", "assemblies", "exterior-wall-ew1-holz.json")
        data = json.load(open(path, encoding="utf-8"))
        change(data["layers"][1])
        json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        os.environ["WEINGAERTEN_HOME"] = temp
        answer = ask({"command": "VALIDATE"})
        messages = [e["message"] for e in answer.get("errors", []) if e["where"] == "storey:upper.w-dg-north"]
        check("Fehler '%s'" % expected, expected in messages, messages)
    finally:
        os.environ["WEINGAERTEN_HOME"] = ROOT
        shutil.rmtree(temp, ignore_errors=True)


os.environ["WEINGAERTEN_HOME"] = ROOT
validate = ask({"command": "VALIDATE"})
facade_errors = [e for e in validate.get("errors", []) if "facade" in e["where"] or "facade" in e["message"]
                 or e["where"].startswith("storey:upper.w-dg")]
check("keine Fassadenfehler", not facade_errors, facade_errors)
check("counts.facade_parts > 0", validate["counts"].get("facade_parts", 0) > 0, validate["counts"])

house = ask({"command": "HOUSE"})
upper = next(s for s in house["storeys"] if s["id"] == "upper")
facade = upper["facade"]
walls = {w["wall"]: w for w in facade["walls"]}
check("Balkonwände ohne Fassade", "w-dg-south-balkon" not in walls and "w-dg-kammer-ost" not in walls, list(walls))
check("4 Fassadenwände", set(walls) == {"w-dg-north", "w-dg-east", "w-dg-south-kammer", "w-dg-west"}, list(walls))
check("Deckbreite 0,17", abs(facade["cover"] - 0.17) < 1e-6, facade["cover"])
check("kein Stück länger als 5 m", all(p["length"] <= 5.0 + 1e-6 for p in facade["parts"]))
check("andere Geschosse ohne Fassade", all(not s.get("facade") for s in house["storeys"] if s["id"] != "upper"))
wall_out = {w["id"]: w for w in upper["walls"]}
check("Wanddicke 0,339 (Farbe 1 mm + Brett 2,5 cm + Mauerwerk)", all(abs(wall_out[w]["thickness"] - 0.339) < 1e-6 for w in walls))
check("Farbe und Brett getrennte Schichten", all(
    [l["material"] for l in wall_out[w]["layers"][:2]] == ["material:facade-paint-taubenblau", "material:facade-board-spruce"]
    for w in walls))
check("Brett-Material Fichte natur", house["materials"]["material:facade-board-spruce"]["appearance"]["color"] == "#D8B991")
check("Innenfläche unverändert (Nord y 2.408, Ost x 6.792, West x 0.328, Süd y 12.802)",
      abs(wall_out["w-dg-north"]["start"][1] + 0.339 - 2.408) < 1e-6
      and abs(wall_out["w-dg-east"]["start"][0] - 0.339 - 6.792) < 1e-6
      and abs(wall_out["w-dg-west"]["start"][0] + 0.339 - 0.328) < 1e-6
      and abs(wall_out["w-dg-south-kammer"]["start"][1] - 0.339 - 12.802) < 1e-6)
for wall_id, row in walls.items():
    wall = wall_out[wall_id]
    top = max(z for _, z in wall["profile"])
    expected = math.ceil((top - 1e-3) / 0.17)
    check("Reihen %s = %d" % (wall_id, expected), row["rows"] == expected, row["rows"])
    u_a, u_b = wall["u_range"]["outside"]
    profile = wall["profile"]
    gross = sum((b[0] - a[0]) * (a[1] + b[1]) / 2.0 for a, b in zip(profile, profile[1:]))
    holes = sum(o["rough"]["area"] for o in wall["openings"])
    check("Fläche %s plausibel" % wall_id, gross - holes - 0.6 <= row["area"] <= gross + 1e-3,
          (row["area"], gross, holes))
    check("Teile unter der Dachlinie %s" % wall_id,
          all(p["z1"] <= upper["elevation"] + top + 1e-6 for p in facade["parts"] if p["wall"] == wall_id))
check("Bretter >= lfm / 5", facade["boards"] >= math.ceil(facade["length"] / 5.0 - 1e-6), facade["boards"])
check("Verschnitt 0..40 %", 0 <= facade["waste_share"] < 0.4, facade["waste_share"])
check("Farbe taubenblau", all(p["color"] == "#7D8FA6" for p in facade["parts"]))
check("Material in HOUSE.materials", "material:facade-paint-taubenblau" in house["materials"])

bom = ask({"command": "BOM"})
check("BOM facade", len(bom["facade"]) == 1 and bom["totals"]["facade_boards"] == facade["boards"], bom["facade"][:1])
board_row = next(m for m in bom["materials"] if m["material"] == "material:facade-board-spruce")
layer_volume = sum(w["layers"][1]["volume"] for w in upper["walls"] if w["id"] in walls)
check("Brettvolumen nur einmal (Wandschicht)", abs(board_row["volume"] - layer_volume) < 0.01,
      (board_row["volume"], layer_volume))
print("Fassade: %d Bretter, %.1f lfm, %.1f m², Verschnitt %.0f %%" % (
    facade["boards"], facade["length"], facade["area"], facade["waste_share"] * 100))
for row in facade["walls"]:
    print("  %-20s Reihen %2d  Stücke %3d  %.1f lfm  %.2f m²" % (row["wall"], row["rows"], row["pieces"],
                                                               row["length"], row["area"]))

with_change(lambda layer: layer["cladding"].update(overlap=0.25), "Maße ungültig")
with_change(lambda layer: layer["cladding"].update(paint="material:gibt-es-nicht"), "unbekannt: material:gibt-es-nicht")
sys.exit(1 if failures else 0)
