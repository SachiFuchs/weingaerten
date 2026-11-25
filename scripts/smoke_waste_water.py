"""Smoke test waste water (Abwasser): runs, slopes, penetrations, overrides, fittings and cutting (stage 1 + 2).

Runs the core directly on temp copies of catalog/ and house/ (one fresh copy per variant).
Usage: python scripts/smoke_waste_water.py
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

FAILURES = []


def check(condition, message):
    print(("ok   " if condition else "FAIL ") + message)
    if not condition:
        FAILURES.append(message)


def compute(edit=None):
    home = tempfile.mkdtemp(prefix="ww_")
    try:
        for sub in ("catalog", "house"):
            shutil.copytree(os.path.join(ROOT, sub), os.path.join(home, sub),
                            ignore=shutil.ignore_patterns("imported_*"))
        if edit:
            edit(home)
        model = ModelLoader(home).load()
        ModelComputer(model).compute()
        return model
    finally:
        shutil.rmtree(home, ignore_errors=True)


def edit_json(home, relative, change):
    path = os.path.join(home, *relative.split("/"))
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    change(data)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle)


def ww_issues(model, kind):
    return [i for i in model[kind] if any(k in i["where"] for k in ("tga", "penetrations", "aw-"))]


def stage1():
    model = compute()
    ww = model["waste_water"]
    check(ww is not None and len(ww["runs"]) == 10, "10 Abwasserleitungen berechnet")
    check(not ww_issues(model, "errors"), "keine Abwasser-Fehler %s" % ww_issues(model, "errors"))
    check(not [w for w in ww_issues(model, "warnings") if "Gefälle" in w["message"]], "alle Gefälle >= Mindestgefälle")
    through = {(p["element"], p["run"]) for p in ww["penetrations"] if p["kind"] == "through"}
    expected = {("wall:ground/w-east", "aw-bad-wc"),
                ("wall:ground/w-east", "aw-bad-dusche"), ("ceiling:ground/c-eg", "aw-kueche-fall"),
                ("floor:ground/f-eg", "aw-kueche-fall"), ("foundation:main", "aw-kueche-fall"),
                ("wall:basement/w-kg-ost", "aw-kueche-kg")}
    check(expected <= through, "Durchbrüche Außenwand Bad, EG-Decke, EG-Boden, Bodenplatte, Kellerwand (fehlt: %s)"
          % sorted(expected - through))
    check(not any(p[1] == "aw-grund-ost" for p in through), "Grundleitung außen ohne Durchbruch")
    drill = {p["run"]: p["core_drill"] for p in ww["penetrations"] if p["kind"] == "through"}
    check(abs(drill["aw-kueche-kg"] - 0.13) < 1e-9 and abs(drill["aw-bad-dusche"] - 0.07) < 1e-9,
          "Kernbohrung = Außendurchmesser + 2 cm (KG 13 cm, HT50 7 cm)")
    check(any(p["kind"] == "embedded" and p["run"] == "aw-bad-dusche" for p in ww["penetrations"]),
          "Duschleitung im Estrich als 'im Bauteil verlegt'")
    check(all(p["airtight"] for p in ww["penetrations"] if p["element"].startswith("wall:ground/w-east")),
          "Außenwand-Durchbrüche abdichten")
    return model


def stage1_variants():
    def overrides(home):
        edit_json(home, "house/penetrations.json", lambda d: d["items"].extend([
            {"element": "wall:ground/w-east", "source": "tga-run:aw-bad-wc", "index": 0, "kind": "through",
             "sealing": "Manschette"},
            {"element": "wall:ground/w-north", "source": "tga-run:aw-bad-wc", "index": 0, "kind": "through"}]))
    model = compute(overrides)
    hit = [p for p in model["waste_water"]["penetrations"] if p["run"] == "aw-bad-wc" and p["kind"] == "through"][0]
    check(hit.get("sealing") == "Manschette", "Override aus penetrations.json übernommen")
    check(any("verwaist" in w["message"] for w in model["warnings"]), "verwaister Override -> Warnung")

    def rising(home):
        edit_json(home, "house/tga/runs/aw-bad-wc.json", lambda d: d["points"][1].__setitem__(2, 0.30))
    model = compute(rising)
    check(any("Gegengefälle" in e["message"] for e in model["errors"]), "steigende Leitung -> Fehler Gegengefälle")

    def flat(home):
        edit_json(home, "house/tga/runs/aw-grund-ost.json", lambda d: d["points"][1].__setitem__(2, -0.70))
    model = compute(flat)
    check(any("Gefälle 0,0" in w["message"] or "Gefälle 0.0" in w["message"] for w in model["warnings"]),
          "Grundleitung ohne Gefälle -> Warnung")

    def off_axis(home):
        edit_json(home, "house/tga/runs/aw-kueche-spuele.json", lambda d: d["points"][-1].__setitem__(0, 6.80))
    model = compute(off_axis)
    check(any("nicht auf der Achse" in e["message"] for e in model["errors"]), "Abzweig neben der Achse -> Fehler")


def stage2(model):
    ww = model["waste_water"]
    parts = ww["parts"]
    if not parts and not ww["cuts"]:
        print("skip Stufe 2 (keine Formteile berechnet)")
        return
    check(not [w for w in ww_issues(model, "warnings") if "Sortiment" in w["message"]],
          "alle Winkel und Abzweige aus dem Sortiment auflösbar")
    by_run = {}
    for cut in ww["cuts"]:
        by_run.setdefault(cut["run"], []).append(cut)
    for run in ww["runs"]:
        cuts = by_run.get(run["id"], [])
        pieces = sum(sum(c["pieces"]) for c in cuts)
        deduction = sum(c["deduction"] for c in cuts)
        check(abs(pieces + deduction - run["length"]) < 0.002,
              "%s: Stücke %.3f + Abzug %.3f = Länge %.3f" % (run["id"], pieces, deduction, run["length"]))
    for run in ww["runs"]:
        bends = [p for p in parts if p["run"] == run["id"] and p["fitting_type"] == "bend"]
        knees = len(run["points"]) - 2
        check(len({p["at"] for p in bends}) == knees, "%s: jeder Knick (%d) hat Bögen" % (run["id"], knees))
    branches = [p for p in parts if p["fitting_type"] == "branch"]
    check(len(branches) == sum(1 for r in ww["runs"] if r["into"] and r["into"]["kind"] == "branch"),
          "ein Abzweig je einmündender Leitung")
    adapters = [p for p in parts if p["fitting_type"] == "adapter"]
    check(len(adapters) == 3, "3 Übergänge HT DN 90 -> KG DN 110 (WC, Sammelleitung, Küche)")
    sticks = {s["component"]: s for s in ww["stock"] if s["kind"] == "pipe"}
    check(all(s["count"] > 0 for s in sticks.values()), "Stangen je Rohr gezählt")
    pipe_lengths = {s["component"]: s["length"] for s in ww["stock"] if s["kind"] == "pipe"}
    check(all(any(abs(s["length"] - l) < 1e-9 for l in (2.0, 1.0, 0.5, 0.25)) for s in ww["stock"] if s["kind"] == "pipe"),
          "Stangen nur in lieferbaren Längen %s" % pipe_lengths)


if __name__ == "__main__":
    base = stage1()
    stage1_variants()
    stage2(base)
    print("FAILED: %d" % len(FAILURES) if FAILURES else "all ok")
    sys.exit(1 if FAILURES else 0)
