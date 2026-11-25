"""Smoke test of floors + floor heating (read-only, real data): VALIDATE, HOUSE.floors/heating, BOM rows."""
import json
import os
import sys

sys.path.insert(0, os.path.join(r"c:\Development\weingaerten", "code"))
os.environ["WEINGAERTEN_HOME"] = os.environ.get("WEINGAERTEN_SMOKE_HOME", r"c:\Development\weingaerten")
import weingaerten_core as core  # noqa: E402


def call(command):
    return json.loads(core.handle(json.dumps({"command": command})))


failures = []


def check(condition, message):
    print(("ok   " if condition else "FAIL ") + message)
    if not condition:
        failures.append(message)


validate = call("VALIDATE")
own = [e for e in validate["errors"] + validate["warnings"] if ".heating" in e["where"] or "f-eg" in e["where"]
       or "floor" in e["where"]]
for issue in own:
    print("     issue:", issue)
check(not [e for e in validate["errors"] if ".heating" in e["where"] or "f-eg" in e["where"]], "no floor/heating errors")
check(validate["counts"].get("floors") == 2, "2 floors (EG + Kellerboden)")
check(validate["counts"].get("heating_circuits") == 7, "7 heating circuits")

ground = [s for s in call("HOUSE")["storeys"] if s["id"] == "ground"][0]
floor = ground["floors"][0]
check(abs(floor["thickness"] - 0.105) < 1e-6, "thickness 0.105 (%s)" % floor["thickness"])
names = [r["name"] for r in floor["rooms"]]
check(names.count("Wohnzimmer") == 1, "Wohnzimmer is one room")
print("     floor area %.2f m², edge %.2f m" % (floor["area"], floor["edge_length"]))
check(55 < floor["area"] < 65, "floor area about 60 m²")
heating = ground["heating"]
check(sum(1 for c in heating["circuits"] if c["room"] == "Wohnzimmer") == 4, "4 circuits in Wohnzimmer")
for c in heating["circuits"]:
    expected = c["area"] / c["spacing"]
    print("     %s %-24s %5.2f m² field %6.1f m feed %5.1f m total %6.1f m (area/spacing %.0f)"
          % (c["id"], c["name"], c["area"], c["length_field"], c["length_feed"], c["length"], expected))
    check(0.6 * expected < c["length_field"] < 1.3 * expected, "%s field length plausible" % c["id"])

bad = [c for c in heating["circuits"] if c["id"] == "hk6"][0]
cx, cy, cw, ch = bad["cutout"]
inside = [p for p in bad["field"] if cx + 0.01 < p[0] < cx + cw - 0.01 and cy + 0.01 < p[1] < cy + ch - 0.01]
check(not inside, "no Bad pipe point in the shower cutout")
south = [c for c in heating["circuits"] if c["id"] in ("hk2", "hk3", "hk4")]
check(all(abs(c["rect"][2] - 0.3 * 6.464) < 0.01 for c in south), "HK2-HK4 each 30 % of the south width")

bom = call("BOM")
check(len(bom["floors"]) == 2 and len(bom["heating"]) == 1, "BOM floors + heating rows")
offer = bom["floors"][0]["offer"]
print("     offer %.2f EUR, model %.2f EUR, pipe %.1f m" % (offer["offer_total"], offer["model_total"],
                                                         bom["totals"]["pipe_length"]))
check(abs(offer["offer_total"] - 4377.5) < 0.01, "offer total pos. 2-6 = 4377.50")
print("FAILED: %d" % len(failures) if failures else "ALL OK")
sys.exit(1 if failures else 0)
