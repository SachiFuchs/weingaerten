"""Adds an install block to every surface junction box (Aufputz-Abzweigkasten) without one, scaled from the
80 x 80 x 37 mm box (dimensions from the name, depth 40 mm when missing; marked estimated in the note).

python scripts/add_surface_box_install.py [--write]
"""
import copy
import json
import os
import re
import sys

ROOT = r"c:\Development\weingaerten"
FOLDER = os.path.join(ROOT, "catalog", "tga-components")
TEMPLATE = "abzweigkasten-80-mm-x-80-mm-x-37-mm-ip55"
NOTE = "install-Block geschätzt (Maße aus dem Namen, Einführungen wie Abzweigkasten 80x80)"


def load(name):
    with open(os.path.join(FOLDER, name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def size_of(name):
    numbers = [float(n.replace(",", ".")) / 1000 for n in re.findall(r"(\d+(?:,\d+)?)\s*mm", name)]
    if len(numbers) < 2:
        return None
    return [numbers[0], numbers[1], numbers[2] if len(numbers) > 2 else 0.04]


def scaled(template, size):
    install = copy.deepcopy(template)
    w, h, d = size
    install["size"] = [w, h, d]
    for port in install["ports"]:
        x, y, _ = port["pos"]
        if port["id"] == "front":
            continue
        port["pos"] = [round(w / 2 * (x / 0.04), 4), round(h / 2 * (y / 0.04), 4), round(-d / 2, 4)]
    return install


def main():
    write = "--write" in sys.argv
    template = load(TEMPLATE)["install"]
    for file in sorted(os.listdir(FOLDER)):
        element = load(file[:-5])
        connection = element.get("connection") or {}
        if (element.get("params") or {}).get("part_type") != "box" or connection.get("box_function") != "junction" \
                or connection.get("mounting") != "surface" or element.get("install"):
            continue
        size = size_of(element["name"])
        if size is None:
            print("ohne Maße:", element["id"])
            continue
        element["install"] = scaled(template, size)
        element["note"] = (element.get("note") + "; " if element.get("note") else "") + NOTE
        print(("schreibe " if write else "würde schreiben ") + element["id"], size)
        if write:
            with open(os.path.join(FOLDER, file), "w", encoding="utf-8") as f:
                json.dump(element, f, ensure_ascii=False, indent=2)
                f.write("\n")


if __name__ == "__main__":
    main()
