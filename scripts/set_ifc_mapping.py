"""Adds the IFC mapping (field `ifc`) to classes, assemblies, TGA classes and selected components.

Inserts one line after the top-level "name" line so the hand formatting of the files stays as is.
Files that already have a top-level "ifc" are left unchanged. Run with --write to change files.
"""
import json
import os
import re
import sys

HOME = os.environ.get("WEINGAERTEN_HOME", os.path.join(os.path.dirname(__file__), ".."))

# folder -> id -> (entity, predefined_type, object_type)
MAPPING = {
    "classes": {
        "window": ("IfcWindow", "WINDOW", None),
        "door": ("IfcDoor", "DOOR", None),
        "passage": ("IfcOpeningElement", "OPENING", None),
        "roof-part": ("IfcBuildingElementProxy", "ELEMENT", None),
    },
    "assemblies": {
        "base-slab-bs1": ("IfcSlab", "BASESLAB", None),
        "ceiling-lining-cl1": ("IfcCovering", "CEILING", None),
        "exterior-wall-ew1": ("IfcWall", "STANDARD", None),
        "exterior-wall-ew1-holz": ("IfcWall", "STANDARD", None),
        "exterior-wall-kw1": ("IfcWall", "STANDARD", None),
        "flat-roof-fd1": ("IfcSlab", "ROOF", None),
        "floor-eg-fbh": ("IfcCovering", "FLOORING", None),
        "floor-kg-beton": ("IfcSlab", "FLOOR", None),
        "interior-wall-iw1": ("IfcWall", "PARTITIONING", None),
        "interior-wall-iw2": ("IfcWall", "STANDARD", None),
        "interior-wall-kw2": ("IfcWall", "PARTITIONING", None),
        "roof-r1": ("IfcSlab", "ROOF", None),
        "terrace-roof-tr1": ("IfcSlab", "ROOF", None),
    },
    "tga-classes": {
        "pipe": ("IfcPipeSegment", "RIGIDSEGMENT", None),
        "cable": ("IfcCableSegment", "CABLESEGMENT", None),
        "duct": ("IfcDuctSegment", "RIGIDSEGMENT", None),
        "terminal": ("IfcFlowTerminal", None, None),
    },
    # overrides where the class mapping does not fit
    "components": {
        "door-balkon-kammer2": ("IfcDoor", "DOOR", None),
        "door-balkon-schlafzimmer": ("IfcDoor", "DOOR", None),
        "door-balkon-treppenzimmer": ("IfcDoor", "DOOR", None),
        "roof-window-velux-ck04": ("IfcWindow", "SKYLIGHT", None),
        "roof-window-velux-fk06": ("IfcWindow", "SKYLIGHT", None),
        "roof-gutter": ("IfcPipeSegment", "GUTTER", None),
        "roof-gutter-bracket": ("IfcDiscreteAccessory", "BRACKET", None),
        "roof-trimmer": ("IfcBeam", "BEAM", None),
        "roof-eaves-boards": ("IfcMember", "MEMBER", None),
        "roof-soffit-cladding": ("IfcCovering", "CLADDING", None),
        "roof-ridge": ("IfcCovering", "ROOFING", None),
        "roof-verge-tile": ("IfcCovering", "ROOFING", None),
        "chimney-cladding": ("IfcCovering", "CLADDING", None),
        "chimney-cap": ("IfcCovering", "USERDEFINED", "Kaminabdeckung"),
        "chimney-flashing": ("IfcCovering", "USERDEFINED", "Verwahrung"),
        "roof-eaves-flashing": ("IfcCovering", "USERDEFINED", "Einlaufblech"),
        "roof-flashing-velux-ck04": ("IfcCovering", "USERDEFINED", "Eindeckrahmen"),
        "roof-flashing-velux-fk06": ("IfcCovering", "USERDEFINED", "Eindeckrahmen"),
    },
}

NAME_LINE = re.compile(r'^(  "name"\s*:\s*"(?:[^"\\]|\\.)*",[ \t]*)(\r?\n)', re.M)


def ifc_line(entity, predefined, object_type):
    value = {"entity": entity}
    if predefined:
        value["predefined_type"] = predefined
    if object_type:
        value["object_type"] = object_type
    return '  "ifc": %s,' % json.dumps(value, ensure_ascii=False).replace("{", "{ ").replace("}", " }")


def update(path, mapping, write):
    raw = open(path, encoding="utf-8", newline="").read()
    if "ifc" in json.loads(raw):
        return "unchanged (has ifc)"
    match = NAME_LINE.search(raw)
    if not match:
        return "ERROR: no top-level name line"
    new = raw[:match.end()] + ifc_line(*mapping) + match.group(2) + raw[match.end():]
    json.loads(new)  # must stay valid JSON
    if write:
        open(path, "w", encoding="utf-8", newline="").write(new)
    return "added" if write else "would add"


def main():
    write = "--write" in sys.argv
    for folder, items in MAPPING.items():
        for element_id, mapping in items.items():
            path = os.path.join(HOME, "catalog", folder, element_id + ".json")
            result = update(path, mapping, write) if os.path.exists(path) else "ERROR: missing"
            print("%-12s %-28s %s" % (folder, element_id, result))


if __name__ == "__main__":
    main()
