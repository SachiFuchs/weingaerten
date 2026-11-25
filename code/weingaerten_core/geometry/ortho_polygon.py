"""Rectangular (axis-parallel) polygons: validation, area, perimeter, decomposition into rects, rect overlaps."""
import logging
from typing import Any, List, Optional, Sequence, Tuple

from ..constants import TOLERANCE
from ..json_values import JsonValues
from .polygon import Polygon

logger = logging.getLogger(__name__)

# edges whose ends differ by less than this in x or y count as axis-parallel (same as the 90° rule of the walls)
AXIS_LIMIT = 0.0005

Rect = List[float]


class OrthoPolygon:
    """Stateless operations on rectangular polygons `[(x, y), ...]` and on rects `[x, y, w, h]`."""

    @staticmethod
    def parse(value: Any) -> Tuple[Optional[List[Tuple[float, float]]], Optional[str]]:
        """Return (counter-clockwise points without collinear middle points, None) or (None, error message)."""
        if not (isinstance(value, list) and len(value) >= 4 and all(
                isinstance(p, list) and len(p) == 2 and all(JsonValues.is_number(v) for v in p) for p in value)):
            return None, "Polygon ungültig (mindestens 4 Punkte [x, y])"
        points = [(float(p[0]), float(p[1])) for p in value]
        for i, a in enumerate(points):
            b = points[(i + 1) % len(points)]
            if abs(a[0] - b[0]) < TOLERANCE and abs(a[1] - b[1]) < TOLERANCE:
                return None, "Polygon hat doppelte Punkte"
            if abs(a[0] - b[0]) >= AXIS_LIMIT and abs(a[1] - b[1]) >= AXIS_LIMIT:
                return None, "Polygon nicht im 90°-Raster (Kante %d)" % (i + 1)
        points = OrthoPolygon._without_collinear(points)
        if len(points) < 4 or OrthoPolygon._self_intersects(points):
            return None, "Polygon überschneidet sich selbst"
        return Polygon.counter_clockwise(points), None

    @staticmethod
    def _without_collinear(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        result = []
        for i, p in enumerate(points):
            a, b = points[i - 1], points[(i + 1) % len(points)]
            vertical = abs(a[0] - p[0]) < AXIS_LIMIT and abs(b[0] - p[0]) < AXIS_LIMIT
            horizontal = abs(a[1] - p[1]) < AXIS_LIMIT and abs(b[1] - p[1]) < AXIS_LIMIT
            if not (vertical or horizontal):
                result.append(p)
        return result

    @staticmethod
    def _self_intersects(points: List[Tuple[float, float]]) -> bool:
        count = len(points)
        edges = [(points[i], points[(i + 1) % count]) for i in range(count)]
        for i in range(count):
            for k in range(i + 1, count):
                if k == i + 1 or (i == 0 and k == count - 1):
                    continue
                if OrthoPolygon._edges_touch(edges[i], edges[k]):
                    return True
        return False

    @staticmethod
    def _edges_touch(e: Tuple[Tuple[float, float], ...], f: Tuple[Tuple[float, float], ...]) -> bool:
        # axis-parallel segments touch when their bounding boxes overlap (within the tolerance)
        ex0, ex1 = sorted((e[0][0], e[1][0]))
        ey0, ey1 = sorted((e[0][1], e[1][1]))
        fx0, fx1 = sorted((f[0][0], f[1][0]))
        fy0, fy1 = sorted((f[0][1], f[1][1]))
        return ex0 <= fx1 + TOLERANCE / 2 and fx0 <= ex1 + TOLERANCE / 2 \
            and ey0 <= fy1 + TOLERANCE / 2 and fy0 <= ey1 + TOLERANCE / 2

    @staticmethod
    def area(points: Sequence[Tuple[float, float]]) -> float:
        """Return the enclosed area."""
        return abs(Polygon.signed_area(points))

    @staticmethod
    def perimeter(points: Sequence[Tuple[float, float]]) -> float:
        """Return the length of the closed outline."""
        count = len(points)
        return sum(abs(points[i][0] - points[(i + 1) % count][0]) + abs(points[i][1] - points[(i + 1) % count][1])
                   for i in range(count))

    @staticmethod
    def rects(points: Sequence[Tuple[float, float]]) -> List[Rect]:
        """Decompose into non-overlapping rects: horizontal bands between the vertex ys, merged downwards."""
        ys = sorted({p[1] for p in points})
        count = len(points)
        verticals = [(points[i], points[(i + 1) % count]) for i in range(count)
                     if abs(points[i][0] - points[(i + 1) % count][0]) < AXIS_LIMIT]
        open_rects, result = {}, []
        for y0, y1 in zip(ys, ys[1:]):
            middle = (y0 + y1) / 2.0
            xs = sorted(a[0] for a, b in verticals if min(a[1], b[1]) < middle < max(a[1], b[1]))
            spans = list(zip(xs[0::2], xs[1::2]))
            still_open = {}
            for span in spans:
                rect = open_rects.get(span)
                if rect is not None and abs(rect[1] + rect[3] - y0) < 1e-9:
                    rect[3] = y1 - rect[1]
                else:
                    rect = [span[0], y0, span[1] - span[0], y1 - y0]
                    result.append(rect)
                still_open[span] = rect
            open_rects = still_open
        return result

    @staticmethod
    def overlap(a: Rect, b: Rect) -> float:
        """Return the intersection area of two rects."""
        width = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
        height = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
        return width * height if width > 0 and height > 0 else 0.0

    @staticmethod
    def overlap_area(rects_a: Sequence[Rect], rects_b: Sequence[Rect]) -> float:
        """Return the intersection area of two sets of non-overlapping rects."""
        return sum(OrthoPolygon.overlap(a, b) for a in rects_a for b in rects_b)

    @staticmethod
    def polygon_overlap(polygon: Sequence[Tuple[float, float]], rects: Sequence[Rect]) -> float:
        """Return the area of any (convex or not) polygon inside the rects (rects do not overlap)."""
        subject = Polygon.counter_clockwise(list(polygon))
        total = 0.0
        for x, y, w, h in rects:
            clipped = Polygon.clip(subject, Polygon.counter_clockwise([(x, y), (x + w, y), (x + w, y + h), (x, y + h)]))
            total += abs(Polygon.signed_area(clipped)) if len(clipped) >= 3 else 0.0
        return total

    @staticmethod
    def to_json(points: Sequence[Tuple[float, float]]) -> List[List[float]]:
        """Return the points as JSON lists."""
        return [[p[0], p[1]] for p in points]
