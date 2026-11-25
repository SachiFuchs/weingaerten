"""DG: the Abseiten beside Durchgangszimmer, Schlafzimmer and Kammer 2 are part of these rooms (user, Nov 2026).

Durchgangszimmer and Schlafzimmer = x 0.328..6.792, Kammer 2 = x 0.328..2.392 (rectangles); the Abseite rooms are removed and the DG
rooms renumbered 1.01.. in list order. Coverings and other fields of the kept rooms stay. Writes only with --write.
"""
import json
import os
import sys

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "house", "storeys", "upper.json")
MERGE = {"room-dg-durchgang": ["room-dg-durchgang-west", "room-dg-durchgang-ost"],
         "room-dg-schlaf": ["room-dg-schlaf-west", "room-dg-schlaf-ost"], "room-dg-kammer2": ["room-dg-kammer2-west"]}


def bounds(polygons):
    xs = [p[0] for pl in polygons for p in pl]
    ys = [p[1] for pl in polygons for p in pl]
    return [[min(xs), min(ys)], [max(xs), min(ys)], [max(xs), max(ys)], [min(xs), max(ys)]]


def main():
    with open(PATH, encoding="utf-8") as handle:
        storey = json.load(handle)
    rooms = {r["id"]: r for r in storey["rooms"]}
    removed = set()
    for keep, parts in MERGE.items():
        parts = [p for p in parts if p in rooms]
        if not parts:
            continue
        polygons = [rooms[keep]["polygon"]] + [rooms[p]["polygon"] for p in parts]
        rooms[keep]["polygon"] = bounds(polygons)
        removed.update(parts)
        print(keep, "->", rooms[keep]["polygon"])
    storey["rooms"] = [r for r in storey["rooms"] if r["id"] not in removed]
    for n, room in enumerate(storey["rooms"], start=1):
        room["number"] = "1.%02d" % n
        print(room["number"], room["id"], room["name"])
    if "--write" in sys.argv:
        with open(PATH + ".tmp", "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(storey, ensure_ascii=False, indent=2) + "\n")
        os.replace(PATH + ".tmp", PATH)
        print("written")


if __name__ == "__main__":
    main()
