"""Storey-wide wall checks: outside orientation, overlapping walls, walls on the foundation."""
import logging
from typing import Any, Dict, List

from ..geometry.polygon import Polygon
from ..geometry.vector2d import Vector2D
from ..model.issue_log import IssueLog
from .wall_data import WallData

logger = logging.getLogger(__name__)

# footprints may touch; an intersection above 1 cm² is a real overlap
OVERLAP_AREA_LIMIT = 1e-4


class StoreyChecks:
    """Checks that need all walls of a storey at once."""

    def __init__(self, issues: IssueLog) -> None:
        """Args:
            issues: receives the errors.
        """
        self._issues = issues

    def check_outside_orientation(self, walls: List[WallData], rooms: List[Dict[str, Any]]) -> None:
        """Report exterior walls whose outside faces a room rect centre beside the wall (parsed rooms)."""
        for wall in walls:
            if not wall.is_exterior:
                continue
            for room in rooms:
                for rect in room["rects"]:
                    if self._faces_inwards(wall, (rect[0] + rect[2] / 2.0, rect[1] + rect[3] / 2.0)):
                        self._issues.error(wall.where, "Außenseite zeigt nach innen (Raum %s)" % room["id"])
                        break

    @staticmethod
    def _faces_inwards(wall: WallData, center: tuple) -> bool:
        relative = Vector2D.sub(center, wall.start)
        return 0 <= Vector2D.dot(relative, wall.direction) <= wall.length and Vector2D.dot(relative, wall.normal) < 0

    def check_overlaps(self, walls: List[WallData]) -> None:
        """Report pairs of walls whose footprints overlap."""
        for i in range(len(walls)):
            for k in range(i + 1, len(walls)):
                intersection = Polygon.clip(walls[i].footprint, walls[k].footprint)
                if len(intersection) >= 3 and abs(Polygon.signed_area(intersection)) > OVERLAP_AREA_LIMIT:
                    self._issues.error(walls[i].where, "überlappt mit Wand %s" % walls[k].id)

    def check_on_foundation(self, walls: List[WallData], foundation_polygon: List[tuple]) -> None:
        """Report walls with a footprint point outside the foundation polygon."""
        for wall in walls:
            if not all(Polygon.contains_or_touches(p, foundation_polygon) for p in wall.footprint):
                self._issues.error(wall.where, "Wand nicht auf der Bodenplatte")
