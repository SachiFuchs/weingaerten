"""Installed parts (house/tga/parts): placement, ports, connections, slots and penetrations -> model["installation"]."""
import logging
import math
from typing import Any, Dict, List, Optional

from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from .box_clamps import BoxClamps
from .palette_tree import ROOTS, PaletteTree
from .part_frame import FACES, PartFrame
from .part_ports import PartPorts
from .penetration_builder import PenetrationBuilder
from .slot_builder import SlotBuilder
from .tga_assembly import TgaAssembly
from .tga_tree import TgaTree

logger = logging.getLogger(__name__)

COLORS = {"waste_water": "#9AA0A6", "cold_water": "#1B7F3B", "hot_water": "#8BC34A", "circulation": "#4CAF7A",
          "conduit": "#C9CDD2", "box": "#9EA3A8", "insert": "#F4F4F0", "cable": "#5F6368"}
CABLE_MAX_LENGTH = 50.0
TRADE_NAMES = {"electrical": "Elektro", "waste_water": "Abwasser", "water_supply": "Zuwasser"}
SURFACE_BOX_GROUP = "Aufputzdose"
FLUSH_BOX_GROUP = "Unterputzdose"
MOUNTINGS = ("flush", "hollow_wall", "surface")
COOKER_BOX_GROUP = "Herd-Anschlussdose"


class PartBuilder:
    """Places every part, matches the ports and derives slots and penetrations (after the TGA runs)."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the computed model (storeys_out, tga.parts, tga.elements).
            issues: receives part errors (kind "part") and warnings.
        """
        self._model = model
        self._issues = issues
        self._tga = model.get("tga") or {}
        self._storeys = {s["id"]: s for s in model.get("storeys_out") or []}
        self._assemblies = TgaAssembly(self._tga.get("elements") or {})

    def build(self) -> Dict[str, Any]:
        """Return `{catalog, cables, parts, slots, penetrations, open_ports}` (parts with world ports and their status)."""
        catalog = self._catalog()
        parts = [p for p in (self._place(ref, source) for ref, source in sorted((self._tga.get("parts") or {}).items()))
                 if p]
        PartPorts(self._issues).match(parts, self._storeys)
        tree = TgaTree(self._tga.get("elements") or {})
        for part in parts:
            warning = tree.placement_warning(part)
            if warning:
                self._issues.warning("tga-part:" + part["id"], warning)
        BoxClamps(self._tga.get("elements") or {}, self._issues).apply(parts)
        slots = SlotBuilder(self._model, self._issues).slots(parts)
        penetrations = self._penetrations(parts)
        logger.debug("installation: %d parts, %d slots, %d penetrations", len(parts), len(slots), len(penetrations))
        return {"catalog": catalog, "palette_roots": ROOTS, "trees": tree.trees(), "cables": self._cables(), "clamps": self._clamp_choices(),
                "parts": parts, "slots": slots,
                "penetrations": penetrations,
                "open_ports": sum(1 for p in parts for q in p["ports"] if q["status"] == "open")}

    def _cables(self) -> List[Dict[str, Any]]:
        # cables that can be pulled into a conduit part
        return [{"ref": ref, "name": e.get("name"), "cores": self._cores(e),
                 "cable_type": (e.get("params") or {}).get("cable_type"), "section": self._section(e)}
                for ref, e in sorted((self._tga.get("elements") or {}).items())
                if ref.startswith("tga-component:") and e.get("class") == "tga-class:cable" and not e.get("abstract")]

    def _clamp_choices(self) -> List[Dict[str, Any]]:
        # clamps that can be chosen per conductor in a box (part_type clamp with a pole count)
        rows = []
        for ref, e in sorted((self._tga.get("elements") or {}).items()):
            poles = (e.get("connection") or {}).get("poles")
            if ref.startswith("tga-component:") and (e.get("params") or {}).get("part_type") == "clamp" \
                    and JsonValues.is_number(poles):
                rows.append({"ref": ref, "name": e.get("name"), "poles": int(poles),
                             "cross_section": (e.get("connection") or {}).get("cross_section")})
        return rows

    @staticmethod
    def _section(element: Dict[str, Any]) -> Optional[float]:
        section = (element.get("params") or {}).get("cross_section_mm2")
        return float(section) if JsonValues.is_number(section) else None

    @staticmethod
    def _cores(element: Dict[str, Any]) -> int:
        # core count of a cable (param cores, else from the conductors, default 3)
        cores = (element.get("params") or {}).get("cores")
        conductors = (element.get("connection") or {}).get("conductors")
        return int(cores) if JsonValues.is_number(cores) else len(conductors) if isinstance(conductors, list) and conductors else 3

    def _catalog(self) -> List[Dict[str, Any]]:
        # the palette of the wall view: every tga-component with an install block (assemblies via their main object)
        rows = []
        for ref, raw in sorted((self._tga.get("elements") or {}).items()):
            element = self._assemblies.effective(raw)
            install = self.install_of(element) if ref.startswith("tga-component:") and not element.get("abstract") else None
            if not isinstance(install, dict):
                continue
            rows.append({"ref": ref, "name": element.get("name"), "trade": install.get("trade"),
                         "trade_name": TRADE_NAMES.get(install.get("trade")), "group": install.get("group"),
                         "paths": PaletteTree.paths(element, install),
                         "shape": install.get("shape"), "outer_diameter": install.get("outer_diameter"),
                         "size": install.get("size"), "stretch": install.get("stretch"), "ports": install.get("ports"),
                         "medium": (element.get("params") or {}).get("medium"),
                         "cable_type": (element.get("params") or {}).get("cable_type"),
                         "cores": self._cores(element) if install.get("shape") == "cable" else None,
                         "cross_section": self._section(element) if install.get("shape") == "cable" else None,
                         "box": self._box_kind(ref, element) if install.get("shape") == "box" and not raw.get("assembly") else None,
                         "assembly": TgaAssembly.is_assembly(raw),
                         "placement": TgaTree.placement_of(element), "layout": install.get("layout"),
                         "color": self._color(install, element, None), "estimated": bool(element.get("estimated"))})
        self._group_variants(rows)
        return rows

    def _group_variants(self, rows: List[Dict[str, Any]]) -> None:
        # NYM-J / NYY-J and the boxes appear once per kind in the palette (ring lengths, pack sizes and colours are
        # purchase details); the variant (cores x cross-section / box type and size) is chosen in the part panel
        for cable_type in sorted({r["cable_type"] for r in rows if r["shape"] == "cable" and r.get("cable_type")}):
            self._group(rows, cable_type, [r for r in rows if r["shape"] == "cable" and r.get("cable_type") == cable_type],
                        lambda r: (r["cores"], r["cross_section"] or 0.0),
                        lambda k: "%d × %s mm²" % (k[0], ("%g" % k[1]).replace(".", ",")), (3, 1.5),
                        "tga-component:cable-")
        boxes = [r for r in rows if r.get("box")]
        # Verteiler = three entries: Aufputzdose, Unterputzdose (flush + hollow wall), Herd-Anschlussdose
        self._group(rows, SURFACE_BOX_GROUP, [r for r in boxes if not r["box"]["cooker"] and r["box"]["mounting"] == "surface"],
                    self._box_key, self._box_label, "tga-component:abzweigkasten-80-mm-x-80-mm-x-37-mm-ip55", None)
        self._group(rows, FLUSH_BOX_GROUP, [r for r in boxes if not r["box"]["cooker"] and r["box"]["mounting"] != "surface"],
                    self._box_key, self._box_label, "tga-component:kaiser-up-geraetedose", None)
        self._group(rows, COOKER_BOX_GROUP, [r for r in boxes if r["box"]["cooker"]],
                    lambda r: (MOUNTINGS.index(r["box"]["mounting"]), "pollmann" in r["ref"]),
                    lambda k: ("Unterputz", "Hohlwand", "Aufputz")[k[0]] + (" (Pollmann, mit WAGO)" if k[1] else ""),
                    "tga-component:herd-anschlussdose", None)
        for row in boxes:
            if row.get("variants"):
                row["paths"] = [["Elektro", "Verteiler"]]
        # Leitungen without sub-folders (one entry per cable type, ring lengths are irrelevant)
        for row in rows:
            if row["shape"] == "cable":
                row["paths"] = [["Elektro", "Leitungen"]]

    @staticmethod
    def _box_kind(ref: str, element: Dict[str, Any]) -> Dict[str, Any]:
        connection = element.get("connection") or {}
        name = (element.get("name") or "").lower()
        multiple = next((n for n in (2, 3, 4, 5) if "%d-fach" % n in name), 1)
        return {"mounting": connection.get("mounting") if connection.get("mounting") in MOUNTINGS else "flush",
                "function": connection.get("box_function") or "device", "multiple": multiple,
                "cooker": "herd" in ref and "anschluss" in ref, "strip": "klemmleiste" in ref}

    @staticmethod
    def _box_key(row: Dict[str, Any]) -> tuple:
        box, size = row["box"], [round(v * 1000) for v in (row["size"] or [0, 0, 0])]
        return (MOUNTINGS.index(box["mounting"]), box["function"], box["multiple"], box["strip"], *size)

    @staticmethod
    def _box_label(key: tuple) -> str:
        mounting, function, multiple, strip, w, h, d = key
        text = ("Hohlwand-" if mounting == 1 else "") + ("Abzweigdose" if function == "junction" else "Gerätedose")
        text += (" %d-fach" % multiple if multiple > 1 else "") + " %d × %d × %d mm" % (w, h, d)
        return text + (" mit Klemmleiste" if strip else "")

    @staticmethod
    def _group(rows: List[Dict[str, Any]], name: str, members: List[Dict[str, Any]], key: Any, label: Any,
               preferred: Any, prefix: Optional[str]) -> None:
        # one palette row per group: the representative carries `variants` [{ref, key, label}] (one ref per key:
        # `prefix` first, then the shortest id); every member keeps its ref, gets `variant_group`/`variant_key`, `palette`;
        # `preferred` = key or ref of the representative
        if not members:
            return
        by_key: Dict[tuple, Dict[str, Any]] = {}
        for row in sorted(members, key=lambda r: (not (prefix and r["ref"].startswith(prefix)), len(r["ref"]), r["ref"])):
            by_key.setdefault(key(row), row)
        if isinstance(preferred, str):
            own = next((r for r in members if r["ref"] == preferred), None)
            if own is not None:
                by_key[key(own)] = own
            preferred = key(own) if own is not None else None
        rep = by_key.get(preferred) or by_key[min(by_key)]
        for row in members:
            row["variant_group"], row["variant_key"], row["palette"] = name, label(key(row)), row is rep
        rep["variants"] = [{"ref": r["ref"], "key": label(k), "label": label(k)} for k, r in sorted(by_key.items())]
        rep["group_name"] = name

    @classmethod
    def install_of(cls, element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Install block of a tga-component; a cable (class cable) without one gets a derived straight cable:
        port a at the origin, port b at the end (`length` along x or the last point of the part's `path`);
        its ends have line `power` and dn = core count."""
        install = element.get("install")
        cut = element.get("cut")
        if isinstance(install, dict) and isinstance(cut, dict):
            # the cut property of the component wins over the legacy install.stretch
            return dict(install, stretch=cut)
        if isinstance(install, dict) or element.get("class") != "tga-class:cable":
            return install
        params = element.get("params") or {}
        diameter = params.get("outer_diameter")
        if not JsonValues.is_number(diameter):
            # estimate: 6 mm sheath + 0.8 mm per core and sqrt(mm²)
            cores, section = params.get("cores") or 3, params.get("cross_section_mm2") or 1.5
            diameter = round(0.006 + 0.0008 * float(cores) * math.sqrt(float(section)), 4)
        port = {"line": "power", "dn": cls._cores(element), "gender": "spigot",
                "cable_type": params.get("cable_type"), "section": cls._section(element)}
        return {"trade": "electrical", "group": "Leitungen", "shape": "cable", "outer_diameter": diameter,
                "stretch": dict(cut) if isinstance(cut, dict) else {"default_length": 1.0, "max_length": CABLE_MAX_LENGTH},
                "derived": True,
                "ports": [dict(port, id="a", pos=[0, 0, 0], dir=[-1, 0, 0]),
                          dict(port, id="b", pos=[0, 0, 0], dir=[1, 0, 0], at_length=True)]}

    @staticmethod
    def _color(install: Dict[str, Any], element: Dict[str, Any], part: Optional[Dict[str, Any]]) -> str:
        if install.get("shape") == "cable":
            return COLORS["cable"]
        if install.get("trade") == "electrical":
            return COLORS["conduit"] if install.get("shape") not in ("box", "insert") else COLORS[install["shape"]]
        if install.get("trade") == "waste_water":
            return COLORS["waste_water"]
        medium = (part or {}).get("medium") or (element.get("params") or {}).get("medium") or "cold_water"
        return COLORS.get(medium, COLORS["cold_water"])

    def _place(self, ref: str, source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        part_id = source.get("id")
        component = self._assemblies.effective((self._tga.get("elements") or {}).get(source.get("component")))
        install = self.install_of(component or {})
        if not isinstance(install, dict) or not isinstance(install.get("ports"), list):
            self._issues.part_error(part_id, "Komponente ohne Einbaudaten: %s" % source.get("component"))
            return None
        storey = self._storeys.get(source.get("storey"))
        if storey is None:
            self._issues.part_error(part_id, "Geschoss unbekannt: %s" % source.get("storey"))
            return None
        length = self._cable_length(part_id, source, install) if install["shape"] == "cable" and source.get("path") is not None \
            else self._length(part_id, source, install)
        if length is False:
            return None
        frame, wall = self._frame(part_id, source, storey)
        if frame is None:
            return None
        return self._output(ref, source, component, install, storey, wall, frame, length)

    def _length(self, part_id: str, source: Dict[str, Any], install: Dict[str, Any]) -> Any:
        # straight pipes carry their own (cut) length; other parts have none
        stretch = install.get("stretch")
        if not stretch:
            return None
        length = source.get("length", stretch.get("default_length", stretch["max_length"]))
        if not JsonValues.is_number(length) or length <= 0 or length < stretch.get("min_length", 0) - 1e-6:
            self._issues.part_error(part_id, "Länge ungültig")
            return False
        if length > stretch["max_length"] + 1e-6:
            self._issues.part_error(part_id, "Rohr länger als %s m" % stretch["max_length"])
            return False
        return float(length)

    def _cable_length(self, part_id: str, source: Dict[str, Any], install: Dict[str, Any]) -> Any:
        # a bent cable: `path` = local points after the origin (the last one is end b); length = sum of the pieces
        path = source.get("path")
        if not (isinstance(path, list) and path and all(isinstance(p, list) and len(p) == 3 and
                                                        all(JsonValues.is_number(v) for v in p) for p in path)):
            self._issues.part_error(part_id, "Leitungsverlauf ungültig (path: Liste von [x, y, w])")
            return False
        points = [[0.0, 0.0, 0.0]] + [[float(v) for v in p] for p in path]
        length = sum(math.dist(points[i], points[i + 1]) for i in range(len(points) - 1))
        max_length = float((install.get("stretch") or {}).get("max_length", CABLE_MAX_LENGTH))
        if length <= 0 or length > max_length + 1e-6:
            self._issues.part_error(part_id, "Leitungslänge ungültig (0 bis %g m)" % max_length)
            return False
        return round(length, 4)

    def _frame(self, part_id: str, source: Dict[str, Any], storey: Dict[str, Any]) -> tuple:
        host = source.get("host")
        if not host:
            if not (isinstance(source.get("position"), list) and isinstance(source.get("axes"), dict)):
                self._issues.part_error(part_id, "freies Teil ohne position/axes")
                return None, None
            frame = PartFrame.free(source)
            if frame is None:
                self._issues.part_error(part_id, "Achsen ungültig")
            return frame, None
        wall = next((w for w in storey["walls"] if w["id"] == host.get("wall")), None)
        if wall is None:
            self._issues.part_error(part_id, "Wand unbekannt: %s" % host.get("wall"))
            return None, None
        if host.get("face") not in FACES.get(wall["category"], ()):
            self._issues.part_error(part_id, "Wandseite ungültig (Außenwand: outside|inside, Innenwand: left|right)")
            return None, None
        if not all(JsonValues.is_number(source.get(k)) for k in ("u", "z", "depth")):
            self._issues.part_error(part_id, "Lage ungültig (u, z, depth)")
            return None, None
        return PartFrame.on_wall(wall, source), wall

    def _output(self, ref: str, source: Dict[str, Any], component: Dict[str, Any], install: Dict[str, Any],
                storey: Dict[str, Any], wall: Optional[Dict[str, Any]], frame: PartFrame,
                length: Optional[float]) -> Dict[str, Any]:
        ports = []
        path = source.get("path") if install["shape"] == "cable" else None
        # a conduit carrying a cable: its ends take the cable's core count (checked against the box entries)
        carried = (self._tga.get("elements") or {}).get(source.get("cable")) if install["shape"] == "pipe" else None
        for port in install["ports"]:
            pos, direction = list(port["pos"]), port["dir"]
            if port.get("at_length") and path:
                # bent cable: end b at the last path point, pointing along the last piece
                prev = path[-2] if len(path) > 1 else [0.0, 0.0, 0.0]
                pos, direction = [float(v) for v in path[-1]], self._unit([path[-1][i] - prev[i] for i in range(3)])
            elif port.get("at_length"):
                pos[0] += length or 0.0
            if port["id"] == "a" and path:
                direction = [-v for v in self._unit(path[0])]
            ports.append({"id": port["id"], "position": frame.point(pos), "direction": frame.vector(direction),
                          "line": port["line"], "dn": port["dn"], "gender": port["gender"], "flow": port.get("flow"),
                          "cores": [self._cores(carried)] if carried and port["line"] == "conduit" else port.get("cores"),
                          "cable_type": port.get("cable_type") if not carried else (carried.get("params") or {}).get("cable_type"),
                          "section": port.get("section") if not carried else self._section(carried),
                          "cable_types": port.get("cable_types"), "cross_section": port.get("cross_section"),
                          "label": port.get("label"), "angle": port.get("angle"),
                          "status": "open", "connected_to": None, "transfer": None})
        legs = self._legs(install["shape"], frame, ports)
        if install["shape"] == "cable":
            points = [frame.origin] + [frame.point(p) for p in (path or [])] if path else [ports[0]["position"], ports[1]["position"]]
            legs = [[points[i], points[i + 1]] for i in range(len(points) - 1)]
        return {"id": source["id"], "ref": ref, "component": source["component"], "component_name": component.get("name"),
                "trade": install.get("trade"), "shape": install["shape"], "storey": storey["id"],
                "host": source.get("host"), "u": source.get("u"), "z": source.get("z"), "depth": source.get("depth"),
                "rot": source.get("rot") or {}, "length": length, "path": path, "outer_diameter": install.get("outer_diameter"),
                "size": install.get("size"), "color": self._color(install, component, source),
                "origin": frame.origin, "axes": {"x": frame.x, "y": frame.y, "w": frame.w}, "legs": legs,
                "ports": ports, "connections": dict(source.get("connections") or {}),
                "open_ok": list(source.get("open_ok") or []), "system": source.get("system"),
                "medium": source.get("medium"), "cable": source.get("cable"), "circuit": source.get("circuit"),
                "clamps": [dict(c) for c in source.get("clamps") or self._assemblies.clamps(component) if isinstance(c, dict)],
                "assembly_main": (component.get("assembly") or {}).get("main"), "assembly_extras": self._assemblies.extras(component),
                "assembly_max_connections": (component.get("assembly") or {}).get("max_connections"),
                "clamp_list": [], "capacity": None,
                "wall_name": (wall or {}).get("name"), "estimated": bool(source.get("estimated") or component.get("estimated")),
                "note": source.get("note")}

    @staticmethod
    def _unit(v: List[float]) -> List[float]:
        n = math.sqrt(sum(float(x) ** 2 for x in v))
        return [float(x) / n for x in v] if n > 1e-9 else [1.0, 0.0, 0.0]

    @staticmethod
    def _legs(shape: str, frame: PartFrame, ports: List[Dict[str, Any]]) -> List[List[List[float]]]:
        # pipe axis pieces of the part: a straight pipe from a to b, a fitting from its origin to every port
        if shape in ("pipe", "cable"):
            return [[ports[0]["position"], ports[1]["position"]]]
        if shape in ("fitting", "valve", "cap"):
            return [[frame.origin, p["position"]] for p in ports]
        return []

    def _penetrations(self, parts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # pipes crossing a whole wall, ceiling or floor; partial hits of the host wall are slots, not penetrations
        runs = [{"id": p["id"], "name": "%s (%s)" % (p["component_name"], p["id"]), "points": p["legs"][0],
                 "outer_diameter": p["outer_diameter"] or 0.02, "dn": p["ports"][0]["dn"], "line": p["ports"][0]["line"],
                 "estimated": p["estimated"]} for p in parts if p["shape"] == "pipe"]
        hits = PenetrationBuilder(self._model, self._issues).hits(runs)
        result = []
        for hit in hits:
            hit["source"] = "tga-part:" + hit["run"]
            if hit["kind"] == "through" and hit["length"] >= self._thickness(hit) - 0.005:
                result.append(hit)
        return result

    def _thickness(self, hit: Dict[str, Any]) -> float:
        for storey in self._model.get("storeys_out") or []:
            for wall in storey["walls"]:
                if hit["element"] == "wall:%s/%s" % (storey["id"], wall["id"]):
                    return float(wall["thickness"])
        return 0.0
