"""Smoke test of the EG stair (Wangentreppe, Viertelwendel links): parts, heights, winders, BOM, error cases."""
import json
import os
import shutil
import sys
import tempfile

ROOT = r"c:\Development\weingaerten"
sys.path.insert(0, os.path.join(ROOT, "code"))
import weingaerten_core  # noqa: E402

failures = []


def check(label, condition, detail=""):
    print(("ok   " if condition else "FAIL ") + label + ("" if condition else "  " + str(detail)))
    if not condition:
        failures.append(label)


def ask(command):
    return json.loads(weingaerten_core.handle(json.dumps(command)))


def near(a, b, eps=2e-3):
    return abs(a - b) < eps


def area(points):
    return abs(sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(points, points[1:] + points[:1]))) / 2


os.environ["WEINGAERTEN_HOME"] = ROOT
validate = ask({"command": "VALIDATE"})
check("VALIDATE ok", validate["ok"], validate["errors"][:3])
check("count stairs 2 (EG + KG)", validate["counts"].get("stairs") == 2, validate["counts"])
check("steep warning", any("steile Treppe" in w["message"] for w in validate["warnings"]))
ground = next(s for s in ask({"command": "HOUSE"})["storeys"] if s["id"] == "ground")
stair = ground["stairs"][0]
check("rise 2.95/16", near(stair["rise"], 2.95 / 16), stair["rise"])
check("going 1.825/11", near(stair["going"], (2.792 - 0.967) / 11), stair["going"])
check("counts", stair["counts"] == {"tread": 15, "riser": 15, "stringer": 2}, stair["counts"])
treads = [p for p in stair["parts"] if p["kind"] == "tread"]
check("last tread top = 15 rises", near(treads[-1]["z1"], 15 * 2.95 / 16), treads[-1]["z1"])
first = treads[0]
check("first tread at the east end", near(max(p[0] for p in first["footprint"]), 3.12), first["footprint"])
winders = treads[11:]
xs = [p[0] for t in winders for p in t["footprint"]]
ys = [p[1] for t in winders for p in t["footprint"]]
check("winders in the west square", min(xs) > 0.328 - 1e-6 and max(xs) < 1.295 + 1e-3 and min(ys) > 2.408 - 1e-6
      and max(ys) < 3.375 + 1e-6, (min(xs), max(xs), min(ys), max(ys)))
check("winder areas = square", near(sum(area(t["footprint"]) for t in winders), 0.967 ** 2, 1e-3))
last = winders[-1]["footprint"]
check("exit to the south edge", sum(1 for p in last if near(p[1], 3.375)) >= 2, last)
bom = ask({"command": "BOM"})
check("BOM stair row", bom["stairs"] and near(bom["stairs"][0]["volume"], stair["volume"], 2e-3))
check("BOM total", near(bom["totals"]["stair_volume"], sum(s["volume"] for s in bom["stairs"]), 2e-3))


def with_change(label, change, expected):
    tmp = tempfile.mkdtemp()
    try:
        for name in ("catalog", "house"):
            shutil.copytree(os.path.join(ROOT, name), os.path.join(tmp, name))
        path = os.path.join(tmp, "house", "storeys", "ground.json")
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        change(data["stairs"][0])
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
        os.environ["WEINGAERTEN_HOME"] = tmp
        messages = [x["message"] for x in ask({"command": "VALIDATE"})["errors"]]
        check(label, any(expected in m for m in messages), messages[:4])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


with_change("error target", lambda s: s.update(to_storey="storey:nope"), "unbekannt: storey:nope")
with_change("error material", lambda s: s.update(material="material:nope"), "unbekannt: material:nope")
with_change("error risers", lambda s: s.update(risers=17), "Maße ungültig")
with_change("error short run", lambda s: s["run"].update(straight_steps=20) or s.update(risers=25), "Lauf zu kurz")
os.environ["WEINGAERTEN_HOME"] = ROOT
print("FAILED: %s" % failures if failures else "all ok")
sys.exit(1 if failures else 0)
