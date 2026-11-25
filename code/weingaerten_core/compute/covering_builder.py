"""Coverings (Beläge, IfcCovering) of the rooms: floor coverings on the whole room or on zones, wall coverings."""
import logging
from typing import Any, Dict, List, Optional

from ..constants import TOLERANCE
from ..geometry.ortho_polygon import OrthoPolygon
from ..model.issue_log import IssueLog
from .assembly_info import AssemblyInfo
from .wall_covering_builder import WallCoveringBuilder
from .wall_data import WallData

logger = logging.getLogger(__name__)

COVERING_CATEGORY = "covering"
AREA_LIMIT = TOLERANCE * TOLERANCE


class CoveringBuilder:
    """Adds `coverings` to every computed room; errors are covering errors (tolerated by WALLS_SAVE)."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog, shaft_rects: List[List[float]]) -> None:
        """Args:
            model: the loaded model (assemblies, materials).
            issues: receives covering errors.
            shaft_rects: rects of the shafts through the floor of this storey (cut out of floor coverings).
        """
        self._model = model
        self._issues = issues
        self._shaft_rects = shaft_rects
        self._walls = WallCoveringBuilder(issues)

    def build(self, storey_ref: str, parsed: List[Dict[str, Any]], rooms: List[Dict[str, Any]],
              walls: List[WallData]) -> None:
        """Compute the coverings of every room (`room["coverings"]`).

        Args:
            storey_ref: storey reference.
            parsed: the parsed rooms (`RoomParser`, with the source JSON).
            rooms: the computed rooms (same order), with `floor_top` set.
            walls: the computed walls.
        """
        seen: List[Any] = []
        by_id = {wall.id: wall for wall in walls}
        for source, room in zip(parsed, rooms):
            room["coverings"] = []
            zones: List[Dict[str, Any]] = []
            whole: List[Dict[str, Any]] = []
            for covering in source["source"].get("coverings") or []:
                where = "%s.%s.%s" % (storey_ref, room["id"], covering.get("id") if isinstance(covering, dict) else "?")
                if not isinstance(covering, dict):
                    self._issues.covering_error(where, "Belag ungültig")
                    continue
                if covering.get("id") in seen:
                    self._issues.error(where, "doppelte Belag-id")
                seen.append(covering.get("id"))
                built = self._covering(where, covering, room, by_id)
                if built is None:
                    continue
                if built["surface"] == "floor":
                    (whole if built["scope"] == "room" else zones).append(built)
                room["coverings"].append(built)
            self._finish_floor(storey_ref, room, whole, zones)

    def _covering(self, where: str, covering: Dict[str, Any], room: Dict[str, Any],
                  walls: Dict[str, WallData]) -> Optional[Dict[str, Any]]:
        info = self._assembly(where, covering.get("assembly"))
        if info is None:
            return None
        base = {"id": covering["id"], "name": covering.get("name"), "surface": covering.get("surface"),
                "assembly": covering["assembly"], "assembly_name": info["el"].get("name"),
                "thickness": info["thickness"], "estimated": bool(covering.get("estimated")),
                "note": covering.get("note"), "source": covering}
        if covering.get("surface") == "floor":
            return self._floor(where, covering, room, base, info)
        if covering.get("surface") == "wall":
            built = self._walls.build(where, covering, room, walls, base)
            if built is not None:
                built["layers"] = self.layers(info, built["area"])
                built["volume"] = sum(layer["volume"] for layer in built["layers"])
            return built
        self._issues.covering_error(where, "Fläche ungültig (floor oder wall)")
        return None

    def _assembly(self, where: str, ref: Any) -> Optional[Dict[str, Any]]:
        assembly = self._model["elements"].get(ref)
        if assembly is None:
            self._issues.covering_error(where, "unbekannt: %s" % ref)
            return None
        if assembly.get("category") != COVERING_CATEGORY:
            self._issues.covering_error(where, "Aufbau ist kein Belag (category covering)")
            return None
        info = AssemblyInfo.of(self._model, ref)
        if info is None or any(layer["material"] not in self._model["elements"] for layer in info["layers"]):
            self._issues.covering_error(where, "Schichten des Belags ungültig")
            return None
        return info

    def _floor(self, where: str, covering: Dict[str, Any], room: Dict[str, Any], base: Dict[str, Any],
               info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        area_value = covering.get("area", "room")
        if area_value == "room":
            polygon, rects = None, room["rects"]
        else:
            points, error = OrthoPolygon.parse(area_value)
            if error:
                self._issues.covering_error(where, "Bereich: " + error)
                return None
            polygon, rects = OrthoPolygon.to_json(points), OrthoPolygon.rects(points)
            if OrthoPolygon.overlap_area(rects, room["rects"]) < OrthoPolygon.area(points) - AREA_LIMIT:
                self._issues.covering_error(where, "Belagsbereich liegt nicht im Raum")
                return None
        gross = sum(r[2] * r[3] for r in rects)
        z0 = room["floor_top"]
        return dict(base, scope="room" if polygon is None else "zone", polygon=polygon, rects=rects,
                    gross_area=gross, shaft_area=OrthoPolygon.overlap_area(rects, self._shaft_rects),
                    zone_area=0.0, area=gross, z0=z0, z1=z0 + info["thickness"], layers=[], volume=0.0, info=info)

    def _finish_floor(self, storey_ref: str, room: Dict[str, Any], whole: List[Dict[str, Any]],
                      zones: List[Dict[str, Any]]) -> None:
        # zones replace the whole-room covering where they lie; the shaft opens every floor covering
        for extra in whole[1:]:
            self._issues.covering_error("%s.%s.%s" % (storey_ref, room["id"], extra["id"]),
                                        "mehrere Beläge für den ganzen Raum")
        for i, zone in enumerate(zones):
            for other in zones[:i]:
                if OrthoPolygon.overlap_area(zone["rects"], other["rects"]) > AREA_LIMIT:
                    self._issues.covering_error("%s.%s.%s" % (storey_ref, room["id"], zone["id"]),
                                                "Belagsbereiche überlappen: %s" % other["id"])
        zone_rects = [r for zone in zones for r in zone["rects"]]
        for covering in whole + zones:
            if covering["scope"] == "room":
                covering["zone_area"] = sum(zone["gross_area"] for zone in zones)
                zone_shaft = OrthoPolygon.overlap_area(zone_rects, self._shaft_rects)
                covering["shaft_area"] -= zone_shaft
            covering["area"] = covering["gross_area"] - covering["zone_area"] - covering["shaft_area"]
            covering["layers"] = self.layers(covering.pop("info"), covering["area"])
            covering["volume"] = sum(layer["volume"] for layer in covering["layers"])

    def layers(self, info: Dict[str, Any], area: float) -> List[Dict[str, Any]]:
        """Return the layer rows (from the substrate to the room) of a covering with this area."""
        rows = []
        for layer in info["layers"]:
            material = self._model["elements"].get(layer["material"], {})
            rows.append({"index": layer["index"], "material": layer["material"], "thickness": layer["thickness"],
                         "offset": layer["offset"], "area": area, "volume": area * layer["thickness"],
                         "color": (material.get("appearance") or {}).get("color")})
        return rows
