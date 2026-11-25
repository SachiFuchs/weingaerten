"""Parity check: the PartFrame formulas of static/install.js (browser) give the same ports as the core PartFrame.

Extracts unit2/faceT/rotated/frame from install.js, runs them in node for random placements on real walls and
compares origin and axes with weingaerten_core.compute.part_frame.PartFrame (tolerance 1e-9).
"""
import json
import os
import random
import subprocess
import sys

ROOT = r"c:\Development\weingaerten"
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ.setdefault("WEINGAERTEN_HOME", ROOT)
from weingaerten_core.compute.part_frame import FACES, PartFrame  # noqa: E402
from weingaerten_core.model.model_cache import ModelCache  # noqa: E402

source = open(os.path.join(ROOT, "code", "weingaerten_web", "static", "install.js"), encoding="utf-8").read()
start, end = source.index(" const unit2="), source.index(" // computed part")
functions = source[start:end]

model = ModelCache.load_and_compute(ROOT)
walls = [w for s in model["storeys_out"] for w in s["walls"]][:12]
random.seed(4)
cases = []
for wall in walls:
    for face in FACES[wall["category"]]:
        part = {"host": {"wall": wall["id"], "face": face}, "u": random.uniform(0, 2), "z": random.uniform(0, 2),
                "depth": random.uniform(-0.1, 0.1),
                "rot": {"plane": random.choice(range(0, 360, 15)), "tilt": random.choice((0, 90, -90, 15)),
                        "turn": random.choice((0, 90, -90, 30)), "flip": random.random() < 0.5}}
        frame = PartFrame.on_wall(wall, part)
        cases.append({"wall": wall, "part": part, "expect": [frame.origin, frame.x, frame.y, frame.w]})

script = functions + "\nconst cases=JSON.parse(require('fs').readFileSync(0,'utf8'));\n" \
    "console.log(JSON.stringify(cases.map(c=>{const f=frame(c.wall,c.part);return [f.o,f.x,f.y,f.w]})));"
result = subprocess.run(["node", "-e", script], input=json.dumps(cases), capture_output=True, text=True, check=True)
got = json.loads(result.stdout)
worst = max(abs(a - b) for case, js in zip(cases, got) for va, vb in zip(case["expect"], js) for a, b in zip(va, vb))
print("%d Fälle, größte Abweichung %.2e" % (len(cases), worst))

# group rotation: rotOf(matrixOf(rot)) must give the same orientation (matrix) for random rotations
group_code = source[source.index(" const mul="):source.index(" function turnGroup")]
check = functions + group_code + """
let worst=0;for(let i=0;i<500;i++){const r={plane:Math.random()*360,tilt:Math.random()*180-90,turn:Math.random()*360-180,flip:Math.random()<.5};
 const a=matrixOf(r),b=matrixOf(rotOf(a));a.forEach((row,i)=>row.forEach((v,j)=>worst=Math.max(worst,Math.abs(v-b[i][j]))))}
console.log(worst)"""
round_trip = float(subprocess.run(["node", "-e", check], capture_output=True, text=True, check=True).stdout)
print("Drehung zurückgerechnet: größte Abweichung %.2e (Winkel auf 1e-6° gerundet)" % round_trip)
worst = max(worst, round_trip / 1000.0)
sys.exit(0 if worst < 1e-9 else 1)
