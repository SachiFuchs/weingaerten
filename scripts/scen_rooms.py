"""Scenario test rooms (Testhaus): polygon areas incl. L-room, heights/volumes, coverings (whole room, zone, skirting),
ROOM_SAVE/DELETE, WALLS_SAVE keeping coverings, shafts and the expected warnings.

Runs in a sandbox (fixture tests/fixtures/testhaus + catalog copy); original data is never touched.
Hand-calculated values: inner area 5.344 x 7.344 m, iw1 = 0.12 m at y 4.0 -> rooms end at 3.94 / start at 4.06.
"""
import copy

from sandbox import Checks, Sandbox

T = Checks("scen_rooms")
NORD = 5.344 * 3.612
KAMMER = 1.112 * 1.88
SUED = NORD - 1.232 * 2.0
DG = 5.344 * 7.344
EXPECTED_WARNINGS = {
    ("storey:ground.w-east", "Wandfläche ohne Raum (3.612–3.732 m)"),
    ("storey:ground.w-east", "Wandfläche ohne Raum (5.612–5.732 m)"),
    ("storey:ground.w-west", "Wandfläche ohne Raum (3.612–3.732 m)"),
    ("storey:ground.iw-mitte", "Wandfläche ohne Raum (4.112–4.232 m)"),
    ("house.shafts.schacht-test", "Schacht liegt in upper nicht vollständig in einem Boden"),
    ("house.shafts.schacht-test", "Deckenbalken von c-eg im Schacht – Wechsel nötig"),
}


def rooms(sb, storey="ground"):
    st = next(s for s in sb.q("HOUSE")["storeys"] if s["id"] == storey)
    return {r["id"]: r for r in st["rooms"]}


def room_json(sb, room_id, storey="ground"):
    return copy.deepcopy(next(r for r in sb.read("house", "storeys", storey + ".json")["rooms"] if r["id"] == room_id))


def save(sb, room, create=False):
    return sb.q("ROOM_SAVE", storey="ground", room=room, create=create)


with Sandbox() as sb:
    v = sb.q("VALIDATE")
    T.ok(v["ok"] and not v["errors"], "Testhaus gültig: %s" % v["errors"])
    got = {(w["where"], w["message"]) for w in v["warnings"]}
    T.ok(got == EXPECTED_WARNINGS, "Warnungen: neu %s, fehlen %s" % (got - EXPECTED_WARNINGS, EXPECTED_WARNINGS - got))
    T.ok(v["counts"]["rooms"] == 4 and v["counts"]["coverings"] == 2 and v["counts"]["shafts"] == 1, "counts %s" % v["counts"])

    # --- areas, perimeter, heights, volumes
    R = rooms(sb)
    T.near(R["room-nord"]["area"], NORD, "Fläche Raum Nord")
    T.near(R["room-sued"]["area"], SUED, "Fläche L-Raum")
    T.near(R["room-kammer"]["area"], KAMMER, "Fläche Kammer")
    T.ok(len(R["room-sued"]["polygon"]) == 6, "L-Raum hat 6 Punkte")
    T.near(R["room-nord"]["perimeter"], 2 * (5.344 + 3.612), "Umfang Raum Nord")
    T.near(R["room-sued"]["perimeter"], 2 * (5.344 + 3.612), "Umfang L-Raum")
    for r in R.values():
        T.near(r["height"], 2.75, "Höhe %s" % r["id"])
        T.near(r["volume"], r["area"] * 2.75, "Volumen %s" % r["id"], 1e-3)
    T.near(rooms(sb, "upper")["room-dg"]["area"], DG, "Fläche Dachraum")
    totals = sb.q("BOM")["totals"]
    T.near(totals["room_area"], NORD + SUED + KAMMER + DG, "BOM room_area")
    T.near(totals["room_volume"], (NORD + SUED + KAMMER) * 2.75 + DG * 2.4, "BOM room_volume", 2e-3)
    T.near(totals["covering_floor_area"], NORD + KAMMER, "BOM covering_floor_area")

    # --- shaft: only the EG ceiling is cut (from upper floor down to the ground ceiling)
    shaft = next(s for s in sb.q("HOUSE")["shafts"] if s["id"] == "schacht-test")
    T.ok(sorted((c["storey"], c["kind"]) for c in shaft["cuts"]) == [("ground", "ceiling")], "Schacht-Schnitte %s" % shaft["cuts"])
    T.near(totals["shaft_cut_area"], 0.372 * 0.372, "BOM shaft_cut_area")

    # --- polygon edit: room Nord gets shorter, covering follows
    nord = room_json(sb, "room-nord")
    nord["polygon"] = [[0.328, 0.328], [5.672, 0.328], [5.672, 3.0], [0.328, 3.0]]
    T.ok("error" not in save(sb, nord), "ROOM_SAVE Polygon")
    R = rooms(sb)
    T.near(R["room-nord"]["area"], 5.344 * 2.672, "Fläche nach Änderung")
    T.near(R["room-nord"]["coverings"][0]["area"], 5.344 * 2.672, "Belag folgt dem Polygon")

    # --- zone + whole-room covering in the L-room, skirting in the Kammer
    sued = room_json(sb, "room-sued")
    sued["coverings"] = [
        {"id": "bel-sued", "surface": "floor", "assembly": "assembly:covering-parkett-eiche", "area": "room"},
        {"id": "bel-sued-feld", "surface": "floor", "assembly": "assembly:covering-fliese-boden",
         "area": [[1.0, 5.0], [2.0, 5.0], [2.0, 6.0], [1.0, 6.0]]}]
    T.ok("error" not in save(sb, sued), "ROOM_SAVE Beläge L-Raum")
    by = {c["id"]: c for c in rooms(sb)["room-sued"]["coverings"]}
    T.near(by["bel-sued-feld"]["area"], 1.0, "Zonenbelag 1 m²")
    T.near(by["bel-sued"]["area"], SUED - 1.0, "Raumbelag = Raum minus Zone")
    kammer = room_json(sb, "room-kammer")
    kammer["coverings"].append({"id": "sockel", "surface": "wall", "assembly": "assembly:covering-sockelleiste-kiefer",
                                "walls": "all", "z": [0, 0.06]})
    T.ok("error" not in save(sb, kammer), "ROOM_SAVE Sockelleiste")
    skirt = next(c for c in rooms(sb)["room-kammer"]["coverings"] if c["id"] == "sockel")
    T.near(skirt["length"], 2 * (1.112 + 1.88), "Sockelleiste = Umfang Kammer (keine Tür)", 1e-3)
    T.near(skirt["area"], skirt["length"] * 0.06, "Sockelleiste Fläche", 1e-3)

    # --- rejected edits leave the file unchanged
    before = open(sb.path("house", "storeys", "ground.json"), encoding="utf-8").read()
    bad = copy.deepcopy(sued)
    bad["coverings"].append({"id": "x", "surface": "floor", "assembly": "assembly:covering-fliese-boden",
                             "area": [[1.5, 5.5], [2.5, 5.5], [2.5, 6.5], [1.5, 6.5]]})
    T.ok("überlappen" in save(sb, bad).get("error", ""), "überlappende Zonen abgelehnt")
    bad = copy.deepcopy(sued)
    bad["coverings"][1]["area"] = [[-1.0, 5.0], [2.0, 5.0], [2.0, 6.0], [-1.0, 6.0]]
    T.ok("nicht im Raum" in save(sb, bad).get("error", ""), "Zone außerhalb abgelehnt")
    bad = dict(sued, polygon=[[0.328, 4.06], [4.44, 4.06], [4.0, 6.0], [0.328, 7.672]])
    T.ok("90°" in save(sb, bad).get("error", ""), "schräges Polygon abgelehnt")
    bad = dict(sued, coverings=[{"id": "w", "surface": "floor", "assembly": "assembly:exterior-wall-ew1"}])
    T.ok("kein Belag" in save(sb, bad).get("error", ""), "Nicht-Belag abgelehnt")
    T.ok("error" in save(sb, {"id": "room-x", "name": "X", "polygon": [[-1, -1], [1, -1], [1, 1], [-1, 1]]}, create=True),
         "Raum außerhalb des Umrisses abgelehnt")
    T.ok("error" in sb.q("ROOM_DELETE", storey="ground", id="room-gibts-nicht"), "ROOM_DELETE unbekannt")
    T.ok(open(sb.path("house", "storeys", "ground.json"), encoding="utf-8").read() == before, "Datei nach Fehlern unverändert")

    # --- WALLS_SAVE (plan editor) sends only the shape: coverings and number stay
    shape = {"id": "room-kammer", "name": "Kammer", "polygon": kammer["polygon"]}
    T.ok("error" not in sb.q("WALLS_SAVE", storey="ground", rooms={"upsert": [shape]}), "WALLS_SAVE Raumform")
    kept = room_json(sb, "room-kammer")
    T.ok(len(kept.get("coverings", [])) == 2 and kept.get("number") == "0.03", "WALLS_SAVE behält Beläge/Nummer %s" % kept)

    # --- delete the Kammer
    T.ok(sb.q("ROOM_DELETE", storey="ground", id="room-kammer").get("deleted"), "ROOM_DELETE Kammer")
    T.ok("room-kammer" not in rooms(sb), "Kammer weg")

    # --- shafts: new shaft, upside down, unknown run, delete
    new = {"id": "schacht-2", "name": "Test 2", "polygon": [[1.0, 1.0], [1.3, 1.0], [1.3, 1.3], [1.0, 1.3]],
           "from_storey": "storey:upper", "to_storey": "storey:ground"}
    T.ok("error" not in sb.q("SHAFT_SAVE", shaft=new, create=True), "SHAFT_SAVE")
    T.ok("error" in sb.q("SHAFT_SAVE", shaft=dict(new, from_storey="storey:ground", to_storey="storey:upper"), create=False),
         "Schacht verkehrt herum abgelehnt")
    T.ok("Leitung unbekannt" in sb.q("SHAFT_SAVE", shaft=dict(new, penetrations=["tga-run:nix"]), create=False).get("error", ""),
         "unbekannte Leitung abgelehnt")
    T.ok(sb.q("SHAFT_DELETE", id="schacht-2") == {"deleted": True}, "SHAFT_DELETE")

T.finish()
