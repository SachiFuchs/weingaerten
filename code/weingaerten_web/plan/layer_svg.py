"""Layer polygons of the walls as SVG (plan section and corner detail)."""
import logging
from typing import Any, Callable, Dict, Optional

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

Transform = Callable[[float], float]
escape = HtmlTools.escape


class LayerSvg:
    """Draws every wall layer of the first storey with material colour, hatch and tooltip data."""

    @staticmethod
    def render(house: Dict[str, Any], to_x: Transform, to_y: Transform, css_class: str,
               cut: Optional[float] = None) -> str:
        """Return the SVG polygons.

        Args:
            house: the HOUSE answer.
            to_x, to_y: plan → SVG coordinate transforms.
            css_class: class of the polygons (`layer` or `layer-d`).
            cut: absolute section height; then only the layer pieces cut at that height are drawn,
                so openings appear as gaps. None draws the full layer footprints.
        """
        out = []
        materials = house.get("materials", {})
        assemblies = house.get("assemblies", {})
        storey = (house.get("storeys") or [{}])[0]
        for wall in storey.get("walls", []):
            for i, layer in enumerate(wall["layers"]):
                material = materials.get(layer["material"], {})
                appearance = material.get("appearance") or {}
                if cut is None:
                    polygons = [layer["footprint"]]
                else:
                    polygons = [piece["footprint"] for piece in layer.get("pieces", [])
                                if piece["z0"] - 1e-6 <= cut <= piece["z1"] + 1e-6]
                for footprint in polygons:
                    points = " ".join("%.2f,%.2f" % (to_x(p[0]), to_y(p[1])) for p in footprint)
                    out.append('<polygon class="%s" points="%s" fill="%s" stroke="#555" stroke-width="0.4" data-wall="%s" '
                               'data-wid="%s" data-storey="%s" '
                               'data-asm="%s" data-layer="%d/%d" data-material="%s" data-thickness="%s" data-color="%s"/>' % (
                                   css_class, points, escape(appearance.get("color", "#ccc")), escape(wall.get("name") or wall["id"]),
                                   escape(wall["id"]), escape(storey.get("id", "")),
                                   escape((assemblies.get(wall["assembly"]) or {}).get("name", "")), i + 1, len(wall["layers"]),
                                   escape(material.get("name", layer["material"])),
                                   escape(GermanFormat.centimetres(layer["thickness"])), escape(appearance.get("color", "#ccc"))))
                    hatch = appearance.get("hatch", "none")
                    if hatch and hatch != "none":
                        out.append('<polygon class="hatch" points="%s" fill="url(#h-%s)" pointer-events="none"/>'
                                   % (points, escape(hatch)))
        return "".join(out)
