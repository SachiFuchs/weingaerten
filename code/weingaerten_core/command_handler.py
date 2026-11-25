"""JSON command interface of the house core: `handle(command_json) -> answer_json`."""
import json
import logging
from typing import Any, Dict, Optional

from .constants import READ_COMMANDS, REF_RE, WRITE_COMMANDS
from .editing.element_editor import ElementEditor
from .editing.lining_editor import LiningEditor
from .editing.opening_editor import OpeningEditor
from .editing.part_editor import PartEditor
from .editing.room_editor import RoomEditor
from .editing.walls_editor import WallsEditor
from .json_values import JsonValues
from .model.model_cache import ModelCache
from .queries.bill_of_materials import BillOfMaterials
from .queries.catalog_lister import CatalogLister
from .queries.element_counter import ElementCounter
from .queries.house_summary import HouseSummary
from .queries.reference_resolver import ReferenceResolver
from .queries.tga_catalog import TgaCatalog
from .queries.usage_finder import UsageFinder

logger = logging.getLogger(__name__)

HOME_MISSING = "WEINGAERTEN_HOME nicht gesetzt"


class CommandHandler:
    """Parses a command, dispatches it to the query or editing classes and serialises the answer."""

    def __init__(self, cache: ModelCache) -> None:
        """Args:
            cache: the model cache shared by all commands (one lock around loading and writing).
        """
        self._cache = cache
        self._elements = ElementEditor(cache)
        self._openings = OpeningEditor(cache)
        self._linings = LiningEditor(cache)
        self._walls = WallsEditor(cache)
        self._rooms = RoomEditor(cache)
        self._parts = PartEditor(cache)

    def handle(self, command_json: str) -> str:
        """Answer one JSON command; every failure becomes `{"error": ...}`."""
        try:
            request = json.loads(command_json)
            if not isinstance(request, dict):
                raise ValueError
        except Exception:
            return json.dumps({"error": "invalid JSON"})
        command = request.get("command")
        try:
            model = self._cache.model()
            if command == "VALIDATE":
                return self._dump(self._validate(model))
            if command not in READ_COMMANDS + WRITE_COMMANDS:
                return json.dumps({"error": "unknown command"})
            if model is None:
                return self._dump({"error": HOME_MISSING})
            logger.debug("command %s", command)
            if command in WRITE_COMMANDS:
                return self._dump(self._write(command, request))
            return self._dump(self._read(command, request, model))
        except Exception as error:
            logger.exception("command %s failed", command)
            return json.dumps({"error": "interner Fehler: %s" % type(error).__name__})

    @staticmethod
    def _dump(answer: Dict[str, Any]) -> str:
        return json.dumps(answer, ensure_ascii=False)

    @staticmethod
    def _validate(model: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if model is None:
            return {"ok": False, "errors": [{"where": "env", "message": HOME_MISSING}], "warnings": [], "counts": {}}
        return {"ok": not model["errors"], "errors": model["errors"], "warnings": model["warnings"],
                "counts": ElementCounter.counts(model)}

    def _write(self, command: str, request: Dict[str, Any]) -> Dict[str, Any]:
        if command == "SAVE":
            return self._elements.save(request)
        if command == "DELETE":
            return self._elements.delete(request)
        if command == "OPENING_SAVE":
            return JsonValues.rounded(self._openings.save(request))
        if command == "OPENING_DELETE":
            return self._openings.delete(request)
        if command == "LINING_SAVE":
            return JsonValues.rounded(self._linings.save(request))
        if command == "LINING_DELETE":
            return self._linings.delete(request)
        if command == "ROOM_SAVE":
            return JsonValues.rounded(self._rooms.save_room(request))
        if command == "ROOM_DELETE":
            return self._rooms.delete_room(request)
        if command == "SHAFT_SAVE":
            return JsonValues.rounded(self._rooms.save_shaft(request))
        if command == "SHAFT_DELETE":
            return self._rooms.delete_shaft(request)
        if command == "PART_SAVE":
            return JsonValues.rounded(self._parts.save(request))
        if command == "PART_DELETE":
            return self._parts.delete(request)
        return JsonValues.rounded(self._walls.save(request))

    @staticmethod
    def _read(command: str, request: Dict[str, Any], model: Dict[str, Any]) -> Dict[str, Any]:
        if command == "CATALOG":
            return CatalogLister(model).catalog(request.get("type"), bool(request.get("full")))
        if command == "HOUSE":
            return JsonValues.rounded(HouseSummary(model).build())
        if command == "BOM":
            return BillOfMaterials(model).build()
        if command == "TGA_CATALOG":
            return TgaCatalog(model).build()
        ref = request.get("ref")
        if command == "USAGE":
            if request.get("all") is True:
                return {"usage": UsageFinder(model).all_users()}
            if not isinstance(ref, str) or not REF_RE.match(ref):
                return {"error": "ungültige Referenz"}
            return {"ref": ref, "used_by": UsageFinder(model).users_of(ref)}
        if not isinstance(ref, str):
            return {"error": "ref fehlt"}
        found = CatalogLister(model).find(ref)
        if found is None:
            return {"error": "unbekannt: " + ref}
        element, file = found
        if command == "ELEMENT":
            return CatalogLister.element_answer(ref, element, file)
        return JsonValues.rounded(ReferenceResolver(model).resolve_element(ref, element))


_HANDLER = CommandHandler(ModelCache())


def handle(command_json: str) -> str:
    """Answer one JSON command of the house core (thread-safe).

    Args:
        command_json: `{"command": <name>, ...}` as JSON text.

    Returns:
        The JSON answer; errors are `{"error": <text>}`.
    """
    return _HANDLER.handle(command_json)
