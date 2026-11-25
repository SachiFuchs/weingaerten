"""Smoke test Elektrik: kitchen cables (HOUSE/BOM on the real data), builder rules on a synthetic model,
pages /mengen, /grundriss, /haus3d rendered in-process. Read-only."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["WEINGAERTEN_HOME"] = ROOT
from weingaerten_core.command_handler import handle  # noqa: E402
from weingaerten_core.compute.electrical_builder import ElectricalBuilder  # noqa: E402
from weingaerten_core.model.issue_log import IssueLog  # noqa: E402

FAILS = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else "  " + str(detail)))
    if not ok:
        FAILS.append(name)


def real_data():
    house = json.loads(handle(json.dumps({"command": "HOUSE"})))
    el = house.get("electrical")
    check("HOUSE.electrical vorhanden", bool(el))
    runs = {r["id"]: r for r in el["runs"]}
    check("2 Leitungen", set(runs) == {"el-kueche-dose", "el-kueche-herd"}, list(runs))
    dose, herd = runs["el-kueche-dose"], runs["el-kueche-herd"]
    check("Dose NYM-J 3x2,5", dose["label"] == "NYM-J 3x2,5", dose["label"])
    check("Herd NYM-J 5x2,5", herd["label"] == "NYM-J 5x2,5", herd["label"])
    check("Rohrlänge Dose 2,22 m", abs(dose["length"] - 2.22) < 0.005, dose["length"])
    check("Kabel = Rohr + 1,5 + 0,5", abs(dose["cable_length"] - dose["length"] - 2.0) < 1e-6)
    bends = {rid: sum(1 for p in el["parts"] if p["run"] == rid and p["fitting_type"] == "bend") for rid in runs}
    check("Bögen 2 / 3", bends == {"el-kueche-dose": 2, "el-kueche-herd": 3}, bends)
    check("alle Bögen 90°", all(p["angle"] == 90 for p in el["parts"] if p["fitting_type"] == "bend"))
    check("2 Dosen", {t["id"] for t in el["terminals"]} == {"el-dose-kueche", "el-dose-herd"})
    check("kein Kabel in KG-Wand", not any(p["element"].startswith("wall:basement") for p in el["penetrations"]),
          [p["element"] for p in el["penetrations"]])
    kinds = {s["kind"] for s in el["stock"]}
    check("Stückliste Kabel/Rohr/Formteile/Dosen", kinds == {"cable", "pipe", "fitting", "box"}, kinds)
    pipe = next(s for s in el["stock"] if s["kind"] == "pipe")
    check("2 Stangen M20 à 3 m", pipe["count"] == 2 and pipe["length"] == 3.0, pipe)
    bom = json.loads(handle(json.dumps({"command": "BOM"})))
    totals = bom["totals"]
    check("BOM electrical", bool(bom.get("electrical")) and len(bom["electrical"]["runs"]) == 2)
    check("Summe Kabel", abs(totals["electrical_cable_length"] - sum(r["cable_length"] for r in el["runs"])) < 0.01,
          totals["electrical_cable_length"])
    check("Preis > 0", totals["electrical_price"] > 0, totals["electrical_price"])
    validate = json.loads(handle(json.dumps({"command": "VALIDATE"})))
    bad = [i for i in validate.get("errors", []) + validate.get("warnings", [])
           if "el-" in i["where"] or "electr" in i["where"]]
    check("keine Elektrik-Meldungen", not bad, bad)
    check("Schacht kennt Elektro-Leitungen", not any("Leitung" in i["message"] and "el-kueche" in i["message"]
                                                    for i in validate.get("errors", [])))


def synthetic():
    elements = {
        "tga-class:cable": {"kind": "cable"},
        "tga-component:c": {"name": "NYM-J 5 x 16 mm² 50 m", "class": "tga-class:cable",
                            "params": {"cable_type": "NYM-J", "cores": 5, "cross_section_mm2": 16,
                                       "outer_diameter": 0.02},
                            "product": {"offers": [{"price": 100.0, "currency": "EUR"}]}},
        "tga-component:r": {"name": "Rohr", "params": {"part_type": "conduit", "size": "M20", "outer_diameter": 0.02,
                                                       "inner_diameter": 0.0175, "stock_length": 3.0}},
    }
    runs = {"tga-run:x": {"id": "x", "component": "tga-component:c", "conduit": {"pipe": "tga-component:r"},
                          "points": [[0, 0, 0], [7, 0, 0], [7, 1, 0.5]]}}
    model = {"tga": {"elements": elements, "terminals": {}, "runs": runs, "penetrations": []}, "storeys_out": []}
    log = {"errors": [], "warnings": []}
    out = ElectricalBuilder(model, IssueLog(log)).build()
    messages = [i["message"] for i in log["errors"] + log["warnings"]]
    check("Kabel zu dick -> Fehler", any("passt nicht" in m for m in messages), messages)
    check("schräge Strecke -> Warnung", any("achsparallel" in m for m in messages), messages)
    check("ohne Ende -> Warnung", any("ohne Endstelle" in m for m in messages), messages)
    check("7 m -> 2 Muffen", sum(1 for p in out["parts"] if p["fitting_type"] == "sleeve") == 2)
    check("Ringpreis je m (100 / 50)", out["stock"][0]["unit_price"] == 2.0, out["stock"][0])
    check("7 m + 1,12 m -> 3 Stangen (Reste 1,0 + 1,118 in einer)",
          next(s for s in out["stock"] if s["kind"] == "pipe")["count"] == 3,
          out["cuts"])


def pages():
    from weingaerten_web.web_application import ServerSettings, WebApplication
    app = WebApplication(ServerSettings.from_arguments(["8099"]))
    html = app.pages.render("/mengen", {})
    check("/mengen Elektrik", "<h2>Elektrik</h2>" in html and "Zuschnitt Schutzrohr" in html)
    html = app.pages.render("/grundriss", {})
    check("/grundriss Elektrik", 'class="electrical"' in html)
    html = app.pages.render("/haus3d", {})
    check("/haus3d Checkbox + Script", 'id="elektrik3d" checked' in html and "window.Electric3d" in html)


real_data()
synthetic()
pages()
print("FEHLER: %s" % FAILS if FAILS else "alle Prüfungen ok")
sys.exit(1 if FAILS else 0)
