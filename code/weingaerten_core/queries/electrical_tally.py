"""BOM rows of the electrical system: runs, penetrations, conduit parts, boxes, cables and the cutting list."""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ElectricalTally:
    """Builds the `electrical` BOM block and adds its totals."""

    def __init__(self, totals: Dict[str, Any]) -> None:
        """Args:
            totals: the BOM totals; receives electrical_conduit_length, electrical_cable_length and
                electrical_price.
        """
        self._totals = totals

    def block(self, electrical: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Return {runs, penetrations, parts, stock, cuts} or None without electrical runs."""
        if not electrical:
            return None
        self._totals["electrical_conduit_length"] += electrical["length"]
        self._totals["electrical_cable_length"] += electrical["cable_length"]
        self._totals["electrical_price"] += sum(s["price"] or 0.0 for s in electrical["stock"])
        runs = [{"run": r["id"], "name": r["name"], "component": r["component"], "component_name": r["component_name"],
                 "label": r["label"], "conduit": (r["conduit"] or {}).get("size"), "length": r["length"],
                 "cable_length": r["cable_length"], "open_end": r["open_end"], "to": r["to"],
                 "estimated": r["estimated"]} for r in electrical["runs"]]
        return {"runs": runs, "penetrations": [p for p in electrical["penetrations"] if p["kind"] == "through"],
                "parts": electrical["parts"], "stock": electrical["stock"], "cuts": electrical["cuts"]}
