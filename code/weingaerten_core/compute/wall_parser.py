"""Parses the walls of a storey file into WallData and reports invalid walls."""
import logging
from typing import Any, Dict, List, Optional

from ..constants import TOLERANCE
from ..geometry.vector2d import Point, Vector2D
from ..model.issue_log import IssueLog
from .assembly_info import AssemblyInfo
from .wall_data import WallData

logger = logging.getLogger(__name__)

# walls must be axis-parallel; a smaller deviation in x or y counts as zero
GRID_LIMIT = 0.0005


class WallParser:
    """Checks assembly, shape, reference line and reference of each wall."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the loaded model with the assemblies.
            issues: receives the wall errors.
        """
        self._model = model
        self._issues = issues

    def parse(self, storey_ref: str, walls: List[Dict[str, Any]]) -> List[WallData]:
        """Return the valid walls in file order; invalid walls are reported and skipped."""
        parsed = []
        for source in walls:
            wall = self._parse_wall(storey_ref, source)
            if wall is not None:
                parsed.append(wall)
        return parsed

    def _parse_wall(self, storey_ref: str, source: Dict[str, Any]) -> Optional[WallData]:
        where = "%s.%s" % (storey_ref, source.get("id"))
        assembly_ref = source.get("assembly")
        assembly = self._model["elements"].get(assembly_ref)
        if assembly is None:
            self._issues.error(where, "unbekannt: %s" % assembly_ref)
            return None
        category = assembly.get("category")
        if category not in ("exterior_wall", "interior_wall"):
            self._issues.error(where, "%s ist keine Wand" % assembly_ref)
            return None
        info = AssemblyInfo.of(self._model, assembly_ref)
        if info is None:
            return None
        kind = (source.get("shape") or {"kind": "rect"}).get("kind", "rect")
        if kind not in ("rect", "roof"):
            self._issues.error(where, "gable noch nicht unterstützt")
            return None
        line = self._reference_line(where, source)
        if line is None:
            return None
        start, end = line
        direction = Vector2D.scale(Vector2D.sub(end, start), 1.0 / Vector2D.length(Vector2D.sub(end, start)))
        placement = self._placement(where, source, category, direction, info["thickness"])
        if placement is None:
            return None
        normal, shift = placement
        if not self._free_ends_valid(where, source, category):
            return None
        return WallData(source, where, category, info, start, end, normal, shift)

    def _free_ends_valid(self, where: str, source: Dict[str, Any], category: str) -> bool:
        # optional `free_ends`: interior wall ends released without a connection
        free_ends = source.get("free_ends")
        if free_ends is None:
            return True
        if category != "interior_wall":
            self._issues.error(where, "free_ends nur bei Innenwänden")
            return False
        if not isinstance(free_ends, list) or any(v not in ("start", "end") for v in free_ends):
            self._issues.error(where, "free_ends ungültig")
            return False
        return True

    def _reference_line(self, where: str, source: Dict[str, Any]) -> Optional[tuple]:
        try:
            start = (float(source["start"][0]), float(source["start"][1]))
            end = (float(source["end"][0]), float(source["end"][1]))
        except Exception:
            self._issues.error(where, "start/end ungültig")
            return None
        length = Vector2D.length(Vector2D.sub(end, start))
        if length >= TOLERANCE and abs(end[0] - start[0]) >= GRID_LIMIT and abs(end[1] - start[1]) >= GRID_LIMIT:
            self._issues.error(where, "Wand nicht im 90°-Raster")
            return None
        if length < TOLERANCE:
            self._issues.error(where, "start = end")
            return None
        return start, end

    def _placement(self, where: str, source: Dict[str, Any], category: str, direction: Point,
                   thickness: float) -> Optional[tuple]:
        # returns (inward normal, depth of the reference line)
        left, right = (direction[1], -direction[0]), (-direction[1], direction[0])
        reference = source.get("reference")
        if category == "exterior_wall":
            outside = source.get("outside")
            if outside not in ("left", "right"):
                self._issues.error(where, "outside fehlt")
                return None
            normal = right if outside == "left" else left
            shift = {"outside_face": 0.0, "center": thickness / 2, "inside_face": thickness}.get(reference)
        else:
            normal = right
            shift = {"left_face": 0.0, "center": thickness / 2, "right_face": thickness}.get(reference)
        if shift is None:
            self._issues.error(where, "reference '%s' passt nicht zur Wand" % reference)
            return None
        return normal, shift
