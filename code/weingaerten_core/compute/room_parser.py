"""Room JSON of a storey → checked rectangular polygons with their decomposition into rects."""
import logging
from typing import Any, Dict, List

from ..constants import ROOM_USAGES
from ..geometry.ortho_polygon import OrthoPolygon
from ..json_values import JsonValues
from ..model.issue_log import IssueLog

logger = logging.getLogger(__name__)


class RoomParser:
    """Parses `storey.rooms[]`; rooms with an invalid polygon are reported and skipped."""

    def __init__(self, issues: IssueLog) -> None:
        """Args:
            issues: receives the room errors.
        """
        self._issues = issues

    def parse(self, storey_ref: str, rooms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return `{id, name, source, polygon (ccw tuples), rects}` per valid room.

        Args:
            storey_ref: storey reference (prefix of the locations).
            rooms: the room JSON objects.
        """
        result = []
        for room in rooms:
            where = "%s.%s" % (storey_ref, room.get("id"))
            points, error = OrthoPolygon.parse(room.get("polygon"))
            if error:
                self._issues.error(where, error)
                continue
            usage = room.get("usage")
            if usage is not None and usage not in ROOM_USAGES:
                self._issues.error(where, "Nutzung ungültig: %s" % usage)
            height = room.get("height")
            if height is not None and not (JsonValues.is_number(height) and height > 0):
                self._issues.error(where, "Raumhöhe ungültig")
            result.append({"id": room.get("id"), "name": room.get("name"), "source": room,
                           "polygon": points, "rects": OrthoPolygon.rects(points)})
        return result
