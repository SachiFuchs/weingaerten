"""Chains the exterior walls of a storey into closed outline rings."""
import logging
from typing import Any, Dict, List, Optional, Tuple

from ..geometry.polygon import Polygon
from ..geometry.vector2d import Vector2D
from ..model.issue_log import IssueLog
from .wall_data import WallData

logger = logging.getLogger(__name__)

# (wall, reversed): reversed walls are walked from end to start
ChainLink = Tuple[WallData, bool]


class OutlineBuilder:
    """Builds the outline rings `{points, inner, walls, area}` of the exterior walls."""

    def __init__(self, issues: IssueLog) -> None:
        """Args:
            issues: receives the `Umriss nicht geschlossen` warnings.
        """
        self._issues = issues

    def rings(self, storey_ref: str, walls: List[WallData]) -> List[Dict[str, Any]]:
        """Return every closed ring; the walls are chained through shared end points in any direction."""
        exterior = [wall for wall in walls if wall.is_exterior]
        used = set()
        rings = []
        for first_wall in exterior:
            if id(first_wall) in used:
                continue
            chain, closed = self._chain(first_wall, exterior, used)
            if not closed:
                self._issues.warning(storey_ref, "Umriss nicht geschlossen (%s)"
                                     % ", ".join(link[0].id for link in chain))
                continue
            rings.append(self._ring(chain))
        return rings

    @staticmethod
    def largest(rings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Return the ring with the largest area (used for rooms, ceilings and the foundation)."""
        return max(rings, key=lambda ring: ring["area"]) if rings else None

    @staticmethod
    def _chain(first_wall: WallData, exterior: List[WallData], used: set) -> Tuple[List[ChainLink], bool]:
        chain = [(first_wall, False)]
        used.add(id(first_wall))
        start_point, current = first_wall.start, first_wall.end
        while True:
            if Vector2D.equal(current, start_point):
                return chain, True
            link = None
            for other in exterior:
                if id(other) in used:
                    continue
                at_end = other.is_free_end_of(current)
                if at_end is not None:
                    link = (other, at_end)
                    current = other.start if at_end else other.end
                    break
            if link is None:
                return chain, False
            chain.append(link)
            used.add(id(link[0]))

    @staticmethod
    def _ring(chain: List[ChainLink]) -> Dict[str, Any]:
        outer = Polygon.counter_clockwise([wall.corner_point(0.0, reverse) for wall, reverse in chain])
        inner = Polygon.counter_clockwise([wall.corner_point(wall.thickness, reverse) for wall, reverse in chain])
        return {"points": [list(p) for p in outer], "inner": [list(p) for p in inner],
                "walls": [wall.id for wall, _ in chain], "area": abs(Polygon.signed_area(outer))}
