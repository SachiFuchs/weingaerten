"""Smoke test of the EG corrections: passages, door, beam, post, terrace, flat roof, plus error cases on a temp copy."""
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


def check(label, condition, detail=""):
    print(("ok   " if condition else "FAIL ") + label + ("" if condition else "  " + str(detail)))
    if not condition:
        failures.append(label)


def ask(command):
    return json.loads(weingaerten_core.handle(json.dumps(command)))


validate = ask({"command": "VALIDATE"})
check("VALIDATE ok", validate["ok"], validate["errors"][:3])
check("counts structure 3 (+ KG Kaminfundament) / outdoor 2 (terrace, DG balcony) / ceilings 3", (validate["counts"]["structure"], validate["counts"]["outdoor_areas"],
      validate["counts"]["ceilings"]) == (3, 2, 3), validate["counts"])

house = ask({"command": "HOUSE"})
storey = house["storeys"][0]
openings = {o["id"]: o for w in storey["walls"] for o in w["openings"]}
for oid, (w, h) in {"o-tuer-bad": (0.82, 1.92), "o-durchgang-kueche": (0.82, 2.02), "o-durchgang-kammer": (0.62, 1.82)}.items():
    rough = openings[oid]["rough"]
    check("%s rough %.2f x %.2f" % (oid, w, h), abs(rough["width"] - w) < 1e-6 and abs(rough["height"] - h) < 1e-6, rough)
passage = openings["o-durchgang-kueche"]
check("passage without parts", passage["parts"] == [] and passage["geometry"] == "passage")
check("passage reveal one zone over the wall depth",
      all(len(r["quads"]) == 1 for r in passage["reveals"]) and abs(passage["reveals"][0]["area"] - 2.02 * 0.12) < 1e-6,
      passage["reveals"][:1])
check("door has frame and leaf", {p["kind"] for p in openings["o-tuer-bad"]["parts"]} == {"frame", "leaf"})
structure = {s["id"]: s for s in storey["structure"]}
beam, post = structure["b-wohnzimmer"], structure["p-terrasse"]
check("beam 0.10 x 0.20 x 3.14 = 0.0628 m3", abs(beam["volume"] - 0.0628) < 1e-6, beam["volume"])
check("beam z 2.55..2.75", abs(beam["z0"] - 2.55) < 1e-9 and abs(beam["z1"] - 2.75) < 1e-9, (beam["z0"], beam["z1"]))
check("post 0.12 x 0.12 x 2.75 = 0.0396 m3", abs(post["volume"] - 0.0396) < 1e-6, post["volume"])
check("terrace 12.25 m2", abs(storey["outdoor_areas"][0]["area"] - 12.2496) < 1e-6, storey["outdoor_areas"])
ceilings = {c["id"]: c for c in storey["ceilings"]}
check("flat roof 10.45 m2, 15.2 cm", abs(ceilings["c-flachdach"]["area"] - 10.4502) < 1e-3
      and abs(ceilings["c-flachdach"]["thickness"] - 0.152) < 1e-9, ceilings["c-flachdach"]["area"])
check("terrace roof has joists", ceilings["c-terrasse"]["joists"]["count"] > 0)
check("spruce and pe-foil used", "material:pe-foil" in house["materials"] and "material:spruce-wood" in house["materials"])

bom = ask({"command": "BOM"})
check("BOM structure 3 rows", len(bom["structure"]) == 3, bom["structure"])
check("BOM structure_volume 0.102 + 0.36 (Kaminfundament)", abs(bom["totals"]["structure_volume"] - 0.462) < 0.0015, bom["totals"])
check("BOM outdoor area", [a for a in bom["outdoor_areas"] if a["storey"] == "ground"] == [{"outdoor_area": "t-terrasse", "storey": "ground",
                                                    "name": "Terrasse (überdacht)", "area": 12.25}], bom["outdoor_areas"])

# error cases on a copy of the project
temp = tempfile.mkdtemp(prefix="weingaerten-eg-")
try:
    for folder in ("catalog", "house"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(temp, folder))
    path = os.path.join(temp, "house", "storeys", "ground.json")
    original = json.load(open(path, encoding="utf-8"))
    broken = copy.deepcopy(original)
    broken["structure"] += [
        {"id": "x-kind", "kind": "truss", "material": "material:spruce-wood", "width": 0.1},
        {"id": "x-mat", "kind": "post", "material": "material:nope", "width": 0.1, "depth": 0.1, "position": [1, 1]},
        {"id": "x-size", "kind": "beam", "material": "material:spruce-wood", "width": 0.1, "height": 0.2,
         "start": [1, 1], "end": [1, 1]},
        {"id": "b-wohnzimmer", "kind": "post", "material": "material:spruce-wood", "width": 0.1, "depth": 0.1,
         "position": [2, 2]}]
    broken["outdoor_areas"].append({"id": "t-bad", "name": "kaputt", "rect": [0, 0, -1, 1]})
    json.dump(broken, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    os.environ["WEINGAERTEN_HOME"] = temp
    errors = {(e["where"], e["message"]) for e in ask({"command": "VALIDATE"})["errors"]}
    for expected in [("storey:ground.x-kind", "Tragwerk-Art unbekannt: truss"),
                     ("storey:ground.x-mat", "unbekannt: material:nope"),
                     ("storey:ground.x-size", "Maße ungültig"),
                     ("storey:ground.b-wohnzimmer", "doppelte Tragwerk-id"),
                     ("storey:ground.t-bad", "rect ungültig")]:
        check("error %s" % (expected,), expected in errors, sorted(errors))

    # free_ends: a shortened interior wall has an open end; free_ends ["end"] releases it, on an exterior wall it is an error
    interior = next(w for w in storey["walls"] if w["category"] == "interior_wall")
    exterior = next(w for w in storey["walls"] if w["category"] == "exterior_wall")
    released = copy.deepcopy(original)
    for wall in released["walls"]:
        if wall["id"] == interior["id"]:
            d = interior["direction"]
            ux, uy = (1, 0) if d == 0 else (0, 1) if d == 90 else (-1, 0) if d == 180 else (0, -1)
            wall["end"] = [round(wall["end"][0] - 0.2 * ux, 4), round(wall["end"][1] - 0.2 * uy, 4)]
    json.dump(released, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    where = "storey:ground." + interior["id"]
    end_point = next(w for w in released["walls"] if w["id"] == interior["id"])["end"]
    open_end = lambda answer: [x for x in answer["warnings"] if x["where"] == where
                               and x["message"] == "offenes Wandende bei [%g, %g]" % tuple(end_point)]
    check("shortened interior wall %s has an open end" % interior["id"], open_end(ask({"command": "VALIDATE"})))
    next(w for w in released["walls"] if w["id"] == interior["id"])["free_ends"] = ["end"]
    json.dump(released, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    answer = ask({"command": "VALIDATE"})
    check("free_ends end -> no open-end warning", not open_end(answer) and answer["ok"], (open_end(answer), answer["errors"][:3]))
    check("HOUSE returns free_ends", next(w for w in ask({"command": "HOUSE"})["storeys"][0]["walls"]
                                          if w["id"] == interior["id"])["free_ends"] == ["end"])
    next(w for w in released["walls"] if w["id"] == exterior["id"])["free_ends"] = ["start"]
    json.dump(released, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    errors = {(e["where"], e["message"]) for e in ask({"command": "VALIDATE"})["errors"]}
    check("free_ends on exterior wall -> error", ("storey:ground." + exterior["id"], "free_ends nur bei Innenwänden") in errors, sorted(errors))
finally:
    os.environ["WEINGAERTEN_HOME"] = ROOT
    shutil.rmtree(temp, ignore_errors=True)

print("%d failures" % len(failures))
sys.exit(1 if failures else 0)
