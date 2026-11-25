"""Fixed tables of the web server: patterns, menu, catalog pages, routes."""
import logging
import re

logger = logging.getLogger(__name__)

CORE_MISSING = "Weingärten-Core fehlt – weingaerten-core.md ausführen"
LIBRARY_FILES = ("three.module.js", "OrbitControls.js")

REF_RE = re.compile(r"^(material|assembly|class|component|company|document|storey):[a-z0-9]+(-[a-z0-9]+)*$")
EDIT_RE = re.compile(r"^(material|assembly|class|component|company|tga-class|tga-component):[a-z0-9]+(-[a-z0-9]+)*$")
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
CATALOG_TYPES = ("material", "assembly", "class", "component", "company", "document")

# (label, url, is sub entry)
MENU = [("Haus 3D", "/haus3d", 0), ("Grundriss", "/grundriss", 0), ("Wände", "/waende", 0), ("Räume", "/raeume", 0),
        ("Katalog", "/katalog", 0),
        ("Materialien", "/katalog/materialien", 1), ("Aufbauten", "/katalog/aufbauten", 1),
        ("Bauteile", "/katalog/bauteile", 1),
        ("Klassen", "/katalog/klassen", 1), ("Firmen", "/katalog/firmen", 1),
        ("Dokumente", "/katalog/dokumente", 1), ("TGA", "/katalog/tga", 1),
        ("Mengen", "/mengen", 0), ("Benutzerhandbuch", "/handbuch", 0), ("Tech.Doku", "/techdoku", 0), ("About", "/about", 0)]

# catalog page slug -> (element type, title, label of the "new" button)
CATALOG_PAGES = {"materialien": ("material", "Materialien", "+ Material"), "aufbauten": ("assembly", "Aufbauten", "+ Aufbau"),
                 "bauteile": ("component", "Bauteile", "+ Bauteil"), "klassen": ("class", "Klassen", "+ Klasse"),
                 "firmen": ("company", "Firmen", "+ Firma"),
                 "dokumente": ("document", "Dokumente", "")}  # documents are read-only: no "new" button

REDIRECTS = {"/": "/haus3d", "/katalog": "/katalog/materialien", "/doku": "/handbuch"}

API_COMMANDS = {"/api/house": "HOUSE", "/api/catalog": "CATALOG", "/api/resolve": "RESOLVE",
                "/api/validate": "VALIDATE", "/api/bom": "BOM", "/api/usage": "USAGE",
                "/api/element/save": "SAVE", "/api/element/delete": "DELETE",
                "/api/opening/save": "OPENING_SAVE", "/api/opening/delete": "OPENING_DELETE",
                "/api/lining/save": "LINING_SAVE", "/api/lining/delete": "LINING_DELETE",
                "/api/walls/save": "WALLS_SAVE", "/api/room/save": "ROOM_SAVE", "/api/room/delete": "ROOM_DELETE",
                "/api/shaft/save": "SHAFT_SAVE", "/api/shaft/delete": "SHAFT_DELETE",
                "/api/part/save": "PART_SAVE", "/api/part/delete": "PART_DELETE"}

MAX_BODY_BYTES = 65536
