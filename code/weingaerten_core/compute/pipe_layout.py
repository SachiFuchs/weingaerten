"""Centre line of a heating circuit inside its laying rect: spiral (Schnecke) or meander.

Supply and return pipes are the centre line moved by ± spacing / 2, so the centre line runs with a pitch
of 2 · spacing and the pipes end up evenly spaced by `spacing` (bifilar laying, counter-flow)."""
import logging
from typing import List, Optional, Tuple

from ..geometry.polygon import Polygon
from ..geometry.vector2d import Point, Vector2D

logger = logging.getLogger(__name__)

# corner of the rect -> (mirror x, mirror y) of the local frame whose origin is that corner
ENTRY_MIRROR = {"nw": (False, False), "ne": (True, False), "sw": (False, True), "se": (True, True)}
Rect = Tuple[float, float, float, float]


class PipeLayout:
    """Builds the centre line of one circuit in plan coordinates."""

    def __init__(self, rect: Rect, spacing: float, edge: float, entry: str,
                 cutout: Optional[Rect] = None) -> None:
        """Args:
            rect: laying area `(x, y, w, h)`.
            spacing: pipe spacing (distance between neighbouring pipes).
            edge: distance of the outermost pipe from the rect border (and from the cutout).
            entry: corner `nw|ne|sw|se` where supply and return leave the area.
            cutout: unheated rect in one corner of `rect` (e.g. a shower), or None.
        """
        self._rect = rect
        self._spacing = spacing
        self._edge = edge
        self._entry = entry
        self._cutout = cutout

    def area_polygon(self) -> List[Point]:
        """Return the laying area (the rect, or the L-shape left by a corner cutout), counter-clockwise."""
        x, y, w, h = self._rect
        if self._cutout is None:
            return Polygon.counter_clockwise([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
        cx, cy, cw, ch = self._cutout
        corner_x = x + w if abs(cx + cw - (x + w)) < 1e-6 else x
        corner_y = y + h if abs(cy + ch - (y + h)) < 1e-6 else y
        inner = (cx if corner_x > x else cx + cw, cy if corner_y > y else cy + ch)
        corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        result: List[Point] = []
        for corner in corners:
            if corner == (corner_x, corner_y):
                # the cut corner is replaced by the three corners of the notch, in walking order
                previous = result[-1] if result else corners[-1]
                first = (inner[0], corner[1]) if previous[1] == corner[1] else (corner[0], inner[1])
                last = (corner[0], inner[1]) if first[0] == inner[0] else (inner[0], corner[1])
                result += [first, inner, last]
            else:
                result.append(corner)
        return Polygon.counter_clockwise(result)

    @staticmethod
    def cutout_in_corner(rect: Rect, cutout: Rect) -> bool:
        """Return True if the cutout lies inside the rect and touches one of its corners."""
        x, y, w, h = rect
        cx, cy, cw, ch = cutout
        inside = cw > 0 and ch > 0 and x - 1e-6 <= cx and cx + cw <= x + w + 1e-6 and y - 1e-6 <= cy \
            and cy + ch <= y + h + 1e-6 and cw < w and ch < h
        at_x = abs(cx - x) < 1e-6 or abs(cx + cw - (x + w)) < 1e-6
        at_y = abs(cy - y) < 1e-6 or abs(cy + ch - (y + h)) < 1e-6
        return inside and at_x and at_y

    def spiral(self) -> List[Point]:
        """Return a spiral from the entry corner inwards: ring after ring of the area moved inwards by the pitch.

        Each ring starts at its vertex nearest to the entry corner and stops one pitch before that start, where
        the line steps inwards to the next ring (for a rect this is the classic rectangular spiral).
        """
        pitch = 2 * self._spacing
        area = self.area_polygon()
        anchor = self._entry_corner()
        points: List[Point] = []
        depth = self._edge + self._spacing / 2
        while True:
            ring = self._ring(area, depth)
            if ring is None:
                break
            start = min(range(len(ring)), key=lambda i: Vector2D.length(Vector2D.sub(ring[i], anchor)))
            ordered = ring[start:] + ring[:start]
            ordered = self._walk_along_first_side(ordered)
            back = Vector2D.sub(ordered[-1], ordered[0])
            stop = Vector2D.add(ordered[0], Vector2D.scale(back, min(1.0, pitch / max(1e-9, Vector2D.length(back)))))
            points += ordered + [stop]
            depth += pitch
        return points

    def _ring(self, area: List[Point], depth: float) -> Optional[List[Point]]:
        # an inward offset is valid while every edge keeps its direction and the ring is still a pitch wide
        ring = Polygon.offset(area, -depth)
        for i in range(len(area)):
            old = Vector2D.sub(area[(i + 1) % len(area)], area[i])
            new = Vector2D.sub(ring[(i + 1) % len(ring)], ring[i])
            if Vector2D.dot(old, new) <= 1e-9:
                return self._main_ring(depth) if self._cutout is not None else None
        xs, ys = [p[0] for p in ring], [p[1] for p in ring]
        if max(xs) - min(xs) < 2 * self._spacing or max(ys) - min(ys) < 2 * self._spacing:
            return None
        return ring

    def _main_ring(self, depth: float) -> Optional[List[Point]]:
        # once the arm beside the cutout is used up, the rest is the larger rect next to the cutout
        x, y, w, h = self._rect
        cx, cy, cw, ch = self._cutout
        beside_x = (x, y, cx - x, h) if cx > x + 1e-6 else (cx + cw, y, x + w - cx - cw, h)
        beside_y = (x, y, w, cy - y) if cy > y + 1e-6 else (x, cy + ch, w, y + h - cy - ch)
        bx, by, bw, bh = max(beside_x, beside_y, key=lambda r: r[2] * r[3])
        if bw - 2 * depth < 2 * self._spacing or bh - 2 * depth < 2 * self._spacing:
            return None
        return Polygon.counter_clockwise([(bx + depth, by + depth), (bx + bw - depth, by + depth),
                                          (bx + bw - depth, by + bh - depth), (bx + depth, by + bh - depth)])

    def _walk_along_first_side(self, ring: List[Point]) -> List[Point]:
        # walk the ring so that it starts along the side the meander also starts on (the u side of the entry)
        mirror_x, mirror_y = ENTRY_MIRROR[self._entry]
        first = Vector2D.sub(ring[1], ring[0])
        wanted = -1.0 if mirror_x else 1.0
        if abs(first[0]) > 1e-9 and first[0] * wanted > 0:
            return ring
        return [ring[0]] + list(reversed(ring[1:]))

    def _entry_corner(self) -> Point:
        x, y, w, h = self._rect
        mirror_x, mirror_y = ENTRY_MIRROR[self._entry]
        return (x + w if mirror_x else x, y + h if mirror_y else y)

    def meander(self) -> List[Point]:
        """Return a serpentine from the entry corner; rows run along the longer side of the rect."""
        x, y, w, h = self._rect
        along_u = w >= h
        length, depth = (w, h) if along_u else (h, w)
        pitch = 2 * self._spacing
        inset = self._edge + self._spacing / 2
        rows, v = [], inset
        while v <= depth - inset + 1e-9:
            rows.append(v)
            v += pitch
        points: List[Point] = []
        for k, v in enumerate(rows):
            ends = (inset, length - inset) if k % 2 == 0 else (length - inset, inset)
            points += [(ends[0], v), (ends[1], v)]
        if not along_u:
            points = [(v, u) for u, v in points]
        return [self._to_plan(p) for p in points]

    def _to_plan(self, point: Point) -> Point:
        x, y, w, h = self._rect
        mirror_x, mirror_y = ENTRY_MIRROR[self._entry]
        u, v = point
        return (x + w - u if mirror_x else x + u, y + h - v if mirror_y else y + v)
