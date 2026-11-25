"""One wall of a storey with its reference line and the corner geometry of its layer lines."""
import logging
import math
from typing import Any, Dict, List, Optional

from ..geometry.polygon import Polygon
from ..geometry.vector2d import Point, Vector2D

logger = logging.getLogger(__name__)


class WallData:
    """A parsed wall and its computed parts.

    Wall coordinates: `u` along the direction `d` from `start`, `t` the depth from the first face
    (outside face for exterior walls, left face for interior walls) along the inward normal `n`.
    `shift` is the depth of the reference line, so a plan point is `start + u*d + (t - shift)*n`.
    """

    def __init__(self, source: Dict[str, Any], where: str, category: str, info: Dict[str, Any],
                 start: Point, end: Point, normal: Point, shift: float) -> None:
        """Args:
            source: the wall JSON of the storey file.
            where: location for messages (`<storey>.<wall>`).
            category: `exterior_wall` or `interior_wall`.
            info: layer info of the assembly (see AssemblyInfo).
            start, end: reference line.
            normal: inward normal `n`.
            shift: depth of the reference line.
        """
        self.source = source
        self.id = source.get("id")
        self.where = where
        self.category = category
        self.info = info
        self.start = start
        self.end = end
        self.length = Vector2D.length(Vector2D.sub(end, start))
        self.direction = Vector2D.scale(Vector2D.sub(end, start), 1.0 / self.length)
        self.normal = normal
        self.shift = shift
        self.thickness = info["thickness"]
        self.height = 0.0
        self.roof = None  # RoofProfile of a `shape: roof` wall; None = rectangular at `height`
        self.neighbours = {False: None, True: None}
        self.tees = {False: None, True: None}
        self.footprint: List[Point] = []
        self.u_ranges: Dict[float, tuple] = {}
        self.openings: list = []
        self.layers: list = []
        self.faces: Dict[str, Any] = {}
        self.openings_out: list = []

    @property
    def is_exterior(self) -> bool:
        """True for exterior walls."""
        return self.category == "exterior_wall"

    @property
    def degrees(self) -> float:
        """Direction angle in degrees, 0 = +x, in [0, 360)."""
        return (math.degrees(math.atan2(self.direction[1], self.direction[0])) + 360.0) % 360.0

    def base(self, t: float) -> Point:
        """Return the start point of the layer line at depth t (before corner trimming)."""
        return Vector2D.add(self.start, Vector2D.scale(self.normal, t - self.shift))

    def u_of(self, point: Point) -> float:
        """Return the wall coordinate u of a plan point."""
        return Vector2D.dot(Vector2D.sub(point, self.start), self.direction)

    def point_3d(self, u: float, t: float, z: float, z0: float) -> List[float]:
        """Return [x, y, z] of wall coordinates (u, t) at storey height z above z0."""
        point = Vector2D.add(self.base(t), Vector2D.scale(self.direction, u))
        return [point[0], point[1], z0 + z]

    def corner_point(self, t: float, at_end: bool) -> Point:
        """Return the end point of the layer line at depth t, trimmed at the corner or T-joint."""
        tee = self.tees[at_end]
        if tee is not None:
            # the far end tells on which side of the crossed wall this wall lies
            far_end = self.start if at_end else self.end
            side = Vector2D.dot(Vector2D.sub(far_end, tee.start), tee.normal) + tee.shift
            crossing = Vector2D.intersect(self.base(t), self.direction,
                                          tee.base(0.0 if side < 0 else tee.thickness), tee.direction)
            if crossing is not None:
                return crossing
        return self._mitred_point(t, at_end)

    def _mitred_point(self, t: float, at_end: bool) -> Point:
        # a corner cuts every layer line with the neighbour's line of the same depth; lines deeper
        # than the neighbour use the neighbour's innermost line
        point = self.end if at_end else self.start
        neighbour = self.neighbours[at_end]
        if neighbour is not None:
            crossing = Vector2D.intersect(self.base(t), self.direction,
                                          neighbour.base(min(t, neighbour.thickness)), neighbour.direction)
            if crossing is not None:
                return crossing
        return Vector2D.add(point, Vector2D.scale(self.normal, t - self.shift))

    def band_polygon(self, t0: float, t1: float) -> List[Point]:
        """Return the counter-clockwise plan polygon between the layer lines t0 and t1."""
        # at a corner with a thinner neighbour the mitre bends at the neighbour's thickness; without that
        # break point the end edge would cut into the neighbour
        start = [self.corner_point(t, False) for t in self._end_depths(t0, t1, False)]
        end = [self.corner_point(t, True) for t in self._end_depths(t0, t1, True)]
        return Polygon.counter_clockwise([start[0]] + end + start[:0:-1])

    def _end_depths(self, t0: float, t1: float, at_end: bool) -> List[float]:
        neighbour = self.neighbours[at_end]
        if self.tees[at_end] is None and neighbour is not None and t0 + 1e-9 < neighbour.thickness < t1 - 1e-9:
            return [t0, neighbour.thickness, t1]
        return [t0, t1]

    def compute_footprint(self) -> None:
        """Compute the footprint and the u range of both face lines."""
        thickness = self.thickness
        self.footprint = self.band_polygon(0, thickness)
        self.u_ranges = {0.0: (self.u_of(self.corner_point(0, False)), self.u_of(self.corner_point(0, True))),
                         thickness: (self.u_of(self.corner_point(thickness, False)),
                                     self.u_of(self.corner_point(thickness, True)))}

    def is_free_end_of(self, point: Point) -> Optional[bool]:
        """Return at_end (False / True) if the point is this wall's start / end, else None."""
        if Vector2D.equal(self.start, point):
            return False
        if Vector2D.equal(self.end, point):
            return True
        return None

    def top_at(self, u: float) -> float:
        """Storey-local height of the wall top at u (roof line on the reference line, else `height`)."""
        if self.roof is None:
            return self.height
        return self.roof.height_at(Vector2D.add(self.start, Vector2D.scale(self.direction, u)))

    def breaks(self, u_a: float, u_b: float) -> List[float]:
        """Return the sorted u values in (u_a, u_b) where the top line has a kink (the ridge)."""
        if self.roof is None:
            return []
        axis = self.roof.axis
        if abs(self.direction[axis]) < 1e-9:
            return []
        u = (self.roof.ridge - self.start[axis]) / self.direction[axis]
        low, high = min(u_a, u_b), max(u_a, u_b)
        return [u] if low + 1e-9 < u < high - 1e-9 else []

    def profile(self, u_a: float, u_b: float) -> List[List[float]]:
        """Return the top line `[[u, z]]` from u_a to u_b (ascending u) with its kinks."""
        low, high = min(u_a, u_b), max(u_a, u_b)
        return [[u, self.top_at(u)] for u in [low] + self.breaks(low, high) + [high]]

    def min_top(self, u_a: float, u_b: float) -> float:
        """Lowest wall top over [u_a, u_b] (piecewise linear, so at an end or a kink)."""
        return min(z for _, z in self.profile(u_a, u_b))

    def top_area(self, u_a: float, u_b: float) -> float:
        """Area below the top line over [u_a, u_b] (exact, piecewise linear)."""
        points = self.profile(u_a, u_b)
        return sum((q[0] - p[0]) * (p[1] + q[1]) / 2.0 for p, q in zip(points, points[1:]))
