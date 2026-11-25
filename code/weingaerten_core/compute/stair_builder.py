"""Stairs of a storey: a straight run with an optional quarter turn of winders (Wangentreppe mit Setzstufen, or a
solid concrete stair of block steps), from the storey floor up to the floor of `to_storey`."""
import logging
import math
from typing import Any, Dict, List, Optional

from ..geometry.polygon import Polygon
from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from ..validation.class_validator import ClassValidator
from .stair_geometry import DIRECTIONS, StairGeometry

logger = logging.getLogger(__name__)

RISER_COLOR = "#F4F4F0"
MIN_GOING, COMFORT_GOING = 0.10, 0.21
NAMES = {"tread": "Trittstufe", "riser": "Setzstufe", "stringer": "Wange", "step": "Stufe"}
CONSTRUCTION_KINDS = {"stringer": ("tread", "riser", "stringer"), "solid": ("step",)}


class StairBuilder:
    """Builds `stairs` of a storey; parts are prisms (stringers between a bottom and a top plane)."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the loaded model (materials, storeys for the target height).
            issues: receives stair errors and warnings.
        """
        self._model = model
        self._issues = issues

    def build(self, storey_ref: str, storey: Dict[str, Any], z0: float) -> List[Dict[str, Any]]:
        """Return the computed stairs (invalid ones are reported and skipped)."""
        result = []
        for spec in storey.get("stairs") or []:
            if isinstance(spec, dict):
                stair = self._stair("%s.%s" % (storey_ref, spec.get("id")), spec, z0)
                if stair is not None:
                    result.append(stair)
        return result

    def _height(self, where: str, spec: Dict[str, Any], z0: float) -> Optional[float]:
        target = self._model["storeys"].get(spec.get("to_storey"))
        if not isinstance(target, dict):
            self._issues.error(where, "unbekannt: %s" % spec.get("to_storey"))
            return None
        height = float(target.get("elevation", 0.0) or 0.0) - z0
        if height <= 0:
            self._issues.error(where, "Zielgeschoss liegt nicht höher")
            return None
        return height

    def _checked(self, where: str, spec: Dict[str, Any]) -> bool:
        if not ClassValidator.is_material(self._model, spec.get("material")):
            self._issues.error(where, "unbekannt: %s" % spec.get("material"))
            return False
        run, turn = spec.get("run") or {}, spec.get("turn") or {"side": "left", "steps": 0}
        rect = run.get("rect")
        construction = spec.get("construction", "stringer")
        numbers = []
        if construction == "stringer":
            numbers = [spec.get(k) for k in ("tread_thickness", "riser_thickness")] + \
                      [(spec.get("stringer") or {}).get(k) for k in ("width", "height")]
        valid = (construction in CONSTRUCTION_KINDS and isinstance(rect, list) and len(rect) == 4 and all(JsonValues.is_number(v) for v in rect)
                 and rect[2] > 0 and rect[3] > 0 and run.get("direction") in DIRECTIONS
                 and turn.get("side") in ("left", "right")
                 and all(isinstance(spec.get("risers"), int) and isinstance(n, int) for n in
                         (run.get("straight_steps"), turn.get("steps")))
                 and all(JsonValues.is_number(n) and n > 0 for n in numbers)
                 and run["straight_steps"] >= 1 and turn["steps"] >= 0
                 and spec["risers"] == run["straight_steps"] + turn["steps"] + 1)
        if not valid:
            self._issues.error(where, "Maße ungültig")
        return valid

    def _stair(self, where: str, spec: Dict[str, Any], z0: float) -> Optional[Dict[str, Any]]:
        height = self._height(where, spec, z0)
        if height is None or not self._checked(where, spec):
            return None
        run, turn = spec["run"], spec.get("turn") or {"side": "left", "steps": 0}
        geo = StairGeometry(run["rect"], run["direction"], turn["side"])
        straight, winders = run["straight_steps"], turn["steps"]
        rise = height / spec["risers"]
        straight_length = geo.length - (geo.width if winders else 0.0)
        going = straight_length / straight
        if going < MIN_GOING:
            self._issues.error(where, "Lauf zu kurz (Auftritt %.1f cm)" % (going * 100))
            return None
        if going < COMFORT_GOING:
            self._issues.warning(where, "steile Treppe (Auftritt %.1f cm)" % (going * 100))
        self._z0, self._geo, self._spec, self._rise = z0, geo, spec, rise
        construction = spec.get("construction", "stringer")
        if construction == "solid":
            parts = self._solid(straight, winders, going)
        else:
            parts = self._straight(straight, going) + self._winders(straight, winders) + \
                self._stringers(straight_length, going)
        counts = {kind: sum(1 for p in parts if p["kind"] == kind) for kind in CONSTRUCTION_KINDS[construction]}
        stair = {"id": spec.get("id"), "name": spec.get("name"), "material": spec["material"],
                 "estimated": bool(spec.get("estimated")), "note": spec.get("note"), "to_storey": spec["to_storey"],
                 "risers": spec["risers"], "rise": rise, "going": going, "height": height, "parts": parts,
                 "counts": counts, "volume": sum(p["volume"] for p in parts)}
        if construction == "solid":
            stair["construction"] = construction
        return stair

    def _solid(self, straight: int, winders: int, going: float) -> List[Dict[str, Any]]:
        # massive block steps standing on the storey floor: step i is a block of the full width up to i·rise
        width, rise = self._geo.width, self._rise
        parts = [self._part("step", i, [((i - 1) * going, 0.0), (i * going, 0.0), (i * going, width),
                                         ((i - 1) * going, width)], 0.0, i * rise) for i in range(1, straight + 1)]
        if winders:
            for k, wedge in enumerate(self._geo.winders(winders)):
                i = straight + k + 1
                parts.append(self._part("step", i, wedge, 0.0, i * rise))
        return parts

    def _part(self, kind: str, index: int, uv: List[tuple], z_bottom: float, z_top: float) -> Dict[str, Any]:
        footprint = [list(p) for p in Polygon.counter_clockwise([tuple(self._geo.plan(u, v)) for u, v in uv])]
        area = abs(Polygon.signed_area([tuple(p) for p in footprint]))
        part = {"id": "%s-%s-%d" % (self._spec.get("id"), kind, index), "kind": kind,
                "name": "%s %d" % (NAMES[kind], index), "material": self._spec["material"], "footprint": footprint,
                "z0": self._z0 + z_bottom, "z1": self._z0 + z_top, "volume": area * (z_top - z_bottom)}
        if kind == "riser":
            part["color"] = RISER_COLOR
        return part

    def _straight(self, steps: int, going: float) -> List[Dict[str, Any]]:
        # tread i covers [(i-1)·going, i·going] between the stringers, its riser stands at the front edge
        tread_t, riser_t, inset = (float(self._spec["tread_thickness"]), float(self._spec["riser_thickness"]),
                                   float(self._spec["stringer"]["width"]))
        width, rise, parts = self._geo.width, self._rise, []
        for i in range(1, steps + 1):
            u0, u1 = (i - 1) * going, i * going
            parts.append(self._part("tread", i, [(u0, inset), (u1, inset), (u1, width - inset), (u0, width - inset)],
                                    i * rise - tread_t, i * rise))
            parts.append(self._part("riser", i, [(u0, inset), (u0 + riser_t, inset), (u0 + riser_t, width - inset),
                                                 (u0, width - inset)], (i - 1) * rise, i * rise - tread_t))
        return parts

    def _winders(self, straight: int, steps: int) -> List[Dict[str, Any]]:
        # wedges around the inner corner; the riser lies along the front ray of each wedge
        if not steps:
            return []
        tread_t, riser_t = float(self._spec["tread_thickness"]), float(self._spec["riser_thickness"])
        geo, rise, parts = self._geo, self._rise, []
        for k, (wedge, angle) in enumerate(zip(geo.winders(steps), geo.winder_angles(steps))):
            i = straight + k + 1
            parts.append(self._part("tread", i, wedge, i * rise - tread_t, i * rise))
            pivot, front = wedge[0], wedge[1]
            n = (-math.sin(math.radians(angle)) * riser_t, math.cos(math.radians(angle)) * riser_t)
            parts.append(self._part("riser", i, [pivot, front, (front[0] + n[0], front[1] + n[1]),
                                                 (pivot[0] + n[0], pivot[1] + n[1])], (i - 1) * rise, i * rise - tread_t))
        return parts

    def _stringers(self, length: float, going: float) -> List[Dict[str, Any]]:
        # two sloped boards along the straight run; bottom on the floor at the start, top above the nosings
        width, sw, sh = self._geo.width, float(self._spec["stringer"]["width"]), float(self._spec["stringer"]["height"])
        slope = self._rise / going
        cos = math.cos(math.atan(slope))
        parts = []
        for index, (v0, v1) in enumerate(((0.0, sw), (width - sw, width)), start=1):
            part = self._part("stringer", index, [(0.0, v0), (length, v0), (length, v1), (0.0, v1)],
                              0.0, slope * length + sh / cos)
            part["bottom_plane"] = self._geo.plane(slope, 0.0, self._z0)
            part["top_plane"] = self._geo.plane(slope, 0.0, self._z0 + sh / cos)
            part["volume"] = sw * sh * length / cos
            parts.append(part)
        return parts
