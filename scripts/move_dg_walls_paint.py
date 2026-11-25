"""One-off: move the four clad DG walls 1 mm further out (paint layer 1 mm), keep inner faces and opening positions."""
import json
import os

PATH = os.path.join(r"c:\Development\weingaerten", "house", "storeys", "upper.json")
MOVE = {-0.01: -0.011, 7.13: 7.131, 2.07: 2.069, 13.14: 13.141}
OFFSETS = {"o-balkon-treppenzimmer": 3.036, "o-fenster-schlaf": 1.776, "o-balkon-schlaf": 2.981}
WALLS = {"w-dg-north", "w-dg-east", "w-dg-south-balkon", "w-dg-kammer-ost", "w-dg-south-kammer", "w-dg-west"}

data = json.load(open(PATH, encoding="utf-8"))
for wall in data["walls"]:
    if wall["id"] in WALLS:
        for key in ("start", "end"):
            wall[key] = [MOVE.get(round(v, 3), v) for v in wall[key]]
        for opening in wall.get("openings") or []:
            opening["offset"] = OFFSETS.get(opening["id"], opening["offset"])
        print(wall["id"], wall["start"], wall["end"], [(o["id"], o["offset"]) for o in wall.get("openings") or []])
with open(PATH, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(data, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
