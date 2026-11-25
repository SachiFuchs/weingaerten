"""Splits every wall layer into solid pieces around the rough openings."""
import logging
from typing import Any, Dict, List, Optional, Tuple

from ..geometry.polygon import Polygon
from ..geometry.vector2d import Point, Vector2D
from .wall_data import WallData

logger = logging.getLogger(__name__)


class LayerPieceBuilder:
    """Builds the layers of a wall with their pieces (footprint, z range, volume)."""

    def __init__(self, z0: float) -> None:
        """Args:
            z0: storey elevation (absolute z of the wall bottom); the top is each wall's own height.
        """
        self._z0 = z0

    def build(self, wall: WallData) -> List[Dict[str, Any]]:
        """Return `[{index, material, offset, thickness, footprint, volume, pieces}]` per layer.

        The wall is cut into vertical slabs at every u0 / u1 of its openings; within a slab the
        free height intervals (outside all covering openings) become one piece each. So the
        openings are real holes and the volumes need no subtraction.
        """
        break_points = sorted({u for opening in wall.openings for u in (opening.u0, opening.u1)}
                              | set(wall.breaks(-1e9, 1e9)))
        bounds = [None] + break_points + [None]
        layers = []
        for layer in wall.info["layers"]:
            t0, t1 = layer["offset"], layer["offset"] + layer["thickness"]
            polygon = wall.band_polygon(t0, t1)
            pieces = self._pieces(wall, polygon, bounds)
            layers.append({"index": layer["index"], "material": layer["material"], "offset": t0,
                           "thickness": layer["thickness"], "footprint": [list(p) for p in polygon],
                           "volume": sum(piece["volume"] for piece in pieces) if pieces else 0.0,
                           "pieces": pieces})
        return layers

    def _pieces(self, wall: WallData, polygon: List[Point], bounds: List[Optional[float]]) -> List[Dict[str, Any]]:
        pieces = []
        for i in range(len(bounds) - 1):
            low, high = bounds[i], bounds[i + 1]
            slab = self._slab(wall, polygon, low, high)
            if len(slab) < 3 or abs(Polygon.signed_area(slab)) < 1e-9:
                continue
            area = abs(Polygon.signed_area(slab))
            plane = self._top_plane(wall, low, high)
            for z_low, z_high in self._free_intervals(wall, self._slab_middle(low, high)):
                piece = {"footprint": [list(p) for p in slab], "z0": self._z0 + z_low,
                         "z1": self._z0 + z_high, "volume": area * (z_high - z_low), "top_plane": None}
                if plane is not None and z_high >= wall.top_at(self._slab_middle(low, high)) - 1e-9:
                    # top interval under a sloped top: the top follows the plane, z1 = its highest corner
                    tops = [plane[0] * p[0] + plane[1] * p[1] + plane[2] for p in slab]
                    centroid = self._centroid(slab)
                    piece.update(z1=max(tops), top_plane=list(plane),
                                 volume=area * (plane[0] * centroid[0] + plane[1] * centroid[1] + plane[2]
                                                - piece["z0"]))
                pieces.append(piece)
        return pieces

    def _top_plane(self, wall: WallData, low: Optional[float], high: Optional[float]) -> Optional[List[float]]:
        # absolute top plane z = a*x + b*y + c of a slab with a sloped top (None when level)
        if wall.roof is None:
            return None
        middle = self._slab_middle(low, high)
        u_a, u_b = middle - 0.5, middle + 0.5
        if low is not None:
            u_a = max(u_a, low)
        if high is not None:
            u_b = min(u_b, high)
        slope = (wall.top_at(u_b) - wall.top_at(u_a)) / (u_b - u_a)
        if abs(slope) < 1e-12:
            return None
        intercept = self._z0 + wall.top_at(u_a) - slope * u_a
        dx, dy = wall.direction
        return [slope * dx, slope * dy, intercept - slope * (dx * wall.start[0] + dy * wall.start[1])]

    @staticmethod
    def _centroid(poly: List[Point]) -> Point:
        area = Polygon.signed_area(poly)
        cx = cy = 0.0
        for i, p in enumerate(poly):
            q = poly[(i + 1) % len(poly)]
            cross = p[0] * q[1] - q[0] * p[1]
            cx += (p[0] + q[0]) * cross
            cy += (p[1] + q[1]) * cross
        return (cx / (6 * area), cy / (6 * area))

    @staticmethod
    def _slab(wall: WallData, polygon: List[Point], low: Optional[float], high: Optional[float]) -> List[Point]:
        slab = list(polygon)
        if low is not None:
            slab = Polygon.clip_half_plane(slab, Vector2D.add(wall.start, Vector2D.scale(wall.direction, low)),
                                           wall.direction)
        if high is not None and slab:
            slab = Polygon.clip_half_plane(slab, Vector2D.add(wall.start, Vector2D.scale(wall.direction, high)),
                                           Vector2D.scale(wall.direction, -1))
        return slab

    @staticmethod
    def _slab_middle(low: Optional[float], high: Optional[float]) -> float:
        # a u value strictly inside the slab; open end slabs use a point just inside their bound
        if low is None:
            return high - 1e-6 if high is not None else 0
        if high is None:
            return low + 1e-6
        return (low + high) / 2.0

    def _free_intervals(self, wall: WallData, middle: float) -> List[Tuple[float, float]]:
        top = wall.top_at(middle)
        holes = sorted((o.z_bottom, o.z_top) for o in wall.openings if o.u0 < middle < o.u1)
        intervals, current = [], 0.0
        for bottom, top_hole in holes:
            if bottom > current + 1e-9:
                intervals.append((current, min(bottom, top)))
            current = max(current, top_hole)
        if current < top - 1e-9:
            intervals.append((current, top))
        return intervals
