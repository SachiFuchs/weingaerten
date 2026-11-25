"""Calibrate the roof covering overhangs against the invoice (Schuck Dach RE 17.07.2023) and print the comparison.

Read-only: computes the covering in a fresh temp copy per (eaves, verge) pair (the core caches per home)."""
import json
import os
import shutil
import sys
import tempfile

ROOT = r"c:\Development\weingaerten"
sys.path.insert(0, os.path.join(ROOT, "code"))
import weingaerten_core  # noqa: E402

INVOICE = {"area": 130.0, "ridge": 10.0, "verge": 22.0, "eaves": 24.0}


def covering(eaves, verge):
    tmp = tempfile.mkdtemp()
    try:
        for name in ("catalog", "house"):
            shutil.copytree(os.path.join(ROOT, name), os.path.join(tmp, name))
        path = os.path.join(tmp, "house", "storeys", "upper.json")
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        data["roof_covering"]["eaves_overhang"], data["roof_covering"]["verge_overhang"] = eaves, verge
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
        os.environ["WEINGAERTEN_HOME"] = tmp
        house = json.loads(weingaerten_core.handle(json.dumps({"command": "HOUSE"})))
        return next(s for s in house["storeys"] if s["id"] == "upper")["roof_covering"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


best = None
for e10 in range(5, 16):
    for v10 in range(3, 16):
        c = covering(e10 / 10, v10 / 10)
        values = {"area": c["area"], **c["edges"]}
        s = sum(((values[k] - v) / v) ** 2 for k, v in INVOICE.items())
        if best is None or s < best[0]:
            best = (s, e10 / 10, v10 / 10, values)
print("best eaves %.1f verge %.1f score %.4f" % (best[1], best[2], best[0]))
for k, v in INVOICE.items():
    print("  %-6s model %7.2f invoice %7.2f diff %+7.2f" % (k, best[3][k], v, best[3][k] - v))
