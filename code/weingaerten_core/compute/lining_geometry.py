"""Cuts one lining rectangle of a wall face into pieces around the openings and below the wall top."""
import logging
from typing import List, Tuple

from .wall_data import WallData

logger = logging.getLogger(__name__)

EPS = 1e-6
# (u0, u1, z_bottom, top0, top1): storey-local; top0/top1 = top at u0/u1 (sloped only below a roof line)
Piece = Tuple[float, float, float, float, float]


class LiningGeometry:
    """Pieces of the rectangle [u0, u1] x [z0, z1] on a wall face: openings (rough) are cut out, the top
    follows the wall top where it is lower than z1."""

    def __init__(self, wall: WallData) -> None:
        """Args:
            wall: the computed wall (openings, top line).
        """
        self._wall = wall
        self._holes = [(o.u0, o.u1, o.z_bottom, o.z_top) for o in wall.openings]

    def pieces(self, u0: float, u1: float, z0: float, z1: float) -> Tuple[List[Piece], float]:
        """Return (pieces, gross area); the gross area is the rectangle below the wall top without the cuts."""
        pieces, gross = [], 0.0
        edges = self._edges(u0, u1, z1)
        for a, b in zip(edges, edges[1:]):
            if b - a < 1e-4:
                continue
            top_a, top_b = min(z1, self._wall.top_at(a)), min(z1, self._wall.top_at(b))
            if (top_a + top_b) / 2.0 <= z0 + 1e-4:
                continue
            gross += (b - a) * ((top_a + top_b) / 2.0 - z0)
            pieces.extend(self._column(a, b, z0, top_a, top_b))
        return pieces, gross

    def _edges(self, u0: float, u1: float, z1: float) -> List[float]:
        # slab borders: rectangle ends, opening sides, kinks of the top and where the top crosses z1
        edges = {u0, u1}
        edges.update(u for h in self._holes for u in h[:2] if u0 < u < u1)
        profile = self._wall.profile(u0, u1)
        edges.update(u for u, _ in profile if u0 < u < u1)
        for (ua, za), (ub, zb) in zip(profile, profile[1:]):
            if abs(zb - za) > EPS:
                u = ua + (z1 - za) * (ub - ua) / (zb - za)
                if ua < u < ub:
                    edges.add(u)
        return sorted(edges)

    def _column(self, a: float, b: float, z0: float, top_a: float, top_b: float) -> List[Piece]:
        # free height intervals of the slab; the last one ends at the (possibly sloped) top
        low_top = min(top_a, top_b)
        cuts = sorted((h[2], h[3]) for h in self._holes if h[0] < b - EPS and h[1] > a + EPS
                      and h[3] > z0 + EPS and h[2] < low_top - EPS)
        pieces, bottom = [], z0
        for zb, zt in cuts:
            if zb > bottom + 1e-4:
                pieces.append((a, b, bottom, zb, zb))
            bottom = max(bottom, zt)
        if low_top > bottom + 1e-4:
            pieces.append((a, b, bottom, top_a, top_b))
        return pieces

    @staticmethod
    def area(piece: Piece) -> float:
        """Face area of a piece."""
        a, b, bottom, top_a, top_b = piece
        return (b - a) * ((top_a + top_b) / 2.0 - bottom)
