"""The foundation slab: reads its definition and builds its layers on a polygon."""
import logging
from typing import Any, Dict, List, Optional

from ..geometry.polygon import Polygon
from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from .assembly_info import AssemblyInfo

logger = logging.getLogger(__name__)


class FoundationBuilder:
    """Turns `house.foundation` into `model["foundation_spec"]` and `model["foundation"]`."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the loaded model; receives foundation_spec and foundation.
            issues: receives foundation errors and warnings.
        """
        self._model = model
        self._issues = issues

    def read_spec(self) -> None:
        """Check the foundation definition and store the spec (None if it cannot be built).

        The polygon of a `follow: outline` foundation is only known after the ground storey is
        computed, so the spec keeps `poly` None and `follow` True for that case.
        """
        self._model["foundation"] = None
        self._model["foundation_spec"] = None
        house = self._model["house"]
        foundation = house.get("foundation") if isinstance(house, dict) else None
        if not isinstance(foundation, dict):
            return
        assembly_ref = foundation.get("assembly")
        assembly = self._model["elements"].get(assembly_ref)
        if assembly is None:
            self._issues.error("house.foundation", "unbekannt: %s" % assembly_ref)
        elif assembly.get("category") != "base_slab":
            self._issues.error("house.foundation", "%s ist keine Bodenplatte (base_slab)" % assembly_ref)
        info = AssemblyInfo.of(self._model, assembly_ref) if assembly else None
        if "plinth" in foundation:
            self._issues.warning("house.foundation.plinth", "Sockel noch nicht unterstützt")
        polygon = self._rect_polygon(foundation)
        cutouts = self._cutouts(foundation)
        if info:
            self._model["foundation_spec"] = {
                "assembly": assembly_ref, "name": assembly.get("name"), "info": info,
                "top": float(foundation.get("top", 0.0)), "poly": polygon, "cutouts": cutouts,
                "follow": foundation.get("follow") == "outline", "overhang": float(foundation.get("overhang", 0) or 0)}

    def _cutouts(self, foundation: Dict[str, Any]) -> List[List[tuple]]:
        # holes through the slab (e.g. a basement stair); invalid rects are reported and ignored
        result = []
        for index, rect in enumerate(foundation.get("cutouts") or []):
            if not (isinstance(rect, list) and len(rect) == 4 and all(JsonValues.is_number(v) for v in rect)
                    and rect[2] > 0 and rect[3] > 0):
                self._issues.error("house.foundation.cutouts.%d" % index, "Aussparung ungültig")
                continue
            x, y, w, h = map(float, rect)
            result.append([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
        return result

    def _rect_polygon(self, foundation: Dict[str, Any]) -> Optional[List[tuple]]:
        rect = foundation.get("rect")
        if isinstance(rect, list) and len(rect) == 4 and all(JsonValues.is_number(v) for v in rect):
            x, y, w, h = map(float, rect)
            return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        if foundation.get("follow") != "outline":
            self._issues.error("house.foundation", "rect oder follow: outline fehlt")
        return None

    def build(self, polygon: List[Any]) -> None:
        """Build `model["foundation"]` on the polygon; layers run downwards from the top."""
        spec = self._model["foundation_spec"]
        polygon = Polygon.counter_clockwise([tuple(p) for p in polygon])
        cutouts = [Polygon.counter_clockwise(c) for c in spec.get("cutouts") or []]
        # a cutout must lie inside the slab; the part outside is not subtracted
        area = abs(Polygon.signed_area(polygon)) - sum(abs(Polygon.signed_area(Polygon.clip(polygon, c)))
                                                        for c in cutouts)
        top = spec["top"]
        layers = []
        for layer in spec["info"]["layers"]:
            material = self._model["elements"].get(layer["material"], {})
            layers.append({"material": layer["material"], "z0": top - layer["offset"] - layer["thickness"],
                           "z1": top - layer["offset"], "thickness": layer["thickness"],
                           "volume": area * layer["thickness"],
                           "color": (material.get("appearance") or {}).get("color")})
        xs, ys = [p[0] for p in polygon], [p[1] for p in polygon]
        foundation = {
            "assembly": spec["assembly"], "name": spec["name"], "polygon": [list(p) for p in polygon], "area": area,
            "rect": [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)], "top": top,
            "layers": layers, "thickness": spec["info"]["thickness"]}
        if cutouts:
            foundation["cutouts"] = [[list(p) for p in c] for c in cutouts]
        self._model["foundation"] = foundation
        logger.debug("foundation built, area %.3f m²", area)
