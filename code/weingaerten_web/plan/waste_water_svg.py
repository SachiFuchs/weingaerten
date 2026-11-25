"""Waste water runs and penetrations in the plan of one storey."""
import logging
from typing import Any, Callable, Dict, Optional

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

Transform = Callable[[float], float]
escape = HtmlTools.escape
decimal = GermanFormat.decimal
BELOW = 1.2   # pipes up to 1.2 m below the floor (ground, basement ceiling) belong to the storey plan
PEN_COLOR = "#E5332A"


class WasteWaterSvg:
    """Draws the waste water pipes near a storey (dashed below its floor) and its penetrations."""

    def __init__(self, to_x: Transform, to_y: Transform, scale: float) -> None:
        """Args:
            to_x, to_y: plan → SVG transforms.
            scale: px per metre (pipe width).
        """
        self._to_x, self._to_y, self._scale = to_x, to_y, scale

    def render(self, waste_water: Optional[Dict[str, Any]], storey: Dict[str, Any], is_ground: bool) -> str:
        """Return a `<g class="wastewater">` or "" without waste water."""
        if not waste_water:
            return ""
        low = storey["elevation"] - BELOW
        high = storey["elevation"] + storey["height"]
        parts = []
        for run in waste_water["runs"]:
            for segment in run["segments"]:
                z0, z1 = sorted((segment["from"][2], segment["to"][2]))
                if z1 >= low and z0 <= high and segment["plan_length"] > 0.001:
                    parts.append(self._segment(run, segment, z1 < storey["elevation"]))
        for pen in waste_water["penetrations"]:
            if pen["kind"] == "through" and (pen["storey"] == storey["id"] or (pen["storey"] is None and is_ground)):
                parts.append(self._penetration(pen))
        for terminal in waste_water["terminals"]:
            if terminal.get("storey") == storey["ref"] and terminal.get("position"):
                parts.append(self._terminal(terminal))
        return '<g class="wastewater">%s</g>' % "".join(parts) if parts else ""

    def _segment(self, run: Dict[str, Any], segment: Dict[str, Any], below: bool) -> str:
        a, b = segment["from"], segment["to"]
        slope = "senkrecht" if segment["slope"] is None else "%s %%" % decimal(segment["slope"] * 100, 1)
        return ('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%.2f" stroke-linecap="round"%s>'
                '<title>%s – %s DN %s, Gefälle %s%s</title></line>'
                % (self._to_x(a[0]), self._to_y(a[1]), self._to_x(b[0]), self._to_y(b[1]), run["color"],
                   max(2.0, run["outer_diameter"] * self._scale), ' stroke-dasharray="6 4" opacity="0.8"' if below else "",
                   escape(run["name"]), run["line"].upper(), run["dn"], slope, " (unter Boden)" if below else ""))

    def _penetration(self, pen: Dict[str, Any]) -> str:
        x, y = self._to_x(pen["position"][0]), self._to_y(pen["position"][1])
        radius = max(4.0, pen["core_drill"] / 2 * self._scale)
        return ('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="none" stroke="%s" stroke-width="1.6">'
                '<title>Durchbruch %s: Kernbohrung Ø %s cm, %s</title></circle>'
                % (x, y, radius, PEN_COLOR, escape(pen["element_name"]), decimal(pen["core_drill"] * 100, 0),
                   escape(pen["run_name"])))

    def _terminal(self, terminal: Dict[str, Any]) -> str:
        x, y = self._to_x(terminal["position"][0]), self._to_y(terminal["position"][1])
        return ('<rect x="%.2f" y="%.2f" width="8" height="8" fill="#2B6CB0"><title>%s</title></rect>'
                % (x - 4, y - 4, escape(terminal["name"])))
