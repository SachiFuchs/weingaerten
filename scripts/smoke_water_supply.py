"""Smoke test drinking water (Zuwasser) version 1: kitchen PPR DN 20 cold + hot, crossing loop, fittings, stock.

Runs the core directly on a temp copy of catalog/ and house/.
Usage: python scripts/smoke_water_supply.py
"""
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
from weingaerten_core.compute.model_computer import ModelComputer  # noqa: E402
from weingaerten_core.model.model_loader import ModelLoader  # noqa: E402
from weingaerten_core.queries.bill_of_materials import BillOfMaterials  # noqa: E402

FAILURES = []


def check(condition, message):
    print(("ok   " if condition else "FAIL ") + message)
    if not condition:
        FAILURES.append(message)


def compute():
    home = tempfile.mkdtemp(prefix="tw_")
    try:
        for sub in ("catalog", "house"):
            shutil.copytree(os.path.join(ROOT, sub), os.path.join(home, sub), ignore=shutil.ignore_patterns("imported_*"))
        model = ModelLoader(home).load()
        ModelComputer(model).compute()
        return model
    finally:
        shutil.rmtree(home, ignore_errors=True)


def main():
    model = compute()
    tw = model.get("water_supply")
    check(tw is not None and len(tw["runs"]) == 9, "9 Trinkwasserleitungen")
    if not tw:
        return
    runs = {r["id"]: r for r in tw["runs"]}
    issues = [i for i in model["errors"] + model["warnings"] if "tw-" in i["where"] or "ws-" in i["where"]]
    check(not issues, "keine Zuwasser-Meldungen %s" % issues)
    check({r["medium"] for r in tw["runs"]} == {"cold_water", "hot_water"}, "Medien kalt + warm")
    check(max(p[2] for p in runs["tw-steig-cold"]["points"]) > 2.95, "Steigleitung kalt bis ins DG")
    check(max(p[2] for p in runs["tw-steig-hot"]["points"]) > 2.95, "Steigleitung warm bis ins DG")
    looped = sorted((l["run"], round(l["position"][0], 2), round(l["position"][1], 2)) for l in tw["loops"])
    check(len(looped) == 4, "4 Kreuzungsschleifen %s" % looped)
    check(all(l[0] in ("tw-eg-hot", "tw-wb-hot") for l in looped), "Schleifen nur an Warmleitungen")
    wb = [l for l in tw["loops"] if l["run"] == "tw-wb-hot"]
    check(wb and min(p[1] for p in wb[0]["points"]) < 2.03 - 0.02, "Waschbecken-Schleife weicht von der Wand weg (-y)")
    main_hot = [l for l in tw["loops"] if l["run"] == "tw-eg-hot"]
    check(main_hot and all(min(p[0] for p in l["points"]) < 6.742 - 0.02 for l in main_hot),
          "Schleifen an der Ostwand weichen in den Raum aus (-x)")
    count = lambda kind: sum(1 for p in tw["parts"] if p["fitting_type"] == kind)  # noqa: E731
    check(count("branch") == 7, "7 T-Stücke (%d)" % count("branch"))
    check(count("plug") == 4, "4 Endkappen: Keller + DG (%d)" % count("plug"))
    check(sum(1 for p in tw["parts"] if p["fitting_type"] == "bend" and p["angle"] == 45) == 16, "16 x 45°")
    stock = {s["component"]: s for s in tw["stock"]}
    check(stock["tga-component:ppr-wall-plate-20"]["count"] == 7, "7 Wandscheiben")
    through = {p["element"] for p in tw["penetrations"] if p["kind"] == "through"}
    check("foundation:main" in through, "Durchbruch Bodenplatte")
    check(any("iw-alt-nord-ost" in e for e in through), "Durchbruch Wand Bad/Küche %s" % sorted(through))
    bom = BillOfMaterials(model).build()
    check(bom["water_supply"] and bom["totals"]["water_supply_length"] > 20, "BOM Zuwasser %.2f m" %
          bom["totals"]["water_supply_length"])
    check(model["waste_water"] is not None and len(model["waste_water"]["runs"]) == 10, "Abwasser unverändert 10 Leitungen")
    for r in tw["runs"]:
        print("     %s %.3f m" % (r["id"], r["length"]))


if __name__ == "__main__":
    main()
    print("FAILURES: %d" % len(FAILURES))
    sys.exit(1 if FAILURES else 0)
