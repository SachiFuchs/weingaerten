"""Drinking water runs, crossing loops and wall plates in the plan of one storey."""
import logging
from typing import Any, Callable, Dict, Optional

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

Transform = Callable[[float], float]
escape = HtmlTools.escape
decimal = GermanFormat.decimal
BELOW = 1.2   # pipes up to 1.2 m below the floor belong to the storey plan (dashed)


class WaterSupplySvg:
    """Draws the drinking water pipes near a storey (dashed below its floor) and their wall plates."""

    def __init__(self, to_x: Transform, to_y: Transform, scale: float) -> None:
        """Args:
            to_x, to_y: plan → SVG transforms.
            scale: px per metre (pipe width).
        """
        self._to_x, self._to_y, self._scale = to_x, to_y, scale

    def render(self, water_supply: Optional[Dict[str, Any]], storey: Dict[str, Any]) -> str:
        """Return a `<g class="watersupply">` or "" without drinking water near the storey."""
        if not water_supply:
            return ""
        low = storey["elevation"] - BELOW
        high = storey["elevation"] + storey["height"]
        parts = []
        for run in water_supply["runs"]:
            for segment in run["segments"]:
                z0, z1 = sorted((segment["from"][2], segment["to"][2]))
                if z1 >= low and z0 <= high:
                    parts.append(self._segment(run, segment, z1 < storey["elevation"]))
        for terminal in water_supply["terminals"]:
            if terminal.get("storey") == storey["ref"] and terminal.get("position"):
                parts.append(self._terminal(terminal))
        return '<g class="watersupply">%s</g>' % "".join(parts) if parts else ""

    def _segment(self, run: Dict[str, Any], segment: Dict[str, Any], below: bool) -> str:
        a, b = segment["from"], segment["to"]
        title = "%s – %s PPR DN %s, z %s bis %s m%s" % (run["name"], run["medium_name"], run["dn"],
                                                       decimal(a[2], 2), decimal(b[2], 2), " (unter Boden)" if below else "")
        if segment["plan_length"] < 0.001:
            return ('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s"><title>%s (senkrecht)</title></circle>'
                    % (self._to_x(a[0]), self._to_y(a[1]), max(2.0, run["outer_diameter"] * self._scale / 2), run["color"],
                       escape(title)))
        return ('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%.2f" stroke-linecap="round"%s>'
                '<title>%s</title></line>'
                % (self._to_x(a[0]), self._to_y(a[1]), self._to_x(b[0]), self._to_y(b[1]), run["color"],
                   max(2.0, run["outer_diameter"] * self._scale), ' stroke-dasharray="4 3"' if below else "",
                   escape(title)))

    def _terminal(self, terminal: Dict[str, Any]) -> str:
        x, y = self._to_x(terminal["position"][0]), self._to_y(terminal["position"][1])
        return ('<rect x="%.2f" y="%.2f" width="6" height="6" fill="#3E8E41" stroke="#FFFFFF" stroke-width="1">'
                '<title>%s</title></rect>' % (x - 3, y - 3, escape(terminal["name"])))
