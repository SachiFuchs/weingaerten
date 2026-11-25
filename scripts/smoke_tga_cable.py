"""Smoke test: drawing shape kind "cable" (ports from/to, bend points) in install.layout.shapes (temp copy).

python scripts/smoke_tga_cable.py
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
    home = tempfile.mkdtemp(prefix="wg-cable-")
    for folder in ("catalog", "house"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(home, folder))
    os.environ["WEINGAERTEN_HOME"] = home
    from weingaerten_core.command_handler import handle
    tga = call(handle, "TGA_CATALOG")
    ref = next(r for r, e in tga["elements"].items()
               if len(((e.get("install") or {}).get("ports") or [])) >= 2 and not e.get("abstract"))
    part = clean(tga["elements"][ref])
    a, b = [p["id"] for p in part["install"]["ports"][:2]]
    cable = {"kind": "cable", "from": a, "to": b, "points": [[0.01, 0.02]], "ends": [[0, 0], [0.02, 0]]}
    part["install"]["layout"] = dict(part["install"].get("layout") or {}, shapes=[cable])
    answer = call(handle, "SAVE", ref=ref, element=part)
    check("SAVE mit Kabel (%s)" % ref, "error" not in answer, answer)
    row = next((r for r in call(handle, "HOUSE")["installation"]["catalog"] if r["ref"] == ref), None)
    check("Palette liefert Kabelform", row is None or any(s.get("kind") == "cable" for s in (row.get("layout") or {}).get("shapes") or []),
          row and row.get("layout"))
    bad = copy.deepcopy(part)
    bad["install"]["layout"]["shapes"][0]["to"] = "gibt-es-nicht"
    check("unbekannter Anschlusspunkt abgelehnt", "error" in call(handle, "SAVE", ref=ref, element=bad))
    bad = copy.deepcopy(part)
    bad["install"]["layout"]["shapes"][0]["to"] = a
    check("gleicher Anfang/Ende abgelehnt", "error" in call(handle, "SAVE", ref=ref, element=bad))
    bad = copy.deepcopy(part)
    del bad["install"]["layout"]["shapes"][0]["from"]
    check("Kabel ohne from abgelehnt", "error" in call(handle, "SAVE", ref=ref, element=bad))
    bad = copy.deepcopy(part)
    bad["install"]["layout"]["shapes"].append({"kind": "rect", "w": 0.01, "h": 0.01})
    check("Rechteck ohne x/y abgelehnt", "error" in call(handle, "SAVE", ref=ref, element=bad))
    shutil.rmtree(home, ignore_errors=True)
    print("alle Prüfungen ok" if not FAILED else "FEHLER: %s" % ", ".join(FAILED))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
