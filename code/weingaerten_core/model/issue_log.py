"""Collects the errors and warnings of a model while it is computed."""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class IssueLog:
    """Appends error and warning entries to the lists of a model dict."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the loaded model; its "errors" and "warnings" lists are extended.
        """
        self._model = model

    def error(self, where: str, message: str) -> None:
        """Record an error at the given location."""
        self._model["errors"].append({"where": where, "message": message})

    def warning(self, where: str, message: str) -> None:
        """Record a warning at the given location."""
        self._model["warnings"].append({"where": where, "message": message})

    def opening_error(self, where: str, message: str) -> None:
        """Record an opening error (kind "opening").

        Wall editing tolerates these errors and reports them as conflicts, so the wall and
        opening ids are kept separately. `where` is "<storey ref>.<wall id>.<opening id>".
        """
        parts = where.split(".")
        self._model["errors"].append({"where": where, "message": message, "kind": "opening",
                                      "wall": parts[-2], "opening": parts[-1]})

    def lining_error(self, where: str, message: str) -> None:
        """Record an interior lining error (kind "lining"); like opening errors, wall editing tolerates them.

        `where` is "<storey ref>.<wall id>.<lining id>".
        """
        parts = where.split(".")
        self._model["errors"].append({"where": where, "message": message, "kind": "lining",
                                      "wall": parts[-2], "lining": parts[-1]})

    def covering_error(self, where: str, message: str) -> None:
        """Record a covering error (kind "covering"); wall editing tolerates them like lining errors.

        `where` is "<storey ref>.<room id>.<covering id>".
        """
        parts = where.split(".")
        self._model["errors"].append({"where": where, "message": message, "kind": "covering",
                                      "room": parts[-2], "covering": parts[-1]})

    def part_error(self, part_id: str, message: str) -> None:
        """Record an error of an installed part (kind "part", where "tga-part:<id>"); the part is skipped."""
        self._model["errors"].append({"where": "tga-part:" + part_id, "message": message, "kind": "part",
                                      "part": part_id})
