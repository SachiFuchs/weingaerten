"""Intersection of a 3D line segment with a vertical prism (plan polygon x z range)."""
import logging
from typing import List, Optional, Sequence, Tuple

from .polygon import Polygon

logger = logging.getLogger(__name__)

Point3 = Sequence[float]
Point = Tuple[float, float]
EPS = 1e-9


class SegmentPrism:
    """Parameter intervals [t0, t1] of a segment p0 -> p1 that lie inside a prism."""

    @staticmethod
    def intervals(p0: Point3, p1: Point3, polygon: Sequence[Point], z0: float, z1: float) -> List[Tuple[float, float]]:
        """Return the inside intervals of the segment (t in 0..1), sorted, possibly empty."""
        z_range = SegmentPrism._z_range(p0[2], p1[2], z0, z1)
        if z_range is None:
            return []
        result = []
        for t0, t1 in SegmentPrism._plan_ranges(p0, p1, polygon):
            low, high = max(t0, z_range[0]), min(t1, z_range[1])
            if high - low > EPS:
                result.append((low, high))
        return result

    @staticmethod
    def point(p0: Point3, p1: Point3, t: float) -> List[float]:
        """Point at parameter t."""
        return [p0[i] + (p1[i] - p0[i]) * t for i in range(3)]

    @staticmethod
    def _z_range(za: float, zb: float, z0: float, z1: float) -> Optional[Tuple[float, float]]:
        if abs(zb - za) < EPS:
            return (0.0, 1.0) if z0 <= za <= z1 else None
        t0, t1 = sorted(((z0 - za) / (zb - za), (z1 - za) / (zb - za)))
        t0, t1 = max(t0, 0.0), min(t1, 1.0)
        return (t0, t1) if t1 > t0 else None

    @staticmethod
    def _plan_ranges(p0: Point3, p1: Point3, polygon: Sequence[Point]) -> List[Tuple[float, float]]:
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        if dx * dx + dy * dy < EPS:
            return [(0.0, 1.0)] if Polygon.contains((p0[0], p0[1]), polygon) else []
        cuts = {0.0, 1.0}
        count = len(polygon)
        for i in range(count):
            a, b = polygon[i], polygon[(i + 1) % count]
            ex, ey = b[0] - a[0], b[1] - a[1]
            denominator = dx * ey - dy * ex
            if abs(denominator) < EPS:
                continue
            t = ((a[0] - p0[0]) * ey - (a[1] - p0[1]) * ex) / denominator
            s = ((a[0] - p0[0]) * dy - (a[1] - p0[1]) * dx) / denominator
            if 0.0 < t < 1.0 and -EPS <= s <= 1.0 + EPS:
                cuts.add(t)
        ordered = sorted(cuts)
        ranges = []
        for t0, t1 in zip(ordered, ordered[1:]):
            middle = (t0 + t1) / 2.0
            if Polygon.contains((p0[0] + dx * middle, p0[1] + dy * middle), polygon):
                if ranges and abs(ranges[-1][1] - t0) < EPS:
                    ranges[-1] = (ranges[-1][0], t1)
                else:
                    ranges.append((t0, t1))
        return ranges
