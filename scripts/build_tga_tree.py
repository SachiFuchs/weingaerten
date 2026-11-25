"""Builds the TGA trees (catalog/tga-trees) and the abstract TGA objects from the current /waende palette.

- install-part class gets the parameters mounting / box_function; boxes get them as params (+ size text)
- cables get params cores / cross_section_mm2 (if missing) and the cut property (ring length from the name, else 50 m)
- boxes and cables get placement (estimated)
- abstract objects: one per cable type (axes cores, cross_section_mm2) and per box kind (Aufputz-, Unterputz-,
  Hohlwanddose: axes box_function, size; Herd-Anschlussdose: axis mounting)
- one tree per trade (Elektro, Abwasser, Zuwasser) from the palette paths; grouped variants -> abstract object

python scripts/build_tga_tree.py [--write]
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ.setdefault("WEINGAERTEN_HOME", ROOT)
from weingaerten_core.command_handler import handle  # noqa: E402

COMPONENTS = os.path.join(ROOT, "catalog", "tga-components")
CLASSES = os.path.join(ROOT, "catalog", "tga-classes")
TREES = os.path.join(ROOT, "catalog", "tga-trees")
TREE_IDS = {"Elektro": ("elektro", 1), "Abwasser": ("abwasser", 2), "Zuwasser": ("zuwasser", 3)}
BOX_PARAMS = [
    {"key": "mounting", "name": "Montage", "type": "choice", "options": ["surface", "flush", "hollow_wall"],
     "required": False},
    {"key": "box_function", "name": "Dosenart", "type": "choice", "options": ["junction", "device", "cooker"],
     "required": False}]
MODES = {"surface": ["on"], "flush": ["in"], "hollow_wall": ["in"]}
BOX_ABSTRACTS = [
    ("abstrakt-aufputzdose", "Aufputzdose", {"mounting": "surface"}, ["box_function", "size"]),
    ("abstrakt-unterputzdose", "Unterputzdose", {"mounting": "flush"}, ["box_function", "size"]),
    ("abstrakt-hohlwanddose", "Hohlwanddose", {"mounting": "hollow_wall"}, ["box_function", "size"]),
    ("abstrakt-herd-anschlussdose", "Herd-Anschlussdose", {"box_function": "cooker"}, ["mounting"])]
AXIS_LABELS = {"cores": ("Pole", None), "cross_section_mm2": ("Querschnitt", "mm²"), "box_function": ("Dosenart", None),
               "size": ("Größe", None), "mounting": ("Montage", None)}
CHANGED = {}


def path_of(folder, eid):
    return os.path.join(folder, eid + ".json")


def load(folder, eid):
    with open(path_of(folder, eid), encoding="utf-8") as f:
        return json.load(f)


def slug(text):
    text = text.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-") or "x"


def put(folder, element):
    CHANGED[path_of(folder, element["id"])] = element


def component(eid):
    path = path_of(COMPONENTS, eid)
    return CHANGED.get(path) or load(COMPONENTS, eid)


def boxes(rows):
    for row in [r for r in rows if r.get("box")]:
        element = component(row["ref"].split(":", 1)[1])
        params = element.setdefault("params", {})
        params.setdefault("mounting", row["box"]["mounting"])
        params.setdefault("box_function", "cooker" if row["box"]["cooker"] else row["box"]["function"])
        if not params.get("size") and row.get("size"):
            params["size"] = "%d × %d × %d mm" % tuple(round(v * 1000) for v in row["size"])
        element.setdefault("placement", {"hosts": ["wall", "ceiling"], "modes": MODES[params["mounting"]],
                                         "estimated": True})
        put(COMPONENTS, element)


def cables(rows):
    for row in [r for r in rows if r["shape"] == "cable"]:
        element = component(row["ref"].split(":", 1)[1])
        params = element.setdefault("params", {})
        params.setdefault("cores", row["cores"])
        if row.get("cross_section") is not None:
            params.setdefault("cross_section_mm2", row["cross_section"])
        ring = re.search(r"(\d+(?:[.,]\d+)?)\s*m\b", element.get("name") or "")
        max_length = float(ring.group(1).replace(",", ".")) if ring else 50.0
        element.setdefault("cut", {"max_length": max_length, "default_length": 1.0})
        element.setdefault("placement", {"hosts": ["wall", "floor", "ceiling", "roof"], "modes": ["in", "on"],
                                         "estimated": True})
        put(COMPONENTS, element)


def abstract(eid, name, rep, fixed, axes, default=None):
    element = {"id": eid, "name": name, "class": rep["class"], "din276": rep["din276"],
               "system_type": rep["system_type"], "params": fixed,
               "abstract": {"axes": [dict({"param": a, "label": AXIS_LABELS.get(a, (a, None))[0]},
                                          **({"unit": AXIS_LABELS[a][1]} if AXIS_LABELS.get(a, (0, None))[1] else {}))
                                     for a in axes]},
               "note": "abstraktes TGA-Objekt (scripts/build_tga_tree.py)"}
    if default:
        element["abstract"]["default"] = default
    put(COMPONENTS, element)
    return "tga-component:" + eid


def abstracts(rows):
    # ref of the palette representative -> ref of its abstract object
    by_rep = {}
    for row in [r for r in rows if r.get("variants") and r["shape"] == "cable"]:
        rep = component(row["ref"].split(":", 1)[1])
        by_rep[row["ref"]] = abstract("abstrakt-kabel-" + slug(row["cable_type"]), row["cable_type"], rep,
                                      {"cable_type": row["cable_type"]}, ["cores", "cross_section_mm2"], row["ref"])
    groups = {r.get("group_name"): r for r in rows if r.get("variants") and r.get("box")}
    for eid, name, fixed, axes in BOX_ABSTRACTS:
        members = [r for r in rows if r.get("box") and all(component(r["ref"].split(":", 1)[1])["params"].get(k) == v
                                                           for k, v in fixed.items())]
        if not members:
            continue
        rep = groups.get(name) or members[0]
        ref = abstract(eid, name, component(rep["ref"].split(":", 1)[1]), dict({"part_type": "box"}, **fixed), axes,
                       rep["ref"] if rep in members else None)
        by_rep[eid] = ref
    return by_rep


def insert(nodes, path, leaf):
    for name in path:
        folder = next((n for n in nodes if n.get("name") == name and "nodes" in n), None)
        if folder is None:
            folder = {"id": slug(name), "name": name, "nodes": []}
            nodes.append(folder)
        nodes = folder["nodes"]
    if not any(n.get("ref") == leaf["ref"] for n in nodes):
        nodes.append(leaf)


def trees(rows, by_rep):
    out = {}
    for row in rows:
        if row.get("variant_group") and not row.get("palette"):
            continue
        if row.get("box"):
            continue
        ref = by_rep.get(row["ref"], row["ref"])
        for path in row["paths"]:
            insert(out.setdefault(path[0], []), path[1:], {"id": slug(ref.split(":", 1)[1]), "ref": ref})
    verteiler = [v for k, v in by_rep.items() if k.startswith("abstrakt-")]
    for ref in verteiler:
        insert(out.setdefault("Elektro", []), ["Verteiler"], {"id": slug(ref.split(":", 1)[1]), "ref": ref})
    result = []
    for name, nodes in out.items():
        eid, order = TREE_IDS.get(name, (slug(name), 9))
        result.append({"id": eid, "name": name, "order": order, "nodes": nodes})
    return result


def main():
    write = "--write" in sys.argv
    house = json.loads(handle(json.dumps({"command": "HOUSE"})))
    installation = house.get("installation") or {}
    rows = installation.get("catalog") or []
    part_class = load(CLASSES, "install-part")
    keys = {p["key"] for p in part_class["parameters"]}
    part_class["parameters"] += [p for p in BOX_PARAMS if p["key"] not in keys]
    put(CLASSES, part_class)
    boxes(rows)
    cables(rows)
    by_rep = abstracts(rows)
    os.makedirs(TREES, exist_ok=True) if write else None
    for tree in trees(rows, by_rep):
        put(TREES, tree)
    for path, element in sorted(CHANGED.items()):
        print(("schreibe " if write else "würde schreiben ") + os.path.relpath(path, ROOT))
        if write:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(element, f, ensure_ascii=False, indent=2)
                f.write("\n")


if __name__ == "__main__":
    main()
