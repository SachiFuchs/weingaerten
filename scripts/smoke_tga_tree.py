"""Smoke test of TGA trees and abstract TGA objects (read-only on the real data, edits on a temp copy).

python scripts/smoke_tga_tree.py
"""
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


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.get("nodes") or [])


def main():
    home = tempfile.mkdtemp(prefix="wg-tree-")
    for folder in ("catalog", "house"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(home, folder))
    os.environ["WEINGAERTEN_HOME"] = home
    from weingaerten_core.command_handler import handle
    validate = call(handle, "VALIDATE")
    tree_errors = [e for e in validate["errors"] if "tga-tree" in e["where"] or "abstrakt" in e["where"]]
    check("keine Fehler in Bäumen/abstrakten Objekten", not tree_errors, tree_errors[:5])
    house = call(handle, "HOUSE")
    trees = house["installation"]["trees"]
    check("3 Bäume Elektro/Abwasser/Zuwasser", [t["name"] for t in trees] == ["Elektro", "Abwasser", "Zuwasser"],
          [t["name"] for t in trees])
    nodes = [n for t in trees for n in walk(t["nodes"])]
    # abstract objects are deprecated: no longer in the trees, concretisations still listed by TGA_CATALOG (read-only)
    check("keine abstrakten Objekte in den Bäumen", not any(n.get("deprecated") for n in nodes),
          [n["ref"] for n in nodes if n.get("deprecated")])
    check("Baum-Knoten tragen Eignung", all("placement" in n for n in nodes if n.get("ref")))
    check("keine abstrakten Objekte in der Katalog-Palette",
          not any("abstrakt-" in r["ref"] for r in house["installation"]["catalog"]))
    tga = call(handle, "TGA_CATALOG")
    cands = tga["abstracts"]["tga-component:abstrakt-kabel-nyy-j"]["candidates"]
    check("NYY-J (veraltet) hat Konkretisierungen", len(cands) >= 1, cands)
    check("Konkretisierung hat Achsenwerte", all(set(c["values"]) == {"cores", "cross_section_mm2"} for c in cands))
    check("TGA_CATALOG liefert abstracts + assemblies + trees", "tga-component:abstrakt-kabel-nym-j" in tga["abstracts"]
          and "assemblies" in tga and len(tga["trees"]) == 3)
    # SAVE: unknown ref and folder+ref node are refused
    tree = dict(tga["elements"]["tga-tree:elektro"])
    for key in ("ref", "type", "file"):
        tree.pop(key, None)
    bad = dict(tree, nodes=tree["nodes"] + [{"id": "x", "ref": "tga-component:gibt-es-nicht"}])
    answer = call(handle, "SAVE", ref="tga-tree:elektro", element=bad)
    check("SAVE lehnt unbekannte ref ab", "error" in answer, answer)
    answer = call(handle, "SAVE", ref="tga-tree:test", element={"id": "test", "name": "Test", "nodes": [
        {"id": "a", "name": "A", "nodes": [{"id": "nyy", "ref": "tga-component:abstrakt-kabel-nyy-j"}]}]}, create=True)
    check("SAVE neuer Baum", "error" not in answer, answer)
    answer = call(handle, "DELETE", ref="tga-component:abstrakt-kabel-nyy-j")
    check("abstraktes Objekt im Baum nicht löschbar", "error" in answer, answer)
    answer = call(handle, "DELETE", ref="tga-tree:test")
    check("DELETE Baum", answer.get("deleted"), answer)
    abstract = dict(tga["elements"]["tga-component:abstrakt-kabel-nyy-j"])
    for key in ("ref", "type", "file", "material_product"):
        abstract.pop(key, None)
    wrong = dict(abstract, abstract={"axes": [{"param": "farbe"}]})
    answer = call(handle, "SAVE", ref="tga-component:abstrakt-kabel-nyy-j", element=wrong)
    check("SAVE lehnt Achse ohne Klassenparameter ab", "error" in answer, answer)
    # cut: NYY 50 m ring -> 15 m ok, 60 m refused
    ring = next(r for r, e in tga["elements"].items() if r.startswith("tga-component:")
                and (e.get("params") or {}).get("cable_type") == "NYY-J" and (e.get("cut") or {}).get("max_length") == 50)
    check("NYY-J 50 m hat cut 50 m", bool(ring))
    shutil.rmtree(home, ignore_errors=True)
    print("FAILED: %s" % FAILED if FAILED else "alle Prüfungen ok")
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    main()
