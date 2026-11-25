"""Light wells (Lichtschächte) in front of basement windows: concrete walls, a floor slab and a grating on top."""
import logging
from typing import Any, Dict, List, Optional

from ..constants import TOLERANCE
from ..geometry.polygon import Polygon
from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from ..validation.class_validator import ClassValidator

logger = logging.getLogger(__name__)

NAMES = {"floor": "Sohle", "wall": "Schachtwand", "grating": "Gitterrost"}
SIZE_KEYS = ("width", "projection", "depth", "wall_thickness")


class LightWellBuilder:
    """Builds `light_wells` of a storey from the computed walls; invalid wells are reported and skipped."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the loaded model (materials).
            issues: receives the light well errors.
        """
        self._model = model
        self._issues = issues

    def build(self, storey_ref: str, storey: Dict[str, Any], walls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return the computed light wells in file order.

        Args:
            storey_ref: storey reference.
            storey: the storey JSON.
            walls: the serialized walls of the storey (absolute coordinates, openings with `rough` and `plan`).
        """
        by_id = {wall["id"]: wall for wall in walls}
        result = []
        for spec in storey.get("light_wells") or []:
            if isinstance(spec, dict):
                well = self._well("%s.%s" % (storey_ref, spec.get("id")), spec, by_id)
                if well is not None:
                    result.append(well)
        return result

    def _opening(self, where: str, spec: Dict[str, Any], walls: Dict[str, Any]) -> Optional[tuple]:
        wall = walls.get(spec.get("wall"))
        if wall is None:
            self._issues.error(where, "unbekannt: %s" % spec.get("wall"))
            return None
        if wall["category"] != "exterior_wall":
            self._issues.error(where, "Lichtschacht nur an Außenwand")
            return None
        opening = next((o for o in wall["openings"] if o["id"] == spec.get("opening")), None)
        if opening is None:
            self._issues.error(where, "unbekannt: %s" % spec.get("opening"))
            return None
        return wall, opening

    def _checked(self, where: str, spec: Dict[str, Any]) -> bool:
        grating = spec.get("grating") or {}
        for ref in (spec.get("material"), grating.get("material")):
            if not ClassValidator.is_material(self._model, ref):
                self._issues.error(where, "unbekannt: %s" % ref)
                return False
        numbers = [spec.get(k) for k in SIZE_KEYS] + [grating.get("thickness")]
        if not (all(JsonValues.is_number(n) and n > 0 for n in numbers) and JsonValues.is_number(spec.get("terrain"))):
            self._issues.error(where, "Maße ungültig")
            return False
        return True

    def _well(self, where: str, spec: Dict[str, Any], walls: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        found = self._opening(where, spec, walls)
        if found is None or not self._checked(where, spec):
            return None
        wall, opening = found
        terrain, depth = float(spec["terrain"]), float(spec["depth"])
        z_floor = terrain - depth
        # the well floor must not lie above the window sill, else the window is buried
        if z_floor > wall["z0"] + opening["rough"]["zb"] + TOLERANCE:
            self._issues.error(where, "Lichtschacht zu flach")
            return None
        parts = self._parts(spec, wall, opening, z_floor)
        concrete = sum(p["volume"] for p in parts if p["kind"] != "grating")
        width, projection = float(spec["width"]), float(spec["projection"])
        return {"id": spec.get("id"), "name": spec.get("name"), "wall": wall["id"], "opening": opening["id"],
                "material": spec["material"], "grating_material": spec["grating"]["material"],
                "estimated": bool(spec.get("estimated")), "note": spec.get("note"), "width": width,
                "projection": projection, "depth": depth, "terrain": terrain, "z_floor": z_floor,
                "area": width * projection, "parts": parts, "volume": concrete,
                "grating_area": width * projection}

    def _parts(self, spec: Dict[str, Any], wall: Dict[str, Any], opening: Dict[str, Any],
               z_floor: float) -> List[Dict[str, Any]]:
        # local frame: a along the wall (0 = centre of the opening), b away from the outside face
        outside = opening["plan"]["outside"]
        centre = ((outside[0][0] + outside[1][0]) / 2.0, (outside[0][1] + outside[1][1]) / 2.0)
        d = (outside[1][0] - outside[0][0], outside[1][1] - outside[0][1])
        length = (d[0] ** 2 + d[1] ** 2) ** 0.5
        self._frame = centre, (d[0] / length, d[1] / length), (-wall["normal_in"][0], -wall["normal_in"][1])
        self._spec = spec
        half, out, t = float(spec["width"]) / 2.0, float(spec["projection"]), float(spec["wall_thickness"])
        terrain, grating_t = float(spec["terrain"]), float(spec["grating"]["thickness"])
        material, grating = spec["material"], spec["grating"]["material"]
        return [self._part("floor", 1, material, (-half - t, half + t), (0.0, out + t), z_floor - t, z_floor),
                self._part("wall", 1, material, (-half - t, -half), (0.0, out), z_floor, terrain),
                self._part("wall", 2, material, (-half - t, half + t), (out, out + t), z_floor, terrain),
                self._part("wall", 3, material, (half, half + t), (0.0, out), z_floor, terrain),
                self._part("grating", 1, grating, (-half, half), (0.0, out), terrain - grating_t, terrain)]

    def _part(self, kind: str, index: int, material: str, a: tuple, b: tuple, z0: float,
              z1: float) -> Dict[str, Any]:
        centre, along, away = self._frame
        corners = [(a[0], b[0]), (a[1], b[0]), (a[1], b[1]), (a[0], b[1])]
        footprint = Polygon.counter_clockwise([(centre[0] + u * along[0] + v * away[0],
                                                centre[1] + u * along[1] + v * away[1]) for u, v in corners])
        area = abs(Polygon.signed_area(footprint))
        element = self._model["elements"].get(material, {})
        return {"id": "%s-%s-%d" % (self._spec.get("id"), kind, index), "kind": kind,
                "name": "%s %d" % (NAMES[kind], index) if kind == "wall" else NAMES[kind], "material": material,
                "footprint": [list(p) for p in footprint], "z0": z0, "z1": z1, "volume": area * (z1 - z0),
                "color": (element.get("appearance") or {}).get("color")}
