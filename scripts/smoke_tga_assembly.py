"""Smoke test of TGA assemblies (Baugruppe) and the strict suitability (read-only on a temp copy of the data).
python scripts/smoke_tga_assembly.py
"""
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
FAILED = []
ASM = "tga-component:verteilerdose-up-3x-wago-3-polig"
MAIN = "tga-component:abzweigkasten-unterputz-95-mm-x-95-mm-schwarz-weiss-ip20"
WAGO = "tga-component:wago-verbindungsdosenklemme-3-polig-0-5-mm-2-5-mm-orange"


def check(name, ok, detail=""):
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else "  " + str(detail)))
    if not ok:
        FAILED.append(name)


def call(handle, command, **kw):
    return json.loads(handle(json.dumps(dict(kw, command=command))))


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get("nodes") or [])


def main():
    home = tempfile.mkdtemp(prefix="wg-asm-")
    for folder in ("catalog", "house"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(home, folder))
    os.environ["WEINGAERTEN_HOME"] = home
    from weingaerten_core.command_handler import handle
    from weingaerten_core.compute.tga_assembly import TgaAssembly
    validate = call(handle, "VALIDATE")
    errors = [e for e in validate["errors"] if ASM in e["where"] or "tga-tree" in e["where"]]
    check("Baugruppe und Bäume ohne Fehler", not errors, errors[:5])
    cat = call(handle, "TGA_CATALOG")
    asm = cat["assemblies"].get(ASM) or {}
    check("assemblies enthält die Baugruppe", asm.get("main") == MAIN, asm)
    check("max. Anschlüsse = 3", asm.get("capacity") == 3, asm.get("capacity"))
    check("Eignung vom Hauptobjekt", cat["placement"][ASM] == cat["placement"][MAIN], cat["placement"].get(ASM))
    none = [r for r, p in cat["placement"].items() if p["none"]]
    check("Objekte ohne Eignung erkannt (none)", all(not cat["placement"][r]["hosts"] for r in none), none[:3])
    nodes = [n for t in cat["trees"] for n in walk(t["nodes"]) if n.get("ref")]
    check("Bäume ohne abstrakte Objekte", not [n for n in nodes if n.get("deprecated")], [n["ref"] for n in nodes if n.get("deprecated")])
    check("Baum-Knoten der Baugruppe", any(n["ref"] == ASM and n["assembly"] for n in nodes))
    house = call(handle, "HOUSE")
    row = next((r for r in house["installation"]["catalog"] if r["ref"] == ASM), None)
    check("Baugruppe in der Palette (Einbau vom Hauptobjekt)", row is not None and row["shape"] == "box" and row["assembly"], row)
    storey = next(s for s in house["storeys"] if s["id"] == "ground")
    wall = next(w for w in storey["walls"] if w["category"] == "exterior_wall")
    box = {"id": "asm-box", "component": ASM, "storey": "ground", "host": {"wall": wall["id"], "face": "inside"},
           "u": 1.5, "z": 0.4, "depth": 0.0}
    answer = call(handle, "PART_SAVE", upsert=[box], delete=[])
    part = next((p for p in call(handle, "HOUSE")["installation"]["parts"] if p["id"] == "asm-box"), {})
    check("eingebaut als ein Teil mit Klemmen der Baugruppe", "error" not in answer and part.get("capacity") == 3
          and len(part.get("clamp_list") or []) == 3, (answer, part.get("capacity")))
    rows = {r["component"]: r["count"] for r in (call(handle, "BOM").get("installation") or {}).get("components", [])}
    check("Stückliste: Hauptobjekt 1, WAGO 3", rows.get(MAIN) == 1 and rows.get(WAGO) == 3 and ASM not in rows, rows)
    elements = {ASM: {"assembly": {"main": ASM, "parts": [{"ref": ASM}, {"ref": WAGO, "role": "L", "count": 2},
                                                              {"ref": MAIN, "role": "N"}]}}}
    elements.update({k: {"params": {"part_type": "clamp"}} for k in (WAGO,)})
    elements[MAIN] = {"install": {}}
    errs = TgaAssembly(elements).errors(elements[ASM])
    check("Validator: Verschachtelung, Anzahl, Leiter nur an Klemmen",
          any("kein Hauptobjekt" in e for e in errs) and any("Baugruppe in Baugruppe" in e for e in errs)
          and any("Anzahl 1" in e for e in errs) and any("nur bei Klemmen" in e for e in errs), errs)
    shutil.rmtree(home, ignore_errors=True)
    print("FAILED: %s" % FAILED if FAILED else "all ok")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
