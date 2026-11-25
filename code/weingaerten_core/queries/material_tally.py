"""Collects the volumes and visible areas per material for the BOM."""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class MaterialTally:
    """Accumulates volume and face areas per material reference."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the computed model (material names and categories).
        """
        self._model = model
        self._entries: Dict[str, Dict[str, Any]] = {}

    def entry(self, ref: str) -> Dict[str, Any]:
        """Return the (created on first use) entry of a material."""
        if ref not in self._entries:
            element = self._model["elements"].get(ref, {})
            self._entries[ref] = {"material": ref, "name": element.get("name"), "category": element.get("category"),
                                  "volume": 0.0, "area_outside": 0.0, "area_inside": 0.0, "area_reveal": 0.0,
                                  "area_total": 0.0}
        return self._entries[ref]

    def add(self, ref: str, key: str, amount: float) -> None:
        """Add an amount to one quantity (`volume`, `area_outside`, `area_inside`, `area_reveal`)."""
        self.entry(ref)[key] += amount

    def sorted_entries(self) -> List[Dict[str, Any]]:
        """Return the entries sorted by material ref, with `area_total` filled in."""
        for entry in self._entries.values():
            entry["area_total"] = entry["area_outside"] + entry["area_inside"] + entry["area_reveal"]
        return [self._entries[ref] for ref in sorted(self._entries)]
