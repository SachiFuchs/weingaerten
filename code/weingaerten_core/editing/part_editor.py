"""PART_SAVE and PART_DELETE: writes installed parts (house/tga/parts) and keeps their connections symmetric."""
import copy
import logging
import os
from typing import Any, Dict, List, Optional, Set

from ..constants import ID_RE
from ..compute.model_computer import ModelComputer
from ..model.model_cache import ModelCache
from ..model.model_loader import ModelLoader
from .json_file_writer import JsonFileWriter
from .storey_change_check import StoreyChangeCheck

logger = logging.getLogger(__name__)

REF = "tga-part:"


class PartEditor:
    """Applies a batch of part changes to a copy of the model and writes it only if it adds no error."""

    def __init__(self, cache: ModelCache) -> None:
        """Args:
            cache: the model cache.
        """
        self._cache = cache

    def save(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create, update and delete parts in one step.

        Args:
            request: `{upsert: [part], delete: [ids]}`; a part id that exists is updated, else created.

        Returns:
            `{saved, deleted, changed, warnings}` or `{error, errors?}`.
        """
        upsert, delete = request.get("upsert") or [], request.get("delete") or []
        if not isinstance(upsert, list) or not isinstance(delete, list):
            return {"error": "upsert/delete ungültig"}
        for part in upsert:
            if not isinstance(part, dict) or not isinstance(part.get("id"), str) or not ID_RE.match(part["id"]):
                return {"error": "ungültige Teil-id"}
        model = self._cache.model()
        original = {ref[len(REF):]: p for ref, p in ((model.get("tga") or {}).get("parts") or {}).items()}
        parts = copy.deepcopy(original)
        for part_id in delete:
            if part_id not in parts:
                return {"error": "unbekannt: %s" % part_id}
            parts.pop(part_id)
        batch = [p["id"] for p in upsert]
        if len(set(batch)) != len(batch) or set(batch) & set(delete):
            return {"error": "Teil doppelt in der Änderung"}
        for part in upsert:
            parts[part["id"]] = copy.deepcopy(part)
        self._link(parts, set(batch))
        rejection = self._check(model, parts)
        if rejection is not None:
            return rejection
        changed = self._write(original, parts)
        warnings = [w for w in self._cache.model()["warnings"] if w["where"].startswith(REF)]
        return {"saved": batch, "deleted": list(delete), "changed": changed, "warnings": warnings}

    def delete(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Delete one part (`{id}`); connections pointing to it are removed."""
        answer = self.save({"delete": [request.get("id")]})
        return {"deleted": True} if "error" not in answer else answer

    @staticmethod
    def _link(parts: Dict[str, Dict[str, Any]], batch: Set[str]) -> None:
        # the sent parts win: their connections are mirrored, stale back-links of other parts are dropped
        for part_id in sorted(batch):
            connections = parts[part_id].get("connections") or {}
            for own, target in list(connections.items()):
                other_id, _, other_port = str(target).partition(".")
                other = parts.get(other_id)
                if other is None or other_id == part_id:
                    connections.pop(own)
                elif other_id not in batch:
                    other.setdefault("connections", {})[other_port] = "%s.%s" % (part_id, own)
            if "connections" in parts[part_id] and not connections:
                parts[part_id].pop("connections")
        for part_id, part in parts.items():
            connections = part.get("connections") or {}
            for own, target in list(connections.items()):
                other_id, _, other_port = str(target).partition(".")
                other = parts.get(other_id)
                back = ((other or {}).get("connections") or {}).get(other_port)
                if other is None or (other_id in batch and back != "%s.%s" % (part_id, own)):
                    connections.pop(own)
            if "connections" in part and not connections:
                part.pop("connections")

    def _check(self, model: Dict[str, Any], parts: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        changed = ModelLoader(self._cache.home()).load()
        changed["tga"]["parts"] = {REF + k: v for k, v in sorted(parts.items())}
        ModelComputer(changed).compute()
        before = {(e["where"], e["message"]) for e in model["errors"]}
        new_errors = [e for e in changed["errors"] if (e["where"], e["message"]) not in before]
        return StoreyChangeCheck.rejection(new_errors) if new_errors else None

    def _write(self, original: Dict[str, Dict[str, Any]], parts: Dict[str, Dict[str, Any]]) -> List[str]:
        folder = os.path.join(self._cache.home(), "house", "tga", "parts")
        changed = []
        with self._cache.lock:
            for part_id in sorted(set(original) - set(parts)):
                os.remove(os.path.join(folder, part_id + ".json"))
                changed.append(part_id)
                logger.debug("part %s deleted", part_id)
            for part_id, part in sorted(parts.items()):
                if original.get(part_id) != part:
                    JsonFileWriter.write(os.path.join(folder, part_id + ".json"), part)
                    changed.append(part_id)
                    logger.debug("part %s written", part_id)
            self._cache.invalidate()
        return changed
