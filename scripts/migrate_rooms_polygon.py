"""Convert storey rooms from rect [x, y, w, h] to rectangular polygons (IfcSpace footprint).

Rects with the same name that touch along an edge are merged into one polygon (L-shaped rooms).
Adds number (EG 0.xx, DG 1.xx, KG -1.xx) and DIN 277 usage, both marked `estimated`.
Renames merged room ids referenced by TGA terminals. Writes only with --write.
"""
import json
import os
import sys

HOME = os.environ.get("WEINGAERTEN_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STOREYS = {"ground": "0", "upper": "1", "basement": "-1"}
USAGE = {"Flur": "VF9", "Treppe": "VF9", "Bad": "NUF7", "Küche": "NUF1", "Kammer": "NUF4", "Wohnzimmer": "NUF1",
         "Zimmer 2 (Winterraum)": "NUF1", "Abseite": "NUF4", "Durchgangszimmer": "NUF1", "Schlafzimmer": "NUF1",
         "Kammer 2": "NUF1", "Keller": "NUF4", "Öltankraum": "TF8"}
MERGED_ID = {"Keller": "room-keller"}
EPS = 1e-6


def touching(a, b):
    ax0, ay0, ax1, ay1 = a[0], a[1], a[0] + a[2], a[1] + a[3]
    bx0, by0, bx1, by1 = b[0], b[1], b[0] + b[2], b[1] + b[3]
    if abs(ax1 - bx0) < EPS or abs(bx1 - ax0) < EPS:
        return min(ay1, by1) - max(ay0, by0) > EPS
    if abs(ay1 - by0) < EPS or abs(by1 - ay0) < EPS:
        return min(ax1, bx1) - max(ax0, bx0) > EPS
    return False


def groups(rooms):
    """Connected groups of same-name rooms (by touching edges)."""
    result, used = [], set()
    for i, room in enumerate(rooms):
        if i in used:
            continue
        group, todo = [], [i]
        used.add(i)
        while todo:
            k = todo.pop()
            group.append(rooms[k])
            for j, other in enumerate(rooms):
                if j not in used and other["name"] == room["name"] and touching(rooms[k]["rect"], other["rect"]):
                    used.add(j)
                    todo.append(j)
        result.append(group)
    return result


def union_outline(rects):
    """Outline of the union of axis-parallel rects (grid cells, boundary edges chained, collinear points removed)."""
    xs = sorted({round(v, 6) for r in rects for v in (r[0], r[0] + r[2])})
    ys = sorted({round(v, 6) for r in rects for v in (r[1], r[1] + r[3])})

    def filled(i, j):
        if i < 0 or j < 0 or i >= len(xs) - 1 or j >= len(ys) - 1:
            return False
        cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
        return any(r[0] < cx < r[0] + r[2] and r[1] < cy < r[1] + r[3] for r in rects)
    edges = {}
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            if not filled(i, j):
                continue
            # directed boundary edges, filled cell on the right side in a y-down plan (clockwise on screen)
            if not filled(i, j - 1):
                edges[(xs[i], ys[j])] = (xs[i + 1], ys[j])
            if not filled(i + 1, j):
                edges[(xs[i + 1], ys[j])] = (xs[i + 1], ys[j + 1])
            if not filled(i, j + 1):
                edges[(xs[i + 1], ys[j + 1])] = (xs[i], ys[j + 1])
            if not filled(i - 1, j):
                edges[(xs[i], ys[j + 1])] = (xs[i], ys[j])
    start = min(edges)
    ring, point = [start], edges[start]
    while point != start:
        ring.append(point)
        point = edges[point]
    if len(edges) != len(ring):
        raise ValueError("union has holes or several parts: %s" % rects)
    cleaned = []
    for k, p in enumerate(ring):
        a, b = ring[k - 1], ring[(k + 1) % len(ring)]
        if not ((abs(a[0] - p[0]) < EPS and abs(b[0] - p[0]) < EPS) or (abs(a[1] - p[1]) < EPS and abs(b[1] - p[1]) < EPS)):
            cleaned.append([p[0], p[1]])
    return cleaned


def migrate_storey(storey_id, renames):
    path = os.path.join(HOME, "house", "storeys", storey_id + ".json")
    with open(path, encoding="utf-8") as handle:
        storey = json.load(handle)
    rooms = storey.get("rooms") or []
    if all("polygon" in r for r in rooms):
        print("%s: already migrated" % storey_id)
        return None
    out = []
    for n, group in enumerate(groups(rooms), start=1):
        first = group[0]
        room_id = MERGED_ID.get(first["name"]) if len(group) > 1 else None
        if room_id is None:
            base = [r["id"] for r in group if not any(r["id"].endswith(s) for s in ("-nord", "-ost", "-west", "-gang", "-sued"))]
            room_id = base[0] if base else first["id"]
        for r in group:
            if r["id"] != room_id:
                renames[r["id"]] = room_id
        room = {"id": room_id, "number": "%s.%02d" % (STOREYS[storey_id], n), "name": first["name"]}
        if first["name"] in USAGE:
            room["usage"] = USAGE[first["name"]]
        room["polygon"] = union_outline([r["rect"] for r in group])
        room["estimated"] = True
        room["note"] = "Nummer und Nutzung geschätzt (Migration Rechteck → Polygon)"
        print("%s: %s %s <- %s, %d Punkte" % (storey_id, room_id, first["name"], [r["id"] for r in group],
                                              len(room["polygon"])))
        out.append(room)
    storey["rooms"] = out
    return path, storey


def rename_terminals(renames, write):
    folder = os.path.join(HOME, "house", "tga", "terminals")
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        with open(path, encoding="utf-8") as handle:
            terminal = json.load(handle)
        if terminal.get("room") in renames:
            print("terminal %s: room %s -> %s" % (name, terminal["room"], renames[terminal["room"]]))
            terminal["room"] = renames[terminal["room"]]
            if write:
                save(path, terminal)


def save(path, value):
    with open(path + ".tmp", "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    os.replace(path + ".tmp", path)


def main():
    write = "--write" in sys.argv
    renames = {}
    results = [migrate_storey(s, renames) for s in STOREYS]
    rename_terminals(renames, write)
    if write:
        for item in results:
            if item:
                save(*item)
        print("written")
    else:
        print("dry run (use --write)")


if __name__ == "__main__":
    main()
