"""Outdoor areas in the plan (e.g. the covered terrace): light fill, dashed outline, name and area."""
import logging
from typing import Any, Callable, Dict

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

Transform = Callable[[float], float]
FILL = "#EFE6D2"
OUTLINE = "#8A7350"


class OutdoorAreaSvg:
    """Draws the `outdoor_areas` of a storey below the walls."""

    @staticmethod
    def render(storey: Dict[str, Any], to_x: Transform, to_y: Transform, scale: float) -> str:
        """Return one `<g class="outdoor">` per outdoor area."""
        out = []
        for area in storey.get("outdoor_areas") or []:
            x, y, w, h = area["rect"]
            center_x, center_y = to_x(x + w / 2), to_y(y + h / 2)
            out.append('<g class="outdoor"><rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s" stroke="%s" '
                       'stroke-width="1" stroke-dasharray="6 3"/>' % (to_x(x), to_y(y), w * scale, h * scale, FILL, OUTLINE))
            out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="15" font-weight="bold" fill="%s">%s</text>'
                       % (center_x, center_y - 4, OUTLINE, HtmlTools.escape(area.get("name") or area["id"])))
            out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="13" fill="%s">%s m²</text></g>'
                       % (center_x, center_y + 14, OUTLINE, GermanFormat.decimal(area["area"], 2)))
        return "".join(out)
