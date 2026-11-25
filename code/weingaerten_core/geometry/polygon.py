"""Polygon operations: area, orientation, clipping, offset and point tests."""
import logging
from typing import List, Sequence

from ..constants import TOLERANCE
from .vector2d import Point, Vector2D

logger = logging.getLogger(__name__)


class Polygon:
    """Stateless operations on polygons given as lists of (x, y) points."""

    @staticmethod
    def signed_area(poly: Sequence[Point]) -> float:
        """Return the shoelace area (> 0 for counter-clockwise in a y-up system)."""
        total = 0.0
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            total += a[0] * b[1] - b[0] * a[1]
        return total / 2.0

    @staticmethod
    def counter_clockwise(poly: Sequence[Point]) -> List[Point]:
        """Return the polygon with non-negative signed area (reversed if needed)."""
        return poly if Polygon.signed_area(poly) >= 0 else list(reversed(poly))

    @staticmethod
    def clip(subject: Sequence[Point], clip: Sequence[Point]) -> List[Point]:
        """Clip a polygon by a convex counter-clockwise polygon (Sutherland–Hodgman)."""
        out = list(subject)
        for i in range(len(clip)):
            a, b = clip[i], clip[(i + 1) % len(clip)]
            points, out = out, []
            if not points:
                break
            edge = Vector2D.sub(b, a)

            def inside(p: Point) -> bool:
                return Vector2D.cross(edge, Vector2D.sub(p, a)) >= -1e-12
            for j in range(len(points)):
                current, previous = points[j], points[j - 1]
                if inside(current):
                    if not inside(previous):
                        Polygon._append_crossing(out, previous, current, a, edge)
                    out.append(current)
                elif inside(previous):
                    Polygon._append_crossing(out, previous, current, a, edge)
        return out

    @staticmethod
    def _append_crossing(out: List[Point], previous: Point, current: Point, origin: Point, edge: Point) -> None:
        crossing = Vector2D.intersect(previous, Vector2D.sub(current, previous), origin, edge)
        if crossing:
            out.append(crossing)

    @staticmethod
    def clip_half_plane(poly: Sequence[Point], origin: Point, normal: Point) -> List[Point]:
        """Keep the part of the polygon with dot(p - origin, normal) >= 0."""
        out = []

        def side(p: Point) -> float:
            return Vector2D.dot(Vector2D.sub(p, origin), normal)
        for j in range(len(poly)):
            current, previous = poly[j], poly[j - 1]
            side_current, side_previous = side(current), side(previous)
            if side_current >= 0:
                if side_previous < 0:
                    out.append(Polygon._lerp(previous, current, side_previous, side_current))
                out.append(current)
            elif side_previous >= 0:
                out.append(Polygon._lerp(previous, current, side_previous, side_current))
        return out

    @staticmethod
    def _lerp(previous: Point, current: Point, side_previous: float, side_current: float) -> Point:
        fraction = side_previous / (side_previous - side_current)
        return Vector2D.add(previous, Vector2D.scale(Vector2D.sub(current, previous), fraction))

    @staticmethod
    def contains(point: Point, poly: Sequence[Point]) -> bool:
        """Even-odd ray test; points on the boundary may count either way."""
        inside = False
        for i in range(len(poly)):
            a, b = poly[i], poly[i - 1]
            if (a[1] > point[1]) != (b[1] > point[1]):
                x = a[0] + (point[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
                if x > point[0]:
                    inside = not inside
        return inside

    @staticmethod
    def contains_or_touches(point: Point, poly: Sequence[Point], tolerance: float = TOLERANCE) -> bool:
        """Return True if the point is inside or within the tolerance of an edge."""
        if Polygon.contains(point, poly):
            return True
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            edge = Vector2D.sub(b, a)
            length_squared = Vector2D.dot(edge, edge)
            t = 0.0 if length_squared == 0 else max(0.0, min(1.0, Vector2D.dot(Vector2D.sub(point, a), edge) / length_squared))
            nearest = Vector2D.add(a, Vector2D.scale(edge, t))
            if Vector2D.length(Vector2D.sub(point, nearest)) <= tolerance:
                return True
        return False

    @staticmethod
    def offset(poly: Sequence[Point], distance: float) -> List[Point]:
        """Move every edge of the polygon outwards by distance and intersect neighbouring edges."""
        if abs(distance) < 1e-12:
            return list(poly)
        poly = Polygon.counter_clockwise(list(poly))
        count = len(poly)
        lines = []
        for i in range(count):
            a, b = poly[i], poly[(i + 1) % count]
            direction = Vector2D.sub(b, a)
            length = Vector2D.length(direction)
            outward = (direction[1] / length, -direction[0] / length)
            lines.append((Vector2D.add(a, Vector2D.scale(outward, distance)), direction))
        out = []
        for i in range(count):
            p1, d1 = lines[i - 1]
            p2, d2 = lines[i]
            corner = Vector2D.intersect(p1, d1, p2, d2)
            out.append(corner if corner is not None else p2)
        return out
