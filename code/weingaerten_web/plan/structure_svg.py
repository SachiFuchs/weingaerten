"""Structure in the plan: posts cut by the section filled, beams above the section dashed."""
import logging
from typing import Any, Callable, Dict

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

Transform = Callable[[float], float]
KIND_NAMES = {"beam": "Unterzug", "post": "Stütze"}
escape = HtmlTools.escape


class StructureSvg:
    """Draws the `structure` elements of a storey at the section height."""

    def __init__(self, house: Dict[str, Any], to_x: Transform, to_y: Transform) -> None:
        """Args:
            house: the HOUSE answer (materials for the names and colours).
            to_x, to_y: plan → SVG transforms.
        """
        self._materials = house.get("materials", {})
        self._to_x, self._to_y = to_x, to_y

    def render(self, storey: Dict[str, Any], cut_level: float) -> str:
        """Return one `<polygon class="structure">` per element; cut_level is absolute."""
        return "".join(self._element(element, cut_level) for element in storey.get("structure") or [])

    def _element(self, element: Dict[str, Any], cut_level: float) -> str:
        material = self._materials.get(element["material"]) or {}
        points = " ".join("%.2f,%.2f" % (self._to_x(p[0]), self._to_y(p[1])) for p in element["footprint"])
        if element["z0"] - 1e-6 <= cut_level <= element["z1"] + 1e-6:
            style = 'fill="%s" stroke="#000" stroke-width="1"' % escape((material.get("appearance") or {}).get("color", "#ccc"))
        else:
            # above (or below) the section: only the dashed outline
            style = 'fill="none" stroke="#555" stroke-width="1" stroke-dasharray="5 3"'
        size = "%s × %s cm" % (GermanFormat.decimal(element["width"] * 100, 0),
                               GermanFormat.decimal(self._cross_section(element) * 100, 0))
        return ('<polygon class="structure" points="%s" %s data-kind="%s" data-name="%s" data-material="%s" '
                'data-size="%s" data-length="%s m"/>'
                % (points, style, escape(KIND_NAMES.get(element["kind"], element["kind"])),
                   escape(element.get("name") or element["id"]), escape(material.get("name") or element["material"]),
                   escape(size), escape(GermanFormat.decimal(element["length"], 2))))

    @staticmethod
    def _cross_section(element: Dict[str, Any]) -> float:
        # beam: width × height of the section; post: width (x) × depth (y) of the footprint
        if element["kind"] == "beam":
            return element["height"]
        ys = [p[1] for p in element["footprint"]]
        return max(ys) - min(ys)
