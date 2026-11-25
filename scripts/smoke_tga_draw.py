"""Smoke test: drawing (layout.shapes), port angle rule, cut default length, tree folder filters (temp copy).

python scripts/smoke_tga_draw.py
"""
import copy
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
FAILED = []


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else "  " + str(detail)))
    if not ok:
        FAILED.append(name)


def call(handle, command, **kw):
    return json.loads(handle(json.dumps(dict(kw, command=command))))


def clean(element):
    element = copy.deepcopy(element)
    for key in ("ref", "type", "file", "material_product"):
        element.pop(key, None)
    return element


def main():
    home = tempfile.mkdtemp(prefix="wg-draw-")
    for folder in ("catalog", "house"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(home, folder))
    os.environ["WEINGAERTEN_HOME"] = home
    from weingaerten_core.command_handler import handle
    from weingaerten_core.compute.part_ports import PartPorts
    tga = call(handle, "TGA_CATALOG")
    ref = "tga-component:kaiser-up-geraetedose"
    box = clean(tga["elements"][ref])
    box["install"]["layout"] = dict(box["install"].get("layout") or {}, shapes=[
        {"kind": "circle", "x": 0, "y": 0, "r": 0.034}, {"kind": "line", "x": -0.02, "y": 0, "x2": 0.02, "y2": 0},
        {"kind": "text", "x": 0, "y": 0.01, "text": "UP", "size": 0.008}])
    answer = call(handle, "SAVE", ref=ref, element=box)
    check("SAVE mit Darstellung", "error" not in answer, answer)
    row = next(r for r in call(handle, "HOUSE")["installation"]["catalog"] if r["ref"] == ref)
    check("Palette liefert layout.shapes", len((row.get("layout") or {}).get("shapes") or []) == 3, row.get("layout"))
    bad = copy.deepcopy(box)
    bad["install"]["ports"] = bad["install"]["ports"] + [dict(bad["install"]["ports"][0])]
    check("doppelte Port-id abgelehnt", "error" in call(handle, "SAVE", ref=ref, element=bad))
    bad = copy.deepcopy(box)
    bad["install"]["ports"][0]["dir"] = [1, 1, 0]
    check("Richtung ohne Einheitsvektor abgelehnt", "error" in call(handle, "SAVE", ref=ref, element=bad))
    bad = copy.deepcopy(box)
    bad["install"]["layout"]["shapes"].append({"kind": "star", "x": 0, "y": 0})
    check("unbekannte Form abgelehnt", "error" in call(handle, "SAVE", ref=ref, element=bad))
    cable_ref = next(r for r, e in tga["elements"].items() if isinstance(e.get("cut"), dict))
    cable = clean(tga["elements"][cable_ref])
    cable["cut"] = {"max_length": 50}
    check("cut ohne Vorgabelänge abgelehnt", "error" in call(handle, "SAVE", ref=cable_ref, element=cable))
    cable["cut"] = {"max_length": 5, "default_length": 10}
    check("Vorgabelänge > max abgelehnt", "error" in call(handle, "SAVE", ref=cable_ref, element=cable))
    cable["cut"] = {"max_length": 50, "default_length": 1}
    check("cut 50 m / 1 m ok", "error" not in call(handle, "SAVE", ref=cable_ref, element=cable))
    # angle rule: right needs opposite directions, any accepts every angle
    a = {"position": [0, 0, 0], "direction": [1, 0, 0], "line": "ht"}
    b = {"position": [0, 0, 0], "direction": [0, 1, 0], "line": "ht"}
    check("rechtwinklig: schräg nicht verbunden", not PartPorts.seated(a, b))
    check("rechtwinklig: gegenüber verbunden", PartPorts.seated(a, dict(b, direction=[-1, 0, 0])))
    check("beliebig: schräg verbunden", PartPorts.seated(dict(a, angle="any"), b))
    check("Kabelende standardmäßig beliebig", PartPorts.angle_of({"line": "power"}) == "any")
    # tree folder filter
    tree = clean(tga["elements"]["tga-tree:elektro"])
    folder = next(n for n in tree["nodes"] if n.get("name") == "Leitungen")
    check("Ordner Leitungen hat Vorgabefilter", (folder.get("filter") or {}).get("class") == "tga-class:cable")
    bad = copy.deepcopy(tree)
    bad["nodes"][0]["filter"] = {"class": "tga-class:gibt-es-nicht"}
    check("Filter mit unbekannter Klasse abgelehnt", "error" in call(handle, "SAVE", ref="tga-tree:elektro", element=bad))
    shutil.rmtree(home, ignore_errors=True)
    print("FAILED: %s" % FAILED if FAILED else "alle Prüfungen ok")
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
