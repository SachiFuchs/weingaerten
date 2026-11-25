"""Roof structure of a storey (Dachstuhl, Pfettendach): rafters, middle purlins, foot purlins and collar beams,
generated from parameters and the storey roof."""
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from ..geometry.polygon import Polygon
from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from ..validation.class_validator import ClassValidator
from .roof_profile import RoofProfile
from .wall_data import WallData

logger = logging.getLogger(__name__)

MEMBER_GROUPS = (("rafters", ("width", "height", "spacing")), ("purlins", ("width", "height", "z_top")),
                 ("foot_purlins", ("width", "height")), ("collars", ("width", "height", "z")))
SIDES = ("west", "east")
SIDE_NAMES = {"west": "West", "east": "Ost"}
SAME = 1e-6
KNEE_WALL_TOLERANCE = 0.05


class RoofStructureBuilder:
    """Builds `roof_structure` of a storey; members are boxes between a bottom and a top plane."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the loaded model (materials).
            issues: receives the roof structure errors.
        """
        self._model = model
        self._issues = issues

    def build(self, storey_ref: str, storey: Dict[str, Any], z0: float, roof: Optional[RoofProfile],
              walls: List[WallData]) -> Optional[Dict[str, Any]]:
        """Return `{material, estimated, note, members, counts}` or None (no or invalid `roof_structure`).

        Args:
            storey_ref: storey reference.
            storey: the storey JSON.
            z0: storey elevation.
            roof: the storey roof (required).
            walls: the storey walls (knee wall thickness for the foot purlins).
        """
        spec = storey.get("roof_structure")
        if not isinstance(spec, dict):
            return None
        where = "%s.roof_structure" % storey_ref
        slopes = self._checked(where, spec, roof)
        if slopes is None:
            return None
        self._roof, self._z0, self._material = roof, z0, spec["material"]
        members: List[Dict[str, Any]] = []
        rafters = {side: [] for side in SIDES}
        for slope in slopes:
            for y in self._positions(slope["range"], spec["rafters"]["spacing"]):
                rafters[slope["side"]].append((y, slope["end"]))
                members.append(self._rafter(slope, y, spec["rafters"], len(members)))
        for side in SIDES:
            ranges = [s["range"] for s in slopes if s["side"] == side]
            if ranges:
                along = (min(r[0] for r in ranges), max(r[1] for r in ranges))
                members.append(self._purlin(side, along, spec["purlins"]))
                members.append(self._foot_purlin(side, along, spec["foot_purlins"], walls))
        members += self._collars(rafters, spec["collars"], spec["rafters"]["width"])
        for index, ridge_purlin in enumerate(spec.get("ridge_purlins") or []):
            members.append(self._ridge_purlin(index, ridge_purlin))
        counts = {kind: sum(1 for m in members if m["kind"] == kind)
                  for kind in ("rafter", "purlin", "foot_purlin", "collar", "ridge_purlin")}
        return {"material": self._material, "estimated": bool(spec.get("estimated")), "note": spec.get("note"),
                "members": members, "counts": counts}

    def _checked(self, where: str, spec: Dict[str, Any], roof: Optional[RoofProfile]) -> Optional[List[Dict[str, Any]]]:
        # returns the slopes with their end (default ridge) or None after reporting the first problem
        if roof is None:
            self._issues.error(where, "Dachstuhl ohne Dach")
            return None
        if not ClassValidator.is_material(self._model, spec.get("material")):
            self._issues.error(where, "unbekannt: %s" % spec.get("material"))
            return None
        for group, keys in MEMBER_GROUPS:
            values = spec.get(group)
            if not isinstance(values, dict) or not all(JsonValues.is_number(values.get(k)) and values[k] > 0
                                                       for k in keys):
                self._issues.error(where, "Maße ungültig")
                return None
        slopes = []
        for slope in spec.get("slopes") or []:
            parsed = self._slope(slope, roof)
            if parsed is None:
                self._issues.error(where, "Dachfläche ungültig")
                return None
            slopes.append(parsed)
        for ridge_purlin in spec.get("ridge_purlins") or []:
            if not self._ridge_purlin_valid(ridge_purlin):
                self._issues.error(where, "Firstpfette ungültig")
                return None
        return slopes

    @staticmethod
    def _ridge_purlin_valid(spec: Any) -> bool:
        span = spec.get("range") if isinstance(spec, dict) else None
        return (isinstance(span, list) and len(span) == 2 and all(JsonValues.is_number(v) for v in span)
                and span[0] < span[1] and all(JsonValues.is_number(spec.get(k)) and spec[k] > 0
                                              for k in ("width", "height")))

    @staticmethod
    def _slope(slope: Any, roof: RoofProfile) -> Optional[Dict[str, Any]]:
        if not isinstance(slope, dict) or slope.get("side") not in SIDES:
            return None
        span = slope.get("range")
        if not (isinstance(span, list) and len(span) == 2 and all(JsonValues.is_number(v) for v in span)
                and span[0] < span[1]):
            return None
        end = slope.get("end", roof.ridge)
        if not JsonValues.is_number(end) or not roof.eaves[0] < end < roof.eaves[1]:
            return None
        return {"id": slope.get("id") or slope["side"], "side": slope["side"], "range": (float(span[0]), float(span[1])),
                "end": float(end)}

    @staticmethod
    def _positions(span: Tuple[float, float], spacing: float) -> List[float]:
        # like the ceiling joists: n = max(1, round(length / spacing)) evenly at the centres of n bays
        length = span[1] - span[0]
        n = max(1, round(length / spacing))
        return [span[0] + (i + 0.5) * length / n for i in range(n)]

    def _point(self, across: float, along: float) -> List[float]:
        return [across, along] if self._roof.axis == 0 else [along, across]

    def _box(self, across: Tuple[float, float], along: Tuple[float, float]) -> List[List[float]]:
        a0, a1 = across
        b0, b1 = along
        corners = [self._point(a0, b0), self._point(a1, b0), self._point(a1, b1), self._point(a0, b1)]
        return [list(p) for p in Polygon.counter_clockwise([tuple(c) for c in corners])]

    def _plane(self, slope: float, at_across: float, z_at: float) -> List[float]:
        # absolute plane z = a*x + b*y + c through z_at at across = at_across, rising by `slope` per metre across
        a = [slope, 0.0] if self._roof.axis == 0 else [0.0, slope]
        return [a[0], a[1], self._z0 + z_at - slope * at_across]

    def _member(self, member_id: str, kind: str, name: str, footprint: List[List[float]], bottom: List[float],
                top: List[float], size: Dict[str, Any], length: float) -> Dict[str, Any]:
        z_of = lambda plane: [plane[0] * p[0] + plane[1] * p[1] + plane[2] for p in footprint]
        return {"id": member_id, "kind": kind, "name": name, "material": self._material, "footprint": footprint,
                "bottom_plane": bottom, "top_plane": top, "z0": min(z_of(bottom)), "z1": max(z_of(top)),
                "width": float(size["width"]), "height": float(size["height"]), "length": length,
                "volume": float(size["width"]) * float(size["height"]) * length}

    def _rafter(self, slope: Dict[str, Any], along: float, size: Dict[str, Any], index: int) -> Dict[str, Any]:
        roof, half = self._roof, float(size["width"]) / 2.0
        cos = math.cos(math.radians(roof.pitch))
        eave = roof.eaves[0] if slope["side"] == "west" else roof.eaves[1]
        rise = roof.slope if slope["side"] == "west" else -roof.slope
        bottom = self._plane(rise, eave, roof.knee)
        top = [bottom[0], bottom[1], bottom[2] + float(size["height"]) / cos]
        across = tuple(sorted((eave, slope["end"])))
        return self._member("%s-s%d" % (slope["id"], index + 1), "rafter", "Sparren %s" % SIDE_NAMES[slope["side"]],
                            self._box(across, (along - half, along + half)), bottom, top, size,
                            (across[1] - across[0]) / cos)

    def _level(self, member_id: str, kind: str, name: str, across: Tuple[float, float], along: Tuple[float, float],
               z_bottom: float, size: Dict[str, Any], length: float) -> Dict[str, Any]:
        bottom = self._plane(0.0, 0.0, z_bottom)
        top = self._plane(0.0, 0.0, z_bottom + float(size["height"]))
        return self._member(member_id, kind, name, self._box(across, along), bottom, top, size, length)

    def _purlin(self, side: str, along: Tuple[float, float], size: Dict[str, Any]) -> Dict[str, Any]:
        # the purlin top carries the rafters: centre where the roof underside is at z_top
        roof, half = self._roof, float(size["width"]) / 2.0
        distance = (float(size["z_top"]) - roof.knee) / roof.slope
        centre = roof.eaves[0] + distance if side == "west" else roof.eaves[1] - distance
        return self._level("purlin-%s" % side, "purlin", "Mittelpfette %s" % SIDE_NAMES[side],
                           (centre - half, centre + half), along, float(size["z_top"]) - float(size["height"]),
                           size, along[1] - along[0])

    def _foot_purlin(self, side: str, along: Tuple[float, float], size: Dict[str, Any],
                     walls: List[WallData]) -> Dict[str, Any]:
        # on the knee wall at the eaves: centred on the wall; its outer face may stand a few cm proud of the eaves
        # line (e.g. a board facade in the wall assembly)
        roof, half = self._roof, float(size["width"]) / 2.0
        eave = roof.eaves[0] if side == "west" else roof.eaves[1]
        wall = next((w for w in walls if w.is_exterior and abs(w.direction[roof.axis]) < SAME
                     and abs(w.start[roof.axis] - eave) < KNEE_WALL_TOLERANCE), None)
        face, thickness = (wall.start[roof.axis], wall.thickness) if wall else (eave, float(size["width"]))
        centre = face + thickness / 2.0 if side == "west" else face - thickness / 2.0
        return self._level("foot-purlin-%s" % side, "foot_purlin", "Fußpfette %s" % SIDE_NAMES[side],
                           (centre - half, centre + half), along, roof.knee, size, along[1] - along[0])

    def _collars(self, rafters: Dict[str, list], size: Dict[str, Any], rafter_width: float) -> List[Dict[str, Any]]:
        # one collar per rafter pair reaching the ridge on both sides, beside the rafters, between the slopes
        roof, ridge = self._roof, self._roof.ridge
        east = [y for y, end in rafters["east"] if abs(end - ridge) < SAME]
        pairs = [y for y, end in rafters["west"] if abs(end - ridge) < SAME and any(abs(y - e) < 1e-3 for e in east)]
        z, height = float(size["z"]), float(size["height"])
        distance = (z + height / 2.0 - roof.knee) / roof.slope
        across = (roof.eaves[0] + distance, roof.eaves[1] - distance)
        offset, half = (rafter_width + float(size["width"])) / 2.0, float(size["width"]) / 2.0
        return [self._level("collar-%d" % (i + 1), "collar", "Kehlbalken", across,
                            (y + offset - half, y + offset + half), z, size, across[1] - across[0])
                for i, y in enumerate(pairs)]

    def _ridge_purlin(self, index: int, spec: Dict[str, Any]) -> Dict[str, Any]:
        # under the ridge: centred on it, the top carries the rafters (roof underside at the ridge)
        roof, half = self._roof, float(spec["width"]) / 2.0
        along = (float(spec["range"][0]), float(spec["range"][1]))
        return self._level(spec.get("id") or "ridge-purlin-%d" % (index + 1), "ridge_purlin", "Firstpfette",
                           (roof.ridge - half, roof.ridge + half), along,
                           roof.ridge_height - float(spec["height"]), spec, along[1] - along[0])
