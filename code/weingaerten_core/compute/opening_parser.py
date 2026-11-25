"""Parses and checks the openings of a wall."""
import logging
from typing import Any, Dict, List, Optional

from ..constants import OPENING_GEOMETRIES, TOLERANCE
from ..model.issue_log import IssueLog
from ..validation.class_validator import ClassValidator
from .opening_data import OpeningData
from .wall_data import WallData

logger = logging.getLogger(__name__)

DEFAULT_JOINT = 0.01
DEFAULT_INSET = 0.10
# overlaps up to 1 cm² are rounding noise of touching openings
OVERLAP_LIMIT = 0.0001


class OpeningParser:
    """Builds the OpeningData of a wall and reports the opening errors (kind "opening")."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the loaded model with components, classes and materials.
            issues: receives the opening errors.
        """
        self._model = model
        self._issues = issues

    def parse(self, wall: WallData, wall_height: float) -> List[OpeningData]:
        """Return the usable openings of the wall in file order.

        Openings that cannot be placed at all are skipped; openings that are placed but violate
        a rule (outside the wall, too high, too deep, overlapping) are kept and reported.
        """
        openings = []
        for source in wall.source.get("openings") or []:
            if not isinstance(source, dict):
                continue
            opening = self._parse_opening(wall, source)
            if opening is not None:
                self._check_fit(wall, opening, wall_height)
                openings.append(opening)
        self._check_overlaps(openings)
        return openings

    def _parse_opening(self, wall: WallData, source: Dict[str, Any]) -> Optional[OpeningData]:
        where = "%s.%s" % (wall.where, source.get("id"))
        component_ref = source.get("component")
        elements = self._model["elements"]
        component = elements.get(component_ref)
        if not isinstance(component, dict):
            self._issues.opening_error(where, "unbekannt: %s" % component_ref)
            return None
        component_class = elements.get(component.get("class")) or {}
        if not component.get("opening_capable"):
            self._issues.opening_error(where, "Bauteil nicht für Öffnungen geeignet: %s" % component_ref)
            return None
        if component_class.get("geometry") not in OPENING_GEOMETRIES:
            self._issues.opening_error(where, "Bauteil-Klasse %s kann nicht in Öffnungen" % component.get("class"))
            return None
        sizes = self._sizes(component.get("params") or {}, source, component_class.get("geometry"))
        if sizes is None:
            self._issues.opening_error(where, "Maße unvollständig")
            return None
        reveal_material = source.get("reveal_material")
        if reveal_material is not None and not ClassValidator.is_material(self._model, reveal_material):
            self._issues.opening_error(where, "unbekannt: %s" % reveal_material)
            reveal_material = None
        return OpeningData(source, where, component_ref, component, component_class, sizes, reveal_material)

    @staticmethod
    def _sizes(params: Dict[str, Any], source: Dict[str, Any], geometry: str) -> Optional[Dict[str, float]]:
        # a passage is a bare hole: no frame, no depth, the reveals start at the outer face
        is_passage = geometry == "passage"
        try:
            sizes = {"width": float(params["width"]), "height": float(params["height"]),
                     "depth": 0.0 if is_passage else float(params["depth"]),
                     "frame_width": 0.0 if is_passage else float(params["frame_width"]),
                     "offset": float(source["offset"]), "sill": float(source["sill"])}
        except Exception:
            return None
        sizes["joint"] = float(source.get("joint", DEFAULT_JOINT))
        sizes["inset"] = 0.0 if is_passage else float(source.get("inset", DEFAULT_INSET))
        return sizes

    def _check_fit(self, wall: WallData, opening: OpeningData, wall_height: float) -> None:
        # the rough opening must lie within the u range of both faces (corners shorten the inner face)
        for u_a, u_b in wall.u_ranges.values():
            if opening.u0 < min(u_a, u_b) - TOLERANCE or opening.u1 > max(u_a, u_b) + TOLERANCE:
                self._issues.opening_error(opening.where, "Öffnung ragt über die Wand")
                break
        if opening.z_top > wall.min_top(opening.u0, opening.u1) + TOLERANCE:
            self._issues.opening_error(opening.where, "Öffnung höher als die Wand")
        if opening.inset + opening.depth > wall.thickness + TOLERANCE:
            self._issues.opening_error(opening.where, "Bauteil tiefer als die Wand")

    def _check_overlaps(self, openings: List[OpeningData]) -> None:
        for i in range(len(openings)):
            for k in range(i + 1, len(openings)):
                first, second = openings[i], openings[k]
                width = max(0.0, min(first.u1, second.u1) - max(first.u0, second.u0))
                height = max(0.0, min(first.z_top, second.z_top) - max(first.z_bottom, second.z_bottom))
                if width * height > OVERLAP_LIMIT:
                    self._issues.opening_error(second.where, "Öffnungen überlappen (%s)" % first.id)
