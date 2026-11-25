"""Floor heating of a storey: manifold and circuits with supply / return pipes in the heated floor layer."""
import logging
from typing import Any, Dict, List, Optional, Tuple

from ..constants import TOLERANCE
from ..geometry.polyline import Polyline
from ..geometry.vector2d import Point, Vector2D
from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from .floor_builder import FloorBuilder
from .pipe_layout import ENTRY_MIRROR, PipeLayout

logger = logging.getLogger(__name__)

DEFAULT_EDGE = 0.1
MIN_SPACING = 0.075
MAX_CIRCUIT_LENGTH = 100.0
# supply and return of a feed line run this far apart
FEED_GAP = 0.05


class HeatingBuilder:
    """Builds the `heating` answer of a storey."""

    def __init__(self, issues: IssueLog) -> None:
        """Args:
            issues: receives heating errors and warnings.
        """
        self._issues = issues

    def build(self, storey_ref: str, storey: Dict[str, Any], floors: List[Dict[str, Any]],
              rooms: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Return the computed heating or None.

        Args:
            storey_ref: storey reference.
            storey: the storey JSON.
            floors: the computed floors (the pipe level is the heated layer of `heating.floor`).
            rooms: the computed rooms.
        """
        spec = storey.get("heating")
        if not isinstance(spec, dict):
            return None
        where = storey_ref + ".heating"
        z = self._pipe_level(where, spec, floors)
        manifold = spec.get("manifold") or {}
        if z is None or not self._is_point(manifold.get("position")):
            if z is not None:
                self._issues.error(where, "Verteiler ungültig")
            return None
        circuits = self._circuits(where, spec, rooms)
        return {"name": spec.get("name"), "pipe": spec.get("pipe"), "pipe_diameter": float(spec["pipe_diameter"]),
                "floor": spec.get("floor"), "estimated": bool(spec.get("estimated")), "note": spec.get("note"),
                "z": z, "manifold": {"name": manifold.get("name"), "position": [float(v) for v in manifold["position"]],
                                     "width": float(manifold.get("width") or 0.5), "z": z},
                "circuits": circuits, "area": sum(c["area"] for c in circuits),
                "length": sum(c["length"] for c in circuits)}

    def _pipe_level(self, where: str, spec: Dict[str, Any], floors: List[Dict[str, Any]]) -> Optional[float]:
        floor = next((f for f in floors if f["id"] == spec.get("floor")), None)
        if floor is None:
            self._issues.error(where, "Boden unbekannt: %s" % spec.get("floor"))
            return None
        heated = [layer for layer in floor["layers"] if layer["heated"]]
        if not heated:
            self._issues.error(where, "Aufbau ohne Rohrebene (heated): %s" % floor["assembly"])
            return None
        if not JsonValues.is_number(spec.get("pipe_diameter")) or spec["pipe_diameter"] <= 0:
            self._issues.error(where, "Maße ungültig")
            return None
        # the pipe lies on the bottom of the heated layer (knob plate)
        return heated[0]["z0"] + float(spec["pipe_diameter"]) / 2

    def _circuits(self, where: str, spec: Dict[str, Any], rooms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        result: List[Dict[str, Any]] = []
        for circuit in spec.get("circuits") or []:
            if not isinstance(circuit, dict):
                continue
            built = self._circuit("%s.%s" % (where, circuit.get("id")), circuit, rooms)
            if built is None:
                continue
            for other in result:
                if self._overlap(built["rect"], other["rect"]):
                    self._issues.error(where, "Heizkreise überlappen: %s, %s" % (other["id"], built["id"]))
            result.append(built)
        return result

    def _circuit(self, where: str, circuit: Dict[str, Any], rooms: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        rect = circuit.get("rect")
        spacing, edge = circuit.get("spacing"), circuit.get("edge", DEFAULT_EDGE)
        feed = circuit.get("feed") or []
        if not (isinstance(rect, list) and len(rect) == 4 and all(JsonValues.is_number(v) for v in rect)
                and rect[2] > 0 and rect[3] > 0 and JsonValues.is_number(spacing) and JsonValues.is_number(edge)
                and circuit.get("entry") in ENTRY_MIRROR and feed and all(self._is_point(p) for p in feed)):
            self._issues.error(where, "Maße ungültig")
            return None
        if spacing < MIN_SPACING:
            self._issues.error(where, "Verlegeabstand zu klein (%g cm)" % round(spacing * 100, 1))
            return None
        rect_t = tuple(float(v) for v in rect)
        cutout = self._cutout(where, circuit.get("cutout"), rect_t)
        room_rects = FloorBuilder.room_rects(rooms, circuit.get("room"))
        if not room_rects:
            self._issues.error(where, "Raum unbekannt: %s" % circuit.get("room"))
        elif not self._covered(rect_t, room_rects):
            self._issues.error(where, "Heizkreis liegt nicht im Raum %s" % circuit.get("room"))
        layout = PipeLayout(rect_t, float(spacing), float(edge), circuit["entry"], cutout)
        centre = Polyline.cleaned(layout.spiral() if circuit.get("pattern") == "spiral" else layout.meander())
        if len(centre) < 2:
            self._issues.error(where, "Verlegefläche zu klein")
            return None
        built = self._pipes(where, circuit, rect_t, float(spacing), centre, feed)
        if cutout is not None:
            built["cutout"] = list(cutout)
            built["area"] -= cutout[2] * cutout[3]
        return built

    def _cutout(self, where: str, value: Any, rect: Tuple[float, ...]) -> Optional[Tuple[float, ...]]:
        # an unheated corner of the laying area (shower tray); the spiral then follows the L-shape
        if value is None:
            return None
        if isinstance(value, list) and len(value) == 4 and all(JsonValues.is_number(v) for v in value):
            cutout = tuple(float(v) for v in value)
            if PipeLayout.cutout_in_corner(rect, cutout):
                return cutout
        self._issues.error(where, "Aussparung ungültig (muss in einer Ecke der Verlegefläche liegen)")
        return None

    def _pipes(self, where: str, circuit: Dict[str, Any], rect: Tuple[float, ...], spacing: float,
               centre: List[Point], feed: List[Any]) -> Dict[str, Any]:
        supply = Polyline.offset(centre, spacing / 2)
        back = Polyline.offset(centre, -spacing / 2)
        # the two pipes meet at the far end of the centre line
        field = supply + list(reversed(back))
        feed_centre = Polyline.cleaned([tuple(map(float, p)) for p in feed] + [centre[0]])
        feed_a, feed_b = Polyline.offset(feed_centre, FEED_GAP / 2), Polyline.offset(feed_centre, -FEED_GAP / 2)
        if Vector2D.length(Vector2D.sub(feed_a[-1], supply[0])) > Vector2D.length(Vector2D.sub(feed_b[-1], supply[0])):
            feed_a, feed_b = feed_b, feed_a
        feed_supply, feed_return = feed_a[:-1] + [supply[0]], feed_b[:-1] + [back[0]]
        length_field = Polyline.length(field)
        length_feed = Polyline.length(feed_supply) + Polyline.length(feed_return)
        if length_field + length_feed > MAX_CIRCUIT_LENGTH:
            self._issues.warning(where, "Heizkreis zu lang (%.0f m)" % (length_field + length_feed))
        return {"id": circuit.get("id"), "name": circuit.get("name"), "room": circuit.get("room"),
                "color": circuit.get("color"), "pattern": circuit.get("pattern"), "spacing": spacing,
                "entry": circuit.get("entry"), "rect": list(rect), "cutout": None, "area": rect[2] * rect[3],
                "field": [list(p) for p in field], "feed_supply": [list(p) for p in feed_supply],
                "feed_return": [list(p) for p in feed_return], "length_field": length_field,
                "length_feed": length_feed, "length": length_field + length_feed}

    @staticmethod
    def _covered(rect: Tuple[float, ...], room_rects: List[List[float]]) -> bool:
        # room rects never overlap, so the circuit lies inside the room when their intersections fill it
        inside = sum(HeatingBuilder._intersection(rect, r) for r in room_rects)
        return inside >= rect[2] * rect[3] - TOLERANCE

    @staticmethod
    def _overlap(a: List[float], b: List[float]) -> bool:
        return HeatingBuilder._intersection(a, b) > TOLERANCE

    @staticmethod
    def _intersection(a: Any, b: Any) -> float:
        width = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
        depth = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
        return max(0.0, width) * max(0.0, depth)

    @staticmethod
    def _is_point(value: Any) -> bool:
        return isinstance(value, list) and len(value) == 2 and all(JsonValues.is_number(v) for v in value)
