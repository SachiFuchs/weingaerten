"""Light wells in the plan: concrete walls and floor outline, the grating hatched."""
import logging
from typing import Any, Callable, Dict, List

from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

Transform = Callable[[float], float]
escape = HtmlTools.escape


class LightWellSvg:
    """Draws the `light_wells` of a storey (Lichtschacht with Gitterrost)."""

    def __init__(self, to_x: Transform, to_y: Transform) -> None:
        """Args:
            to_x, to_y: plan → SVG transforms.
        """
        self._to_x, self._to_y = to_x, to_y

    def render(self, storey: Dict[str, Any]) -> str:
        """Return a `<g class="lightwell">` per light well."""
        wells = storey.get("light_wells") or []
        if not wells:
            return ""
        pattern = ('<defs><pattern id="grating-hatch" width="6" height="6" patternUnits="userSpaceOnUse">'
                   '<path d="M0,0 L0,6 M3,0 L3,6" stroke="#5A6168" stroke-width="0.8"/></pattern></defs>')
        return pattern + "".join(self._well(well) for well in wells)

    def _points(self, points: List[List[float]]) -> str:
        return " ".join("%.2f,%.2f" % (self._to_x(p[0]), self._to_y(p[1])) for p in points)

    def _well(self, well: Dict[str, Any]) -> str:
        walls = "".join('<polygon points="%s" fill="#B5B5B0" stroke="#333" stroke-width="0.6"/>'
                        % self._points(p["footprint"]) for p in well["parts"] if p["kind"] == "wall")
        grating = "".join('<polygon points="%s" fill="url(#grating-hatch)" stroke="#5A6168" stroke-width="0.6"/>'
                          % self._points(p["footprint"]) for p in well["parts"] if p["kind"] == "grating")
        return ('<g class="lightwell" data-name="%s" data-size="%.0f × %.0f × %.0f cm">%s%s</g>'
                % (escape(well.get("name") or well["id"]), well["width"] * 100, well["projection"] * 100,
                   well["depth"] * 100, walls, grating))
