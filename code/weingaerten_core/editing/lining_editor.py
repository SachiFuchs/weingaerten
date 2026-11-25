"""LINING_SAVE and LINING_DELETE: changes the interior linings (Innendämmung) of one wall."""
import copy
import logging
from typing import Any, Dict, Optional

from ..constants import ID_RE
from ..model.model_cache import ModelCache
from .storey_change_check import StoreyChangeCheck

logger = logging.getLogger(__name__)


class LiningEditor:
    """Edits a copy of the storey and writes it only if the change adds no error."""

    def __init__(self, cache: ModelCache) -> None:
        """Args:
            cache: the model cache.
        """
        self._cache = cache
        self._check = StoreyChangeCheck(cache)

    def save(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a lining.

        Args:
            request: `{storey, wall, lining, create}`.

        Returns:
            `{storey, wall, lining, warnings}` or `{error, errors?}`.
        """
        model, storey, wall = self._load(request)
        if wall is None:
            return storey
        lining = request.get("lining")
        if not isinstance(lining, dict) or not isinstance(lining.get("id"), str) or not ID_RE.match(lining["id"]):
            return {"error": "ungültige Dämmbereich-id"}
        linings = wall.setdefault("linings", [])
        index = next((i for i, l in enumerate(linings) if isinstance(l, dict) and l.get("id") == lining["id"]), None)
        if request.get("create"):
            storey_ids = {l.get("id") for w in storey.get("walls") or [] if isinstance(w, dict)
                          for l in (w.get("linings") or []) if isinstance(l, dict)}
            if lining["id"] in storey_ids:
                return {"error": "existiert bereits: %s" % lining["id"]}
            linings.append(lining)
        else:
            if index is None:
                return {"error": "unbekannt: %s" % lining["id"]}
            linings[index] = lining
        rejection = self._apply(model, request, storey)
        if rejection is not None:
            return rejection
        return {"storey": request.get("storey"), "wall": request.get("wall"), "lining": lining,
                "warnings": self._cache.model()["warnings"]}

    def delete(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a lining.

        Args:
            request: `{storey, wall, id}`.

        Returns:
            `{deleted: true}` or `{error, errors?}`.
        """
        model, storey, wall = self._load(request)
        if wall is None:
            return storey
        linings = wall.get("linings") or []
        index = next((i for i, l in enumerate(linings) if isinstance(l, dict) and l.get("id") == request.get("id")),
                     None)
        if index is None:
            return {"error": "unbekannt: %s" % request.get("id")}
        linings.pop(index)
        if not linings:
            wall.pop("linings", None)
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
        logger.debug("linings of %s.%s changed", request.get("storey"), request.get("wall"))
        return None
