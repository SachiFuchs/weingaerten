"""Smoke test wall heating (naturbo Lehm-Wandheizung DG): panels, circuits, prices, BOM and the checks.

Runs the core directly on temp copies of catalog/ and house/ (one fresh copy per variant).
Usage: python scripts/smoke_wall_heating.py
"""
import json
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
UPPER = os.path.join("house", "storeys", "upper.json")


def check(condition, message):
    print(("ok   " if condition else "FAIL ") + message)
    if not condition:
        FAILURES.append(message)


def compute(edit=None):
    home = tempfile.mkdtemp(prefix="wh_")
    try:
        for sub in ("catalog", "house"):
            shutil.copytree(os.path.join(ROOT, sub), os.path.join(home, sub),
                            ignore=shutil.ignore_patterns("imported_*"))
        if edit:
            path = os.path.join(home, UPPER)
            with open(path, encoding="utf-8") as f:
                storey = json.load(f)
            edit(storey)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(storey, f, ensure_ascii=False)
        model = ModelLoader(home).load()
        ModelComputer(model).compute()
        return model
    finally:
        shutil.rmtree(home, ignore_errors=True)


def upper(model):
    return next(s for s in model["storeys_out"] if s["id"] == "upper")


def issues(model, kind):
    return [i for i in model[kind] if ".wall_heating" in i["where"]]


def main():
    model = compute()
    heating = upper(model)["wall_heating"]
    check(heating is not None, "DG hat wall_heating")
    check(not issues(model, "errors"), "keine Fehler (%s)" % issues(model, "errors"))
    counts = " ".join("%s%d" % kv for kv in heating["counts"].items())
    check(counts == "D7 E2 F1 G3 I8 K8 L3", "Plattentypen D7 E2 F1 G3 I8 K8 L3 (%s)" % counts)
    check(heating["panel_count"] == 32, "32 Platten = 32 Pressfenster-Einleger")
    check(abs(heating["area"] - 21.0) < 0.01, "Heizfläche 21,00 m² (%.3f)" % heating["area"])
    circuits = {c["id"]: c for c in heating["circuits"]}
    check(sorted(circuits) == ["hk01", "hk02", "hk03", "hk04"], "4 Heizkreise")
    output = sum(c["design_output"] for c in heating["circuits"])
    check(abs(output - 1822.81) < 0.05, "Heizleistung 1822,8 W (%.2f)" % output)
    for cid, area in (("hk01", 6.5625), ("hk02", 5.90625), ("hk03", 4.59375), ("hk04", 3.9375)):
        check(abs(circuits[cid]["area"] - area) < 0.001, "%s Fläche %.3f m²" % (cid, area))
    check(heating["adapters"] == 16 and heating["couplings"] == 24, "16 Übergänge 11,6/16, 24 Plattenkupplungen")
    check(len(heating["fields"]) == 8, "8 Plattenfelder")
    check(all(len(p["pipe"]) >= 4 for f in heating["fields"] for p in f["panels"]), "jede Platte hat einen Rohrmäander")
    check(all(f["feed_supply"] and f["feed_return"] for f in heating["fields"]), "jedes Feld hat Vor- und Rücklauf")
    # Heizschleifen: D = 10 Lagen, Zu-/Abfluss auf der Anschlussseite (oben seitlich raus, unten nach unten raus)
    tga = model["tga"]["elements"]
    exits = lambda p: 2 if (tga[p["component"]].get("params") or {}).get("port_exits") and not p["rotated"] else 0
    runs = {}
    for p in (p for f in heating["fields"] for p in f["panels"]):
        runs.setdefault(p["type"], set()).add((len(p["pipe"]) - exits(p)) // 2)
    runs = {t: min(v) if len(v) == 1 else sorted(v) for t, v in runs.items()}
    check(runs.get("D") == 10 and runs.get("E") == 10 and runs.get("F") == 10 and runs.get("G") == 6
          and runs.get("K") == 4, "Heizschleifen: Lagen je Typ %s" % runs)
    d = next(p for f in heating["fields"] for p in f["panels"] if p["type"] == "D" and not p["rotated"])
    u_of = lambda q: (q[0] - d["corners"][0][0]) ** 2 + (q[1] - d["corners"][0][1]) ** 2
    first, last, z_low = d["pipe"][0], d["pipe"][-1], d["corners"][0][2]
    check(abs(last[2] - z_low) < 1e-6 and abs(first[2] - z_low) > 0.9
          and abs(u_of(first) ** 0.5 - u_of(last) ** 0.5) < 0.1,
          "Typ D: oberer Austritt seitlich, unterer nach unten, beide auf der Anschlussseite")
    # Verbindungen: Schleifenende -> Schleifenanfang der nächsten Platte, Kupplung unterhalb der Platten
    same = lambda a, b: all(abs(x - y) < 1e-9 for x, y in zip(a, b))
    links_ok = all(same(k["points"][0], f["panels"][k["from"]]["pipe"][-1])
                   and same(k["points"][-1], f["panels"][k["to"]]["pipe"][0])
                   and k["position"][2] < min(p["z0"] for p in f["panels"]) + upper(model)["elevation"]
                   for f in heating["fields"] for k in f["links"])
    check(links_ok, "Verbindungen von Schleifenende zu Schleifenanfang, Kupplung unter den Platten")
    rooms = {r["name"] for r in upper(model)["rooms"]}
    check({"Treppenzimmer", "Bad DG"} <= rooms and "Durchgangszimmer" not in rooms, "Durchgangszimmer aufgeteilt")

    bom = BillOfMaterials(model).build()
    row = bom["wall_heating"][0]
    prices = {i["type"]: i["unit_price"] for i in row["items"] if i["kind"] == "panel"}
    check(prices == {"D": 78.62, "E": 78.62, "F": 78.62, "G": 93.59, "I": 93.59, "K": 63.64, "L": 63.64},
          "Preis je Typ über material_offer (%s)" % prices)
    panel_price = sum(i["price"] for i in row["items"] if i["kind"] == "panel")
    check(abs(panel_price - 2515.73) < 0.01, "Platten 2515,73 € netto = Rechnung Pos. 3–9 (%.2f)" % panel_price)
    check(abs(bom["totals"]["wall_heating_area"] - 21.0) < 0.01, "totals.wall_heating_area")
    check(bom["totals"]["wall_heating_panels"] == 32, "totals.wall_heating_panels")
    plaster = next(m for m in bom["materials"] if m["material"] == "material:naturbo-lehm-finishputz-weiss")
    check(plaster["area_inside"] >= 21.0 - 0.01, "Lehm-Finishputz Fläche aus der Wandheizung")

    # checks
    def overlap(storey):
        storey["wall_heating"]["fields"][4]["panels"][0]["u"] = 0.8
    check(any("überlappen" in i["message"] for i in issues(compute(overlap), "errors")), "Platten überlappen -> Fehler")

    def roof(storey):
        for p in storey["wall_heating"]["fields"][1]["panels"]:
            p["z"] += 0.5
    check(any("Dachschräge" in i["message"] for i in issues(compute(roof), "errors")), "Platte über der Dachschräge -> Fehler")

    def unknown(storey):
        storey["wall_heating"]["fields"][0]["panels"][0]["type"] = "X"
    check(any("Plattentyp unbekannt" in i["message"] for i in issues(compute(unknown), "errors")), "Plattentyp unbekannt")

    def outlets(storey):
        storey["wall_heating"]["distributor"]["outlets"] = 3
    check(any("Abgänge" in i["message"] for i in issues(compute(outlets), "errors")), "zu wenig Verteilerabgänge")

    def area(storey):
        storey["wall_heating"]["circuits"][0]["design_area"] = 8.0
    check(any("Auslegung" in i["message"] for i in issues(compute(area), "warnings")), "Heizfläche weicht von Auslegung ab -> Warnung")

    def room(storey):
        storey["wall_heating"]["fields"][4]["room"] = "Treppenzimmer"
    check(any("nicht im Raum" in i["message"] for i in issues(compute(room), "errors")), "Feld im falschen Raum -> Fehler")

    print("\n%s" % ("all checks passed" if not FAILURES else "%d FAILED" % len(FAILURES)))
    for w in issues(model, "warnings"):
        print("  Warnung:", w["where"], w["message"])
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
