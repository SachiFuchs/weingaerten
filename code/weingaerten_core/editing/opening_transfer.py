"""Keeps openings at their absolute position when walls move or openings change walls."""
import copy
import logging
from typing import Any, Dict, List

from ..constants import TOLERANCE
from ..geometry.vector2d import Point, Vector2D
from ..json_values import JsonValues

logger = logging.getLogger(__name__)

# directions with a dot product above this are treated as unchanged
SAME_DIRECTION = 0.9999


class OpeningTransfer:
    """Recomputes opening offsets for changed walls; walls with invalid lines keep the offsets."""

    @staticmethod
    def _line(wall: Dict[str, Any]) -> tuple:
        return ((float(wall["start"][0]), float(wall["start"][1])), (float(wall["end"][0]), float(wall["end"][1])))

    @staticmethod
    def _unit(start: Point, end: Point) -> Point:
        direction = Vector2D.sub(end, start)
        return Vector2D.scale(direction, 1 / Vector2D.length(direction))

    @staticmethod
    def shifted_openings(old_wall: Dict[str, Any], new_wall: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return copies of the old wall's openings with offsets for the new start point.

        Only for an unchanged direction; after a rotation or reversal the offsets are kept.
        """
        openings = copy.deepcopy(old_wall.get("openings") or [])
        shift = OpeningTransfer._shift(old_wall, new_wall)
        for opening in openings:
            if shift and JsonValues.is_number(opening.get("offset")):
                opening["offset"] = round(opening["offset"] + shift, 4)
        return openings

    @staticmethod
    def shifted_linings(old_wall: Dict[str, Any], new_wall: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return copies of the old wall's linings with `u0`/`u1` for the new start point (same rule as openings)."""
        linings = copy.deepcopy(old_wall.get("linings") or [])
        shift = OpeningTransfer._shift(old_wall, new_wall)
        for lining in linings:
            for key in ("u0", "u1"):
                if shift and isinstance(lining, dict) and JsonValues.is_number(lining.get(key)):
                    lining[key] = round(lining[key] + shift, 4)
        return linings

    @staticmethod
    def _shift(old_wall: Dict[str, Any], new_wall: Dict[str, Any]) -> float:
        # u shift that keeps absolute positions; 0 after a rotation or reversal or for invalid lines
        try:
            old_start, old_end = OpeningTransfer._line(old_wall)
            new_start, new_end = OpeningTransfer._line(new_wall)
            old_direction, new_direction = Vector2D.sub(old_end, old_start), Vector2D.sub(new_end, new_start)
            old_length, new_length = Vector2D.length(old_direction), Vector2D.length(new_direction)
            if old_length > TOLERANCE and new_length > TOLERANCE:
                old_direction = Vector2D.scale(old_direction, 1 / old_length)
                new_direction = Vector2D.scale(new_direction, 1 / new_length)
                if Vector2D.dot(old_direction, new_direction) > SAME_DIRECTION:
                    return Vector2D.dot(Vector2D.sub(old_start, new_start), new_direction)
        except Exception:
            logger.debug("wall line invalid, offsets kept")
        return 0.0

    @staticmethod
    def moved_opening(opening: Dict[str, Any], source_wall: Dict[str, Any], target_wall: Dict[str, Any],
                      model: Dict[str, Any]) -> Dict[str, Any]:
        """Return a copy of an opening moved to a parallel target wall, offset from its absolute position.

        For opposite directions the offset refers to the other side of the rough opening, so the
        rough width (component width plus two joints) is added.
        """
        moved = copy.deepcopy(opening)
        try:
            source_start, source_end = OpeningTransfer._line(source_wall)
            target_start, target_end = OpeningTransfer._line(target_wall)
            source_direction = OpeningTransfer._unit(source_start, source_end)
            target_direction = OpeningTransfer._unit(target_start, target_end)
            if abs(Vector2D.cross(source_direction, target_direction)) < 1e-6:
                position = Vector2D.add(source_start, Vector2D.scale(source_direction, float(moved["offset"])))
                if Vector2D.dot(source_direction, target_direction) < 0:
                    component = model["elements"].get(moved.get("component")) or {}
                    width = float((component.get("params") or {}).get("width", 0)) + 2 * float(moved.get("joint", 0.01))
                    position = Vector2D.add(position, Vector2D.scale(source_direction, width))
                moved["offset"] = round(Vector2D.dot(Vector2D.sub(position, target_start), target_direction), 4)
        except Exception:
            logger.debug("wall line invalid, opening offset kept")
        return moved
