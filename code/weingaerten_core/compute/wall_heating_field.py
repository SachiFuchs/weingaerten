"""One wall heating field: its panels in the field frame, their pipe meanders, the checks against rooms, roof and
openings, the port and the feed lines to the distributor."""
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from ..constants import TOLERANCE
from ..geometry.polyline import Polyline
from ..geometry.vector2d import Point, Vector2D
from ..json_values import JsonValues
from ..model.issue_log import IssueLog

logger = logging.getLogger(__name__)

PANEL_CLASS = "tga-class:wall-heating-panel"
FEED_Z = 0.03
# supply and return of a feed line run this far apart
FEED_GAP = 0.04
DEFAULT_SPACING = 0.1
# panel links run this far below the lowest panel edge (in the strip below the panels)
LINK_DROP = 0.02
# a link closer than this to a foreign pipe end touches it (branch)
BRANCH_TOLERANCE = 0.005
# a panel edge closer than this to the room face of a wall counts as in front of it
FACE_TOLERANCE = 0.02


class WallHeatingField:
    """Builds the fields of a `wall_heating` answer."""

    def __init__(self, tga: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            tga: the TGA catalog elements (panel components).
            issues: receives field errors and warnings.
        """
        self._tga = tga
        self._issues = issues

    def build(self, where: str, source: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Return the computed field or None (errors logged).

        Args:
            where: issue location of the field.
            source: the field JSON.
            context: spec, z0, rooms, walls, roof, layer and distributor of the wall heating.
        """
        origin, direction = source.get("origin"), source.get("direction")
        if not (self.is_point(origin) and self.is_point(direction) and JsonValues.is_number(source.get("port_u"))
                and abs(Vector2D.length(tuple(direction)) - 1.0) < TOLERANCE
                and min(abs(direction[0]), abs(direction[1])) < TOLERANCE):
            self._issues.error(where, "Maße ungültig (origin, direction achsparallel, port_u)")
            return None
        frame = {"origin": (float(origin[0]), float(origin[1])), "d": (float(direction[0]), float(direction[1]))}
        frame["n"] = (-frame["d"][1], frame["d"][0])
        panels = []
        for i, panel in enumerate(source.get("panels") or []):
            built = self._panel("%s.panels[%d]" % (where, i), panel, frame, context)
            if built is not None:
                built["index"] = i
                panels.append(built)
        if not panels:
            self._issues.error(where, "Feld ohne Platten")
            return None
        self._check_panels(where, source, panels, frame, context)
        port = self._port(where, source, panels, frame, context)
        feed_supply, feed_return = self._feeds(where, source, port, context)
        wall = next((w for w in context["walls"] if w["id"] == source.get("wall")), None)
        links = self._links(panels, context)
        self._check_branches(where, panels, links)
        return {"id": source.get("id"), "name": source.get("name"), "circuit": source.get("circuit"),
                "room": source.get("room"), "wall": source.get("wall"), "wall_name": (wall or {}).get("name"),
                "origin": list(frame["origin"]), "direction": list(frame["d"]), "normal": list(frame["n"]),
                "panels": panels, "links": links, "port": port, "feed_supply": feed_supply, "feed_return": feed_return,
                "area": sum(p["area"] for p in panels), "pipe_length": sum(p["pipe_length"] for p in panels),
                "feed_length": self.length3(feed_supply) + self.length3(feed_return),
                "couplings": len(panels) - 1, "adapters": 2}

    def _panel(self, where: str, source: Any, frame: Dict[str, Point],
               context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not (isinstance(source, dict) and JsonValues.is_number(source.get("u")) and JsonValues.is_number(source.get("z"))):
            self._issues.error(where, "Maße ungültig")
            return None
        kind = source.get("type")
        ref = (context["spec"].get("panel_components") or {}).get(kind)
        component = self._tga.get(ref) if isinstance(ref, str) else None
        if component is None:
            self._issues.error(where, "Plattentyp unbekannt: %s" % kind)
            return None
        params = component.get("params") or {}
        if component.get("class") != PANEL_CLASS or not all(JsonValues.is_number(params.get(k)) for k in ("width", "height")):
            self._issues.error(where, "%s ist keine Wandheizungsplatte" % ref)
            return None
        width, height = float(params["width"]), float(params["height"])
        direction = params.get("pipe_direction")
        if source.get("rotated") is True:
            # laid landscape instead of portrait: width and height swap and the pipe runs turn with the panel
            # (naturbo plan: D horizontal loops upright, vertical loops in landscape)
            width, height = height, width
            direction = {"vertical": "horizontal", "horizontal": "vertical"}.get(direction, direction)
            params = dict(params, pipe_direction=direction)
        u0, z_bottom = float(source["u"]), float(source["z"])
        layer, z0 = context["layer"], context["z0"]
        front, back = layer["offset"], layer["offset"] + layer["thickness"]
        corners = [self._world(frame, u, front, z0 + z) for u, z in ((u0, z_bottom), (u0 + width, z_bottom),
                                                                     (u0 + width, z_bottom + height), (u0, z_bottom + height))]
        pipe = [self._world(frame, u0 + s, layer["pipe_depth"], z0 + z_bottom + h)
                for s, h in self._meander(width, height, params)]
        length = params.get("pipe_length") if JsonValues.is_number(params.get("pipe_length")) else self.length3(pipe)
        return {"type": kind, "component": ref, "name": component.get("name"), "u0": u0, "u1": u0 + width,
                "z0": z_bottom, "z1": z_bottom + height, "width": width, "height": height,
                "pipe_direction": direction, "rotated": source.get("rotated") is True, "port_side": params.get("port_corner"),
                "depth": [front, back], "corners": corners, "pipe": pipe, "area": width * height,
                "pipe_length": float(length), "estimated": bool(component.get("estimated"))}

    @staticmethod
    def _links(panels: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        # consecutive panels are joined pipe end -> pipe start: down along the panel edge into the strip below the
        # panels, along it and up again; the press coupling sits in the middle of the bottom run
        result = []
        z_link = context["z0"] + min(p["z0"] for p in panels) - LINK_DROP
        for a, b in zip(panels, panels[1:]):
            start, end = a["pipe"][-1], b["pipe"][0]
            low_a, low_b = [start[0], start[1], z_link], [end[0], end[1], z_link]
            points = [start, low_a, low_b, end]
            middle = [(s + e) / 2 for s, e in zip(low_a, low_b)]
            axis = [e - s for s, e in zip(low_a, low_b)]
            result.append({"from": a["index"], "to": b["index"], "points": points, "axis": axis,
                           "coupling": context["spec"].get("coupling"), "position": middle,
                           "length": WallHeatingField.length3(points)})
        return result

    def _check_branches(self, where: str, panels: List[Dict[str, Any]], links: List[Dict[str, Any]]) -> None:
        # a link must not touch the pipe end of a panel it does not join (two joints at one end = branch)
        for link in links:
            own = {(link["from"], -1), (link["to"], 0)}
            for panel in panels:
                for end in (0, -1):
                    if (panel["index"], end) in own:
                        continue
                    point = panel["pipe"][end]
                    if any(self._on_segment(point, p, q) for p, q in zip(link["points"], link["points"][1:])):
                        self._issues.warning(where, "Abzweig: Verbindung %d -> %d läuft durch %s von Platte %d (%s)"
                                             % (link["from"], link["to"], "Anfang" if end == 0 else "Ende",
                                                panel["index"], panel["type"]))

    @staticmethod
    def _on_segment(point: List[float], p: List[float], q: List[float]) -> bool:
        seg = [q[i] - p[i] for i in range(3)]
        length2 = sum(v * v for v in seg)
        if length2 < 1e-12:
            return math.dist(point, p) < BRANCH_TOLERANCE
        t = max(0.0, min(1.0, sum((point[i] - p[i]) * seg[i] for i in range(3)) / length2))
        return math.dist(point, [p[i] + t * seg[i] for i in range(3)]) < BRANCH_TOLERANCE

    @staticmethod
    def _meander(width: float, height: float, params: Dict[str, Any]) -> List[Tuple[float, float]]:
        # pipe loops of the panel in local (s along u, h up); the runs follow pipe_direction
        spacing = float(params["pipe_spacing"]) if JsonValues.is_number(params.get("pipe_spacing")) else DEFAULT_SPACING
        vertical = params.get("pipe_direction") == "vertical"
        across, along = (width, height) if vertical else (height, width)
        margin = spacing / 2
        runs = max(1, int(round((across - spacing) / spacing)) + 1)
        if JsonValues.is_number(params.get("pipe_runs")):
            runs = max(1, int(params["pipe_runs"]))
        points: List[Tuple[float, float]] = []
        for k in range(runs):
            c = margin + k * (across - 2 * margin) / max(runs - 1, 1)
            ends = (margin, along - margin) if k % 2 == 0 else (along - margin, margin)
            for a in ends:
                points.append((c, a) if vertical else (a, c))
        if params.get("port_exits") in ("side_bottom", "side_bottom_180") and not vertical:
            # naturbo D/E/I/K: supply and return on the port side; the top run leaves through the side edge, the
            # bottom run turns down and leaves through the bottom edge
            points = list(reversed(points))
            points = [(0.0, points[0][1])] + points + [(points[-1][0], 0.0)]
            if params["port_exits"] == "side_bottom_180":
                # naturbo G/L: the same loop turned by 180° (port right, one end up through the top edge)
                return [(width - s, height - h) for s, h in points]
        if str(params.get("port_corner") or "").endswith("right"):
            # loop begins and ends at the port: mirror for panels connected on the right
            points = [(width - s, h) for s, h in points]
        return points

    def _check_panels(self, where: str, source: Dict[str, Any], panels: List[Dict[str, Any]],
                      frame: Dict[str, Point], context: Dict[str, Any]) -> None:
        for i, a in enumerate(panels):
            for b in panels[i + 1:]:
                if self._overlap(a, b):
                    self._issues.error(where, "Platten überlappen: %d (%s), %d (%s)"
                                       % (a["index"], a["type"], b["index"], b["type"]))
        rects = [r for room in context["rooms"] if room.get("name") == source.get("room") for r in room["rects"]]
        if not rects:
            self._issues.error(where, "Raum unbekannt: %s" % source.get("room"))
        roof = context["roof"]
        openings = self._openings(frame, context["walls"])
        for panel in panels:
            label = "Platte %d (%s)" % (panel["index"], panel["type"])
            inner = [self._plan(frame, u, panel["depth"][1]) for u in (panel["u0"] + 0.01, panel["u1"] - 0.01)]
            if rects and not all(any(self._in_rect(p, r) for r in rects) for p in inner):
                self._issues.error(where, "%s liegt nicht im Raum %s" % (label, source.get("room")))
            if roof is not None and any(roof.height_at(self._plan(frame, u, 0.0)) < panel["z1"] - TOLERANCE
                                        for u in (panel["u0"], panel["u1"])):
                self._issues.error(where, "%s ragt über die Dachschräge" % label)
            for opening in openings:
                if self._overlap(panel, opening):
                    self._issues.warning(where, "%s überdeckt Öffnung %s" % (label, opening["id"]))

    @staticmethod
    def _overlap(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        return min(a["u1"], b["u1"]) - max(a["u0"], b["u0"]) > TOLERANCE \
            and min(a["z1"], b["z1"]) - max(a["z0"], b["z0"]) > TOLERANCE

    @staticmethod
    def _openings(frame: Dict[str, Point], walls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # openings of every wall whose face lies in the field plane, in field u / storey-local z
        result = []
        for wall in walls:
            for opening in wall.get("openings") or []:
                plan = opening.get("plan") or {}
                for side in ("inside", "outside"):
                    points = plan.get(side) or []
                    if len(points) != 2:
                        continue
                    offsets = [Vector2D.dot(Vector2D.sub(tuple(p), frame["origin"]), frame["n"]) for p in points]
                    if all(abs(o) < FACE_TOLERANCE for o in offsets):
                        us = sorted(Vector2D.dot(Vector2D.sub(tuple(p), frame["origin"]), frame["d"]) for p in points)
                        rough = opening["rough"]
                        result.append({"id": opening["id"], "u0": us[0], "u1": us[1],
                                       "z0": rough["zb"], "z1": rough["zt"]})
                        break
        return result

    def _port(self, where: str, source: Dict[str, Any], panels: List[Dict[str, Any]], frame: Dict[str, Point],
              context: Dict[str, Any]) -> Dict[str, Any]:
        u = float(source["port_u"])
        z_bottom = min(p["z0"] for p in panels)
        if not any(p["u0"] - TOLERANCE <= u <= p["u1"] + TOLERANCE and abs(p["z0"] - z_bottom) < TOLERANCE
                   for p in panels):
            self._issues.warning(where, "Anschluss liegt an keiner Plattenunterkante (u %.3f)" % u)
        depth = context["layer"]["pipe_depth"]
        return {"u": u, "position": self._world(frame, u, depth, context["z0"] + z_bottom)}

    def _feeds(self, where: str, source: Dict[str, Any], port: Dict[str, Any],
               context: Dict[str, Any]) -> Tuple[List[List[float]], List[List[float]]]:
        feed = [p for p in source.get("feed") or [] if self.is_point(p)]
        if not feed:
            self._issues.error(where, "Anbindeleitung fehlt")
            return [], []
        z_feed = context["z0"] + FEED_Z
        centre = Polyline.cleaned([tuple(map(float, p)) for p in feed] + [tuple(port["position"][:2])])
        if len(centre) < 2:
            return [], []
        z_start = context["distributor"]["z"]
        result = []
        for side in (FEED_GAP / 2, -FEED_GAP / 2):
            line = Polyline.offset(centre, side)
            points = [[line[0][0], line[0][1], z_start]] + [[x, y, z_feed] for x, y in line]
            points.append([line[-1][0], line[-1][1], port["position"][2]])
            result.append(points)
        return result[0], result[1]

    @staticmethod
    def _plan(frame: Dict[str, Point], u: float, w: float) -> Point:
        return Vector2D.add(Vector2D.add(frame["origin"], Vector2D.scale(frame["d"], u)), Vector2D.scale(frame["n"], w))

    @staticmethod
    def _world(frame: Dict[str, Point], u: float, w: float, z: float) -> List[float]:
        x, y = WallHeatingField._plan(frame, u, w)
        return [x, y, z]

    @staticmethod
    def _in_rect(p: Point, rect: List[float]) -> bool:
        return rect[0] - TOLERANCE <= p[0] <= rect[0] + rect[2] + TOLERANCE \
            and rect[1] - TOLERANCE <= p[1] <= rect[1] + rect[3] + TOLERANCE

    @staticmethod
    def is_point(value: Any) -> bool:
        """True for a plan point `[x, y]` of numbers."""
        return isinstance(value, list) and len(value) == 2 and all(JsonValues.is_number(v) for v in value)

    @staticmethod
    def length3(points: List[List[float]]) -> float:
        """Length of a 3D polyline."""
        return sum(sum((b[i] - a[i]) ** 2 for i in range(3)) ** 0.5 for a, b in zip(points, points[1:]))
