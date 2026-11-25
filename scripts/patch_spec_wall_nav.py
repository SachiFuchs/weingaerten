"""Spec/handbook patch: navigation arrows around the /waende wall view (CRLF -> bytes)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIRST = ("left / right by the screen position of the join centre against the face middle")
FINAL = ("left / right by the u of the join centre against the face middle, swapped in mirrored views; walls whose "
         "footprint touches one of the two wall ends within the wall thickness (corners, outside the shorter face) are "
         "added to that end's side")
PATCHES = [
    ("weingaerten-web.md",
     "- **Zoom** (edit modes only: `Bearbeiten` of the openings",
     "- **Navigation arrows**: bar `wnavtop` between the zoom bar and the wall view: left the buttons `◀ <wall>`, right "
     "`<wall> ▶` for every neighbour wall joining the shown face (the joins of the face, see joint zones; one button per "
     "wall, " + FINAL + ") → `pickWall` (the view side "
     "stays); in the middle `▲ Decke`, disabled (title `Decke – noch nicht implementiert`). Bar `wnavbot` below the view: "
     "`▼ <number> <room>` for every storey room with a face on this wall and the shown side (exterior walls: only the "
     "inside view) → `/raeume?storey=<storey>#<room id>`.\r\n"
     "- **Zoom** (edit modes only: `Bearbeiten` of the openings"),
    ("weingaerten-handbuch.md",
     "- **Außenansicht / Innenansicht** wechselt die Seite der Wand.",
     "- **Außenansicht / Innenansicht** wechselt die Seite der Wand.\r\n"
     "- **Pfeile um die Wand:** über der Ansicht links **◀ <Wand>** und rechts **<Wand> ▶** – je angrenzender Wand ein "
     "Pfeil – wechseln zur Nachbarwand (die Seite bleibt). **▲ Decke** ist vorgesehen, aber noch nicht umgesetzt. Unter der "
     "Ansicht führt **▼ <Raum>** zum Raum vor dieser Wandseite (bei Außenwänden nur in der Innenansicht)."),
]

for name, old, new in PATCHES:
    path = ROOT / name
    data = path.read_bytes().replace(FIRST.encode("utf-8"), FINAL.encode("utf-8"))
    o, n = old.encode("utf-8"), new.encode("utf-8")
    if n in data:
        path.write_bytes(data)
        print(name, "ok")
    elif data.count(o) == 1:
        path.write_bytes(data.replace(o, n))
        print(name, "patched")
    else:
        raise SystemExit("%s: anchor not found (%d)" % (name, data.count(o)))
