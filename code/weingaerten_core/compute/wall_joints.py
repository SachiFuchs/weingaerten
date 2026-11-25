"""Finds the corner neighbours and T-joints of the walls of a storey."""
import logging
from typing import List, Optional

from ..constants import TOLERANCE
from ..geometry.vector2d import Point, Vector2D
from ..model.issue_log import IssueLog
from .wall_data import WallData

logger = logging.getLogger(__name__)

# walls whose directions differ by less than this cross product are parallel and never form a corner
PARALLEL_LIMIT = 1e-6


class WallJoints:
    """Connects every wall end to a corner neighbour or to a wall it meets (T-joint)."""

    def __init__(self, issues: IssueLog) -> None:
        """Args:
            issues: receives the `offenes Wandende` warnings.
        """
        self._issues = issues

    def connect(self, walls: List[WallData]) -> None:
        """Set `neighbours` and `tees` of every wall; an end without either is an open end
        (warning unless listed in the wall's `free_ends`)."""
        # corners first: the T-joint test needs the corner neighbours (corner block)
        for wall in walls:
            for at_end in (False, True):
                wall.neighbours[at_end] = self._corner_neighbour(wall, walls, wall.end if at_end else wall.start)
        for wall in walls:
            for at_end in (False, True):
                if wall.neighbours[at_end] is not None:
                    continue
                point = wall.end if at_end else wall.start
                tee = self._tee_wall(wall, walls, point)
                if tee is not None:
                    wall.tees[at_end] = tee
                elif ("end" if at_end else "start") not in (wall.source.get("free_ends") or []):
                    self._issues.warning(wall.where, "offenes Wandende bei [%g, %g]" % (point[0], point[1]))

    @staticmethod
    def _crosses(wall: WallData, other: WallData) -> bool:
        return abs(Vector2D.cross(wall.direction, other.direction)) > PARALLEL_LIMIT

    def _corner_neighbour(self, wall: WallData, walls: List[WallData], point: Point) -> Optional[WallData]:
        for other in walls:
            if other is not wall and other.is_free_end_of(point) is not None and self._crosses(wall, other):
                return other
        return None

    def _tee_wall(self, wall: WallData, walls: List[WallData], point: Point) -> Optional[WallData]:
        # the end point lies inside the band of another, crossing wall, or inside the corner block of
        # that wall with its corner neighbour (both bands meet there, beyond the wall's own end)
        for other in walls:
            if other is wall or not self._crosses(wall, other):
                continue
            along = Vector2D.dot(Vector2D.sub(point, other.start), other.direction)
            if not self._inside_depth(other, point):
                continue
            if -TOLERANCE <= along <= other.length + TOLERANCE:
                return other
            neighbour = other.neighbours[along > other.length]
            if neighbour is not None and self._inside_depth(neighbour, point):
                return other
        return None

    @staticmethod
    def _inside_depth(wall: WallData, point: Point) -> bool:
        across = Vector2D.dot(Vector2D.sub(point, wall.start), wall.normal) + wall.shift
        return -TOLERANCE <= across <= wall.thickness + TOLERANCE
