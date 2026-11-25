"""Computes one storey: walls, openings, layers, faces, outline, foundation (ground storey), rooms, ceilings,
structure and outdoor areas."""
import logging
from typing import Any, Dict, List, Optional

from ..constants import TOLERANCE
from ..geometry.polygon import Polygon
from ..model.issue_log import IssueLog
from .ceiling_builder import CeilingBuilder
from .covering_builder import CoveringBuilder
from .facade_builder import FacadeBuilder
from .floor_builder import FloorBuilder
from .foundation_builder import FoundationBuilder
from .heating_builder import HeatingBuilder
from .layer_piece_builder import LayerPieceBuilder
from .light_well_builder import LightWellBuilder
from .lining_builder import LiningBuilder
from .opening_output_builder import OpeningOutputBuilder
from .opening_parser import OpeningParser
from .outdoor_area_builder import OutdoorAreaBuilder
from .outline_builder import OutlineBuilder
from .room_builder import RoomBuilder
from .room_parser import RoomParser
from .roof_covering_builder import RoofCoveringBuilder
from .roof_profile import RoofProfile
from .roof_structure_builder import RoofStructureBuilder
from .shaft_builder import ShaftBuilder
from .stair_builder import StairBuilder
from .storey_checks import StoreyChecks
from .structure_builder import StructureBuilder
from .wall_data import WallData
from .wall_face_builder import WallFaceBuilder
from .wall_heating_builder import WallHeatingBuilder
from .wall_joints import WallJoints
from .wall_parser import WallParser
from .wall_serializer import WallSerializer

logger = logging.getLogger(__name__)


class StoreyBuilder:
    """Builds the HOUSE answer of one storey; the order of the steps fixes the order of the messages."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the loaded model (elements, foundation spec; receives the foundation).
            issues: receives all storey errors and warnings.
        """
        self._model = model
        self._issues = issues

    def build(self, storey_ref: str, storey: Dict[str, Any], is_ground: bool) -> Dict[str, Any]:
        """Compute the storey.

        Args:
            storey_ref: `storey:<id>`.
            storey: the storey JSON.
            is_ground: True for the first storey; it builds a `follow: outline` foundation and must stand on it.

        Returns:
            `{id, ref, name, elevation, height, outline, walls, rooms, floors, heating, wall_heating, ceilings, structure,
            outdoor_areas, roof_structure, roof_covering, stairs, light_wells, facade, linings}`.
        """
        z0 = float(storey.get("elevation", 0.0) or 0.0)
        height = float(storey.get("height", 0.0) or 0.0)
        foundation_spec = self._model["foundation_spec"]
        if is_ground and foundation_spec and abs(z0 - foundation_spec["top"]) > TOLERANCE:
            self._issues.error(storey_ref, "elevation muss der Oberkante der Bodenplatte entsprechen")
        walls_in = [w for w in (storey.get("walls") or []) if isinstance(w, dict)]
        rooms_in = [r for r in (storey.get("rooms") or []) if isinstance(r, dict)]
        self._check_duplicate_ids(storey_ref, walls_in, rooms_in)
        parsed_rooms = RoomParser(self._issues).parse(storey_ref, rooms_in)
        shaft_cuts = ShaftBuilder.cuts_of(self._model, storey_ref)

        walls = WallParser(self._model, self._issues).parse(storey_ref, walls_in)
        WallJoints(self._issues).connect(walls)
        roof = RoofProfile.parse(storey_ref, storey, self._issues)
        self._build_walls(walls, parsed_rooms, z0, height, roof)

        checks = StoreyChecks(self._issues)
        checks.check_outside_orientation(walls, parsed_rooms)
        checks.check_overlaps(walls)
        rings = OutlineBuilder(self._issues).rings(storey_ref, walls)
        largest = OutlineBuilder.largest(rings)
        if is_ground and foundation_spec:
            self._place_foundation(walls, largest, foundation_spec)
        outline = [tuple(p) for p in largest["inner"]] if largest else None
        rooms = RoomBuilder(self._issues).build(storey_ref, parsed_rooms, walls, outline)
        floors = FloorBuilder(self._model, self._issues, shaft_cuts["floor"]).build(storey_ref, storey, z0, rooms)
        RoomBuilder.apply_floors(rooms, floors, z0, height)
        CoveringBuilder(self._model, self._issues, shaft_cuts["floor"]).build(storey_ref, parsed_rooms, rooms, walls)
        heating = HeatingBuilder(self._issues).build(storey_ref, storey, floors, rooms)
        roof_structure = RoofStructureBuilder(self._model, self._issues).build(storey_ref, storey, z0, roof, walls)
        walls_out = [WallSerializer.to_json(wall, z0) for wall in walls]
        wall_heating = WallHeatingBuilder(self._model, self._issues).build(storey_ref, storey, z0, rooms, walls_out, roof)

        return {"id": storey.get("id"), "ref": storey_ref, "name": storey.get("name"), "elevation": z0,
                "height": height, "roof": roof.to_json() if roof else None, "outline": rings,
                "walls": walls_out, "rooms": rooms,
                "floors": floors, "heating": heating, "wall_heating": wall_heating,
                "ceilings": CeilingBuilder(self._model, self._issues, shaft_cuts["ceiling"]).build(
                    storey_ref, storey, z0, height, largest),
                "structure": StructureBuilder(self._model, self._issues).build(storey_ref, storey, z0, height),
                "outdoor_areas": OutdoorAreaBuilder(self._issues).build(storey_ref, storey),
                "stairs": StairBuilder(self._model, self._issues).build(storey_ref, storey, z0),
                "light_wells": LightWellBuilder(self._model, self._issues).build(storey_ref, storey, walls_out),
                "roof_structure": roof_structure,
                "roof_covering": RoofCoveringBuilder(self._model, self._issues).build(storey_ref, storey, z0, roof,
                                                                                        roof_structure),
                "facade": FacadeBuilder(self._model, self._issues).build(storey_ref, z0, walls_out),
                "linings": LiningBuilder(self._model, self._issues).build(storey_ref, z0, walls)}

    def _check_duplicate_ids(self, storey_ref: str, walls: List[Dict[str, Any]], rooms: List[Dict[str, Any]]) -> None:
        for items, what in ((walls, "Wand"), (rooms, "Raum")):
            self._report_duplicates(storey_ref, [item.get("id") for item in items], "doppelte %s-id" % what)
        opening_ids = [o.get("id") for w in walls for o in (w.get("openings") or []) if isinstance(o, dict)]
        self._report_duplicates(storey_ref, opening_ids, "doppelte Öffnungs-id")

    def _report_duplicates(self, storey_ref: str, ids: List[Any], message: str) -> None:
        for duplicate in set(ids):
            if ids.count(duplicate) > 1:
                self._issues.error("%s.%s" % (storey_ref, duplicate), message)

    def _build_walls(self, walls: List[WallData], rooms: List[Dict[str, Any]], z0: float, height: float,
                     roof: Optional[RoofProfile]) -> None:
        opening_parser = OpeningParser(self._model, self._issues)
        piece_builder = LayerPieceBuilder(z0)
        for wall in walls:
            wall.compute_footprint()
            self._set_top(wall, height, roof)
            wall.openings = opening_parser.parse(wall, wall.height)
            wall.layers = piece_builder.build(wall)
        face_builder = WallFaceBuilder(self._model, self._issues, rooms)
        for wall in walls:
            wall.faces = face_builder.build(wall)
        output_builder = OpeningOutputBuilder(z0)
        for wall in walls:
            wall.openings_out = output_builder.build(wall)

    def _set_top(self, wall: WallData, storey_height: float, roof: Optional[RoofProfile]) -> None:
        # `shape: roof` follows the storey roof (height = highest point over the outside u range)
        if (wall.source.get("shape") or {}).get("kind") == "roof":
            if roof is None:
                self._issues.error(wall.where, "Dach fehlt für Dachwand")
            else:
                wall.roof = roof
                u_a, u_b = wall.u_ranges[0.0]
                wall.height = max(z for _, z in wall.profile(u_a, u_b))
                return
        wall.height = self._wall_height(wall, storey_height)

    def _wall_height(self, wall: WallData, storey_height: float) -> float:
        # optional wall.height (e.g. knee wall) must lie in (0, storey height]
        value = wall.source.get("height")
        if value is None:
            return storey_height
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or value <= 0 or value > storey_height + TOLERANCE:
            self._issues.error(wall.where, "Wandhöhe ungültig")
            return storey_height
        return float(value)

    def _place_foundation(self, walls: List[WallData], largest: Optional[Dict[str, Any]],
                          spec: Dict[str, Any]) -> None:
        if self._model["foundation"] is None:
            polygon = spec["poly"]
            if spec["follow"] and largest:
                polygon = Polygon.offset([tuple(p) for p in largest["points"]], spec["overhang"])
            elif spec["follow"]:
                self._issues.warning("house.foundation",
                                     "Bodenplatte nicht berechnet – Umriss des Erdgeschosses nicht geschlossen")
            if polygon:
                FoundationBuilder(self._model, self._issues).build(polygon)
        if self._model["foundation"]:
            polygon = [tuple(p) for p in self._model["foundation"]["polygon"]]
            StoreyChecks(self._issues).check_on_foundation(walls, polygon)
