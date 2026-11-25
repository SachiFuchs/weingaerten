"""Open polylines: length, duplicate removal and parallel offset with mitred corners."""
import logging
from typing import List, Sequence

from .vector2d import Point, Vector2D

logger = logging.getLogger(__name__)

# below this length a segment counts as a duplicate point
MIN_SEGMENT = 1e-6


class Polyline:
    """Stateless operations on open polylines given as lists of (x, y) tuples."""

    @staticmethod
    def cleaned(points: Sequence[Point]) -> List[Point]:
        """Return the points without consecutive duplicates and without collinear middle points."""
        result: List[Point] = []
        for point in points:
            point = (float(point[0]), float(point[1]))
            if result and Vector2D.length(Vector2D.sub(point, result[-1])) < MIN_SEGMENT:
                continue
            if len(result) >= 2:
                a, b = Vector2D.sub(result[-1], result[-2]), Vector2D.sub(point, result[-1])
                if abs(Vector2D.cross(a, b)) < 1e-12 and Vector2D.dot(a, b) > 0:
                    result[-1] = point
                    continue
            result.append(point)
        return result

    @staticmethod
    def length(points: Sequence[Point]) -> float:
        """Return the sum of the segment lengths."""
        return sum(Vector2D.length(Vector2D.sub(points[i + 1], points[i])) for i in range(len(points) - 1))

    @staticmethod
    def offset(points: Sequence[Point], distance: float) -> List[Point]:
        """Return the polyline moved sideways by `distance` (> 0: to the left of the direction of travel).

        Corners are mitred: each vertex is the intersection of the two moved segments, so a pipe pair
        following one centre line keeps its spacing around every bend.
        """
        line = Polyline.cleaned(points)
        if len(line) < 2:
            return list(line)
        normals = [Polyline._left_normal(line[i], line[i + 1]) for i in range(len(line) - 1)]
        result = [Vector2D.add(line[0], Vector2D.scale(normals[0], distance))]
        for i in range(1, len(line) - 1):
            n1, n2 = normals[i - 1], normals[i]
            # mitre factor 1 / (1 + cos); a reversal (cos = -1) cannot occur in a cleaned layout
            factor = distance / max(1e-9, 1.0 + Vector2D.dot(n1, n2))
            result.append(Vector2D.add(line[i], Vector2D.scale(Vector2D.add(n1, n2), factor)))
        result.append(Vector2D.add(line[-1], Vector2D.scale(normals[-1], distance)))
        return result

    @staticmethod
    def _left_normal(a: Point, b: Point) -> Point:
        d = Vector2D.sub(b, a)
        length = Vector2D.length(d)
        return (-d[1] / length, d[0] / length)
