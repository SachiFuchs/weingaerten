"""Rooms of a storey: checks against the outline and other rooms, wall faces, height and volume per room."""
import logging
from typing import Any, Dict, List, Optional

from ..constants import ROOM_USAGES, TOLERANCE
from ..geometry.ortho_polygon import OrthoPolygon
from ..geometry.polygon import Polygon
from ..geometry.vector2d import Vector2D
from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from .wall_data import WallData

logger = logging.getLogger(__name__)

# a room edge midpoint within 2 mm of a face segment counts as bounded by a wall
EDGE_ON_WALL_LIMIT = 0.002


class RoomBuilder:
    """Builds `{id, number, name, usage, polygon, rects, area, perimeter, height, volume, wall_area, faces}` per room."""

    def __init__(self, issues: IssueLog) -> None:
        """Args:
            issues: receives room errors and warnings.
        """
        self._issues = issues

    def build(self, storey_ref: str, rooms: List[Dict[str, Any]], walls: List[WallData],
              outline: Optional[List[tuple]]) -> List[Dict[str, Any]]:
        """Return the computed rooms (height and volume are completed by `apply_floors`).

        Args:
            storey_ref: storey reference (prefix of the locations).
            rooms: the parsed rooms of `RoomParser`.
            walls: the computed walls (faces with room segments).
            outline: inner polygon of the largest outline ring, or None if not closed.
        """
        result, seen = [], []
        for room in rooms:
            where = "%s.%s" % (storey_ref, room["id"])
            for rect in room["rects"]:
                if outline and not self._inside(rect, outline):
                    self._issues.error(where, "Raum liegt nicht innerhalb der Außenwände")
                    break
            self._check_overlaps(where, room, seen)
            seen.append(room)
            self._check_edges(where, room["polygon"], walls)
            faces = self._faces(room["id"], walls)
            source = room["source"]
            area = OrthoPolygon.area(room["polygon"])
            result.append({"id": room["id"], "number": source.get("number"), "name": room["name"],
                           "usage": source.get("usage"), "usage_name": ROOM_USAGES.get(source.get("usage")),
                           "estimated": bool(source.get("estimated")), "note": source.get("note"),
                           "polygon": OrthoPolygon.to_json(room["polygon"]), "rects": room["rects"], "area": area,
                           "perimeter": OrthoPolygon.perimeter(room["polygon"]),
                           "height": float(source["height"]) if JsonValues.is_number(source.get("height")) else None,
                           "height_given": JsonValues.is_number(source.get("height")), "volume": None,
                           "floor_top": None, "wall_area": sum(face["area"] for face in faces), "faces": faces,
                           "source": source})
        return result

    @staticmethod
    def apply_floors(rooms: List[Dict[str, Any]], floors: List[Dict[str, Any]], z0: float, height: float) -> None:
        """Set `floor_top` (top of the floor build-up), the clear `height` (if not given) and the `volume`."""
        for room in rooms:
            floor = next((f for f in floors if any(r["name"] == room["name"] for r in f["rooms"])), None)
            room["floor_top"] = floor["z_top"] if floor else z0
            if not room.pop("height_given"):
                room["height"] = max(0.0, z0 + height - room["floor_top"])
            room["volume"] = room["area"] * room["height"]

    @staticmethod
    def _inside(rect: List[float], outline: List[tuple]) -> bool:
        x, y, w, h = rect
        # shrink by the tolerance so rooms touching the inner wall faces count as inside
        shrunk = [(x + TOLERANCE, y + TOLERANCE), (x + w - TOLERANCE, y + TOLERANCE),
                  (x + w - TOLERANCE, y + h - TOLERANCE), (x + TOLERANCE, y + h - TOLERANCE)]
        return all(Polygon.contains(corner, outline) for corner in shrunk)

    def _check_overlaps(self, where: str, room: Dict[str, Any], seen: List[Dict[str, Any]]) -> None:
        for other in seen:
            if OrthoPolygon.overlap_area(room["rects"], other["rects"]) > TOLERANCE * TOLERANCE:
                self._issues.error(where, "überlappt mit Raum %s" % other["id"])

    @staticmethod
    def _faces(room_id: Any, walls: List[WallData]) -> List[Dict[str, Any]]:
        faces = []
        for wall in walls:
            for side, face in wall.faces.items():
                for segment in face.get("segments", []):
                    if segment["room"] == room_id:
                        faces.append({"wall": wall.id, "side": side, "length": segment["length"],
                                      "area": segment["area"], "material": face["material"],
                                      "line": segment["line"]})
        return faces

    def _check_edges(self, where: str, polygon: List[tuple], walls: List[WallData]) -> None:
        for i in range(len(polygon)):
            middle = Vector2D.scale(Vector2D.add(polygon[i], polygon[(i + 1) % len(polygon)]), 0.5)
            if not self._on_any_face(middle, walls):
                self._issues.warning(where, "Raumkante ohne Wand (Kante %d)" % (i + 1))

    @staticmethod
    def _on_any_face(point: tuple, walls: List[WallData]) -> bool:
        for wall in walls:
            for face in wall.faces.values():
                for segment in face.get("segments", []):
                    p, q = segment["line"]
                    edge = Vector2D.sub(q, p)
                    length = Vector2D.length(edge)
                    if length >= TOLERANCE:
                        u = Vector2D.dot(Vector2D.sub(point, p), edge) / length
                        if -TOLERANCE <= u <= length + TOLERANCE \
                                and abs(Vector2D.cross(edge, Vector2D.sub(point, p))) / length <= EDGE_ON_WALL_LIMIT:
                            return True
        return False
