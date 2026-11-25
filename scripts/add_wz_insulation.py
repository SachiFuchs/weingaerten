"""Adds the interior insulation (interior-insulation-ii1) on every exterior wall face of the ground storey that
borders the Wohnzimmer: one lining per contiguous Wohnzimmer segment of the inside face, full height."""
import json
import os
import sys

ROOT = r"c:\Development\weingaerten"
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["WEINGAERTEN_HOME"] = ROOT
import weingaerten_core  # noqa: E402

ASM = "assembly:interior-insulation-ii1"


def ask(command):
    return json.loads(weingaerten_core.handle(json.dumps(command)))


ground = next(s for s in ask({"command": "HOUSE"})["storeys"] if s["id"] == "ground")
wz = {r["id"] for r in ground["rooms"] if r["name"] == "Wohnzimmer"}
existing = {l["wall"] for l in ground.get("linings") or []}
for wall in ground["walls"]:
    if wall["category"] != "exterior_wall" or wall["id"] in existing:
        continue
    s, d = wall["start"], wall["direction"]
    import math
    dx, dy = math.cos(math.radians(d)), math.sin(math.radians(d))
    u_of = lambda p: (p[0] - s[0]) * dx + (p[1] - s[1]) * dy  # noqa: E731
    spans = sorted(tuple(sorted(u_of(p) for p in seg["line"])) for seg in wall["faces"]["inside"]["segments"]
                   if seg["room"] in wz)
    merged = []
    for a, b in spans:
        if merged and a <= merged[-1][1] + 1e-3:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    for n, (a, b) in enumerate(merged, 1):
        lining = {"id": "id-wz-%s%s" % (wall["id"].replace("w-", ""), "" if len(merged) == 1 else "-%d" % n),
                  "assembly": ASM, "face": "inside", "u0": round(a, 4), "u1": round(b, 4),
                  "note": "Innendämmung Wohnzimmer"}
        answer = ask({"command": "LINING_SAVE", "storey": "ground", "wall": wall["id"], "lining": lining, "create": True})
        print(wall["id"], lining["id"], "%.3f..%.3f" % (a, b), answer.get("error") or "ok", answer.get("errors") or "")
for l in next(s for s in ask({"command": "HOUSE"})["storeys"] if s["id"] == "ground")["linings"]:
    print("%-28s %-14s netto %.2f m² (brutto %.2f, ausgespart %s)" % (l["id"], l["wall"], l["area"], l["gross_area"],
                                                                       ", ".join(l["openings"]) or "-"))
