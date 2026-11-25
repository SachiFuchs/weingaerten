"""2D vector maths on (x, y) tuples."""
import logging
import math
from typing import Optional, Tuple

from ..constants import TOLERANCE

logger = logging.getLogger(__name__)

Point = Tuple[float, float]


class Vector2D:
    """Stateless operations on 2D points / vectors given as (x, y) tuples."""

    @staticmethod
    def sub(a: Point, b: Point) -> Point:
        """Return a - b."""
        return (a[0] - b[0], a[1] - b[1])

    @staticmethod
    def add(a: Point, b: Point) -> Point:
        """Return a + b."""
        return (a[0] + b[0], a[1] + b[1])

    @staticmethod
    def scale(a: Point, factor: float) -> Point:
        """Return a * factor."""
        return (a[0] * factor, a[1] * factor)

    @staticmethod
    def dot(a: Point, b: Point) -> float:
        """Return the dot product."""
        return a[0] * b[0] + a[1] * b[1]

    @staticmethod
    def cross(a: Point, b: Point) -> float:
        """Return the z component of the 3D cross product (> 0: b is counter-clockwise of a)."""
        return a[0] * b[1] - a[1] * b[0]

    @staticmethod
    def length(a: Point) -> float:
        """Return the Euclidean length."""
        return math.hypot(a[0], a[1])

    @staticmethod
    def equal(a: Point, b: Point, tolerance: float = TOLERANCE) -> bool:
        """Return True if both coordinates differ by at most the tolerance."""
        return abs(a[0] - b[0]) <= tolerance and abs(a[1] - b[1]) <= tolerance

    @staticmethod
    def intersect(p: Point, d: Point, q: Point, e: Point) -> Optional[Point]:
        """Intersect the lines p + s*d and q + r*e.

        Returns:
            The intersection point, or None for (nearly) parallel lines.
        """
        denominator = Vector2D.cross(d, e)
        if abs(denominator) < 1e-12:
            return None
        s = Vector2D.cross(Vector2D.sub(q, p), e) / denominator
        return Vector2D.add(p, Vector2D.scale(d, s))
