"""Smoke test of box clamps per conductor (part.clamps): active entries, wire warnings, BOM clamp rows.

Runs on a temp copy of catalog + house (WEINGAERTEN_HOME), the project data stays unchanged.
"""
import json
import os
import shutil
import sys
import tempfile

ROOT = r"c:\Development\weingaerten"
sys.path.insert(0, os.path.join(ROOT, "code"))
import weingaerten_core  # noqa: E402

failures = []
W3 = "tga-component:wago-verbindungsdosenklemme-3-polig-0-5-mm-2-5-mm-orange"
W5 = "tga-component:wago-hebelklemme-0-2-4-mm2-5-polig-5-stueck"


def ask(command):
    return json.loads(weingaerten_core.handle(json.dumps(command)))


def check(name, condition, detail=""):
    print(("ok   " if condition else "FAIL ") + name + ("" if condition else "  " + str(detail)))
    if not condition:
        failures.append(name)


temp = tempfile.mkdtemp()
try:
    for folder in ("catalog", "house"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(temp, folder), ignore=shutil.ignore_patterns("imported_*"))
    os.environ["WEINGAERTEN_HOME"] = temp
    house = ask({"command": "HOUSE"})
    inst = house["installation"]
    choices = {c["ref"]: c for c in inst["clamps"]}
    check("Klemmenauswahl 3- und 5-polig", choices.get(W3, {}).get("poles") == 3 and choices.get(W5, {}).get("poles") == 5,
          sorted(choices))
    cat = {c["ref"]: c for c in inst["catalog"]}
    storey = next(s for s in house["storeys"] if s["id"] == "ground")
    wall = next(w for w in storey["walls"] if w["category"] == "exterior_wall")
    base = {"storey": "ground", "host": {"wall": wall["id"], "face": "inside"}, "u": 1.5, "z": 0.4, "depth": 0.0}
    top = next(q["pos"] for q in cat["tga-component:kaiser-up-geraetedose"]["ports"] if q["id"] == "top")
    cable = dict(base, id="k-cab", component="tga-component:cable-nym-3x15", u=1.5 + top[0], z=0.4 + top[1], depth=top[2],
                 rot={"plane": 90}, length=0.5)

    def run(clamps):
        box = dict(base, id="k-box", component="tga-component:kaiser-up-geraetedose")
        if clamps is not None:
            box["clamps"] = clamps
        answer = ask({"command": "PART_SAVE", "upsert": [box, cable], "delete": []})
        model = ask({"command": "HOUSE"})
        part = next(p for p in model["installation"]["parts"] if p["id"] == "k-box")
        return answer, part, json.dumps(ask({"command": "VALIDATE"}), ensure_ascii=False)

    answer, part, _ = run(None)
    check("ohne Klemmen: alle Einführungen aktiv", "error" not in answer and all(q["active"] for q in part["ports"]), answer)

    answer, part, issues = run([{"role": r, "clamp": W3} for r in ("L", "N", "PE")])
    entries = [q for q in part["ports"] if q.get("cores")]
    check("3-polig: Kapazität 3", part["capacity"] == 3, part.get("capacity"))
    check("3-polig: 3 von %d Einführungen aktiv" % len(entries), sum(q["active"] for q in entries) == min(3, len(entries)))
    check("verbundene Einführung bleibt aktiv", next(q for q in part["ports"] if q["id"] == "top")["active"])
    check("inaktive Einführung Status inactive", all(q["status"] == "inactive" for q in entries if not q["active"]))
    check("jede Klemme 1 Ader", [c["wires"] for c in part["clamp_list"]] == [1, 1, 1], part["clamp_list"])

    answer, part, issues = run([{"role": r, "clamp": W5} for r in ("L", "N", "PE")])
    check("5-polig: Kapazität 5, alle Einführungen aktiv", part["capacity"] == 5 and all(q["active"] for q in part["ports"]))

    answer, part, issues = run([{"role": "L", "clamp": W5}, {"role": "N", "clamp": W5}])
    check("PE ohne Klemme gewarnt", "Leiter PE" in issues and "ohne Klemme" in issues)

    answer = ask({"command": "PART_SAVE", "upsert": [dict(base, id="k-box", component="tga-component:kaiser-up-geraetedose",
                                                          clamps=[{"role": "L", "clamp": "tga-component:cable-nym-3x15"}])],
                  "delete": []})
    check("keine Klemme -> abgelehnt", "error" in answer, answer)

    run([{"role": r, "clamp": W3} for r in ("L", "N", "PE")])
    bom = ask({"command": "BOM"})
    row = next((r for r in (bom.get("installation") or {}).get("components", []) if r["component"] == W3), None)
    check("Stückliste: 3 Klemmen 3-polig", row and row["count"] == 3 and row["shape"] == "clamp", row)
finally:
    os.environ.pop("WEINGAERTEN_HOME", None)
    shutil.rmtree(temp, ignore_errors=True)
print("alles ok" if not failures else "FEHLER: %s" % failures)
sys.exit(1 if failures else 0)
