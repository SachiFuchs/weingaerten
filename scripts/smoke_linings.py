"""Smoke test of the interior linings (Innendämmung): LINING_SAVE/DELETE, HOUSE, BOM, WALLS_SAVE, errors.

Runs on a temp copy of catalog + house (WEINGAERTEN_HOME), the project data stays unchanged.
"""
import json
import os
import shutil
import sys
import tempfile

ROOT = r"c:\Development\weingaerten"
sys.path.insert(0, os.path.join(ROOT, "code"))
import weingaerten_core  # noqa: E402

ASM = "assembly:interior-insulation-ii1"
failures = []


def ask(command):
    return json.loads(weingaerten_core.handle(json.dumps(command)))


def check(name, condition, detail=""):
    print(("ok   " if condition else "FAIL ") + name + ("" if condition else "  " + str(detail)))
    if not condition:
        failures.append(name)


def storey_out(storey_id):
    return next(s for s in ask({"command": "HOUSE"})["storeys"] if s["id"] == storey_id)


def wall_out(storey, wall_id):
    return next(w for w in storey["walls"] if w["id"] == wall_id)


def save(storey, wall, lining, create=True):
    return ask({"command": "LINING_SAVE", "storey": storey, "wall": wall, "lining": lining, "create": create})


# catalog of the project itself: the new elements are valid
os.environ["WEINGAERTEN_HOME"] = ROOT
validate = ask({"command": "VALIDATE"})
new_refs = ("lehmkleber", "holzfaserplatte", "lehmputz", "lehmfarbe", "naturbo", "fesche-farbe", "interior-insulation")
own = [e for e in validate["errors"] if any(r in e["where"] for r in new_refs) or e.get("kind") == "lining"]
check("neue Katalogelemente ohne Fehler", not own, own)

temp = tempfile.mkdtemp()
try:
    for folder in ("catalog", "house"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(temp, folder))
    os.environ["WEINGAERTEN_HOME"] = temp
    ground_file = os.path.join(temp, "house", "storeys", "ground.json")

    ground = storey_out("ground")
    north = wall_out(ground, "w-north")
    u0, u1 = sorted(north["u_range"]["inside"])
    answer = save("ground", "w-north", {"id": "id-nord", "assembly": ASM, "face": "inside", "u0": u0, "u1": u1})
    check("LINING_SAVE Außenwand innen", "error" not in answer, answer)
    ground = storey_out("ground")
    lining = next(l for l in ground["linings"] if l["id"] == "id-nord")
    holes = sum(o["rough"]["area"] for o in north["openings"])
    gross = (u1 - u0) * north["height"]
    check("Bruttofläche = Rechteck", abs(lining["gross_area"] - gross) < 1e-3, (lining["gross_area"], gross))
    check("Öffnungen ausgespart", abs(lining["area"] - (gross - holes)) < 1e-3, (lining["area"], gross, holes))
    check("4 Schichten, Dicke 6,7 cm", len(lining["layers"]) == 4 and abs(lining["thickness"] - 0.067) < 1e-6)
    check("Holzfaser-Volumen = 0,06 · Fläche", abs(lining["layers"][1]["volume"] - 0.06 * lining["area"]) < 1e-3)
    check("Öffnungen gelistet", set(lining["openings"]) == {o["id"] for o in north["openings"]}, lining["openings"])
    check("Teile vorhanden", len(lining["parts"]) >= 4 and all(len(p["footprint"]) == 4 for p in lining["parts"]))
    check("Wand unverändert", wall_out(ground, "w-north")["thickness"] == north["thickness"])

    answer = save("ground", "w-north", {"id": "id-nord2", "assembly": ASM, "face": "inside", "u0": u0, "u1": u0 + 1})
    check("Überlappung abgelehnt", "überlappt" in answer.get("error", ""), answer)
    answer = save("ground", "w-north", {"id": "id-x", "assembly": ASM, "face": "left", "u0": u0, "u1": u0 + 1})
    check("Seite left an Außenwand abgelehnt", "Seite ungültig" in answer.get("error", ""), answer)
    answer = save("ground", "w-north", {"id": "id-x", "assembly": ASM, "face": "inside", "u0": u0, "u1": u1 + 1, "z0": 0})
    check("außerhalb der Wand abgelehnt", "außerhalb" in answer.get("error", ""), answer)
    answer = save("ground", "w-north", {"id": "id-x", "assembly": "assembly:interior-wall-iw1", "face": "inside",
                                        "u0": u0, "u1": u0 + 1})
    check("falscher Aufbau abgelehnt", "keine Innendämmung" in answer.get("error", ""), answer)
    answer = save("ground", "w-north", {"id": "id-nord", "assembly": ASM, "face": "inside", "u0": u0, "u1": u1})
    check("doppelte id abgelehnt", "existiert bereits" in answer.get("error", ""), answer)

    answer = save("ground", "w-north", {"id": "id-nord", "assembly": ASM, "face": "inside", "u0": u0, "u1": u1,
                                        "z0": 0.5, "z1": 1.2}, create=False)
    check("Update z0/z1", "error" not in answer, answer)
    lining = next(l for l in storey_out("ground")["linings"] if l["id"] == "id-nord")
    check("Teilhöhe 0,5..1,2 (unter dem Fenster)", abs(lining["gross_area"] - (u1 - u0) * 0.7) < 1e-3, lining["gross_area"])

    inner = wall_out(storey_out("ground"), "iw-flur-bad")
    for face in ("left", "right"):
        a, b = sorted(inner["u_range"][face])
        answer = save("ground", "iw-flur-bad", {"id": "id-bad-" + face, "assembly": ASM, "face": face, "u0": a, "u1": b})
        check("Innenwand Seite %s" % face, "error" not in answer, answer)
    lining = next(l for l in storey_out("ground")["linings"] if l["id"] == "id-bad-left")
    check("Innenwand links liegt vor der linken Fläche", lining["parts"] and lining["face"] == "left")

    upper = storey_out("upper")
    west = wall_out(upper, "w-dg-west")
    a, b = sorted(west["u_range"]["inside"])
    answer = save("upper", "w-dg-west", {"id": "id-dg-west", "assembly": ASM, "face": "inside", "u0": a, "u1": b})
    check("Dachwand", "error" not in answer, answer)
    lining = next(l for l in storey_out("upper")["linings"] if l["id"] == "id-dg-west")
    top = max(z for _, z in west["profile"])
    check("Dachwand unter der Dachlinie", lining["gross_area"] <= (b - a) * top + 1e-6
          and all(p["z1"] <= west["z0"] + top + 1e-6 for p in lining["parts"]), lining["gross_area"])

    bom = ask({"command": "BOM"})
    check("BOM linings (4 Bereiche)", len(bom["linings"]) == 4, len(bom["linings"]))
    check("BOM lining_area", abs(bom["totals"]["lining_area"] - sum(r["area"] for r in bom["linings"])) < 1e-2)
    board = next((m for m in bom["materials"] if m["material"] == "material:holzfaserplatte-naturbo"), None)
    check("Holzfaser in Materialliste", board is not None and board["volume"] > 0, board)
    check("counts.linings", ask({"command": "VALIDATE"})["counts"].get("linings") == 4)

    # WALLS_SAVE keeps the linings (request without linings), moved start shifts u0/u1
    data = json.load(open(ground_file, encoding="utf-8"))
    wall = next(w for w in data["walls"] if w["id"] == "w-north")
    plain = {k: v for k, v in wall.items() if k not in ("openings", "linings")}
    answer = ask({"command": "WALLS_SAVE", "storey": "ground", "upsert": [plain]})
    check("WALLS_SAVE ok", "error" not in answer, answer)
    data = json.load(open(ground_file, encoding="utf-8"))
    wall = next(w for w in data["walls"] if w["id"] == "w-north")
    check("WALLS_SAVE behält linings", [l["id"] for l in wall.get("linings", [])] == ["id-nord"], wall.get("linings"))
    check("lining_conflicts im Ergebnis", answer.get("lining_conflicts") == [], answer.get("lining_conflicts"))

    answer = ask({"command": "LINING_DELETE", "storey": "ground", "wall": "w-north", "id": "id-nord"})
    check("LINING_DELETE", answer.get("deleted") is True, answer)
    answer = ask({"command": "LINING_DELETE", "storey": "ground", "wall": "w-north", "id": "id-nord"})
    check("LINING_DELETE unbekannt", "unbekannt" in answer.get("error", ""), answer)
finally:
    os.environ["WEINGAERTEN_HOME"] = ROOT
    shutil.rmtree(temp, ignore_errors=True)
sys.exit(1 if failures else 0)
