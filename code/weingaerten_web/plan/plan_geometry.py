"""Plan coordinates of a wall from the HOUSE answer, and half-plane clipping for the section."""
import logging
import math
from typing import Any, Dict, List, Sequence, Tuple

logger = logging.getLogger(__name__)

PlanPoint = Tuple[float, float]


class PlanGeometry:
    """Wall frame (`d`, `n`, thickness) of one HOUSE wall; `point(u, t)` gives plan coordinates."""

    def __init__(self, wall: Dict[str, Any]) -> None:
        """Args:
            wall: a wall object of the HOUSE answer.
        """
        angle = math.radians(wall["direction"])
        self.direction = (math.cos(angle), math.sin(angle))
        self.normal = tuple(wall["normal_in"])
        self.thickness = wall["thickness"]
        # depth of the reference line below the first face
        self._shift = {"outside_face": 0.0, "left_face": 0.0, "center": self.thickness / 2}.get(
            wall.get("reference"), self.thickness)
        self._start = wall["start"]

    def point(self, u: float, t: float) -> PlanPoint:
        """Return the plan point at wall coordinate u and depth t."""
        x, y = self._start
        return (x + self.direction[0] * u + self.normal[0] * (t - self._shift),
                y + self.direction[1] * u + self.normal[1] * (t - self._shift))

    def along(self, u: float) -> PlanPoint:
        """Return the point at u on the reference line (the origin of a section plane)."""
        x, y = self._start
        return (x + self.direction[0] * u, y + self.direction[1] * u)

    @staticmethod
    def clip_half_plane(poly: Sequence[Sequence[float]], origin: PlanPoint, normal: PlanPoint) -> List[PlanPoint]:
        """Keep the part of the polygon with dot(p - origin, normal) >= 0."""
        out = []

        def side(p: Sequence[float]) -> float:
            return (p[0] - origin[0]) * normal[0] + (p[1] - origin[1]) * normal[1]
        for j in range(len(poly)):
            current, previous = poly[j], poly[j - 1]
            side_current, side_previous = side(current), side(previous)
            if side_current >= 0:
                if side_previous < 0:
                    out.append(PlanGeometry._lerp(previous, current, side_previous / (side_previous - side_current)))
                out.append(tuple(current))
            elif side_previous >= 0:
                out.append(PlanGeometry._lerp(previous, current, side_previous / (side_previous - side_current)))
        return out

    @staticmethod
    def _lerp(previous: Sequence[float], current: Sequence[float], fraction: float) -> PlanPoint:
        return (previous[0] + (current[0] - previous[0]) * fraction, previous[1] + (current[1] - previous[1]) * fraction)
