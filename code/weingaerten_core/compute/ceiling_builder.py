"""Ceilings of a storey: layers hanging below the joists and the joists distributed over the outline."""
import logging
from typing import Any, Dict, List, Optional

from ..geometry.ortho_polygon import OrthoPolygon
from ..geometry.polygon import Polygon
from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from .assembly_info import AssemblyInfo

logger = logging.getLogger(__name__)


class CeilingBuilder:
    """Builds the `ceilings` answer of a storey."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog, shaft_rects: List[List[float]]) -> None:
        """Args:
            model: the loaded model (assemblies, materials).
            issues: receives ceiling errors and warnings.
            shaft_rects: rects of the shafts that open the ceilings of this storey (`ShaftBuilder`).
        """
        self._model = model
        self._issues = issues
        self._shaft_rects = shaft_rects

    def build(self, storey_ref: str, storey: Dict[str, Any], z0: float, height: float,
              ring: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return the computed ceilings.

        Args:
            storey_ref: storey reference.
            storey: the storey JSON.
            z0: storey elevation.
            height: storey height (default ceiling level).
            ring: largest outline ring (its inner polygon is the default ceiling outline), or None.
        """
        result = []
        for ceiling in storey.get("ceilings") or []:
            if not isinstance(ceiling, dict):
                continue
            built = self._ceiling(storey_ref, ceiling, z0, height, ring)
            if built is not None:
                result.append(built)
        return result

    def _ceiling(self, storey_ref: str, ceiling: Dict[str, Any], z0: float, height: float,
                 ring: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        where = "%s.%s" % (storey_ref, ceiling.get("id"))
        assembly_ref = ceiling.get("assembly")
        assembly = self._model["elements"].get(assembly_ref)
        if assembly is None:
            self._issues.error(where, "unbekannt: %s" % assembly_ref)
            return None
        if assembly.get("category") != "slab":
            self._issues.error(where, "%s ist keine Decke (slab)" % assembly_ref)
            return None
        info = AssemblyInfo.of(self._model, assembly_ref)
        if info is None:
            return None
        outline = ceiling.get("outline", "storey")
        if outline == "storey" or outline is None:
            if not ring:
                self._issues.warning(where, "Decke nicht berechnet – Umriss des Geschosses nicht geschlossen")
                return None
            polygon = [tuple(p) for p in ring["inner"]]
        else:
            polygon = [tuple(map(float, p)) for p in outline]
        polygon = Polygon.counter_clockwise(polygon)
        # a shaft opens the ceiling: its layers lose the cut area, the joists stay (warning by the shaft)
        shaft_area = OrthoPolygon.polygon_overlap(polygon, self._shaft_rects)
        area = abs(Polygon.signed_area(polygon)) - shaft_area
        # the ceiling level is the top of the assembly and the underside of the joists
        level = z0 + float(ceiling["z"] if JsonValues.is_number(ceiling.get("z")) else height)
        return {"id": ceiling.get("id"), "name": ceiling.get("name"), "assembly": assembly_ref,
                "polygon": [list(p) for p in polygon], "area": area, "shaft_area": shaft_area,
                "z_bottom": level - info["thickness"],
                "z_top": level, "thickness": info["thickness"],
                "layers": self._layers(assembly, info, level, area),
                "joists": self._joists(where, ceiling.get("joists"), polygon, level)}

    def _layers(self, assembly: Dict[str, Any], info: Dict[str, Any], level: float, area: float) -> List[Dict[str, Any]]:
        layers = []
        for layer in info["layers"]:
            material = self._model["elements"].get(layer["material"], {})
            source = assembly["layers"][layer["index"]]
            layers.append({"index": layer["index"], "material": layer["material"],
                           "z0": level - layer["offset"] - layer["thickness"], "z1": level - layer["offset"],
                           "thickness": layer["thickness"], "volume": area * layer["thickness"],
                           "direction": source.get("direction"),
                           "color": (material.get("appearance") or {}).get("color")})
        return layers

    def _joists(self, where: str, joists: Any, polygon: List[tuple], level: float) -> Optional[Dict[str, Any]]:
        if not isinstance(joists, dict):
            return None
        if joists.get("material") not in self._model["elements"]:
            self._issues.error(where + ".joists", "unbekannt: %s" % joists.get("material"))
            return None
        if not all(JsonValues.is_number(joists.get(k)) and joists[k] > 0 for k in ("width", "height", "spacing")):
            return None
        width, beam_height, spacing = float(joists["width"]), float(joists["height"]), float(joists["spacing"])
        west_east = joists.get("direction") == "west_east"
        xs, ys = [p[0] for p in polygon], [p[1] for p in polygon]
        low, high = (min(ys), max(ys)) if west_east else (min(xs), max(xs))
        span = high - low
        count = max(1, int(round(span / spacing)))
        beams = []
        for i in range(count):
            center = low + (i + 0.5) * span / count
            a0, a1 = center - width / 2, center + width / 2
            strip = ([(min(xs), a0), (max(xs), a0), (max(xs), a1), (min(xs), a1)] if west_east
                     else [(a0, min(ys)), (a1, min(ys)), (a1, max(ys)), (a0, max(ys))])
            clipped = Polygon.clip(polygon, Polygon.counter_clockwise(strip))
            beam_area = abs(Polygon.signed_area(clipped)) if len(clipped) >= 3 else 0.0
            if beam_area < 1e-9:
                continue
            beams.append({"polygon": [list(p) for p in clipped], "center": center, "length": beam_area / width,
                          "volume": beam_area * beam_height})
        return {"material": joists["material"], "width": width, "height": beam_height, "spacing": spacing,
                "spacing_actual": span / count, "direction": joists.get("direction"),
                "estimated": bool(joists.get("estimated")), "z0": level, "z1": level + beam_height,
                "count": len(beams), "length": sum(b["length"] for b in beams),
                "volume": sum(b["volume"] for b in beams), "beams": beams}
