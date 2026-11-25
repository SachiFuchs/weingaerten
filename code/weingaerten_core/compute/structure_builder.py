"""Structure of a storey (Tragwerk): beams (Unterzüge) and posts (Stützen) outside of walls and ceilings."""
import logging
import math
from typing import Any, Dict, List, Optional

from ..geometry.polygon import Polygon
from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from ..validation.class_validator import ClassValidator

logger = logging.getLogger(__name__)

STRUCTURE_KINDS = ("beam", "post")
# a beam needs a real line; shorter ones are treated as start = end
MIN_LENGTH = 1e-6


class StructureBuilder:
    """Builds the `structure` answer of a storey; invalid elements are reported and skipped."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the loaded model (materials).
            issues: receives the structure errors.
        """
        self._model = model
        self._issues = issues

    def build(self, storey_ref: str, storey: Dict[str, Any], z0: float, height: float) -> List[Dict[str, Any]]:
        """Return the computed structure elements in file order.

        Args:
            storey_ref: storey reference.
            storey: the storey JSON.
            z0: storey elevation.
            height: storey height (default top of beams and posts).
        """
        items = [item for item in (storey.get("structure") or []) if isinstance(item, dict)]
        ids = [item.get("id") for item in items]
        for duplicate in sorted(set(i for i in ids if ids.count(i) > 1), key=str):
            self._issues.error("%s.%s" % (storey_ref, duplicate), "doppelte Tragwerk-id")
        result = []
        for item in items:
            built = self._element("%s.%s" % (storey_ref, item.get("id")), item, z0, height)
            if built is not None:
                result.append(built)
        return result

    def _element(self, where: str, item: Dict[str, Any], z0: float, height: float) -> Optional[Dict[str, Any]]:
        kind = item.get("kind")
        if kind not in STRUCTURE_KINDS:
            self._issues.error(where, "Tragwerk-Art unbekannt: %s" % kind)
            return None
        material_ref = item.get("material")
        if not ClassValidator.is_material(self._model, material_ref):
            self._issues.error(where, "unbekannt: %s" % material_ref)
            return None
        shape = self._beam(item, height) if kind == "beam" else self._post(item, height)
        if shape is None:
            self._issues.error(where, "Maße ungültig")
            return None
        footprint, bottom, top, length = shape
        material = self._model["elements"].get(material_ref, {})
        area = abs(Polygon.signed_area(footprint))
        return {"id": item.get("id"), "name": item.get("name"), "kind": kind, "material": material_ref,
                "footprint": [list(p) for p in footprint], "z0": z0 + bottom, "z1": z0 + top,
                "width": float(item["width"]), "height": top - bottom, "length": length,
                "volume": area * (top - bottom), "color": (material.get("appearance") or {}).get("color")}

    @staticmethod
    def _positive(item: Dict[str, Any], keys: tuple) -> bool:
        return all(JsonValues.is_number(item.get(key)) and item[key] > 0 for key in keys)

    @staticmethod
    def _point(value: Any) -> Optional[tuple]:
        if isinstance(value, list) and len(value) == 2 and all(JsonValues.is_number(v) for v in value):
            return (float(value[0]), float(value[1]))
        return None

    def _beam(self, item: Dict[str, Any], height: float) -> Optional[tuple]:
        # a box of `width` centred on the line start -> end, `height` below its top edge
        start, end = self._point(item.get("start")), self._point(item.get("end"))
        if not self._positive(item, ("width", "height")) or start is None or end is None:
            return None
        length = math.hypot(end[0] - start[0], end[1] - start[1])
        if length < MIN_LENGTH:
            return None
        top = float(item["z_top"]) if JsonValues.is_number(item.get("z_top")) else height
        half = float(item["width"]) / 2.0
        nx, ny = -(end[1] - start[1]) / length * half, (end[0] - start[0]) / length * half
        footprint = [(start[0] - nx, start[1] - ny), (end[0] - nx, end[1] - ny),
                     (end[0] + nx, end[1] + ny), (start[0] + nx, start[1] + ny)]
        return Polygon.counter_clockwise(footprint), top - float(item["height"]), top, length

    def _post(self, item: Dict[str, Any], height: float) -> Optional[tuple]:
        # a box of width (x) × depth (y) centred on the position, from z0 to z1
        position = self._point(item.get("position"))
        if not self._positive(item, ("width", "depth")) or position is None:
            return None
        bottom = float(item["z0"]) if JsonValues.is_number(item.get("z0")) else 0.0
        top = float(item["z1"]) if JsonValues.is_number(item.get("z1")) else height
        if top <= bottom:
            return None
        half_x, half_y = float(item["width"]) / 2.0, float(item["depth"]) / 2.0
        x, y = position
        footprint = [(x - half_x, y - half_y), (x + half_x, y - half_y), (x + half_x, y + half_y),
                     (x - half_x, y + half_y)]
        return footprint, bottom, top, top - bottom
