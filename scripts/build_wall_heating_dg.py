"""DG wall heating (naturbo Lehm-Wandheizung, laying sketch 260508_01DG_B, quantity sheet MEER):

1. split the Durchgangszimmer into Treppenzimmer (west) and Bad DG (east) with a new partition and door,
2. write `storey.wall_heating`: heating circuits HK01-HK04 (design values from the MEER sheet), 8 panel fields on
   the room faces (panel types and positions from the sketch views), distributor and duct to the basement,
3. move the DG stub terminals (and the generator scripts) to the new room id.

    python scripts/build_wall_heating_dg.py           # dry run: prints the result
    python scripts/build_wall_heating_dg.py --write
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STOREY = ROOT / "house" / "storeys" / "upper.json"
TERMINALS = ["stutzen-dg-kueche", "tw-stutzen-dg-cold", "tw-stutzen-dg-hot"]
SCRIPTS = ["build_waste_water_data.py", "build_water_supply_data.py"]
OLD_ROOM_IDS = ("room-dg-durchgang-ost", "room-dg-durchgang")

# room faces of the DG (inner faces of the walls)
NORTH, SOUTH_SCHLAF, WEST, EAST = 2.408, 9.612, 0.328, 6.792
PART_NORTH, PART_SOUTH = 5.4, 5.52          # faces of iw-dg-durchgang-schlaf
IW_HALF = 0.0605                            # half thickness of assembly interior-wall-iw1
BAD_WIDTH = 2.05                            # naturbo plan
BAD_WEST = round(EAST - BAD_WIDTH, 3)       # 4.742
PARTITION_X = round(BAD_WEST - IW_HALF, 4)  # 4.6815
TREPPE_EAST = round(PARTITION_X - IW_HALF, 3)
Z0 = 0.06                                   # panel bottom above the floor (sketch)
CORNER = 0.07                               # gap in a corner for the lining of the other wall
FEED_Z = 0.03                               # feed lines run in the 6 cm strip below the panels


def panels_dki(u):
    """D (vertical) next to a K-over-I column, starting at u."""
    return [{"type": "D", "u": u, "z": Z0}, {"type": "I", "u": round(u + 0.625, 3), "z": Z0},
            {"type": "K", "u": round(u + 0.625, 3), "z": round(Z0 + 0.625, 3)}]


def panels_glki(u):
    """G-over-L column next to a K-over-I column, starting at u."""
    return [{"type": "L", "u": u, "z": Z0}, {"type": "G", "u": u, "z": round(Z0 + 0.425, 3)},
            {"type": "I", "u": round(u + 1.25, 3), "z": Z0}, {"type": "K", "u": round(u + 1.25, 3), "z": round(Z0 + 0.625, 3)}]


def field(fid, name, circuit, room, wall, origin, direction, panels, port_u, feed):
    return {"id": fid, "name": name, "circuit": circuit, "room": room, "wall": wall, "origin": origin,
            "direction": direction, "panels": panels, "port_u": port_u, "feed": feed}


DIST = [6.762, 5.25]
# feeds from the distributor run along the faces 3 cm in front of them, through the partitions where needed
NORTH_STRIP = PART_NORTH - 0.03
SOUTH_STRIP = PART_SOUTH + 0.03
FIELDS = [
    field("wand-01-west", "01 DA Wand Schlafzimmer (West)", "hk01", "Schlafzimmer", "iw-dg-schlaf-kammer2",
          [EAST, SOUTH_SCHLAF], [-1, 0], panels_glki(3.894), 5.144,
          [DIST, [6.762, SOUTH_STRIP], [WEST + 0.03, SOUTH_STRIP], [WEST + 0.03, SOUTH_SCHLAF - 0.03],
           [EAST - 5.144, SOUTH_SCHLAF - 0.03]]),
    field("wand-02", "02 DA Wand Schlafzimmer (Kniestock West)", "hk01", "Schlafzimmer", "w-dg-west",
          [WEST, SOUTH_SCHLAF], [0, -1], panels_dki(CORNER) + panels_dki(CORNER + 1.875), CORNER + 0.625,
          [DIST, [6.762, SOUTH_STRIP], [WEST + 0.03, SOUTH_STRIP], [WEST + 0.03, round(SOUTH_SCHLAF - CORNER - 0.625, 3)]]),
    field("wand-01-ost", "01 DA Wand Schlafzimmer (Ost)", "hk02", "Schlafzimmer", "w-dg-south-balkon",
          [EAST, SOUTH_SCHLAF], [-1, 0],
          [{"type": "E", "u": CORNER, "z": Z0, "rotated": True},
           {"type": "F", "u": CORNER + 1.05, "z": Z0, "rotated": True},
           {"type": "D", "u": round(CORNER + 2.1, 3), "z": Z0, "rotated": True}], round(CORNER + 3.15, 3),
          [DIST, [6.762, SOUTH_SCHLAF - 0.03], [round(EAST - CORNER - 3.15, 3), SOUTH_SCHLAF - 0.03]]),
    field("wand-03", "03 DA Wand Schlafzimmer (Kniestock Ost)", "hk02", "Schlafzimmer", "w-dg-east",
          [EAST, PART_SOUTH], [0, 1], panels_dki(0.272) + panels_dki(2.147), 0.897,
          [DIST, [6.762, PART_SOUTH + 0.897]]),
    field("wand-04", "04 DA Wand Bad (Nord)", "hk03", "Bad DG", "w-dg-north",
          [BAD_WEST, NORTH], [1, 0], panels_dki(0.1), 0.725,
          [DIST, [6.762, NORTH + 0.03], [round(BAD_WEST + 0.725, 3), NORTH + 0.03]]),
    field("wand-05", "05 DA Wand Bad (Kniestock Ost)", "hk03", "Bad DG", "w-dg-east",
          [EAST, NORTH], [0, 1], panels_glki(CORNER), CORNER + 1.25,
          [DIST, [6.762, round(NORTH + CORNER + 1.25, 3)]]),
    field("wand-07", "07 DA Wand Treppenzimmer (Kniestock West)", "hk04", "Treppenzimmer", "w-dg-west",
          [WEST, PART_NORTH], [0, -1], panels_glki(0.192), 1.442,
          [DIST, [6.762, NORTH_STRIP], [WEST + 0.03, NORTH_STRIP], [WEST + 0.03, round(PART_NORTH - 1.442, 3)]]),
    field("wand-08", "08 DA Wand Treppenzimmer (Nord)", "hk04", "Treppenzimmer", "w-dg-north",
          [WEST, NORTH], [1, 0], [{"type": "D", "u": CORNER, "z": Z0}, {"type": "E", "u": CORNER + 0.625, "z": Z0}],
          CORNER + 0.625,
          [DIST, [6.762, NORTH_STRIP], [WEST + 0.03, NORTH_STRIP], [WEST + 0.03, NORTH + 0.03],
           [WEST + CORNER + 0.625, NORTH + 0.03]]),
]
CIRCUITS = [
    {"id": "hk01", "name": "HK 01 Schlafzimmer West", "room": "Schlafzimmer", "design_area": 6.56, "design_output": 569.63},
    {"id": "hk02", "name": "HK 02 Schlafzimmer Ost", "room": "Schlafzimmer", "design_area": 5.91, "design_output": 512.66},
    {"id": "hk03", "name": "HK 03 Bad", "room": "Bad DG", "design_area": 4.59, "design_output": 398.74},
    {"id": "hk04", "name": "HK 04 Treppenzimmer", "room": "Treppenzimmer", "design_area": 3.94, "design_output": 341.78},
]
WALL_HEATING = {
    "name": "Lehm-Wandheizung DG (naturbo)",
    "assembly": "assembly:interior-lining-wandheizung-naturbo",
    "pipe": "tga-component:naturbo-alu-verbundrohr-11-6",
    "pipe_diameter": 0.0116,
    "feed_diameter": 0.016,
    "panel_components": {t: "tga-component:naturbo-klima-platte-%s" % t.lower() for t in "DEFGIKL"},
    "coupling": "tga-component:naturbo-presskupplung-11-6",
    "adapter": "tga-component:naturbo-presskupplung-11-6-16",
    "supply_temperature": 38,
    "return_temperature": 33,
    "estimated": True,
    "note": "naturbo Verlegeskizze 260508_01DG_B (08.05.2026) und Massenermittlung MEER: Auslegung 38/33 °C, "
            "50 W/m²; Plattenlage aus den Wandansichten, an die Modellmaße angepasst; Anbindeleitungen 16 mm "
            "und Verteilerlage geschätzt",
    "distributor": {"name": "Verteiler Wandheizung DG", "component": "tga-component:kermi-x-net-verteiler-5",
                    "wall": "w-dg-east", "position": DIST, "z": 0.1, "width": 0.3, "height": 0.45, "outlets": 5,
                    "note": "rotes Viereck Anlage 2: Ostwand am Ende der Innenwand, im Leitungskanal"},
    "duct": {"name": "Leitungskanal zum Keller", "rect": [round(EAST - 0.3, 3), round(PART_NORTH - 0.3, 3), 0.3, 0.3]},
    "circuits": CIRCUITS,
    "fields": FIELDS,
}

PARTITION = {
    "id": "iw-dg-treppe-bad", "name": "Innenwand Treppenzimmer/Bad DG", "assembly": "assembly:interior-wall-iw1",
    "start": [PARTITION_X, NORTH], "end": [PARTITION_X, PART_NORTH], "reference": "center", "shape": {"kind": "roof"},
    "openings": [{"id": "o-tuer-bad-dg", "component": "component:door-dg-durchgang", "offset": 0.15, "sill": 0,
                  "joint": 0.01, "inset": 0.03, "reveal_material": "material:interior-plaster"}],
}
ROOMS = [
    {"id": "room-dg-treppe", "number": "1.01", "name": "Treppenzimmer", "usage": "NUF1",
     "polygon": [[WEST, NORTH], [TREPPE_EAST, NORTH], [TREPPE_EAST, PART_NORTH], [WEST, PART_NORTH]],
     "estimated": True, "note": "aus dem Durchgangszimmer (naturbo-Plan: 4,56 m breit, Modell schmaler)"},
    {"id": "room-dg-bad", "number": "1.04", "name": "Bad DG", "usage": "NUF7",
     "polygon": [[BAD_WEST, NORTH], [EAST, NORTH], [EAST, PART_NORTH], [BAD_WEST, PART_NORTH]],
     "estimated": True, "note": "aus dem Durchgangszimmer (naturbo-Plan: 2,05 × 3,05 m)"},
]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data, write):
    if write:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(("wrote " if write else "would write ") + str(path.relative_to(ROOT)))


def storey_update(storey):
    walls = [w for w in storey["walls"] if w["id"] != PARTITION["id"]]
    index = next(i for i, w in enumerate(walls) if w["id"] == "iw-dg-durchgang-schlaf")
    walls[index]["name"] = "Innenwand Treppenzimmer, Bad DG/Schlafzimmer"
    walls.insert(index + 1, PARTITION)
    storey["walls"] = walls
    rooms = [r for r in storey["rooms"] if r["id"] not in ("room-dg-durchgang",) + tuple(x["id"] for x in ROOMS)]
    storey["rooms"] = ROOMS + rooms
    storey["wall_heating"] = WALL_HEATING
    return storey


def summary():
    counts, areas = {}, {}
    size = {"D": 0.65625, "E": 0.65625, "F": 0.65625, "G": 0.78125, "I": 0.78125, "K": 0.53125, "L": 0.53125}
    for f in FIELDS:
        for p in f["panels"]:
            counts[p["type"]] = counts.get(p["type"], 0) + 1
            areas[f["circuit"]] = areas.get(f["circuit"], 0) + size[p["type"]]
    print("Räume: Treppenzimmer x %.3f–%.3f, Bad DG x %.3f–%.3f (y %.3f–%.3f), Trennwand x %.4f"
          % (WEST, TREPPE_EAST, BAD_WEST, EAST, NORTH, PART_NORTH, PARTITION_X))
    print("Platten:", " ".join("%s%d" % (t, counts[t]) for t in sorted(counts)), "=", sum(counts.values()))
    for c in CIRCUITS:
        print("  %s %-24s Fläche %.3f m² (MEER %.2f)" % (c["id"], c["name"], areas[c["id"]], c["design_area"]))
    for f in FIELDS:
        print("  Feld %-12s %-4s Wand %-18s Platten %s" % (f["id"], f["circuit"], f["wall"],
                                                          "".join(p["type"] for p in f["panels"])))


def main(write):
    summary()
    save(STOREY, storey_update(load(STOREY)), write)
    for name in TERMINALS:
        path = ROOT / "house" / "tga" / "terminals" / (name + ".json")
        data = load(path)
        if data.get("room") in OLD_ROOM_IDS:
            data["room"] = "room-dg-bad"
            save(path, data, write)
    for name in SCRIPTS:
        path = ROOT / "scripts" / name
        text = path.read_text(encoding="utf-8")
        if "room-dg-durchgang-ost" in text:
            print(("patched " if write else "would patch ") + name)
            if write:
                path.write_text(text.replace("room-dg-durchgang-ost", "room-dg-bad"), encoding="utf-8")


if __name__ == "__main__":
    main("--write" in sys.argv)
