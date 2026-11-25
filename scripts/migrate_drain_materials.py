"""Turn the HT/KG drain and PP-R materials (shop imports, no DN/angle) into tga-components with params.

The material stays (documents and receipts point at it); the new tga-component has the same id, the product block of
the material and `catalog_material` pointing back. DN, angle and length are parsed from the id; the connection block
(ends, flow) is written afterwards by scripts/fill_connection_rules.py.

    python scripts/migrate_drain_materials.py          # dry run
    python scripts/migrate_drain_materials.py --write
"""
import json
import os
import re
import sys

ROOT = r"c:\Development\weingaerten"
MATERIALS = os.path.join(ROOT, "catalog", "materials")
TARGET = os.path.join(ROOT, "catalog", "tga-components")

OD = {30: 0.032, 40: 0.04, 50: 0.05, 75: 0.075, 90: 0.09, 110: 0.11, 125: 0.125, 160: 0.16, 20: 0.02}
Z_LENGTH = 0.03   # Baulänge je Anschluss, geschätzt (nicht im Shop angegeben)


def _line(mid):
    if mid.startswith(("pp-r-", "ppr-")):
        return "ppr"
    return "kg" if ("kanalgrund" in mid or mid.startswith("kg-")) else "ht"


def _pipe(line, dn, length_mm):
    return ("pipe", {"nominal_size_dn": dn, "outer_diameter": OD[dn], "medium": "waste_water", "system_line": line},
            {"lengths": [round(length_mm / 1000.0, 3)], "cuttable": True})


def _fitting(kind, line, dn, **extra):
    params = {"fitting_type": kind, "system_line": line, "dn": dn, "z_length": Z_LENGTH}
    params.update(extra)
    return ("pipe-fitting", params, None)


# (regex on the material id, builder) - first match wins
RULES = [
    (r"^marley-ht-rohr-mit-steckmuffe-dn-(\d+)-.*?(\d+)-mm$", lambda m, l: _pipe(l, int(m[1]), int(m[2]))),
    (r"^ht-rohr-dn-(\d+)-(\d+)-mm$", lambda m, l: _pipe(l, int(m[1]), int(m[2]))),
    (r"^marley-kanalgrundrohr-dn-(\d+)-(1-000|500)-mm$", lambda m, l: _pipe(l, int(m[1]), int(m[2].replace("-", "")))),
    (r"^kg-rohr-dn-(\d+)-(\d+)-mm$", lambda m, l: _pipe(l, int(m[1]), int(m[2]))),
    (r"^marley-ht-bogen-(\d+)(?:deg|-grad)-dn-(\d+)", lambda m, l: _fitting("bend", l, int(m[2]), angle=int(m[1]))),
    (r"^(?:ht-b|kg)-bogen-(\d+)-dn-(\d+)-mm$", lambda m, l: _fitting("bend", l, int(m[2]), angle=int(m[1]))),
    (r"^marley-kanalgrundrohr-bogen-(\d+)-grad-dn-(\d+)$", lambda m, l: _fitting("bend", l, int(m[2]), angle=int(m[1]))),
    (r"einfachabzweig(?:-rohr)?-(\d+)(?:deg|-grad)-dn-(\d+)-(\d+)$",
     lambda m, l: _fitting("branch", l, int(m[2]), angle=int(m[1]), dn_branch=int(m[3]))),
    (r"^ht-ea-abzweig-(\d+)-dn-(\d+)-(\d+)-mm$",
     lambda m, l: _fitting("branch", l, int(m[2]), angle=int(m[1]), dn_branch=int(m[3]))),
    (r"^marley-abfluss-abzweig-(\d+)-mm-(\d+)-mm-(\d+)deg$",
     lambda m, l: _fitting("branch", l, int(m[1]), angle=int(m[3]), dn_branch=int(m[2]))),
    (r"uebergangsrohr-exzentrisch-dn-(\d+)-(\d+)$",
     lambda m, l: _fitting("adapter", l, int(m[1]), line_to=l, dn_to=int(m[2]))),
    (r"muffenstopfen-dn-(\d+)", lambda m, l: _fitting("plug", l, int(m[1]))),
    (r"^kg-ueberschiebmuffe-dn-(\d+)-mm$", lambda m, l: _fitting("coupling", l, int(m[1]))),
    (r"gummimanschette-dn-(\d+)-(\d+)", lambda m, l: _fitting("adapter", l, int(m[1]), line_to="other", dn_to=int(m[2]))),
    (r"anschlussstueck-an-metallrohr(?:-dn-(\d+)-(\d+))?$",
     lambda m, l: _fitting("adapter", l, int(m[1] or 40), line_to="metal", dn_to=int(m[2] or 40))),
    (r"^pp-r-schweissmuffe-dn-(\d+)$", lambda m, l: _fitting("coupling", l, int(m[1]))),
    (r"^pp-r-schweisswinkel-dn-(\d+)-(\d+)$", lambda m, l: _fitting("bend", l, int(m[1]), angle=int(m[2]))),
    (r"^pp-r-schweiss-t-stueck-dn-(\d+)$", lambda m, l: _fitting("branch", l, int(m[1]), angle=90, dn_branch=int(m[1]))),
    (r"^pp-r-schweiss-endkappe-dn-(\d+)$", lambda m, l: _fitting("plug", l, int(m[1]))),
    (r"^pp-r-schweiss-uebergangsstueck-dn-(\d+)-(ig|ag)-1-2$",
     lambda m, l: _fitting("adapter", l, int(m[1]), line_to="thread", dn_to=15)),
    (r"^pp-r-schweiss-(kugelhahn)-dn-(\d+)$", lambda m, l: ("install-part", {"part_type": "valve", "size": "DN %s" % m[2]}, None)),
    (r"^pp-r-ventil-set-dn-(\d+)-handrad$", lambda m, l: ("install-part", {"part_type": "valve", "size": "DN %s" % m[1]}, None)),
    (r"^pp-r-(?:schweiss-wandscheibe|montageeinheit)-dn-(\d+)-ig-1-2$",
     lambda m, l: ("terminal", {"terminal_type": "wall_plate", "mounting": "flush"}, None)),
]


def build(mid, material):
    line = _line(mid)
    for pattern, maker in RULES:
        match = re.search(pattern, mid)
        if match:
            cls, params, stock = maker(match, line)
            break
    else:
        return None
    water = line == "ppr"
    element = {"id": mid, "name": material["name"], "class": "tga-class:" + cls,
               "din276": "412" if water else "411", "system_type": "Trinkwasser" if water else "Abwasser",
               "params": params}
    if material.get("description"):
        element["description"] = material["description"]
    if stock:
        element["stock"] = stock
    for key in ("photos", "imported_from", "product"):
        if material.get(key):
            element[key] = material[key]
    element["catalog_material"] = "material:" + mid
    element["note"] = "aus Material übernommen (scripts/migrate_drain_materials.py); Baulänge geschätzt"
    return element


def main(write):
    made, skipped = 0, []
    for name in sorted(os.listdir(MATERIALS)):
        mid = name[:-5]
        if not re.search(r"^(marley-(ht|kanalgrund|abfluss)|ht-|kg-|pp-r-)", mid):
            continue
        with open(os.path.join(MATERIALS, name), encoding="utf-8") as handle:
            material = json.load(handle)
        element = build(mid, material)
        if element is None:
            skipped.append(mid)
            continue
        path = os.path.join(TARGET, mid + ".json")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as handle:
                old = json.load(handle)
            # keep what the fill script or the web form added later
            for key in ("connection", "install", "estimated"):
                if key in old:
                    element[key] = old[key]
            if old == element:
                continue
        made += 1
        print(("write " if write else "would write ") + mid, element["class"], json.dumps(element["params"]))
        if write:
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(element, ensure_ascii=False, indent=2) + "\n")
    print("%d components, skipped (no connection article): %s" % (made, ", ".join(skipped)))


if __name__ == "__main__":
    main("--write" in sys.argv)
