"""Answers of CATALOG and ELEMENT."""
import logging
from typing import Any, Dict, Optional

from ..constants import TYPE_ORDER

logger = logging.getLogger(__name__)


class CatalogLister:
    """Lists catalog elements and looks up single elements or storeys."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the loaded model.
        """
        self._model = model

    def catalog(self, element_type: Optional[str], full: bool = False) -> Dict[str, Any]:
        """Return `{elements: [{ref, type, id, name, category}]}`, sorted by type order and id.

        Args:
            element_type: only elements of this type, or all for None / empty.
            full: each entry is the ELEMENT answer instead (one call instead of one ELEMENT per element).
        """
        elements = []
        for ref, element in self._model["elements"].items():
            ref_type = ref.split(":")[0]
            if element_type and ref_type != element_type:
                continue
            if full:
                elements.append(self.element_answer(ref, element, self._model["files"].get(ref)))
                continue
            elements.append({"ref": ref, "type": ref_type, "id": element.get("id"), "name": element.get("name"),
                             "category": self._category(ref_type, element)})
        elements.sort(key=lambda e: (TYPE_ORDER.index(e["type"]), str(e.get("id"))))
        return {"elements": elements}

    @staticmethod
    def _category(ref_type: str, element: Dict[str, Any]) -> Any:
        # the list column "category" shows the most useful grouping per type
        if ref_type == "component":
            return element.get("class")
        if ref_type == "class":
            return element.get("geometry")
        if ref_type == "company":
            return ", ".join(map(str, element.get("roles") or []))
        return element.get("category")

    def find(self, ref: str) -> Optional[tuple]:
        """Return (element, file) of a catalog element or storey, or None if unknown."""
        element, file = self._model["elements"].get(ref), self._model["files"].get(ref)
        if element is None and ref in self._model["storeys"]:
            element, file = self._model["storeys"][ref], self._model["storey_files"][ref]
        if element is None:
            return None
        return element, file

    @staticmethod
    def element_answer(ref: str, element: Dict[str, Any], file: str) -> Dict[str, Any]:
        """Return the ELEMENT answer: the raw JSON plus ref, type and file."""
        out = dict(element)
        out.update({"ref": ref, "type": ref.split(":")[0], "file": file})
        return out
