"""Outdoor areas of a storey (e.g. a covered terrace) – rectangles outside the exterior walls."""
import logging
from typing import Any, Dict, List

from ..json_values import JsonValues
from ..model.issue_log import IssueLog

logger = logging.getLogger(__name__)


class OutdoorAreaBuilder:
    """Builds the `outdoor_areas` answer of a storey; areas with an invalid rect are reported and skipped."""

    def __init__(self, issues: IssueLog) -> None:
        """Args:
            issues: receives the `rect ungültig` errors.
        """
        self._issues = issues

    def build(self, storey_ref: str, storey: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return `[{id, name, rect, area}]` in file order."""
        result = []
        for item in storey.get("outdoor_areas") or []:
            if not isinstance(item, dict):
                continue
            rect = item.get("rect")
            if not (isinstance(rect, list) and len(rect) == 4 and all(JsonValues.is_number(v) for v in rect)
                    and rect[2] > 0 and rect[3] > 0):
                self._issues.error("%s.%s" % (storey_ref, item.get("id")), "rect ungültig")
                continue
            rect = [float(v) for v in rect]
            result.append({"id": item.get("id"), "name": item.get("name"), "rect": rect, "area": rect[2] * rect[3]})
        return result
