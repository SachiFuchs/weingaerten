"""Writes the drinking water (Zuwasser) catalog parts and the first kitchen runs (PPR DN 20, cold + hot).

Version 2 (Nov 2026, user sketch): risers cold + hot in the supply shaft beside the waste riser aw-kueche-fall from the
basement (open ends with caps, z -0.30) up to the DG (closed stubs for the later DG bathroom). EG mains branch off the
risers with T-pieces and run 5 cm in front of the inner face of w-east (x 6.792 - 0.05) north into the bathroom,
hot above (z 0.25), cold below (z 0.20) above the raw EG floor. Sink, shower, washbasin (hot + cold) and WC (cold)
branch off the mains with T-pieces up to PP-R wall plates. Every branch run ends on the axis of its feeding run.
Crossings are NOT in the data: the core inserts the 45° loops.
Run: python scripts/build_water_supply_data.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPONENTS = os.path.join(ROOT, "catalog", "tga-components")
MATERIALS = os.path.join(ROOT, "catalog", "materials")
TGA = os.path.join(ROOT, "house", "tga")
DIN = "412"
ESTIMATED = "Baulänge z geschätzt (Muffenschweiß-Formteil DN 20) - bitte prüfen"
WALL_X = round(6.792 - 0.05, 3)      # pipe axis 5 cm in front of the inner face of w-east
Z = {"cold": 0.20, "hot": 0.25}
Z_PLATE, Z_SHOWER, Z_BASEMENT, Z_DG = 0.50, 1.10, -0.30, 2.95 + 0.30
Y_RISER = {"cold": 4.93, "hot": 5.03}  # beside the waste riser (x 6.65, y 5.00), 10 cm apart, inside the basement
Y_BASIN = 2.08 - 0.05                    # 5 cm in front of the bath face of the wall bath / kitchen
PPR_MATERIALS = ("pp-r-ventil-set-dn-20-handrad", "pp-r-schweisswinkel-dn-20-90", "pp-r-schweissmuffe-dn-20",
                 "pp-r-schweiss-wandscheibe-dn-20-ig-1-2", "pp-r-schweiss-uebergangsstueck-dn-20-ig-1-2",
                 "pp-r-schweiss-uebergangsstueck-dn-20-ag-1-2", "pp-r-schweiss-kugelhahn-dn-20",
                 "pp-r-schweiss-endkappe-dn-20", "pp-r-montageeinheit-dn-20-ig-1-2")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def update(cid, change):
    path = os.path.join(COMPONENTS, cid + ".json")
    data = read(path)
    change(data)
    write(path, data)


def fix_imported():
    # the OBI pipe is DN 20 (name), the OBI 45° elbow becomes a real fitting of the PPR line
    def pipe(data):
        data["params"].update({"nominal_size_dn": 20, "system_line": "ppr"})
        data["note"] = "Baumarkt-Artikel (Import); Medium je Leitung (kalt/warm) in tga-run.medium"

    def elbow(data):
        data["class"] = "tga-class:pipe-fitting"
        data["params"] = {"fitting_type": "bend", "system_line": "ppr", "dn": 20, "angle": 45, "z_length": 0.005}
        data["estimated"] = True
        data["note"] = ESTIMATED
    update("ppr-rohr-dn-20-x-2-m", pipe)
    update("ppr-winkel-45deg-dn-20", elbow)
    for mid in PPR_MATERIALS:
        path = os.path.join(MATERIALS, mid + ".json")
        if os.path.isfile(path):
            data = read(path)
            data["category"] = "Trinkwasser"
            write(path, data)


def catalog():
    items = [
        {"id": "ppr-bend-20-90", "name": "PP-R Schweißwinkel DN 20 90°", "class": "tga-class:pipe-fitting",
         "din276": DIN, "system_type": "Trinkwasser", "estimated": True,
         "params": {"fitting_type": "bend", "system_line": "ppr", "dn": 20, "angle": 90, "z_length": 0.011},
         "note": ESTIMATED + "; Artikel = Material pp-r-schweisswinkel-dn-20-90"},
        {"id": "ppr-cap-20", "name": "PP-R Schweiß-Endkappe DN 20", "class": "tga-class:pipe-fitting",
         "din276": DIN, "system_type": "Trinkwasser", "estimated": True,
         "params": {"fitting_type": "plug", "system_line": "ppr", "dn": 20, "z_length": 0.0},
         "note": "offenes Ende im Keller bis zum Anschluss; Artikel = Material pp-r-schweiss-endkappe-dn-20"},
        {"id": "ppr-wall-plate-20", "name": "PP-R Schweiß-Wandscheibe DN 20, IG ½″", "class": "tga-class:terminal",
         "din276": DIN, "system_type": "Trinkwasser",
         "params": {"terminal_type": "wall_plate", "mounting": "surface"},
         "note": "Artikel = Material pp-r-schweiss-wandscheibe-dn-20-ig-1-2"},
        {"id": "ppr-tee-20", "name": "PP-R Schweiß-T-Stück DN 20", "class": "tga-class:pipe-fitting",
         "din276": DIN, "system_type": "Trinkwasser", "estimated": True,
         "params": {"fitting_type": "branch", "system_line": "ppr", "dn": 20, "dn_branch": 20, "angle": 90,
                    "z_length": 0.011},
         "note": "Platzhalter: Schweiß-T-Stück DN 20/20 nicht im Sortiment (nur PPR-T-Stück mit Rp ½) - bitte bestätigen"},
        {"id": "water-stub", "name": "Anschluss Trinkwasser verschlossen", "class": "tga-class:terminal",
         "din276": DIN, "system_type": "Trinkwasser", "params": {"terminal_type": "stub", "mounting": "free"}},
        {"id": "water-transfer", "name": "Übergabe Trinkwasser (offenes Ende)", "class": "tga-class:terminal",
         "din276": DIN, "system_type": "Trinkwasser", "params": {"terminal_type": "transfer", "mounting": "free"}},
    ]
    for item in items:
        write(os.path.join(COMPONENTS, item["id"] + ".json"), item)
    return len(items)


MEDIUM = {"cold": "cold_water", "hot": "hot_water"}
LABEL = {"cold": "Kaltwasser", "hot": "Warmwasser"}
X = WALL_X


def run(rid, name, kind, points, system, into=None, **extra):
    data = {"id": rid, "name": "%s %s" % (LABEL[kind], name), "component": "tga-component:ppr-rohr-dn-20-x-2-m",
            "system": system, "medium": MEDIUM[kind], "installation": "surface", "points": points, "estimated": True}
    if into:
        data["into"] = {"run": "tga-run:" + into, "kind": "branch"}
    note = extra.pop("note", None)
    data.update({("from" if k == "from_" else k): "tga-terminal:" + v for k, v in extra.items()})
    if note:
        data["note"] = note
    return data


def branch(rid, name, kind, plate, main, along):
    # from a wall plate down to the main: `along` = "y" (east wall) or "x" (wall bath / kitchen)
    z = Z[kind]
    if along == "y":
        points = [[X, plate[1], plate[2]], [X, plate[1], z]]
    else:
        points = [[plate[0], Y_BASIN, plate[2]], [plate[0], Y_BASIN, z], [X, Y_BASIN, z]]
    return run(rid, name, kind, points, "drinking-water-eg", into=main, from_="ws-" + rid[3:])


def runs():
    items = []
    for kind in ("cold", "hot"):
        y = Y_RISER[kind]
        items.append(run("tw-steig-" + kind, "Steigleitung Keller bis DG", kind,
                         [[X, y, Z_BASEMENT], [X, y, Z_DG]], "drinking-water",
                         from_="tw-uebergabe-kg-" + kind, to="tw-stutzen-dg-" + kind,
                         note="im Versorgungsschacht neben dem Fallrohr; DG-Ende verschlossen für das spätere Bad"))
    # EG mains from the bath end back to the riser; the cold main starts at the WC, the hot one at the shower
    items.append(run("tw-eg-cold", "EG Hauptleitung (WC bis Steigleitung)", "cold",
                     [[X, 0.65, Z_PLATE], [X, 0.65, Z["cold"]], [X, Y_RISER["cold"], Z["cold"]]],
                     "drinking-water-eg", into="tw-steig-cold", from_="ws-wc-cold"))
    items.append(run("tw-eg-hot", "EG Hauptleitung (Dusche bis Steigleitung)", "hot",
                     [[X, 1.63, Z_SHOWER], [X, 1.63, Z["hot"]], [X, Y_RISER["hot"], Z["hot"]]],
                     "drinking-water-eg", into="tw-steig-hot", from_="ws-dusche-hot"))
    items.append(branch("tw-dusche-cold", "Dusche", "cold", [X, 1.73, Z_SHOWER], "tw-eg-cold", "y"))
    items.append(branch("tw-spuele-hot", "Spüle", "hot", [X, 3.85, Z_PLATE], "tw-eg-hot", "y"))
    items.append(branch("tw-spuele-cold", "Spüle", "cold", [X, 3.95, Z_PLATE], "tw-eg-cold", "y"))
    items.append(branch("tw-wb-hot", "Waschbecken", "hot", [4.60, Y_BASIN, Z_PLATE], "tw-eg-hot", "x"))
    items.append(branch("tw-wb-cold", "Waschbecken", "cold", [4.70, Y_BASIN, Z_PLATE], "tw-eg-cold", "x"))
    return items


def terminals():
    def plate(tid, name, kind, room, wall, position):
        return {"id": tid, "name": "Wandscheibe %s %s" % (LABEL[kind], name), "component": "tga-component:ppr-wall-plate-20",
                "storey": "storey:ground", "room": room, "wall": wall, "position": position, "estimated": True}
    items = [plate("ws-wc-cold", "WC (Spülkasten)", "cold", "room-bad", "w-east", [X, 0.65, Z_PLATE]),
             plate("ws-dusche-hot", "Dusche", "hot", "room-bad", "w-east", [X, 1.63, Z_SHOWER]),
             plate("ws-dusche-cold", "Dusche", "cold", "room-bad", "w-east", [X, 1.73, Z_SHOWER]),
             plate("ws-spuele-hot", "Spüle", "hot", "room-kueche", "w-east", [X, 3.85, Z_PLATE]),
             plate("ws-spuele-cold", "Spüle", "cold", "room-kueche", "w-east", [X, 3.95, Z_PLATE]),
             plate("ws-wb-hot", "Waschbecken", "hot", "room-bad", "iw-alt-nord-ost", [4.60, Y_BASIN, Z_PLATE]),
             plate("ws-wb-cold", "Waschbecken", "cold", "room-bad", "iw-alt-nord-ost", [4.70, Y_BASIN, Z_PLATE])]
    for kind in ("cold", "hot"):
        items.append({"id": "tw-uebergabe-kg-" + kind, "name": "Übergabe %s Keller (offen)" % LABEL[kind],
                      "component": "tga-component:water-transfer", "storey": "storey:basement", "room": "room-keller",
                      "position": [X, Y_RISER[kind], Z_BASEMENT], "estimated": True})
        items.append({"id": "tw-stutzen-dg-" + kind, "name": "Anschluss %s DG (verschlossen)" % LABEL[kind],
                      "component": "tga-component:water-stub", "storey": "storey:upper", "room": "room-dg-bad",
                      "position": [X, Y_RISER[kind], Z_DG], "estimated": True})
    return items


def house_data():
    # version 1 files (kitchen only) are replaced
    for name in ("runs/tw-kueche-cold", "runs/tw-kueche-hot", "terminals/ws-kueche-cold", "terminals/ws-kueche-hot"):
        path = os.path.join(TGA, *name.split("/")) + ".json"
        if os.path.isfile(path):
            os.remove(path)
    items = runs()
    for item in items:
        write(os.path.join(TGA, "runs", item["id"] + ".json"), item)
    for item in terminals():
        write(os.path.join(TGA, "terminals", item["id"] + ".json"), item)
    return len(items)


if __name__ == "__main__":
    fix_imported()
    print("components:", catalog())
    print("runs:", house_data())
