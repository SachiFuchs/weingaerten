"""ROOM_SAVE / ROOM_DELETE (one room of a storey with its coverings) and SHAFT_SAVE / SHAFT_DELETE (house shafts)."""
import copy
import logging
from typing import Any, Dict, List, Optional

from ..constants import ID_RE
from ..model.model_cache import ModelCache
from .storey_change_check import StoreyChangeCheck

logger = logging.getLogger(__name__)


class RoomEditor:
    """Edits a copy of the storey (rooms) or of the house (shafts) and writes it only if the change adds no error."""

    def __init__(self, cache: ModelCache) -> None:
        """Args:
            cache: the model cache.
        """
        self._cache = cache
        self._check = StoreyChangeCheck(cache)

    def save_room(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create or replace a complete room object.

        Args:
            request: `{storey, room, create}`.

        Returns:
            `{storey, room, warnings}` or `{error, errors?}`.
        """
        model = self._cache.model()
        storey = self._storey_copy(model, request.get("storey"))
        if "error" in storey:
            return storey
        room = request.get("room")
        if not isinstance(room, dict) or not isinstance(room.get("id"), str) or not ID_RE.match(room["id"]):
            return {"error": "ungültige Raum-id"}
        error = self._upsert(storey.setdefault("rooms", []), room, bool(request.get("create")))
        if error:
            return error
        new_errors, _ = self._check.new_errors(model, "storey:%s" % request["storey"], storey)
        if new_errors:
            return StoreyChangeCheck.rejection(new_errors)
        self._check.write(request["storey"], storey)
        logger.debug("room %s.%s saved", request["storey"], room["id"])
        return {"storey": request["storey"], "room": room, "warnings": self._cache.model()["warnings"]}

    def delete_room(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a room.

        Args:
            request: `{storey, id}`.

        Returns:
            `{deleted: true}` or `{error, errors?}`.
        """
        model = self._cache.model()
        storey = self._storey_copy(model, request.get("storey"))
        if "error" in storey:
            return storey
        rooms = storey.get("rooms") or []
        if not any(isinstance(r, dict) and r.get("id") == request.get("id") for r in rooms):
            return {"error": "unbekannt: %s" % request.get("id")}
        storey["rooms"] = [r for r in rooms if not (isinstance(r, dict) and r.get("id") == request.get("id"))]
        new_errors, _ = self._check.new_errors(model, "storey:%s" % request["storey"], storey)
        if new_errors:
            return StoreyChangeCheck.rejection(new_errors)
        self._check.write(request["storey"], storey)
        return {"deleted": True}

    def save_shaft(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create or replace a shaft of `house.json`.

        Args:
            request: `{shaft, create}`.

        Returns:
            `{shaft, warnings}` or `{error, errors?}`.
        """
        model = self._cache.model()
        house = copy.deepcopy(model["house"])
        shaft = request.get("shaft")
        if not isinstance(shaft, dict) or not isinstance(shaft.get("id"), str) or not ID_RE.match(shaft["id"]):
            return {"error": "ungültige Schacht-id"}
        error = self._upsert(house.setdefault("shafts", []), shaft, bool(request.get("create")))
        return error or self._apply_house(model, house, {"shaft": shaft})

    def delete_shaft(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a shaft.

        Args:
            request: `{id}`.

        Returns:
            `{deleted: true}` or `{error, errors?}`.
        """
        model = self._cache.model()
        house = copy.deepcopy(model["house"])
        shafts = house.get("shafts") or []
        if not any(isinstance(s, dict) and s.get("id") == request.get("id") for s in shafts):
            return {"error": "unbekannt: %s" % request.get("id")}
        house["shafts"] = [s for s in shafts if not (isinstance(s, dict) and s.get("id") == request.get("id"))]
        if not house["shafts"]:
            house.pop("shafts")
        return self._apply_house(model, house, {"deleted": True})

    @staticmethod
    def _storey_copy(model: Dict[str, Any], storey_id: Any) -> Dict[str, Any]:
        storey_ref = "storey:%s" % storey_id
        if not isinstance(storey_id, str) or storey_ref not in model["storeys"]:
            return {"error": "unbekannt: %s" % storey_ref}
        return copy.deepcopy(model["storeys"][storey_ref])

    @staticmethod
    def _upsert(items: List[Any], item: Dict[str, Any], create: bool) -> Optional[Dict[str, Any]]:
        # order kept, a new item appended
        index = next((i for i, x in enumerate(items) if isinstance(x, dict) and x.get("id") == item["id"]), None)
        if create:
            if index is not None:
                return {"error": "existiert bereits: %s" % item["id"]}
            items.append(item)
        elif index is None:
            return {"error": "unbekannt: %s" % item["id"]}
        else:
            items[index] = item
        return None

    def _apply_house(self, model: Dict[str, Any], house: Dict[str, Any], answer: Dict[str, Any]) -> Dict[str, Any]:
        new_errors, _ = self._check.new_house_errors(model, house)
        if new_errors:
            return StoreyChangeCheck.rejection(new_errors)
        self._check.write_house(house)
        logger.debug("shafts of the house changed")
        if "shaft" in answer:
            answer["warnings"] = self._cache.model()["warnings"]
        return answer
