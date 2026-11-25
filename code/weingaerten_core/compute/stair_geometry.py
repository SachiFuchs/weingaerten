"""Local frame of a stair run (u along the run, v across towards the turn side) and the winder polygons."""
import logging
import math
from typing import List, Tuple

logger = logging.getLogger(__name__)

DIRECTIONS = {"west": (-1.0, 0.0), "east": (1.0, 0.0), "north": (0.0, -1.0), "south": (0.0, 1.0)}
UV = Tuple[float, float]


class StairGeometry:
    """Maps run coordinates to plan coordinates for a stair in a rectangle (plan y grows southwards).

    u runs from the start edge in the walking direction, v from the side opposite the turn (v = 0) to the turn
    side (v = width); the winder square is the last `width` of the run, the pivot its inner corner (L - W, W)."""

    def __init__(self, rect: List[float], direction: str, side: str) -> None:
        """Args:
            rect: [x, y, w, h] of the whole stair.
            direction: walking direction of the straight run (west|east|north|south).
            side: turn side `left` or `right` (seen in walking direction).
        """
        x, y, w, h = (float(v) for v in rect)
        self.d = DIRECTIONS[direction]
        left = (self.d[1], -self.d[0])  # plan y points south: left of west is south
        self.l = left if side == "left" else (-left[0], -left[1])
        corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        # origin: corner of the start edge (lowest u) on the side opposite the turn (lowest v)
        self.o = min(corners, key=lambda p: (round(self._dot(p, self.d), 9), self._dot(p, self.l)))
        self.length = abs(w if self.d[1] == 0 else h)
        self.width = abs(h if self.d[1] == 0 else w)

    @staticmethod
    def _dot(p: Tuple[float, float], q: Tuple[float, float]) -> float:
        return p[0] * q[0] + p[1] * q[1]

    def plan(self, u: float, v: float) -> List[float]:
        """Plan point of run coordinates."""
        return [self.o[0] + u * self.d[0] + v * self.l[0], self.o[1] + u * self.d[1] + v * self.l[1]]

    def plane(self, a_u: float, a_v: float, c: float) -> List[float]:
        """Absolute plane `[a, b, c]` (z = a·x + b·y + c) of the run plane z = a_u·u + a_v·v + c."""
        a = a_u * self.d[0] + a_v * self.l[0]
        b = a_u * self.d[1] + a_v * self.l[1]
        return [a, b, c - a_u * self._dot(self.o, self.d) - a_v * self._dot(self.o, self.l)]

    def winders(self, steps: int) -> List[List[UV]]:
        """Wedges of the winder square around the pivot, from the run (ray towards v = 0) to the exit (ray
        towards u = L), each as a run-coordinate polygon."""
        length, width = self.length, self.width
        pivot = (length - width, width)

        def hit(theta: float) -> UV:
            # ray from the pivot with angle theta (-90 = towards v = 0, 0 = towards u = L) meets the square edge
            if theta < -45.0:
                t = width / -math.sin(math.radians(theta))
                return (pivot[0] + t * math.cos(math.radians(theta)), 0.0)
            return (length, width + width * math.tan(math.radians(theta)))

        angles = [-90.0 + 90.0 * k / steps for k in range(steps + 1)]
        wedges = []
        for a0, a1 in zip(angles, angles[1:]):
            points = [pivot, hit(a0)]
            if a0 < -45.0 < a1:
                points.append((length, 0.0))
            points.append(hit(a1))
            wedges.append(points)
        return wedges

    def winder_angles(self, steps: int) -> List[float]:
        """Angles (degrees, run frame) of the front edges of the winders, from the run boundary (-90)."""
        return [-90.0 + 90.0 * k / steps for k in range(steps)]
