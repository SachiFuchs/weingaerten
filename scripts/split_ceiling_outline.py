"""One-off: split the inner outline of the ground storey at the old north wall (Flachdach north, Decke EG south)."""
import json
import os
import sys

sys.path.insert(0, os.path.join(r"c:\Development\weingaerten", "code"))
import weingaerten_core  # noqa: E402
from weingaerten_core.geometry.polygon import Polygon  # noqa: E402

# boundary between the flat roof and the timber ceiling: middle of the old north wall (iw2, y 2.23 / 2.258)
SPLIT_Y = 2.244

house = json.loads(weingaerten_core.handle(json.dumps({"command": "HOUSE"})))
storey = house["storeys"][0]
ring = max(storey["outline"], key=lambda r: r["area"])
inner = Polygon.counter_clockwise([tuple(p) for p in ring["inner"]])
north = Polygon.clip_half_plane(inner, (0.0, SPLIT_Y), (0.0, -1.0))
south = Polygon.clip_half_plane(inner, (0.0, SPLIT_Y), (0.0, 1.0))
for name, poly in (("inner", inner), ("north", north), ("south", south)):
    print(name, round(abs(Polygon.signed_area(poly)), 3), json.dumps([[round(x, 4), round(y, 4)] for x, y in poly]))
