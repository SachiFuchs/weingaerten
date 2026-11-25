"""SAVE and DELETE of catalog elements."""
import json
import logging
import os
from typing import Any, Dict, List, Optional

from ..constants import CATALOG_FOLDERS, EDIT_RE, TGA_FOLDERS
from ..model.model_cache import ModelCache
from ..queries.usage_finder import UsageFinder
from ..validation.component_validator import ComponentValidator
from ..validation.connection_validator import ConnectionValidator
from ..validation.element_validator import ElementValidator
from ..validation.product_validator import ProductValidator
from .json_file_writer import JsonFileWriter

logger = logging.getLogger(__name__)


class ElementEditor:
    """Writes or deletes one catalog element file after checking the element and its dependants."""

    def __init__(self, cache: ModelCache) -> None:
        """Args:
            cache: the model cache (lock, invalidation).
        """
        self._cache = cache

    def _paths(self, ref: Any) -> Optional[tuple]:
        # (absolute path, path relative to home) of an editable ref, else None
        match = EDIT_RE.match(ref) if isinstance(ref, str) else None
        if not match:
            return None
        folders = dict(CATALOG_FOLDERS, **TGA_FOLDERS)
        folder = [f for f, t in folders.items() if t == match.group(1)][0]
        return (os.path.join(self._cache.home(), "catalog", folder, match.group(2) + ".json"),
                "catalog/%s/%s.json" % (folder, match.group(2)))

    def save(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update an element.

        Args:
            request: `{ref, element, create}`.

        Returns:
            `{ref, element, file, warnings}` or `{error, errors?}`; nothing is written on error.
        """
        ref, element, create = request.get("ref"), request.get("element"), bool(request.get("create"))
        paths = self._paths(ref)
        if paths is None:
            return {"error": "ungültige Referenz"}
        path, relative = paths
        if not isinstance(element, dict) or element.get("id") != ref.split(":", 1)[1]:
            return {"error": "id passt nicht zur Referenz"}
        model = self._cache.model()
        with self._cache.lock:
            exists = os.path.isfile(path)
            if create and exists:
                return {"error": "existiert bereits: " + ref}
            if not create and not exists:
                return {"error": "unbekannt: " + ref}
            errors = ElementValidator(model).errors(ref, element)
            if not errors:
                errors = self._dependant_errors(model, ref, element)
            if errors:
                return {"error": errors[0], "errors": errors}
            JsonFileWriter.write(path, element)
            self._cache.invalidate()
        logger.debug("saved %s", ref)
        return {"ref": ref, "element": element, "file": relative, "warnings": self._cache.model()["warnings"]}

    def _dependant_errors(self, model: Dict[str, Any], ref: str, element: Dict[str, Any]) -> List[str]:
        # a changed class or company must still fit every element that uses it
        elements = model["elements"]
        if ref.startswith("class:"):
            headline = "Bauteile passen nicht mehr zur Klasse: "
            components = ComponentValidator(model)
            results = {r: components.errors(e, element) for r, e in elements.items()
                       if r.startswith("component:") and e.get("class") == ref}
        elif ref.startswith("company:"):
            headline = "Bauteile/Materialien passen nicht mehr zur Firma: "
            products = ProductValidator(model)
            results = {r: products.errors(e, {ref: element}) for r, e in elements.items()
                       if r.startswith(("component:", "material:")) and isinstance(e.get("product"), dict)}
        elif ref.startswith("tga-class:"):
            headline = "TGA-Bauteile passen nicht mehr zur Klasse: "
            connections = ConnectionValidator(model)
            results = {r: connections.errors(r, e, element) for r, e in model["tga"]["elements"].items()
                       if r.startswith("tga-component:") and e.get("class") == ref}
        else:
            return []
        failing = [r for r, errors in results.items() if errors]
        if not failing:
            return []
        messages = ["%s: %s" % (r, message) for r in failing for message in results[r]]
        return [headline + ", ".join(sorted(failing))] + messages

    @staticmethod
    def _tga_users(model: Dict[str, Any], ref: str) -> List[str]:
        # every TGA element or house file (runs, terminals, parts, penetrations) mentioning the ref
        tga = model.get("tga") or {}
        needle = json.dumps(ref)
        users = [r for group in ("elements", "runs", "terminals", "parts") for r, e in (tga.get(group) or {}).items()
                 if r != ref and needle in json.dumps(e, ensure_ascii=False)]
        if any(needle in json.dumps(item, ensure_ascii=False) for item in tga.get("penetrations") or []):
            users.append("house/penetrations.json")
        return sorted(users)

    def delete(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an element that nothing references.

        Args:
            request: `{ref}`.

        Returns:
            `{ref, deleted: true}` or `{error}`.
        """
        ref = request.get("ref")
        paths = self._paths(ref)
        if paths is None:
            return {"error": "ungültige Referenz"}
        path = paths[0]
        model = self._cache.model()
        with self._cache.lock:
            if not os.path.isfile(path):
                return {"error": "unbekannt: " + ref}
            users = self._tga_users(model, ref) if ref.startswith("tga-") else UsageFinder(model).users_of(ref)
            if users:
                return {"error": "wird verwendet von: " + ", ".join(users)}
            os.remove(path)
            self._cache.invalidate()
        logger.debug("deleted %s", ref)
        return {"ref": ref, "deleted": True}
