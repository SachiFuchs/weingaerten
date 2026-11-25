"""Adds `cores` (allowed core counts of a cable entering) to the entry ports of boxes and creates two placeholders:
a cooker connection box (5 cores) and an E27 lamp holder (3 cores). Idempotent. Usage: python add_cable_cores.py [--write]
"""
import copy
import json
import os
import sys

ROOT = r"c:\Development\weingaerten\catalog\tga-components"
CORES = {"kaiser-up-geraetedose": [3], "abzweigkasten-80-mm-x-80-mm-x-37-mm-ip55": [3]}
WRITE = "--write" in sys.argv


def load(name):
    with open(os.path.join(ROOT, name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def store(name, data):
    print(("schreibe " if WRITE else "würde schreiben ") + name)
    if WRITE:
        with open(os.path.join(ROOT, name + ".json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")


for name, cores in CORES.items():
    data = load(name)
    for port in data["install"]["ports"]:
        if port["line"] == "conduit":
            port["cores"] = cores
    store(name, data)

box = load("abzweigkasten-80-mm-x-80-mm-x-37-mm-ip55")
herd = {"id": "herd-anschlussdose", "name": "Herd-Anschlussdose (5-adrig)", "class": "tga-class:install-part",
        "din276": "440", "system_type": "Stromkreis", "params": {"part_type": "box"}, "estimated": True,
        "note": "Platzhalter: Anschlussdose für den Herd (NYM 5 x 2,5), Maße wie Abzweigkasten 80 x 80 angenommen",
        "install": copy.deepcopy(box["install"]),
        "connection": {"line": "power", "mounting": "flush", "box_function": "device"}}
herd["install"]["group"] = "Herdanschlussdosen"
for port in herd["install"]["ports"]:
    if port["line"] == "conduit":
        port["cores"] = [5]
store("herd-anschlussdose", herd)

lamp = {"id": "lampenfassung-e27", "name": "Lampenfassung E27", "class": "tga-class:install-part",
        "din276": "440", "system_type": "Stromkreis", "params": {"part_type": "other"}, "estimated": True,
        "note": "Platzhalter: Birnenfassung E27 mit Zuleitung von oben (3-adrig), Maße geschätzt",
        "install": {"trade": "electrical", "group": "Fassungen", "shape": "box", "size": [0.04, 0.06, 0.04],
                    "ports": [{"id": "top", "pos": [0, 0.03, 0], "dir": [0, 1, 0], "line": "conduit", "dn": 20,
                               "gender": "any", "cores": [3]}]},
        "connection": {"line": "power", "accepts": ["L", "N", "PE"]}}
store("lampenfassung-e27", lamp)
