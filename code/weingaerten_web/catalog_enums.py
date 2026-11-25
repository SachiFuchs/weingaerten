"""Choice lists and defaults embedded into the catalog and wall pages (used by the browser forms)."""
import logging

logger = logging.getLogger(__name__)

# CSS backgrounds that imitate the plan hatches in the browser forms
HATCH_CSS = {"masonry": "repeating-linear-gradient(45deg,rgba(80,30,10,.55) 0 1px,transparent 1px 6px)",
             "plaster": "radial-gradient(rgba(0,0,0,.35) 0.6px,transparent 0.8px) 0 0/4px 4px",
             "concrete": "radial-gradient(rgba(0,0,0,.45) 0.8px,transparent 1px) 0 0/7px 7px",
             "insulation": "repeating-linear-gradient(0deg,rgba(0,0,0,.25) 0 1px,transparent 1px 5px)",
             "wood": "repeating-linear-gradient(90deg,rgba(80,50,20,.4) 0 1px,transparent 1px 6px)"}

PANE_OPENING_NAMES = {"fixed": "fest", "turn_left": "Dreh links", "turn_right": "Dreh rechts", "tilt": "Kipp",
                      "tilt_turn_left": "Dreh-Kipp links", "tilt_turn_right": "Dreh-Kipp rechts", "pivot": "Schwing"}

# IFC4 occurrence entities with their PredefinedType values (USERDEFINED / NOTDEFINED are added by the form)
IFC_ENTITIES = {
    "IfcWall": ["STANDARD", "PARTITIONING", "SHEAR", "SOLIDWALL", "ELEMENTEDWALL", "PARAPET", "PLUMBINGWALL", "MOVABLE", "POLYGONAL"],
    "IfcSlab": ["FLOOR", "ROOF", "BASESLAB", "LANDING"],
    "IfcCovering": ["CEILING", "FLOORING", "CLADDING", "ROOFING", "MOLDING", "SKIRTINGBOARD", "INSULATION", "MEMBRANE",
                    "SLEEVING", "WRAPPING"],
    "IfcFooting": ["STRIP_FOOTING", "PAD_FOOTING", "FOOTING_BEAM", "PILE_CAP", "CAISSON_FOUNDATION"],
    "IfcPlate": ["CURTAIN_PANEL", "SHEET"],
    "IfcWindow": ["WINDOW", "SKYLIGHT", "LIGHTDOME"],
    "IfcDoor": ["DOOR", "GATE", "TRAPDOOR"],
    "IfcOpeningElement": ["OPENING", "RECESS"],
    "IfcBuildingElementProxy": ["ELEMENT", "COMPLEX", "PARTIAL", "PROVISIONFORVOID", "PROVISIONFORSPACE"],
    "IfcBeam": ["BEAM", "JOIST", "LINTEL", "HOLLOWCORE", "SPANDREL", "T_BEAM"],
    "IfcMember": ["MEMBER", "RAFTER", "PURLIN", "COLLAR", "BRACE", "CHORD", "MULLION", "PLATE", "POST", "STRINGER", "STRUT", "STUD"],
    "IfcColumn": ["COLUMN", "PILASTER"],
    "IfcChimney": [],
    "IfcRailing": ["HANDRAIL", "GUARDRAIL", "BALUSTRADE"],
    "IfcDiscreteAccessory": ["ANCHORPLATE", "BRACKET", "SHOE"],
    "IfcPipeSegment": ["RIGIDSEGMENT", "FLEXIBLESEGMENT", "GUTTER", "CULVERT", "SPOOL"],
}
# entities offered per catalog page
IFC_PAGE_ENTITIES = {
    "assembly": ["IfcWall", "IfcSlab", "IfcCovering", "IfcFooting", "IfcPlate"],
    "class": ["IfcWindow", "IfcDoor", "IfcOpeningElement", "IfcBuildingElementProxy", "IfcCovering", "IfcBeam", "IfcMember",
              "IfcColumn", "IfcPlate", "IfcChimney", "IfcRailing", "IfcDiscreteAccessory", "IfcPipeSegment"],
}
IFC_PAGE_ENTITIES["component"] = IFC_PAGE_ENTITIES["class"]

FORM_ENUMS = {
    "assembly_category": [["exterior_wall", "Außenwand"], ["interior_wall", "Innenwand"], ["base_slab", "Bodenplatte"],
                          ["slab", "Decke"], ["roof", "Dach"], ["plinth", "Sockel"], ["interior_lining", "Innendämmung"],
                          ["covering", "Belag"]],
    "layer_order": {"exterior_wall": "outside_in", "interior_wall": "left_right", "base_slab": "top_down",
                    "slab": "top_down", "roof": "top_down", "plinth": "top_down", "interior_lining": "wall_out",
                    "covering": "wall_out"},
    "layer_order_de": {"outside_in": "außen → innen", "left_right": "links → rechts", "top_down": "oben → unten",
                       "wall_out": "Wand → Raum"},
    "hatch": [["none", "keine"], ["plaster", "Putz"], ["masonry", "Mauerwerk"], ["concrete", "Beton"],
              ["insulation", "Dämmung"], ["wood", "Holz"]],
    "view": [["outer_layers", "äußere Schichten"], ["all_layers", "alle Schichten"], ["solid", "Volumen"]],
    "room_usage": [["NUF1", "NUF 1 Wohnen und Aufenthalt"], ["NUF2", "NUF 2 Büroarbeit"],
                   ["NUF3", "NUF 3 Produktion, Hand- und Maschinenarbeit"], ["NUF4", "NUF 4 Lagern, Verteilen, Verkaufen"],
                   ["NUF5", "NUF 5 Bildung, Unterricht, Kultur"], ["NUF6", "NUF 6 Heilen und Pflegen"],
                   ["NUF7", "NUF 7 Sonstige Nutzungen"], ["TF8", "TF 8 Technikfläche"], ["VF9", "VF 9 Verkehrsfläche"]],
    "shaft_purpose": [["supply", "Versorgung"], ["ventilation", "Lüftung"], ["chimney", "Kamin"], ["other", "Sonstiges"]],
    "hatch_css": HATCH_CSS,
    "ifc_entities": IFC_ENTITIES,
    "ifc_page_entities": IFC_PAGE_ENTITIES,
    "geometry": [["window", "Fenster"], ["door", "Tür"], ["box", "Quader"], ["passage", "Durchgang"]],
    "ptype": [["length", "Länge"], ["number", "Zahl"], ["choice", "Auswahl"], ["bool", "Ja/Nein"]],
    "recipe": {
        "window": [{"key": "width", "name": "Breite", "type": "length", "default": 1.0, "min": 0.3, "max": 4.0, "required": True},
                   {"key": "height", "name": "Höhe", "type": "length", "default": 1.2, "min": 0.3, "max": 3.0, "required": True},
                   {"key": "depth", "name": "Tiefe", "type": "length", "default": 0.08, "min": 0.04, "max": 0.3, "required": True},
                   {"key": "frame_width", "name": "Rahmenbreite", "type": "length", "default": 0.07, "min": 0.03, "max": 0.2, "required": True},
                   {"key": "sashes", "name": "Anzahl Flügel", "type": "choice", "default": 1, "options": [0, 1, 2, 3], "required": True}],
        "door": [{"key": "width", "name": "Breite", "type": "length", "default": 1.0, "min": 0.6, "max": 2.5, "required": True},
                 {"key": "height", "name": "Höhe", "type": "length", "default": 2.1, "min": 1.8, "max": 2.8, "required": True},
                 {"key": "depth", "name": "Tiefe", "type": "length", "default": 0.08, "min": 0.04, "max": 0.3, "required": True},
                 {"key": "frame_width", "name": "Rahmenbreite", "type": "length", "default": 0.07, "min": 0.03, "max": 0.2, "required": True},
                 {"key": "swing", "name": "Anschlag", "type": "choice", "default": "left", "options": ["left", "right"], "required": True}],
        "box": [{"key": "width", "name": "Breite", "type": "length", "default": 1.0, "required": True},
                {"key": "height", "name": "Höhe", "type": "length", "default": 1.0, "required": True},
                {"key": "depth", "name": "Tiefe", "type": "length", "default": 0.1, "required": True}],
        "passage": [{"key": "width", "name": "Breite", "type": "length", "default": 0.8, "min": 0.4, "max": 3.0, "required": True},
                    {"key": "height", "name": "Höhe", "type": "length", "default": 2.0, "min": 1.5, "max": 2.8, "required": True}]},
    "required_keys": {"window": ["width", "height", "depth", "frame_width", "sashes"],
                      "door": ["width", "height", "depth", "frame_width"], "box": ["width", "height", "depth"],
                      "passage": ["width", "height"]},
    "choice_de": {"sashes": {"0": "fest verglast", "1": "1 Flügel", "2": "2 Flügel", "3": "3 Flügel"},
                  "swing": {"left": "links", "right": "rechts"},
                  **{"opening_%d" % i: PANE_OPENING_NAMES for i in (1, 2, 3)}},
}
