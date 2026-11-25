"""Adds estimated install blocks to the flush / hollow-wall boxes (scaled from the Kaiser UP Gerätedose, sizes from
the article names) and gives the Pollmann Herdanschlussdose the ports of the Herd-Anschlussdose.

python scripts/add_flush_box_install.py [--write]
"""
import copy
import json
import os
import sys

FOLDER = r"c:\Development\weingaerten\catalog\tga-components"
TEMPLATE = "kaiser-up-geraetedose"
NOTE = "install-Block geschätzt (Maße aus dem Namen, Einführungen wie Kaiser UP Gerätedose)"
# width, height, depth in m (round boxes: width = height = diameter)
SIZES = {
    "abzweigkasten-unterputz-95-mm-x-95-mm-schwarz-weiss-ip20": [0.095, 0.095, 0.047],
    "geraetedose-mit-membran-68-mm-tiefe": [0.068, 0.068, 0.068],
    "hohlwand-abzweigkasten-115-x-115-x-47-mm-orange-weiss-ip30": [0.115, 0.115, 0.047],
    "hohlwanddose-61-mm-10-er-beutel": [0.061, 0.061, 0.047],
    "hohlwanddose-68-mm-x-35-mm-orange-ip30": [0.068, 0.068, 0.035],
    "hohlwanddose": [0.068, 0.068, 0.047],
    "iso-abzweigdose-70-mm-x-36-mm-schwarz": [0.070, 0.070, 0.036],
    "kaiser-9062-02-hohlwand-geraetedose-2-fach-t47-mm": [0.139, 0.068, 0.047],
    "kaiser-9063-02-hohlwand-geraetedose-o-range-49-mm": [0.068, 0.068, 0.049],
    "kaiser-9064-02-hohlwand-geraeteverbindun": [0.068, 0.068, 0.062],
    "kaiser-9196-91-hohlwand-abzweigkasten-mit-deckel-165x165x72-mm": [0.165, 0.165, 0.072],
    "kaiser-9263-22-geraetedose-o-range-econ-63-68x49-mm-25-stueck": [0.068, 0.068, 0.049],
    "kombi-geraetedose-3-fach-218-mm-x-75-mm-schwarz-ip20": [0.218, 0.075, 0.047],
    "obo-hohlwanddose-luftdicht-68-mm-x-47-mm-orange": [0.068, 0.068, 0.047],
}
POLLMANN = "pollmann-herdanschlussdose-mit-wago-verbindungsklemmen"


def load(name):
    with open(os.path.join(FOLDER, name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def save(element, write):
    print(("schreibe " if write else "würde schreiben ") + element["id"], element["install"]["size"])
    if write:
        with open(os.path.join(FOLDER, element["id"] + ".json"), "w", encoding="utf-8") as f:
            json.dump(element, f, ensure_ascii=False, indent=2)
            f.write("\n")


def scaled(template, size):
    install = copy.deepcopy(template)
    w, h, d = size
    half = template["size"][0] / 2
    install["size"] = size
    for port in install["ports"]:
        if port["id"] != "front":
            x, y, _ = port["pos"]
            port["pos"] = [round(w / 2 * x / half, 4), round(h / 2 * y / half, 4), round(-d / 2, 4)]
    return install


def note(element, text):
    return (element.get("note") + "; " if element.get("note") else "") + text


def main():
    write = "--write" in sys.argv
    template = load(TEMPLATE)["install"]
    for eid, size in SIZES.items():
        element = load(eid)
        if element.get("install"):
            continue
        element["install"] = scaled(template, size)
        element["note"] = note(element, NOTE)
        save(element, write)
    pollmann = load(POLLMANN)
    if not pollmann.get("install"):
        pollmann["install"] = copy.deepcopy(load("herd-anschlussdose")["install"])
        pollmann["note"] = note(pollmann, "install-Block wie Herd-Anschlussdose (geschätzt)")
        save(pollmann, write)


if __name__ == "__main__":
    main()
