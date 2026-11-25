"""Write the `install` block (shape, size, ports) into the placeable tga-components and create the missing placeholders.

Local part frame: x, y in the wall plane, w out of the wall (towards the room). Fittings have their origin where the
pipe axes meet; a port lies at the joint plane (z_length from the origin) and points outwards. Straight pipes run from
port a (origin, upstream, socket for HT) to port b (x = length, downstream, spigot for HT).

    python scripts/build_ports.py          # dry run: lists the changes
    python scripts/build_ports.py --write  # writes the catalog files
"""
import json
import math
import os
import sys

ROOT = r"c:\Development\weingaerten"
FOLDER = os.path.join(ROOT, "catalog", "tga-components")

NEW_COMPONENTS = {
    "ht-reducer-90-50": {
        "id": "ht-reducer-90-50", "name": "HT-Reduzierstück DN 90/50", "class": "tga-class:pipe-fitting",
        "din276": "411", "system_type": "Abwasser",
        "params": {"fitting_type": "adapter", "system_line": "ht", "dn": 90, "z_length": 0.04,
                   "line_to": "ht", "dn_to": 50},
        "estimated": True,
        "note": "Platzhalter für den Einbau in Wänden (Übergang DN 90 > DN 50), Baulänge geschätzt - bitte bestätigen"},
    "ppr-valve-20": {
        "id": "ppr-valve-20", "name": "PP-R Absperrventil DN 20 (Unterputz)", "class": "tga-class:install-part",
        "din276": "412", "system_type": "Trinkwasser", "params": {"part_type": "valve", "size": "DN 20"},
        "estimated": True,
        "note": "Platzhalter für den Einbau in Wänden, Maße geschätzt - bitte Produkt wählen"},
}


def port(pid, pos, direction, line, dn, gender, at_length=False):
    entry = {"id": pid, "pos": [round(v, 4) for v in pos], "dir": [round(v, 6) for v in direction],
             "line": line, "dn": dn, "gender": gender}
    if at_length:
        entry["at_length"] = True
    return entry


def pipe(trade, line, dn, od, max_length, ends):
    return {"trade": trade, "group": "Rohre", "shape": "pipe", "outer_diameter": od,
            "stretch": {"max_length": max_length, "default_length": min(1.0, max_length)},
            "ports": [port("a", (0, 0, 0), (-1, 0, 0), line, dn, ends[0]),
                      port("b", (0, 0, 0), (1, 0, 0), line, dn, ends[1], at_length=True)]}


def bend(trade, line, dn, od, angle, z, genders, group="Bögen"):
    a = math.radians(angle)
    return {"trade": trade, "group": group, "shape": "fitting", "outer_diameter": od,
            "ports": [port("a", (-z, 0, 0), (-1, 0, 0), line, dn, genders[0]),
                      port("b", (z * math.cos(a), z * math.sin(a), 0), (math.cos(a), math.sin(a), 0), line, dn,
                           genders[1])]}


def branch(trade, line, dn, dn_branch, od, angle, z, genders):
    # the branch leg points upstream at (180 - angle) degrees, so a 45 degree Y joins with the flow
    a = math.radians(180 - angle)
    return {"trade": trade, "group": "Abzweige", "shape": "fitting", "outer_diameter": od,
            "ports": [port("a", (-z, 0, 0), (-1, 0, 0), line, dn, genders[0]),
                      port("b", (z, 0, 0), (1, 0, 0), line, dn, genders[1]),
                      port("c", (z * math.cos(a), z * math.sin(a), 0), (math.cos(a), math.sin(a), 0), line,
                           dn_branch, genders[2])]}


def inline(trade, group, shape, line, dn_a, dn_b, od, z, genders):
    return {"trade": trade, "group": group, "shape": shape, "outer_diameter": od,
            "ports": [port("a", (-z, 0, 0), (-1, 0, 0), line, dn_a, genders[0]),
                      port("b", (z, 0, 0), (1, 0, 0), line, dn_b, genders[1])]}


def cap(trade, group, line, dn, od, gender):
    return {"trade": trade, "group": group, "shape": "cap", "outer_diameter": od,
            "ports": [port("a", (0, 0, 0), (-1, 0, 0), line, dn, gender)]}


def box(size, entries, group="Dosen"):
    # origin = centre of the front face (flush with the wall face at depth 0); the body goes into the wall (-w)
    w, h, d = size
    ports = [port("front", (0, 0, 0), (0, 0, 1), "insert", 60, "socket")]
    sides = {"top": ((0, h / 2, -d / 2), (0, 1, 0)), "bottom": ((0, -h / 2, -d / 2), (0, -1, 0)),
             "left": ((-w / 2, 0, -d / 2), (-1, 0, 0)), "right": ((w / 2, 0, -d / 2), (1, 0, 0))}
    for side in entries:
        pos, direction = sides[side]
        ports.append(port(side, pos, direction, "conduit", 20, "any"))
    return {"trade": "electrical", "group": group, "shape": "box", "size": list(size), "ports": ports}


def wall_plate():
    # PP-R socket from below, threaded outlet into the room (fixture connection, normally left open)
    return {"trade": "water_supply", "group": "Endstücke", "shape": "fitting", "outer_diameter": 0.02,
            "ports": [port("a", (0, -0.03, 0), (0, -1, 0), "ppr", 20, "socket"),
                      port("out", (0, 0, 0.02), (0, 0, 1), "insert", 15, "any")]}


HT = ("spigot", "socket")
INSTALL = {
    "ht-pipe-50": pipe("waste_water", "ht", 50, 0.05, 2.0, ("socket", "spigot")),
    "ht-pipe-90": pipe("waste_water", "ht", 90, 0.09, 2.0, ("socket", "spigot")),
    "ht-reducer-90-50": inline("waste_water", "Übergänge", "fitting", "ht", 50, 90, 0.09, 0.04, ("socket", "spigot")),
    "ht-plug-50": cap("waste_water", "Stopfen", "ht", 50, 0.05, "spigot"),
    "ht-plug-90": cap("waste_water", "Stopfen", "ht", 90, 0.09, "spigot"),
    "ppr-rohr-dn-20-x-2-m": pipe("water_supply", "ppr", 20, 0.02, 2.0, ("spigot", "spigot")),
    "ppr-bend-20-90": bend("water_supply", "ppr", 20, 0.02, 90, 0.011, ("socket", "socket")),
    "ppr-winkel-45deg-dn-20": bend("water_supply", "ppr", 20, 0.02, 45, 0.005, ("socket", "socket")),
    "ppr-tee-20": branch("water_supply", "ppr", 20, 20, 0.02, 90, 0.011, ("socket", "socket", "socket")),
    "ppr-cap-20": cap("water_supply", "Endstücke", "ppr", 20, 0.02, "socket"),
    "ppr-valve-20": inline("water_supply", "Ventile", "valve", "ppr", 20, 20, 0.02, 0.03, ("socket", "socket")),
    "ppr-wall-plate-20": wall_plate(),
    "installationsrohr-m20-starr-lichtgrau-dr": pipe("electrical", "conduit", 20, 0.02, 3.0, ("spigot", "spigot")),
    "steckbogen-m20-fuer-installationsrohr-2": bend("electrical", "conduit", 20, 0.02, 90, 0.06, ("socket", "socket")),
    "steckmuffe-m20-fuer-installationsrohr-5": inline("electrical", "Muffen", "fitting", "conduit", 20, 20, 0.022,
                                                      0.025, ("socket", "socket")),
    "kaiser-up-geraetedose": box((0.068, 0.068, 0.047), ("top", "bottom", "left", "right")),
    "abzweigkasten-80-mm-x-80-mm-x-37-mm-ip55": box((0.08, 0.08, 0.037), ("top", "bottom", "left", "right"),
                                                    "Verteilerdosen"),
    "jung-steckdose-1-stueck": {"trade": "electrical", "group": "Steckdosen", "shape": "insert",
                                "size": [0.071, 0.071, 0.012],
                                "ports": [port("back", (0, 0, 0), (0, 0, -1), "insert", 60, "spigot")]},
}
for dn, od in ((50, 0.05), (90, 0.09)):
    for angle in (15, 30, 45):
        INSTALL["ht-bend-%d-%d" % (dn, angle)] = bend("waste_water", "ht", dn, od, angle, 0.03, HT[::-1])
    for angle in (45, 90):
        INSTALL["ht-branch-%d-50-%d" % (dn, angle)] = branch("waste_water", "ht", dn, 50, od, angle, 0.03,
                                                             ("socket", "spigot", "socket"))


def main(write):
    changed = 0
    for cid, install in INSTALL.items():
        path = os.path.join(FOLDER, cid + ".json")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as handle:
                element = json.load(handle)
        elif cid in NEW_COMPONENTS:
            element = dict(NEW_COMPONENTS[cid])
        else:
            print("missing component:", cid)
            continue
        if element.get("install") == install:
            continue
        element["install"] = install
        changed += 1
        print(("write " if write else "would write ") + cid)
        if write:
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(element, ensure_ascii=False, indent=2) + "\n")
    print("%d components changed" % changed)


if __name__ == "__main__":
    main("--write" in sys.argv)
