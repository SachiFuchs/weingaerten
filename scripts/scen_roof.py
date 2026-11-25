"""Scenario test roof (Testhaus DG): gable/knee walls following the roof, Dachstuhl members, Dachdeckung faces/area/edges/
items, roof window in BOM, pitch change, error variants.

Runs in a sandbox (fixture tests/fixtures/testhaus + catalog copy); original data is never touched.
Hand-calculated: half width 3.0, pitch 30 -> ridge 1.25 + 3 tan30 above the DG floor (2.95); overhangs 0.5.
"""
import math

from sandbox import Checks, Sandbox

T = Checks("scen_roof")
TAN, COS = math.tan(math.radians(30)), math.cos(math.radians(30))
RIDGE = 1.25 + 3.0 * TAN


def upper(sb):
    return next(s for s in sb.q("HOUSE")["storeys"] if s["id"] == "upper")


def errors_of(change):
    with Sandbox() as sb:
        sb.edit_storey("upper", change)
        return [e["message"] for e in sb.q("VALIDATE")["errors"]]


with Sandbox() as sb:
    up = upper(sb)
    W = {w["id"]: w for w in up["walls"]}

    # --- walls follow the roof
    T.near(W["w-dg-north"]["height"], RIDGE, "Giebel Nord bis First")
    T.near(W["w-dg-south"]["z1"], 2.95 + RIDGE, "Giebel Süd Oberkante")
    T.near(W["w-dg-east"]["height"], 1.25, "Kniestock Ost")
    T.near(W["w-dg-west"]["z1"], 4.2, "Kniestock West Oberkante")
    gable = sum(L["volume"] for L in W["w-dg-north"]["layers"] if L["material"] == "material:hollow-brick")
    T.near(gable, 3.6791, "Ziegel Giebel Nord (Fünfeck, Gehrung)", 2e-3)
    T.ok(len(W["w-dg-north"]["layers"][0]["pieces"]) == 2, "Giebel geteilt am First (2 Stücke)")

    # --- Dachstuhl
    rs = up["roof_structure"]
    T.ok(rs["counts"] == {"rafter": 20, "purlin": 2, "foot_purlin": 2, "collar": 10, "ridge_purlin": 0}, "Anzahl Hölzer %s" % rs["counts"])
    M = {m["id"]: m for m in rs["members"]}
    rafters = [m for m in rs["members"] if m["kind"] == "rafter"]
    T.ok(all(abs(m["length"] - 3.0 / COS) < 2e-3 for m in rafters), "Sparrenlänge 3.0/cos30 %s" % rafters[0]["length"])
    T.near(rafters[0]["volume"], 0.08 * 0.16 * rafters[0]["length"], "Sparrenvolumen b·h·l", 1e-4)
    p = M["purlin-west"]
    T.near(sum(q[0] for q in p["footprint"]) / 4, 0.85 / TAN, "Mittelpfette West x", 2e-3)
    T.near(p["z0"], 4.85, "Mittelpfette z0")
    T.near(p["z1"], 5.05, "Mittelpfette z1")
    T.near(p["length"], 8.0, "Mittelpfette Länge")
    f = M["foot-purlin-west"]
    T.near(sum(q[0] for q in f["footprint"]) / 4, 0.164, "Fußpfette auf Kniestock-Mitte", 2e-3)
    T.near(f["z0"], 4.2, "Fußpfette z0")
    c = M["collar-1"]
    T.near(c["z0"], 5.35, "Kehlbalken z0")
    T.near(c["length"], 6.0 - 2 * (1.23 / TAN), "Kehlbalken Länge", 2e-3)
    bom = sb.q("BOM")
    T.near(bom["totals"]["roof_structure_volume"], sum(m["volume"] for m in rs["members"]), "BOM Dachstuhl-Volumen", 2e-3)

    # --- Dachdeckung
    rc = up["roof_covering"]
    faces = {x["id"]: x for x in rc["faces"]}
    T.ok(faces["west"]["across"] == [-0.5, 3.0], "Fläche West quer %s" % faces["west"]["across"])
    T.near(faces["west"]["along"][0], -0.5, "Ortgang-Überstand Nord")
    T.near(faces["east"]["along"][1], 8.5, "Ortgang-Überstand Süd")
    T.near(faces["east"]["across"][1], 6.5, "Traufe Ost")
    T.near(rc["area"], 2 * 3.5 * 9.0 / COS, "Dachfläche brutto", 2e-3)
    T.near(rc["thickness"], 0.2305, "Dicke roof-r1")
    T.ok(faces["west"]["layers"][0]["material"] == "material:clay-tile-rubin", "Ziegel oben")
    T.near(faces["west"]["base_plane"][2] - 4.2, 0.16 / COS, "Deckung auf Sparrenoberkante", 2e-3)
    win = next(o for o in rc["openings"] if o["id"] == "dfe-west")
    T.near(win["area"], 0.55 * 0.98, "Dachfenster-Fläche")
    T.near(rc["area_net"], rc["area"] - win["area"], "Dachfläche netto", 2e-3)
    T.near(rc["edges"]["eaves"], 18.0, "Traufe 2 x 9 m")
    T.near(rc["edges"]["ridge"], 9.0, "First 9 m")
    items = {i["component"]: i for i in rc["items"]}
    T.near(items["component:roof-gutter"]["quantity"], 18.0, "Rinne = Traufe")
    T.near(items["component:roof-ridge"]["quantity"], 9.0, "Firstziegel = First")
    T.near(bom["totals"]["roof_area"], rc["area_net"], "BOM roof_area", 2e-3)
    comps = {x["component"]: x["count"] for x in bom["components"]}
    T.ok(comps.get("component:roof-window-velux-ck04") == 1 and comps.get("component:roof-flashing-velux-ck04") == 1,
         "BOM Dachfenster + Eindeckrahmen %s" % comps)

    # --- pitch 45: ridge = knee + 3.0
    sb.edit_storey("upper", lambda d: d["roof"].update(pitch=45))
    up = upper(sb)
    T.near(next(w for w in up["walls"] if w["id"] == "w-dg-north")["height"], 1.25 + 3.0, "45°: Giebelhöhe")
    T.near(up["roof_covering"]["area"], 2 * 3.5 * 9.0 / math.cos(math.radians(45)), "45°: Dachfläche", 2e-3)

# --- invalid variants
for label, change, expected in (
        ("Dach fehlt", lambda d: d.pop("roof"), "Dachdeckung ohne Dach"),
        ("falscher Aufbau", lambda d: d["roof_covering"].update(assembly="assembly:exterior-wall-ew1"), "kein Dachaufbau"),
        ("Überstand negativ", lambda d: d["roof_covering"].update(eaves_overhang=-1), "Überstand ungültig"),
        ("Fenster unter Kniestock", lambda d: d["roof_covering"]["openings"][0].update(sill=1.0), "Unterkante unter dem Kniestock"),
        ("Fenster außerhalb", lambda d: d["roof_covering"]["openings"][0].update(y=30), "außerhalb der Dachfläche"),
        ("Sparrenabstand 0", lambda d: d["roof_structure"]["rafters"].update(spacing=0), "Maße ungültig"),
        ("Material unbekannt", lambda d: d["roof_structure"].update(material="material:nope"), "unbekannt: material:nope")):
    msgs = errors_of(change)
    T.ok(any(expected in m for m in msgs), "Fehler '%s': %s" % (label, msgs[:3]))

T.finish()
