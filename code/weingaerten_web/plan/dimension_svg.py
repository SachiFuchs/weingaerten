"""Dimension lines of the plan (horizontal, vertical, chain along a wall)."""
import logging
from typing import Any, Callable, Dict

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools
from .plan_geometry import PlanGeometry

logger = logging.getLogger(__name__)

Transform = Callable[[float], float]
TICKS = ('<g stroke="%s" stroke-width="1" pointer-events="none"><line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>'
         '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/><line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/></g>')
CHAIN_LINE = '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#1C69D4" stroke-width="1"/>'
# the chain runs 25 cm outside the outer face, ticks reach 6 cm to each side
CHAIN_OFFSET = -0.25
TICK_HALF = 0.06


class DimensionSvg:
    """SVG snippets for dimension lines with oblique ticks."""

    @staticmethod
    def horizontal(xa: float, ya: float, xb: float, yb: float, label: str, color: str) -> str:
        """Return a dimension line from a to b with the label centred above it."""
        return (TICKS + '<text x="%.1f" y="%.1f" text-anchor="middle" font-size="13" fill="%s">%s</text>') % (
            color, xa, ya, xb, yb, xa - 4, ya + 4, xa + 4, ya - 4, xb - 4, yb + 4, xb + 4, yb - 4,
            (xa + xb) / 2, ya - 5, color, HtmlTools.escape(label))

    @staticmethod
    def vertical(xa: float, ya: float, xb: float, yb: float, label: str, color: str) -> str:
        """Return a vertical dimension line with the label rotated beside it."""
        mx, my = xa, (ya + yb) / 2
        return (TICKS + '<text x="%.1f" y="%.1f" text-anchor="middle" font-size="13" fill="%s" '
                'transform="rotate(-90 %.1f %.1f)">%s</text>') % (
            color, xa, ya, xb, yb, xa - 4, ya + 4, xa + 4, ya - 4, xb - 4, yb + 4, xb + 4, yb - 4,
            mx - 5, my, color, mx - 5, my, HtmlTools.escape(label))

    @staticmethod
    def wall_chain(wall: Dict[str, Any], frame: PlanGeometry, to_x: Transform, to_y: Transform) -> str:
        """Return the chain of the wall ends and the rough opening edges along the outer face."""
        u_range = wall["u_range"].get("outside") or wall["u_range"].get("left")
        stops = sorted({round(x, 4) for x in u_range}
                       | {round(x, 4) for o in wall["openings"] for x in (o["rough"]["u0"], o["rough"]["u1"])})
        normal = frame.normal
        angle = wall["direction"] % 360
        # keep the text upright
        rotation = angle + 180 if 90 < angle <= 270 else angle
        out = []
        for u in stops:
            a = frame.point(u, 0)
            tick_a = (a[0] + normal[0] * (CHAIN_OFFSET - TICK_HALF), a[1] + normal[1] * (CHAIN_OFFSET - TICK_HALF))
            tick_b = (a[0] + normal[0] * (CHAIN_OFFSET + TICK_HALF), a[1] + normal[1] * (CHAIN_OFFSET + TICK_HALF))
            out.append(CHAIN_LINE % (to_x(tick_a[0]), to_y(tick_a[1]), to_x(tick_b[0]), to_y(tick_b[1])))
        for k in range(len(stops) - 1):
            a, b = frame.point(stops[k], 0), frame.point(stops[k + 1], 0)
            a = (a[0] + normal[0] * CHAIN_OFFSET, a[1] + normal[1] * CHAIN_OFFSET)
            b = (b[0] + normal[0] * CHAIN_OFFSET, b[1] + normal[1] * CHAIN_OFFSET)
            mx, my = to_x((a[0] + b[0]) / 2), to_y((a[1] + b[1]) / 2)
            out.append(CHAIN_LINE % (to_x(a[0]), to_y(a[1]), to_x(b[0]), to_y(b[1])))
            out.append('<text x="%.1f" y="%.1f" font-size="11" fill="#1C69D4" text-anchor="middle" '
                       'transform="rotate(%.1f %.1f %.1f)" dy="-3">%s</text>' % (
                           mx, my, rotation, mx, my, HtmlTools.escape(GermanFormat.decimal(stops[k + 1] - stops[k], 2))))
        return "".join(out)
