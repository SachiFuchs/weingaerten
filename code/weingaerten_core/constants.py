"""Fixed patterns and tables of the house core (references, catalog folders, layer orders, class recipes)."""
import logging
import re

logger = logging.getLogger(__name__)

ID_PATTERN = r"[a-z0-9]+(-[a-z0-9]+)*"
ID_RE = re.compile("^" + ID_PATTERN + "$")
REF_RE = re.compile(r"^(material|assembly|class|component|company|document|storey):(" + ID_PATTERN + ")$")
EDIT_RE = re.compile(r"^(material|assembly|class|component|company|tga-class|tga-component|tga-tree):(" + ID_PATTERN + ")$")
# TGA catalog folders (loaded by TgaLoader into model["tga"], editable through SAVE / DELETE)
TGA_FOLDERS = {"tga-classes": "tga-class", "tga-components": "tga-component", "tga-trees": "tga-tree"}

# catalog folder -> element type of the files in it
CATALOG_FOLDERS = {"materials": "material", "assemblies": "assembly",
                   "classes": "class", "components": "component", "companies": "company",
                   "documents": "document"}
TYPE_ORDER = ["material", "assembly", "class", "component", "company", "document"]

LAYER_ORDER_BY_CATEGORY = {"exterior_wall": "outside_in", "interior_wall": "left_right", "base_slab": "top_down",
                           "slab": "top_down", "roof": "top_down", "plinth": "top_down", "interior_lining": "wall_out",
                           "covering": "wall_out"}

# parameters (key, type) a class of the given geometry must define so the drawing recipe works
RECIPE_PARAMETERS = {
    "window": [("width", "length"), ("height", "length"), ("depth", "length"), ("frame_width", "length"),
               ("sashes", "choice")],
    "door": [("width", "length"), ("height", "length"), ("depth", "length"), ("frame_width", "length")],
    "box": [("width", "length"), ("height", "length"), ("depth", "length")],
    "passage": [("width", "length"), ("height", "length")],
}
# class geometries a component must have to be placed in a wall opening
OPENING_GEOMETRIES = ("window", "door", "passage")

TOLERANCE = 0.001
# DIN 277 usage groups of a room (Nutzungsfläche 1-7, Technikfläche, Verkehrsfläche)
ROOM_USAGES = {"NUF1": "Wohnen und Aufenthalt", "NUF2": "Büroarbeit", "NUF3": "Produktion, Hand- und Maschinenarbeit",
               "NUF4": "Lagern, Verteilen und Verkaufen", "NUF5": "Bildung, Unterricht und Kultur",
               "NUF6": "Heilen und Pflegen", "NUF7": "Sonstige Nutzungen", "TF8": "Technikfläche",
               "VF9": "Verkehrsfläche"}
PANE_OPENING_TYPES = {"fixed", "turn_left", "turn_right", "tilt", "tilt_turn_left", "tilt_turn_right", "pivot"}

READ_COMMANDS = ("CATALOG", "ELEMENT", "RESOLVE", "HOUSE", "BOM", "USAGE", "TGA_CATALOG")
WRITE_COMMANDS = ("SAVE", "DELETE", "OPENING_SAVE", "OPENING_DELETE", "LINING_SAVE", "LINING_DELETE", "WALLS_SAVE",
                  "ROOM_SAVE", "ROOM_DELETE", "SHAFT_SAVE", "SHAFT_DELETE", "PART_SAVE", "PART_DELETE")
