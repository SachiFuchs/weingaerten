"""OPENING_SAVE and OPENING_DELETE: changes the openings of one wall."""
import copy
import logging
from typing import Any, Dict, Optional

from ..constants import ID_RE
from ..model.model_cache import ModelCache
from .storey_change_check import StoreyChangeCheck

logger = logging.getLogger(__name__)


class OpeningEditor:
    """Edits a copy of the storey and writes it only if the change adds no error."""

    def __init__(self, cache: ModelCache) -> None:
        """Args:
            cache: the model cache.
        """
        self._cache = cache
        self._check = StoreyChangeCheck(cache)

    def save(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update an opening.

        Args:
            request: `{storey, wall, opening, create}`.

        Returns:
            `{storey, wall, opening, warnings}` or `{error, errors?}`.
        """
        model, storey, wall = self._load(request)
        if wall is None:
            return storey
        opening = request.get("opening")
        if not isinstance(opening, dict) or not isinstance(opening.get("id"), str) or not ID_RE.match(opening["id"]):
            return {"error": "ungültige Öffnungs-id"}
        openings = wall.setdefault("openings", [])
        index = next((i for i, o in enumerate(openings) if o.get("id") == opening["id"]), None)
        if request.get("create"):
            storey_ids = {o.get("id") for w in storey.get("walls") or [] for o in (w.get("openings") or [])
                          if isinstance(o, dict)}
            if opening["id"] in storey_ids:
                return {"error": "existiert bereits: %s" % opening["id"]}
            openings.append(opening)
        else:
            if index is None:
                return {"error": "unbekannt: %s" % opening["id"]}
            openings[index] = opening
        rejection = self._apply(model, request, storey)
        if rejection is not None:
            return rejection
        return {"storey": request.get("storey"), "wall": request.get("wall"), "opening": opening,
                "warnings": self._cache.model()["warnings"]}

    def delete(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an opening.

        Args:
            request: `{storey, wall, id}`.

        Returns:
            `{deleted: true}` or `{error, errors?}`.
        """
        model, storey, wall = self._load(request)
        if wall is None:
            return storey
        openings = wall.setdefault("openings", [])
        opening_id = request.get("id")
        index = next((i for i, o in enumerate(openings) if o.get("id") == opening_id), None)
        if index is None:
            return {"error": "unbekannt: %s" % opening_id}
        openings.pop(index)
        rejection = self._apply(model, request, storey)
        if rejection is not None:
            return rejection
        return {"deleted": True}

    def _load(self, request: Dict[str, Any]) -> tuple:
        # (model, storey copy, wall of the copy); on error (model, error answer, None)
        model = self._cache.model()
        storey_id, wall_id = request.get("storey"), request.get("wall")
        storey_ref = "storey:%s" % storey_id
        if not isinstance(storey_id, str) or storey_ref not in model["storeys"]:
            return model, {"error": "unbekannt: %s" % storey_ref}, None
        storey = copy.deepcopy(model["storeys"][storey_ref])
        wall = next((w for w in storey.get("walls") or [] if isinstance(w, dict) and w.get("id") == wall_id), None)
        if wall is None:
            return model, {"error": "unbekannt: Wand %s" % wall_id}, None
        return model, storey, wall

    def _apply(self, model: Dict[str, Any], request: Dict[str, Any], storey: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # any new error rejects the change; otherwise the storey file is written
        new_errors, _ = self._check.new_errors(model, "storey:%s" % request.get("storey"), storey)
        if new_errors:
            return StoreyChangeCheck.rejection(new_errors)
        self._check.write(request.get("storey"), storey)
        logger.debug("openings of %s.%s changed", request.get("storey"), request.get("wall"))
        return None
