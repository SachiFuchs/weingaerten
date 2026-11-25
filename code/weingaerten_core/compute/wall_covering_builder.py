"""Wall coverings of a room (Fliesenspiegel, Sockelleiste): height band on the room's wall face segments."""
import logging
from typing import Any, Dict, List, Optional

from ..constants import TOLERANCE
from ..geometry.vector2d import Vector2D
from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from .wall_data import WallData

logger = logging.getLogger(__name__)


class WallCoveringBuilder:
    """Builds one wall covering: segments with net length (openings in the band removed) and net area."""

    def __init__(self, issues: IssueLog) -> None:
        """Args:
            issues: receives covering errors.
        """
        self._issues = issues

    def build(self, where: str, covering: Dict[str, Any], room: Dict[str, Any], walls: Dict[str, WallData],
              base: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Return the covering with `z0, z1, segments, length, area` or None after an error.

        Args:
            where: location of the messages.
            covering: the covering JSON (`walls`: "all" or [{wall, u?}], `z`: [z0, z1] storey-local).
            room: the computed room (its `faces` are the wall face segments bounding it).
            walls: the computed walls by id.
            base: the common covering fields.
        """
        band = covering.get("z")
        if band is not None and not (isinstance(band, list) and len(band) == 2 and all(JsonValues.is_number(v) for v in band)
                                     and 0 <= band[0] < band[1]):
            self._issues.covering_error(where, "Maße ungültig")
            return None
        ranges = self._ranges(where, covering.get("walls", "all"), room, walls)
        if ranges is None:
            return None
        segments = []
        for face in room["faces"]:
            wall = walls.get(face["wall"])
            if wall is None or face["wall"] not in ranges:
                continue
            segment = self._segment(face, wall, ranges[face["wall"]], band)
            if segment is not None:
                segments.append(segment)
        if not segments:
            self._issues.covering_error(where, "Wandbelag ohne Wandfläche")
            return None
        return dict(base, scope="wall", z0=min(s["z0"] for s in segments), z1=max(s["z1"] for s in segments),
                    segments=segments, length=sum(s["length"] for s in segments),
                    area=sum(s["area"] for s in segments))

    def _ranges(self, where: str, value: Any, room: Dict[str, Any], walls: Dict[str, WallData]) -> Optional[Dict[str, Any]]:
        # wall id -> optional [u0, u1] along the wall (like opening.offset); "all" = every face of the room
        bounding = {face["wall"] for face in room["faces"]}
        if value == "all":
            return {wall_id: None for wall_id in bounding}
        if not isinstance(value, list) or not value:
            self._issues.covering_error(where, "Wände ungültig (\"all\" oder [{wall, u}])")
            return None
        ranges = {}
        for item in value:
            wall_id = item.get("wall") if isinstance(item, dict) else None
            if wall_id not in walls:
                self._issues.covering_error(where, "Wand unbekannt: %s" % wall_id)
                return None
            if wall_id not in bounding:
                self._issues.covering_error(where, "Wand %s grenzt nicht an den Raum" % wall_id)
                return None
            u = item.get("u")
            if u is not None and not (isinstance(u, list) and len(u) == 2 and all(JsonValues.is_number(v) for v in u)
                                      and u[0] < u[1]):
                self._issues.covering_error(where, "Maße ungültig")
                return None
            ranges[wall_id] = u
        return ranges

    @staticmethod
    def _segment(face: Dict[str, Any], wall: WallData, u_range: Any, band: Any) -> Optional[Dict[str, Any]]:
        p, q = face["line"]
        u_a, u_b = sorted((wall.u_of(tuple(p)), wall.u_of(tuple(q))))
        if u_range is not None:
            u_a, u_b = max(u_a, float(u_range[0])), min(u_b, float(u_range[1]))
        if u_b - u_a <= TOLERANCE:
            return None
        # sloped tops (roof walls) are approximated by their lowest point over the segment
        top = wall.min_top(u_a, u_b)
        z0, z1 = (float(band[0]), min(float(band[1]), top)) if band else (0.0, top)
        if z1 - z0 <= TOLERANCE:
            return None
        length, area = u_b - u_a, (u_b - u_a) * (z1 - z0)
        openings = []
        for opening in wall.openings:
            along = max(0.0, min(u_b, opening.u1) - max(u_a, opening.u0))
            height = max(0.0, min(z1, opening.z_top) - max(z0, opening.z_bottom))
            if along > TOLERANCE and height > TOLERANCE:
                length -= along
                area -= along * height
                openings.append(opening.id)
        return {"wall": wall.id, "side": face["side"], "u0": u_a, "u1": u_b, "z0": z0, "z1": z1,
                "line": [WallCoveringBuilder._point(face, wall, u_a), WallCoveringBuilder._point(face, wall, u_b)],
                "length": length, "area": area, "openings": openings}

    @staticmethod
    def _point(face: Dict[str, Any], wall: WallData, u: float) -> List[float]:
        # point of the face line at wall coordinate u
        p = tuple(face["line"][0])
        moved = Vector2D.add(p, Vector2D.scale(wall.direction, u - wall.u_of(p)))
        return [moved[0], moved[1]]
