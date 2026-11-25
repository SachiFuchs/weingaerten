"""Applies a storey change to a copy of the model and writes it only if it adds no errors."""
import logging
import os
from typing import Any, Dict, List

from ..model.model_cache import ModelCache
from ..model.model_loader import ModelLoader
from ..compute.model_computer import ModelComputer
from .json_file_writer import JsonFileWriter

logger = logging.getLogger(__name__)


class StoreyChangeCheck:
    """Shared "compute a copy, compare the errors, then write" step of the opening, wall, room and shaft editors."""

    def __init__(self, cache: ModelCache) -> None:
        """Args:
            cache: the model cache (lock, invalidation).
        """
        self._cache = cache

    def new_errors(self, model: Dict[str, Any], storey_ref: str, storey: Dict[str, Any]) -> tuple:
        """Compute the model with the changed storey.

        Args:
            model: the current model (its errors are the comparison base).
            storey_ref: the changed storey.
            storey: the changed storey JSON.

        Returns:
            (errors that are not present in the current model, all errors of the changed model).
        """
        changed = ModelLoader(self._cache.home()).load()
        changed["storeys"][storey_ref] = storey
        return self._compare(model, changed)

    def new_house_errors(self, model: Dict[str, Any], house: Dict[str, Any]) -> tuple:
        """Like `new_errors`, for a changed `house.json` (e.g. its shafts)."""
        changed = ModelLoader(self._cache.home()).load()
        changed["house"] = house
        return self._compare(model, changed)

    @staticmethod
    def _compare(model: Dict[str, Any], changed: Dict[str, Any]) -> tuple:
        ModelComputer(changed).compute()
        before = {(e["where"], e["message"]) for e in model["errors"]}
        return [e for e in changed["errors"] if (e["where"], e["message"]) not in before], changed["errors"]

    @staticmethod
    def rejection(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Return the error answer `{error: <first>, errors: ["where: message", ...]}`."""
        return {"error": errors[0]["message"], "errors": ["%s: %s" % (e["where"], e["message"]) for e in errors]}

    def write(self, storey_id: str, storey: Dict[str, Any]) -> None:
        """Write the storey file and invalidate the cached model."""
        with self._cache.lock:
            JsonFileWriter.write(os.path.join(self._cache.home(), "house", "storeys", storey_id + ".json"), storey)
            self._cache.invalidate()
        logger.debug("storey %s written", storey_id)

    def write_house(self, house: Dict[str, Any]) -> None:
        """Write `house/house.json` and invalidate the cached model."""
        with self._cache.lock:
            JsonFileWriter.write(os.path.join(self._cache.home(), "house", "house.json"), house)
            self._cache.invalidate()
        logger.debug("house written")
