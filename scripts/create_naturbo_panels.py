"""Create tga-class wall-heating-panel and the 7 naturbo Klima panel types D-L (idempotent).

Panel sizes and pipe direction from the naturbo laying sketch 260508_01DG_B; pipe spacing,
pipe length and port corners are estimates (no data sheet) and marked `estimated`.
"""
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parent.parent / "catalog"
DOC = "document:2026-06-16-naturbo-13202600675-lehmplatten-wandhzg"
SPACING = 0.10  # estimated pipe spacing of the meander

# type: (width, height, pipe_direction, port side, invoice pos, material offer index); port sides from the
# couplings drawn in the sketch (D/E end panels, F through panel, G/L ports right, I/K ports left)
TYPES = {
    "d": (0.625, 1.05, "horizontal", "bottom_right", 3, 0),
    "e": (0.625, 1.05, "horizontal", "bottom_left", 4, 0),
    "f": (0.625, 1.05, "horizontal", "bottom", 5, 0),
    "g": (1.25, 0.625, "horizontal", "right", 6, 1),
    "i": (1.25, 0.625, "horizontal", "left", 7, 1),
    "k": (1.25, 0.425, "horizontal", "left", 8, 2),
    "l": (1.25, 0.425, "horizontal", "right", 9, 2),
}

PANEL_CLASS = {
    "id": "wall-heating-panel",
    "name": "Wandheizungsplatte",
    "ifc": {"entity": "IfcSpaceHeater", "predefined_type": "RADIATOR"},
    "description": "Dämmplatte mit eingelegtem Heizrohr (Register); wird mit Lehm verputzt",
    "kind": "terminal",
    "parameters": [
        {"key": "panel_type", "name": "Plattentyp", "type": "text", "required": True},
        {"key": "width", "name": "Breite", "type": "length", "min": 0.1, "max": 3.0, "required": True},
        {"key": "height", "name": "Höhe", "type": "length", "min": 0.1, "max": 3.0, "required": True},
        {"key": "thickness", "name": "Dicke", "type": "length", "min": 0.01, "max": 0.2, "required": True},
        {"key": "pipe_direction", "name": "Rohrverlauf", "type": "choice",
         "options": ["vertical", "horizontal"], "required": True},
        {"key": "pipe_spacing", "name": "Rohrabstand", "type": "length", "min": 0.03, "max": 0.3, "required": False},
        {"key": "pipe_length", "name": "Rohrlänge je Platte", "type": "length", "min": 0.1, "max": 50, "required": False},
        {"key": "port_corner", "name": "Anschlussecke", "type": "choice",
         "options": ["bottom_left", "bottom_right", "bottom", "left", "right"], "required": False},
    ],
    "material_roles": [{"key": "board", "name": "Platte"}],
    "connection_rules": [
        {"line": "alu_composite", "medium": "heating", "method": "press",
         "partners": ["pipe", "fitting"],
         "note": "Rohrenden der Platte mit Presskupplung 11,6 an Nachbarplatte bzw. Anbindeleitung 16"},
    ],
}


def component(key, spec):
    width, height, direction, corner, pos, offer = spec
    run = height if direction == "vertical" else width
    across = width if direction == "vertical" else height
    pipe_length = round(run * round(across / SPACING) + across, 2)
    return {
        "id": "naturbo-klima-platte-%s" % key,
        "name": "Naturbo Klima-Dämmplatte Typ %s" % key.upper(),
        "class": "tga-class:wall-heating-panel",
        "din276": "420",
        "system_type": "Wandheizung",
        "catalog_material": "material:naturbo-klima-daemmplatte",
        "material_offer": offer,
        "params": {
            "panel_type": key.upper(),
            "width": width,
            "height": height,
            "thickness": 0.06,
            "pipe_direction": direction,
            "pipe_spacing": SPACING,
            "pipe_length": pipe_length,
            "port_corner": corner,
        },
        "estimated": True,
        "note": "Maße/Rohrverlauf/Anschlussseite aus Verlegeskizze 260508_01DG_B; Rohrabstand und Rohrlänge geschätzt;"
                " Preis Rechnung 13202600675 Pos. %d" % pos,
        "connection": {
            "line": "alu_composite",
            "ends": [
                {"id": "supply", "dn": 11.6, "gender": "spigot", "flow": "in"},
                {"id": "return", "dn": 11.6, "gender": "spigot", "flow": "out"},
            ],
        },
    }


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", path.relative_to(CATALOG))


def main():
    write(CATALOG / "tga-classes" / "wall-heating-panel.json", PANEL_CLASS)
    for key, spec in TYPES.items():
        data = component(key, spec)
        write(CATALOG / "tga-components" / (data["id"] + ".json"), data)


if __name__ == "__main__":
    main()
