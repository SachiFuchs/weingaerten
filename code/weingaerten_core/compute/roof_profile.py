"""The roof of a storey (gable): height of the roof underside above the storey floor at a plan point."""
import logging
import math
from typing import Any, Dict, Optional

from ..geometry.vector2d import Point
from ..model.issue_log import IssueLog

logger = logging.getLogger(__name__)

RIDGE_DIRECTIONS = ("south_north", "west_east")


class RoofProfile:
    """Gable roof: eaves lines at `eaves[0]` / `eaves[1]` (x for a south_north ridge, y for west_east) with the
    knee wall height there, rising with `pitch` to the ridge in the middle."""

    def __init__(self, pitch: float, knee: float, ridge_direction: str, eaves: tuple) -> None:
        """Args:
            pitch: roof pitch in degrees (0 < pitch < 90).
            knee: height of the roof line at the eaves (knee wall), storey-local.
            ridge_direction: `south_north` (height varies with x) or `west_east` (varies with y).
            eaves: the two eaves coordinates, ascending.
        """
        self.pitch = pitch
        self.knee = knee
        self.ridge_direction = ridge_direction
        self.eaves = eaves
        self.axis = 0 if ridge_direction == "south_north" else 1
        self.slope = math.tan(math.radians(pitch))
        self.ridge = (eaves[0] + eaves[1]) / 2.0
        self.ridge_height = knee + self.slope * (eaves[1] - eaves[0]) / 2.0

    @classmethod
    def parse(cls, storey_ref: str, storey: Dict[str, Any], issues: IssueLog) -> Optional["RoofProfile"]:
        """Return the roof of a storey or None (no `roof`, or invalid → error `Dach ungültig`)."""
        roof = storey.get("roof")
        if roof is None:
            return None
        try:
            pitch, knee = float(roof["pitch"]), float(roof["knee_wall_height"])
            eaves = (float(roof["eaves"][0]), float(roof["eaves"][1]))
            direction = roof.get("ridge_direction", "south_north")
            valid = roof.get("kind", "gable") == "gable" and 0 < pitch < 90 and knee > 0 \
                and eaves[0] < eaves[1] and direction in RIDGE_DIRECTIONS
        except (KeyError, TypeError, ValueError, IndexError):
            valid = False
        if not valid:
            issues.error("%s.roof" % storey_ref, "Dach ungültig")
            return None
        return cls(pitch, knee, direction, eaves)

    def height_at(self, point: Point) -> float:
        """Storey-local height of the roof underside above a plan point (knee height outside the eaves)."""
        c = point[self.axis]
        distance = max(0.0, min(c - self.eaves[0], self.eaves[1] - c))
        return self.knee + self.slope * distance

    def to_json(self) -> Dict[str, Any]:
        """Return the storey output `roof` object."""
        return {"kind": "gable", "pitch": self.pitch, "knee_wall_height": self.knee,
                "ridge_direction": self.ridge_direction, "eaves": list(self.eaves), "ridge": self.ridge,
                "ridge_height": self.ridge_height}
