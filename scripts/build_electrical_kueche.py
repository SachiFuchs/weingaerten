"""Electrical data for the first kitchen cables (plan kueche-stromkabel-elektrik).

Sets the parameters of the stock parts used (conduit, bend, sleeve, clamp, boxes, cable diameters) and writes
the runs el-kueche-dose / el-kueche-herd, the terminals el-dose-kueche / el-dose-herd and the shaft penetrations.
Idempotent; usage: python scripts/build_electrical_kueche.py [--write]
"""
import json
import os
import sys

HOME = os.environ.get("WEINGAERTEN_HOME") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMP = os.path.join(HOME, "catalog", "tga-components")

PARAMS = {
    "installationsrohr-m20-starr-lichtgrau-dr": {"part_type": "conduit", "unit": "pcs", "size": "M20",
                                                 "outer_diameter": 0.02, "inner_diameter": 0.0175,
                                                 "stock_length": 3.0},
    "steckbogen-m20-fuer-installationsrohr-2": {"part_type": "conduit", "unit": "pcs", "size": "M20", "pack_size": 2},
    "steckmuffe-m20-fuer-installationsrohr-5": {"part_type": "conduit", "unit": "pcs", "size": "M20", "pack_size": 5},
    "klemmschelle-m20-fuer-installationsrohr": {"part_type": "cable_fixing", "unit": "pcs", "size": "M20",
                                                "pack_size": 10},
    "abzweigkasten-aufputz-100-mm-x-100-mm-grau-ip54": {"part_type": "box", "unit": "pcs", "size": "100x100x37"},
    "abzweigkasten-mit-klemmleiste-aufputz-85-mm-x-85-mm-grau": {"part_type": "box", "unit": "pcs", "size": "85x85"},
    # NYM-J outer diameters (manufacturer data sheets, typical values)
    "emskabel-feuchtraumleitung-nym-j-3-x-2-5-mm2-50-m": {"outer_diameter": 0.0105, "conduit_type": "rigid"},
    "emskabel-feuchtraumleitung-nym-j-5-x-2-5-mm2-50-m": {"outer_diameter": 0.0125, "conduit_type": "rigid"},
}

CONDUIT = {"pipe": "tga-component:installationsrohr-m20-starr-lichtgrau-dr",
           "bend": "tga-component:steckbogen-m20-fuer-installationsrohr-2",
           "sleeve": "tga-component:steckmuffe-m20-fuer-installationsrohr-5",
           "clamp": "tga-component:klemmschelle-m20-fuer-installationsrohr", "clamp_spacing": 0.5}
OPEN_END = {"reserve": 1.5, "note": "Keller, offen gelassen – Anschluss Sicherungskasten später"}

RUNS = [
    {"id": "el-kueche-dose", "name": "Stromleitung Küche Verteilerdose (NYM-J 3x2,5)",
     "component": "tga-component:emskabel-feuchtraumleitung-nym-j-3-x-2-5-mm2-50-m",
     "system": "electrical-kueche", "installation": "surface",
     "points": [[6.78, 4.87, -0.6], [6.78, 4.87, 0.6], [6.78, 4.30, 0.6], [6.78, 4.30, 1.05]],
     "conduit": CONDUIT, "open_end": OPEN_END, "reserve": 0.5, "to": "tga-terminal:el-dose-kueche",
     "estimated": True,
     "note": "im M20-Rohr aus dem Keller durch den Versorgungsschacht, waagrecht an der Ostwand, gerade Strecken"},
    {"id": "el-kueche-herd", "name": "Stromleitung Herd (NYM-J 5x2,5)",
     "component": "tga-component:emskabel-feuchtraumleitung-nym-j-5-x-2-5-mm2-50-m",
     "system": "electrical-kueche", "installation": "surface",
     "points": [[6.575, 5.06, -0.6], [6.575, 5.06, 0.6], [6.575, 5.38, 0.6], [6.20, 5.38, 0.6],
                [6.20, 5.38, 0.4425]],
     "conduit": CONDUIT, "open_end": OPEN_END, "reserve": 0.5, "to": "tga-terminal:el-dose-herd",
     "estimated": True,
     "note": "im M20-Rohr aus dem Keller durch den Versorgungsschacht, waagrecht an der Wand Küche/Kammer"},
]
TERMINALS = [
    {"id": "el-dose-kueche", "name": "Aufputz-Verteilerdose Küche",
     "component": "tga-component:abzweigkasten-aufputz-100-mm-x-100-mm-grau-ip54",
     "storey": "storey:ground", "room": "room-kueche", "wall": "w-east", "position": [6.7735, 4.30, 1.10],
     "estimated": True},
    {"id": "el-dose-herd", "name": "Aufputz-Verteiler Herd",
     "component": "tga-component:abzweigkasten-mit-klemmleiste-aufputz-85-mm-x-85-mm-grau",
     "storey": "storey:ground", "room": "room-kueche", "wall": "iw-kueche-kammer", "position": [6.20, 5.3715, 0.40],
     "estimated": True},
]


def _write(path, data, write):
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    old = open(path, encoding="utf-8").read() if os.path.isfile(path) else None
    if old == text:
        return
    print(("schreibe " if write else "würde schreiben ") + os.path.relpath(path, HOME))
    if write:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)


def main():
    write = "--write" in sys.argv
    for cid, params in PARAMS.items():
        path = os.path.join(COMP, cid + ".json")
        data = json.load(open(path, encoding="utf-8"))
        data["params"] = {**(data.get("params") or {}), **params}
        _write(path, data, write)
    for folder, items in (("runs", RUNS), ("terminals", TERMINALS)):
        for item in items:
            _write(os.path.join(HOME, "house", "tga", folder, item["id"] + ".json"), item, write)
    # house.json is hand formatted: only insert the refs textually
    path = os.path.join(HOME, "house", "house.json")
    text = open(path, encoding="utf-8").read()
    old = '"tga-run:tw-steig-hot" ]'
    new = '"tga-run:tw-steig-hot", "tga-run:el-kueche-dose", "tga-run:el-kueche-herd" ]'
    if "tga-run:el-kueche-dose" not in text:
        if old not in text:
            sys.exit("house.json: Schacht-Eintrag nicht gefunden")
        print(("schreibe " if write else "würde schreiben ") + "house/house.json (Schacht-Durchführungen)")
        if write:
            with open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write(text.replace(old, new, 1))


if __name__ == "__main__":
    main()
