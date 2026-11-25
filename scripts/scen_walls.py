"""Scenario test walls (Testhaus EG): geometry, mitre corners, T-joints, opening holes/pieces, OPENING_SAVE/DELETE,
WALLS_SAVE (move, split, height, delete, 90° rule, overlap), absolute opening positions, error variants.

Runs in a sandbox (fixture tests/fixtures/testhaus + catalog copy); original data is never touched.
Hand-calculated: ew1 brick 0.30 at offset 0.015 -> mitred band (L-0.03 + L-0.63)/2 x 0.30 x 2.75;
window-eg-kueche rough 0.92 x 1.03, door-dg-durchgang rough 0.82 x 2.02, window-wz-gross (3 Flügel) rough 2.99 x 1.195 (Ost),
door-d1 rough 1.07 x 2.03 (Süd), door-balkon-rehau-synego rough 1.06 x 2.24 (West).
"""
import copy

from sandbox import Checks, Sandbox

T = Checks("scen_walls")
H = 2.75
EAST_HOLE = 2.99 * 1.195 * 0.30
SOUTH_HOLE = 1.07 * 2.03 * 0.30
WEST_HOLE = 1.06 * 2.24 * 0.30


def band(length):
    return ((length - 0.03) + (length - 0.63)) / 2 * 0.30 * H


def walls(sb, storey="ground"):
    st = next(s for s in sb.q("HOUSE")["storeys"] if s["id"] == storey)
    return {w["id"]: w for w in st["walls"]}


def brick(w):
    return sum(L["volume"] for L in w["layers"] if L["material"] == "material:hollow-brick")


def raw(sb):
    return {w["id"]: copy.deepcopy(w) for w in sb.read("house", "storeys", "ground.json")["walls"]}


def shape(w, **kw):
    out = {k: v for k, v in w.items() if k != "openings"}
    out.update(kw)
    return out


def ground_text(sb):
    return open(sb.path("house", "storeys", "ground.json"), encoding="utf-8").read()


with Sandbox() as sb:
    # --- geometry of the fixture
    W = walls(sb)
    for wid, length in (("w-north", 6), ("w-east", 8), ("w-south", 6), ("w-west", 8)):
        T.near(W[wid]["length"], length, "Länge %s" % wid)
        T.near(W[wid]["thickness"], 0.328, "Dicke %s" % wid)
        T.near(W[wid]["height"], H, "Höhe %s" % wid)
        T.ok(not W[wid]["free_ends"], "keine freien Enden %s" % wid)
    T.near(brick(W["w-north"]), band(6) - 0.92 * 1.03 * 0.30, "Ziegel Nord (Gehrung, Fensterloch)")
    T.near(brick(W["w-east"]), band(8) - EAST_HOLE, "Ziegel Ost (3er-Fenster, T-Stoß zieht nichts ab)")
    T.near(brick(W["w-south"]), band(6) - SOUTH_HOLE, "Ziegel Süd (Haustür)")
    T.near(brick(W["w-west"]), band(8) - WEST_HOLE, "Ziegel West (Balkontür)")
    T.near(brick(W["iw-mitte"]), 5.344 * 0.10 * H - 0.82 * 2.02 * 0.10, "Ziegel Innenwand mit Tür")
    T.ok(all(len(L["pieces"]) == 4 for L in W["w-north"]["layers"]), "Nord: 4 Stücke je Schicht (links/rechts/unten/oben)")
    T.ok(all(len(L["pieces"]) == 3 for L in W["iw-mitte"]["layers"]), "Innenwand: 3 Stücke je Schicht (Tür)")
    T.ok(all(len(L["pieces"]) == 3 for L in W["w-south"]["layers"]), "Süd: 3 Stücke je Schicht (Tür)")
    T.ok(all(len(L["pieces"]) == 4 for L in W["w-east"]["layers"]), "Ost: 4 Stücke je Schicht (Fenster)")
    T.ok(W["iw-kammer"]["footprint"][0] == [4.56, 4.06], "T-Stoß an der Wandfläche getrimmt %s" % W["iw-kammer"]["footprint"])
    T.ok(W["iw-kammer"]["u_range"]["left"] == [0.06, 1.94], "T-Stoß u_range %s" % W["iw-kammer"]["u_range"])
    T.near(W["iw-kammer-sued"]["footprint"][1][0], 5.672, "Innenwand endet an der Innenseite Ost")
    o = W["w-north"]["openings"][0]
    T.near(o["rough"]["width"], 0.92, "Rohbaubreite Fenster")
    T.near(o["rough"]["height"], 1.03, "Rohbauhöhe Fenster")
    T.ok(any(p["kind"] == "glass" for p in o["parts"]), "Fenster hat Glas")
    T.ok(any(p["kind"] == "leaf" for p in W["iw-mitte"]["openings"][0]["parts"]), "Tür hat Blatt")
    east = W["w-east"]["openings"][0]
    T.near(east["rough"]["width"], 2.99, "Rohbaubreite 3er-Fenster")
    T.ok(sum(1 for p in east["parts"] if p["kind"] == "glass") == 3, "3er-Fenster hat 3 Gläser")
    T.ok(any(p["kind"] == "leaf" for p in W["w-south"]["openings"][0]["parts"]), "Haustür hat Blatt")
    T.ok(any(p["kind"] == "glass" for p in W["w-west"]["openings"][0]["parts"]), "Balkontür hat Glas")
    bom = sb.q("BOM")
    rows = {r["wall"]: r for r in bom["walls"]}
    T.ok(rows["w-north"]["openings"] == 1 and rows["w-east"]["openings"] == 1 and rows["w-south"]["openings"] == 1
         and rows["w-west"]["openings"] == 1, "BOM Öffnungen je Wand")
    T.near(rows["w-north"]["length_inside"], 5.344, "BOM Innenlänge Nord")
    cc = {c["component"]: c["count"] for c in bom["components"]}
    T.ok(cc.get("component:window-eg-kueche") == 1 and cc.get("component:door-dg-durchgang") == 1
         and cc.get("component:window-wz-gross") == 1 and cc.get("component:door-d1") == 1
         and cc.get("component:door-balkon-rehau-synego") == 1, "BOM Bauteile %s" % cc)
    T.near(bom["totals"]["opening_area"], 0.92 * 1.03 + 0.82 * 2.02 + 0.55 * 0.98 + 2.99 * 1.195 + 1.07 * 2.03 + 1.06 * 2.24,
           "BOM Öffnungsfläche", 2e-3)
    plaster = next(m for m in bom["materials"] if m["material"] == "material:interior-plaster")
    T.ok(plaster.get("area_reveal", 0) > 0, "Leibung wird gezählt")

    # --- openings: move, out of the wall, overlap, delete
    before = brick(W["w-north"])
    op = copy.deepcopy(raw(sb)["w-north"]["openings"][0])
    T.ok("error" not in sb.q("OPENING_SAVE", storey="ground", wall="w-north", opening=dict(op, offset=3.0), create=False),
         "Fenster verschieben")
    T.near(brick(walls(sb)["w-north"]), before, "Volumen nach Verschieben gleich")
    text = ground_text(sb)
    r = sb.q("OPENING_SAVE", storey="ground", wall="w-north", opening=dict(op, offset=5.5), create=False)
    T.ok("ragt über die Wand" in r.get("error", "") and ground_text(sb) == text, "Fenster außerhalb abgelehnt %s" % r)
    r = sb.q("OPENING_SAVE", storey="ground", wall="w-north", opening=dict(op, id="o-2", offset=3.5), create=True)
    T.ok("überlappen" in r.get("error", ""), "Überlappung abgelehnt %s" % r)
    T.ok("error" not in sb.q("OPENING_SAVE", storey="ground", wall="w-south", opening=dict(op, id="o-sued", offset=1.0),
                             create=True), "Fenster Süd anlegen")
    T.near(brick(walls(sb)["w-south"]), band(6) - SOUTH_HOLE - 0.92 * 1.03 * 0.30, "Süd mit Fenster- und Türloch")
    T.ok(sb.q("OPENING_DELETE", storey="ground", wall="w-south", id="o-sued").get("deleted"), "Fenster löschen")
    T.near(brick(walls(sb)["w-south"]), band(6) - SOUTH_HOLE, "Süd wieder nur mit Tür")

    # --- WALLS_SAVE: split south wall at x=1.5 (door x 2.43..3.5 stays on the first part), volume stays
    R = raw(sb)
    s1 = shape(R["w-south"], end=[1.5, 8])
    s2 = shape(R["w-south"], id="w-south-2", name="Außenwand Süd 2", start=[1.5, 8], end=[0, 8])
    r = sb.q("WALLS_SAVE", storey="ground", upsert=[s1, s2])
    W = walls(sb)
    T.ok("error" not in r and "w-south-2" in W, "Wand teilen %s" % r.get("error"))
    T.near(W["w-south"]["length"] + W["w-south-2"]["length"], 6, "Summe Teillängen")
    T.near(brick(W["w-south"]) + brick(W["w-south-2"]), band(6) - SOUTH_HOLE, "Volumen nach Teilen gleich", 2e-3)
    T.ok([o["id"] for o in W["w-south"]["openings"]] == ["o-haustuer"] and not W["w-south-2"]["openings"],
         "Haustür bleibt auf dem ersten Teil")
    T.ok(not W["w-south"]["free_ends"] and not W["w-south-2"]["free_ends"], "Teilstücke ohne freie Enden")
    T.ok("ceilings" in sb.read("house", "storeys", "ground.json"), "WALLS_SAVE behält Decken")

    # --- move west wall outward by 0.5: window keeps its absolute position (offset + 0.5)
    R = raw(sb)
    r = sb.q("WALLS_SAVE", storey="ground", upsert=[shape(R["w-west"], start=[-0.5, 8], end=[-0.5, 0]),
                                                    shape(R["w-north"], start=[-0.5, 0]),
                                                    shape(R["w-south-2"], end=[-0.5, 8])])
    T.ok("error" not in r, "Westwand verschieben %s" % r.get("error"))
    T.near(raw(sb)["w-north"]["openings"][0]["offset"], 3.5, "Fenster bleibt absolut (Offset 3.0 -> 3.5)")
    T.near(next(o for o in raw(sb)["w-west"]["openings"])["offset"], 1.5, "Balkontür: Wand nur verschoben, Offset bleibt")
    T.near(walls(sb)["w-north"]["length"], 6.5, "Nordwand 6.5 m")
    T.near(sb.q("BOM")["totals"]["foundation_volume"], 6.5 * 8 * 0.25, "Fundament folgt dem Umriss")

    # --- rejected: diagonal, duplicate overlap
    R = raw(sb)
    text = ground_text(sb)
    r = sb.q("WALLS_SAVE", storey="ground", upsert=[shape(R["w-west"], start=[-1, 8])])
    T.ok("90°-Raster" in str(r.get("error", "")) + str(r), "schräge Wand abgelehnt %s" % r.get("error"))
    r = sb.q("WALLS_SAVE", storey="ground", upsert=[shape(R["w-east"], id="w-dup", name="Doppelt")])
    T.ok("error" in r and ground_text(sb) == text, "überlappende Wand abgelehnt")

    # --- storey height 2.0: the 2.02 m door no longer fits -> conflict, but saved
    r = sb.q("WALLS_SAVE", storey="ground", height=2.0)
    T.ok("error" not in r and {c["opening"] for c in r.get("opening_conflicts", [])} >= {"o-tuer", "o-haustuer", "o-balkontuer"},
         "Tür-Konflikte bei 2.0 m %s" % r.get("opening_conflicts"))
    T.near(walls(sb)["w-east"]["height"], 2.0, "Wandhöhe 2.0")
    sb.q("WALLS_SAVE", storey="ground", height=H)

    # --- delete an interior wall
    T.ok("error" not in sb.q("WALLS_SAVE", storey="ground", delete=["iw-kammer-sued"]), "Wand löschen")
    T.ok("iw-kammer-sued" not in walls(sb), "Wand weg")

# --- invalid data variants (each on a fresh sandbox)
def variant(edit):
    with Sandbox() as sb:
        sb.edit_storey("ground", edit)
        return sb.q("VALIDATE")


def by_id(d, wid):
    return next(w for w in d["walls"] if w["id"] == wid)


def has(v, text, where=None):
    return any(text in e["message"] and (where is None or where in e["where"]) for e in v["errors"])


v = variant(lambda d: by_id(d, "w-east").update(assembly="assembly:gibt-es-nicht"))
T.ok(has(v, "assembly:gibt-es-nicht", "w-east"), "unbekannter Aufbau erkannt")
v = variant(lambda d: by_id(d, "w-east").pop("outside"))
T.ok(has(v, "outside fehlt"), "outside fehlt erkannt")
v = variant(lambda d: by_id(d, "w-east").update(end=[6, 7]))
T.ok(any("offenes Wandende" in w["message"] for w in v["warnings"]), "offenes Wandende erkannt")
v = variant(lambda d: by_id(d, "w-north")["openings"][0].update(component="component:roof-ridge"))
T.ok(has(v, "nicht für Öffnungen geeignet") or has(v, "roof-ridge"), "ungeeignetes Bauteil erkannt %s" % v["errors"][:2])

T.finish()
