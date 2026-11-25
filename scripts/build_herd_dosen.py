"""Herd-Anschlussdose (Unterputz + Aufputz): Zulauf NYM-J 5 x 2,5 (oben), Abgang Herdanschlussleitung H05VV-F 5G2,5
(unten), Abgang NYM-J 3 x 2,5 einphasig (rechts). Rewrites herd-anschlussdose, creates herd-anschlussdose-aufputz.

python scripts/build_herd_dosen.py
"""
import json
import os

FOLDER = r"c:\Development\weingaerten\catalog\tga-components"
D = 0.037


def entry(pid, pos, direction, cores, types, label):
    return {"id": pid, "pos": pos, "dir": direction, "line": "conduit", "dn": 20, "gender": "any", "cores": [cores],
            "cable_types": types, "cross_section": 2.5, "label": label}


PORTS = [
    {"id": "front", "pos": [0, 0, 0], "dir": [0, 0, 1], "line": "insert", "dn": 60, "gender": "socket"},
    entry("top", [0, 0.04, -D / 2], [0, 1, 0], 5, ["NYM-J"], "Zulauf"),
    entry("bottom", [0, -0.04, -D / 2], [0, -1, 0], 5, ["H05VV-F"], "Abgang Herd"),
    entry("right", [0.04, 0, -D / 2], [1, 0, 0], 3, ["NYM-J"], "Abgang einphasig"),
]


def element(eid, name, mounting, note):
    return {"id": eid, "name": name, "class": "tga-class:install-part", "din276": "440", "system_type": "Stromkreis",
            "params": {"part_type": "box"}, "estimated": True, "note": note,
            "install": {"trade": "electrical", "group": "Herdanschlussdosen", "shape": "box", "size": [0.08, 0.08, D],
                        "ports": PORTS},
            "connection": {"line": "power", "mounting": mounting, "box_function": "device"}}


NOTE = ("Platzhalter: Zulauf NYM-J 5 x 2,5; Abgänge Herdanschlussleitung H05VV-F 5G2,5 und NYM-J 3 x 2,5 (einphasig); "
        "Maße wie Abzweigkasten 80 x 80 angenommen")
for item in (element("herd-anschlussdose", "Herd-Anschlussdose Unterputz", "flush", NOTE),
             element("herd-anschlussdose-aufputz", "Herd-Anschlussdose Aufputz", "surface", NOTE)):
    with open(os.path.join(FOLDER, item["id"] + ".json"), "w", encoding="utf-8") as f:
        json.dump(item, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("geschrieben", item["id"])
