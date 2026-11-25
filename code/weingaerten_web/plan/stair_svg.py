"""Stairs in the plan: tread outlines and the walking line (Lauflinie) with an arrow at the top."""
import logging
from typing import Any, Callable, Dict, List

from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

Transform = Callable[[float], float]
escape = HtmlTools.escape


class StairSvg:
    """Draws the `stairs` of a storey (all treads, also above the section)."""

    def __init__(self, to_x: Transform, to_y: Transform) -> None:
        """Args:
            to_x, to_y: plan → SVG transforms.
        """
        self._to_x, self._to_y = to_x, to_y

    def render(self, storey: Dict[str, Any]) -> str:
        """Return a `<g class="stair">` per stair."""
        return "".join(self._stair(stair) for stair in storey.get("stairs") or [])

    def _points(self, points: List[List[float]]) -> str:
        return " ".join("%.2f,%.2f" % (self._to_x(p[0]), self._to_y(p[1])) for p in points)

    def _stair(self, stair: Dict[str, Any]) -> str:
        # stringer stairs: wooden treads; solid stairs: concrete block steps
        treads = [p for p in stair["parts"] if p["kind"] in ("tread", "step")]
        fill, stroke = ("#D9D9D6", "#555") if stair.get("construction") == "solid" else ("#F3E2C4", "#7A5A30")
        outlines = "".join('<polygon points="%s" fill="%s" stroke="%s" stroke-width="0.6"/>'
                           % (self._points(t["footprint"]), fill, stroke) for t in treads)
        # walking line through the tread centroids, arrow head at the last tread
        centres = [[sum(p[0] for p in t["footprint"]) / len(t["footprint"]),
                    sum(p[1] for p in t["footprint"]) / len(t["footprint"])] for t in treads]
        line = ('<polyline points="%s" fill="none" stroke="#333" stroke-width="1" marker-end="url(#stair-arrow)"/>'
                % self._points(centres)) if len(centres) > 1 else ""
        marker = ('<defs><marker id="stair-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
                  'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#333"/></marker></defs>')
        return ('<g class="stair" data-name="%s" data-steps="%d" data-rise="%.1f" data-going="%.1f">%s%s%s</g>'
                % (escape(stair.get("name") or stair["id"]), stair["risers"], stair["rise"] * 100,
                   stair["going"] * 100, marker, outlines, line))
