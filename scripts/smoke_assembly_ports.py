"""Smoke test: tga assembly max_connections (allowed connection points) and "used in assemblies" data (temp copy).

python scripts/smoke_assembly_ports.py
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
REF = "tga-component:verteilerdose-up-3x-wago-3-polig"


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else "  " + str(detail)))
    if not ok:
        FAILED.append(name)


def call(handle, command, **kw):
    return json.loads(handle(json.dumps(dict(kw, command=command))))


def main():
    home = tempfile.mkdtemp(prefix="wg-asmports-")
    for folder in ("catalog", "house"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(home, folder))
    os.environ["WEINGAERTEN_HOME"] = home
    from weingaerten_core.command_handler import handle
    tga = call(handle, "TGA_CATALOG")
    element = copy.deepcopy(tga["elements"][REF])
    for key in ("ref", "type", "file", "material_product"):
        element.pop(key, None)
    ports = tga["assemblies"][REF]["main_ports"]
    check("Hauptobjekt hat Anschlusspunkte", ports > 0, ports)
    element["assembly"]["max_connections"] = 2
    answer = call(handle, "SAVE", ref=REF, element=element)
    check("SAVE mit 2 erlaubten Anschlusspunkten", "error" not in answer, answer)
    row = call(handle, "TGA_CATALOG")["assemblies"][REF]
    check("Kapazität = 2", row["capacity"] == 2 and row["max_connections"] == 2, row)
    element["assembly"]["max_connections"] = ports + 1
    check("mehr als Anschlusspunkte abgelehnt", "error" in call(handle, "SAVE", ref=REF, element=element))
    element["assembly"]["max_connections"] = 0
    check("0 abgelehnt", "error" in call(handle, "SAVE", ref=REF, element=element))
    shutil.rmtree(home, ignore_errors=True)
    print("alle Prüfungen ok" if not FAILED else "FEHLER: %s" % ", ".join(FAILED))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
