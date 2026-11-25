"""Smoke test of the installed parts (house/tga/parts): ports, snapping, rotation, slots, transfers, PART_SAVE/DELETE.

Runs on a temp copy of catalog + house (WEINGAERTEN_HOME), the project data stays unchanged.
"""
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


def save(*parts, delete=()):
    answer = ask({"command": "PART_SAVE", "upsert": list(parts), "delete": list(delete)})
    if "error" in answer:
        print("     (abgelehnt: %s)" % (answer.get("errors") or answer["error"]))
    return answer


def parts_out():
    return {p["id"]: p for p in (ask({"command": "HOUSE"}).get("installation") or {}).get("parts") or []}


def port(parts, part_id, port_id):
    return next(q for q in parts[part_id]["ports"] if q["id"] == port_id)


def hosted(pid, component, wall, face, u, z, depth, rot=None, length=None):
    part = {"id": pid, "component": "tga-component:" + component, "storey": "ground",
            "host": {"wall": wall, "face": face}, "u": u, "z": z, "depth": depth, "rot": rot or {}}
    if length is not None:
        part["length"] = length
    return part


temp = tempfile.mkdtemp()
try:
    for folder in ("catalog", "house"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(temp, folder),
                        ignore=shutil.ignore_patterns("imported_*"))
    shutil.rmtree(os.path.join(temp, "house", "tga", "parts"), ignore_errors=True)
    os.environ["WEINGAERTEN_HOME"] = temp
    house = ask({"command": "HOUSE"})
    catalog = {c["ref"]: c for c in house["installation"]["catalog"]}
    check("Palette enthält HT, PP-R und Elektro", {"waste_water", "water_supply", "electrical"}
          <= {c["trade"] for c in catalog.values()}, sorted(catalog))
    ground = next(s for s in house["storeys"] if s["id"] == "ground")
    wall = next(w for w in ground["walls"] if w["category"] == "interior_wall" and w["length"] > 2
                and w["thickness"] >= 0.1)
    wid, u0 = wall["id"], min(wall["u_range"]["left"]) + 0.5
    print("Wand", wid, "Dicke", wall["thickness"])

    # PP-R pipe + 90 degree bend at its end b: seated -> both ports green
    answer = save(hosted("t-pipe", "ppr-rohr-dn-20-x-2-m", wid, "left", u0, 0.5, 0.03, length=0.5),
                  hosted("t-bend", "ppr-bend-20-90", wid, "left", u0 + 0.5 + 0.011, 0.5, 0.03))
    check("PART_SAVE Rohr + Bogen", "error" not in answer, answer)
    parts = parts_out()
    check("Rohr b verbunden", port(parts, "t-pipe", "b")["connected_to"] == "t-bend.a", port(parts, "t-pipe", "b"))
    check("Bogen a grün", port(parts, "t-bend", "a")["status"] == "connected")
    check("Rohr a offen (rot)", port(parts, "t-pipe", "a")["status"] == "open")
    b = port(parts, "t-bend", "b")
    check("Bogen b zeigt nach oben", abs(b["direction"][2] - 1) < 1e-6, b["direction"])

    # a second pipe on the occupied port b of t-pipe, and a pipe at 45 degrees on the free end a: not joined, warned
    save(hosted("t-second", "ppr-rohr-dn-20-x-2-m", wid, "left", u0 + 0.5, 0.5, 0.03, {"plane": 180, "flip": True}, 0.3),
         hosted("t-angle", "ppr-bend-20-90", wid, "left", u0 - 0.011, 0.5, 0.03, {"plane": 45}))
    parts = parts_out()
    warnings = [w["message"] for w in ask({"command": "VALIDATE"})["warnings"] if "t-second" in w["where"]
                or "t-angle" in w["where"] or "t-pipe" in w["where"]]
    check("zweites Teil am belegten Anschluss nicht verbunden", all(q["connected_to"] is None or q["connected_to"] != "t-pipe.b"
                                                                for q in parts["t-second"]["ports"]))
    check("Warnung ohne Verbindung", sum("ohne Verbindung" in m for m in warnings) >= 2, warnings)
    check("schräger Bogen nicht verbunden", port(parts, "t-pipe", "a")["status"] == "open")
    save(delete=["t-second", "t-angle"])

    # rotation: plane 90 makes the pipe vertical, turn -90 points it out of / into the wall
    save(hosted("t-vert", "ppr-rohr-dn-20-x-2-m", wid, "left", u0 + 1.0, 0.2, 0.03, {"plane": 90}, 0.4))
    v = parts_out()["t-vert"]
    check("Drehung plane 90 -> senkrecht", abs(v["ports"][1]["position"][2] - v["ports"][0]["position"][2] - 0.4) < 1e-6)

    # waste water: DN 90 pipe against a DN 50 bend -> warning, reducer 90/50 accepted
    save(hosted("t-ht90", "ht-pipe-90", wid, "left", u0, 1.5, 0.06, length=0.3),
         hosted("t-b50", "ht-bend-50-45", wid, "left", u0 + 0.3 + 0.03, 1.5, 0.06))
    warnings = ask({"command": "VALIDATE"})["warnings"]
    check("DN 90 an DN 50 abgelehnt (Warnung)", any("t-ht90" in w["where"] or "t-b50" in w["where"] for w in warnings
                                                     if "passt nicht" in w["message"]))
    check("DN 90 an DN 50 nicht verbunden", port(parts_out(), "t-ht90", "b")["status"] != "connected")
    save(hosted("t-ht50", "ht-pipe-50", wid, "left", u0, 1.8, 0.06, length=0.3),
         hosted("t-red", "ht-reducer-90-50", wid, "left", u0 + 0.3 + 0.04, 1.8, 0.06))
    check("Reduzierstück 90/50 passt", port(parts_out(), "t-ht50", "b")["connected_to"] == "t-red.a")

    # slot: pipe 3 cm deep in the wall -> slot row, warning in the load-bearing layer
    save(hosted("t-slot", "ppr-rohr-dn-20-x-2-m", wid, "left", u0, 1.0, -0.03, length=0.6))
    house = ask({"command": "HOUSE"})
    slots = [s for s in house["installation"]["slots"] if s["part"] == "t-slot"]
    check("Schlitz berechnet", len(slots) == 1 and abs(slots[0]["depth"] - 0.04) < 1e-6, slots)
    check("Schlitz Volumen > 0", slots and slots[0]["volume"] > 0)
    bom = ask({"command": "BOM"})
    check("BOM installation", bom.get("installation") and bom["totals"]["installation_part_count"] == 8,
          bom["totals"].get("installation_part_count"))
    check("BOM Schlitzvolumen", bom["totals"]["installation_slot_volume"] > 0)

    # transfer: pipe through the whole wall (turn -90 = into the wall) ends on the other face -> transfer + penetration
    save(hosted("t-through", "ppr-rohr-dn-20-x-2-m", wid, "left", u0 + 1.1, 0.8, 0.0, {"turn": 90},
                wall["thickness"]))
    through = parts_out()["t-through"]
    ends = {q["id"]: q for q in through["ports"]}
    check("Ende auf der anderen Wandseite = Übergabe", any(q["transfer"] == "beside" for q in ends.values()), ends)
    pens = [p for p in ask({"command": "HOUSE"})["installation"]["penetrations"] if p["run"] == "t-through"]
    check("Durchbruch der Wand", len(pens) == 1, pens)

    # bewusst offen
    part = hosted("t-pipe", "ppr-rohr-dn-20-x-2-m", wid, "left", u0, 0.5, 0.03, length=0.5)
    part["open_ok"] = ["a"]
    save(part)
    check("bewusst offen = blau", port(parts_out(), "t-pipe", "a")["status"] == "open_ok")

    # stored connections stay symmetric; delete removes the back-link
    part["connections"] = {"b": "t-bend.a"}
    save(part)
    with open(os.path.join(temp, "house", "tga", "parts", "t-bend.json"), encoding="utf-8") as handle:
        check("Rückverbindung geschrieben", json.load(handle).get("connections") == {"a": "t-pipe.b"})
    answer = ask({"command": "PART_DELETE", "id": "t-bend"})
    check("PART_DELETE", answer.get("deleted") is True, answer)
    with open(os.path.join(temp, "house", "tga", "parts", "t-pipe.json"), encoding="utf-8") as handle:
        check("Verbindung nach Löschen entfernt", "connections" not in json.load(handle))

    # errors reject the change
    too_long = hosted("t-long", "ht-pipe-50", wid, "left", u0, 0.5, 0.06, length=2.5)
    check("Rohr > 2 m abgelehnt", "error" in save(too_long))
    check("unbekannte Wand abgelehnt", "error" in save(hosted("t-x", "ht-pipe-50", "nix", "left", 0, 0, 0)))
    check("falsche Wandseite abgelehnt", "error" in save(hosted("t-x", "ht-pipe-50", wid, "inside", 0, 0, 0)))
    check("Löschen unbekannt", "error" in ask({"command": "PART_DELETE", "id": "gibt-es-nicht"}))
finally:
    os.environ["WEINGAERTEN_HOME"] = ROOT
    shutil.rmtree(temp, ignore_errors=True)

print("%d Fehler" % len(failures) if failures else "alles ok")
sys.exit(1 if failures else 0)
