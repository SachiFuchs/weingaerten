"""Electrical cables (in conduit) and their boxes in the plan of one storey."""
import logging
from typing import Any, Callable, Dict, Optional

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

Transform = Callable[[float], float]
escape = HtmlTools.escape
decimal = GermanFormat.decimal
BELOW = 1.2   # cables up to 1.2 m below the floor belong to the storey plan (dashed)


class ElectricalSvg:
    """Draws the cable runs near a storey (dash-dot, dashed below its floor) and their boxes."""

    def __init__(self, to_x: Transform, to_y: Transform, scale: float) -> None:
        """Args:
            to_x, to_y: plan → SVG transforms.
            scale: px per metre (line width).
        """
        self._to_x, self._to_y, self._scale = to_x, to_y, scale

    def render(self, electrical: Optional[Dict[str, Any]], storey: Dict[str, Any]) -> str:
        """Return a `<g class="electrical">` or "" without cables near the storey."""
        if not electrical:
            return ""
        low = storey["elevation"] - BELOW
        high = storey["elevation"] + storey["height"]
        parts = []
        for run in electrical["runs"]:
            for segment in run["segments"]:
                z0, z1 = sorted((segment["from"][2], segment["to"][2]))
                if z1 >= low and z0 <= high:
                    parts.append(self._segment(run, segment, z1 < storey["elevation"]))
        for terminal in electrical["terminals"]:
            if terminal.get("storey") == storey["ref"] and terminal.get("position"):
                parts.append(self._terminal(terminal))
        return '<g class="electrical">%s</g>' % "".join(parts) if parts else ""

    def _segment(self, run: Dict[str, Any], segment: Dict[str, Any], below: bool) -> str:
        a, b = segment["from"], segment["to"]
        title = "%s – %s im %s, z %s bis %s m%s" % (run["name"], run["label"], run["line"], decimal(a[2], 2),
                                                   decimal(b[2], 2), " (unter Boden)" if below else "")
        if segment["plan_length"] < 0.001:
            return ('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s"><title>%s (senkrecht)</title></circle>'
                    % (self._to_x(a[0]), self._to_y(a[1]), max(2.0, run["outer_diameter"] * self._scale / 2),
                       run["color"], escape(title)))
        return ('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%.2f" '
                'stroke-dasharray="%s"><title>%s</title></line>'
                % (self._to_x(a[0]), self._to_y(a[1]), self._to_x(b[0]), self._to_y(b[1]), run["color"],
                   max(2.0, run["outer_diameter"] * self._scale), "4 3" if below else "8 2 2 2", escape(title)))

    def _terminal(self, terminal: Dict[str, Any]) -> str:
        x, y = self._to_x(terminal["position"][0]), self._to_y(terminal["position"][1])
        return ('<rect x="%.2f" y="%.2f" width="7" height="7" fill="#FFFFFF" stroke="#E53935" stroke-width="1.5">'
                '<title>%s – %s</title></rect>' % (x - 3.5, y - 3.5, escape(terminal["name"]),
                                                  escape(terminal["component_name"] or "")))
