"""Visible faces of a wall and their split into room segments."""
import logging
from typing import Any, Dict, List, Optional, Tuple

from ..constants import TOLERANCE
from ..geometry.vector2d import Point, Vector2D
from ..model.issue_log import IssueLog
from .wall_data import WallData

logger = logging.getLogger(__name__)

# a room edge lies on a face line if both its corners are within 2 mm of that line
ON_LINE_LIMIT = 0.002


class WallFaceBuilder:
    """Builds the faces (outside / inside or left / right) with areas net of the rough openings."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog, rooms: List[Dict[str, Any]]) -> None:
        """Args:
            model: the loaded model (material colours).
            issues: receives the `Wandfläche ohne Raum` warnings.
            rooms: the parsed rooms of the storey (`RoomParser`; face areas use each wall's own height).
        """
        self._model = model
        self._issues = issues
        self._rooms = rooms

    def build(self, wall: WallData) -> Dict[str, Dict[str, Any]]:
        """Return the faces of a wall; room-side faces carry `segments` per room."""
        layers = wall.info["layers"]
        first_material, last_material = layers[0]["material"], layers[-1]["material"]
        if wall.is_exterior:
            inside = self._face(wall, wall.thickness, last_material)
            inside["segments"] = self._room_segments(wall, wall.thickness)
            return {"outside": self._face(wall, 0.0, first_material), "inside": inside}
        left, right = self._face(wall, 0.0, first_material), self._face(wall, wall.thickness, last_material)
        left["segments"], right["segments"] = self._room_segments(wall, 0.0), self._room_segments(wall, wall.thickness)
        return {"left": left, "right": right}

    def _face(self, wall: WallData, t: float, material_ref: str) -> Dict[str, Any]:
        p, q = wall.corner_point(t, False), wall.corner_point(t, True)
        length = Vector2D.length(Vector2D.sub(q, p))
        holes = sum((o.u1 - o.u0) * (o.z_top - o.z_bottom) for o in wall.openings)
        color = (self._model["elements"].get(material_ref, {}).get("appearance") or {}).get("color")
        return {"material": material_ref, "line": [list(p), list(q)], "length": length,
                "area": wall.top_area(wall.u_of(p), wall.u_of(q)) - holes, "color": color}

    def _room_segments(self, wall: WallData, t: float) -> List[Dict[str, Any]]:
        p, q = wall.corner_point(t, False), wall.corner_point(t, True)
        length = Vector2D.length(Vector2D.sub(q, p))
        if length < TOLERANCE:
            return []
        direction = Vector2D.scale(Vector2D.sub(q, p), 1.0 / length)
        u_base = wall.u_of(p)
        result = []
        for v0, v1, room_id in self._segments(self._room_intervals(p, direction, length), length):
            if v1 - v0 <= TOLERANCE:
                continue
            if room_id is None:
                self._issues.warning(wall.where, "Wandfläche ohne Raum (%.3f–%.3f m)" % (v0, v1))
            holes = 0.0
            for opening in wall.openings:
                overlap = max(0.0, min(u_base + v1, opening.u1) - max(u_base + v0, opening.u0))
                holes += overlap * (opening.z_top - opening.z_bottom)
            a, b = Vector2D.add(p, Vector2D.scale(direction, v0)), Vector2D.add(p, Vector2D.scale(direction, v1))
            result.append({"room": room_id, "line": [list(a), list(b)], "length": v1 - v0,
                           "area": wall.top_area(u_base + v0, u_base + v1) - holes})
        return result

    def _room_intervals(self, p: Point, direction: Point, length: float) -> List[Tuple[float, float, Any]]:
        # every room edge on the face line gives an interval (distance from p) of that room
        intervals = []
        for room in self._rooms:
            polygon = room["polygon"]
            for i in range(len(polygon)):
                a, b = polygon[i], polygon[(i + 1) % len(polygon)]
                if abs(Vector2D.cross(direction, Vector2D.sub(a, p))) <= ON_LINE_LIMIT \
                        and abs(Vector2D.cross(direction, Vector2D.sub(b, p))) <= ON_LINE_LIMIT:
                    v0, v1 = sorted((Vector2D.dot(Vector2D.sub(a, p), direction),
                                     Vector2D.dot(Vector2D.sub(b, p), direction)))
                    v0, v1 = max(v0, 0.0), min(v1, length)
                    if v1 - v0 > TOLERANCE:
                        intervals.append((v0, v1, room.get("id")))
        intervals.sort()
        return intervals

    @staticmethod
    def _segments(intervals: List[Tuple[float, float, Any]], length: float) -> List[Tuple[float, float, Optional[Any]]]:
        # fill the gaps between room intervals with segments without room (None)
        segments, current = [], 0.0
        for v0, v1, room_id in intervals:
            if v0 > current + TOLERANCE:
                segments.append((current, v0, None))
            segments.append((max(v0, current), v1, room_id))
            current = max(current, v1)
        if current < length - TOLERANCE:
            segments.append((current, length, None))
        return segments
