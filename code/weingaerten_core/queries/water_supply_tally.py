"""BOM rows of the drinking water system: runs, crossing loops, penetrations, fittings, wall plates and stock pipes."""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class WaterSupplyTally:
    """Builds the `water_supply` BOM block and adds its totals."""

    def __init__(self, totals: Dict[str, Any]) -> None:
        """Args:
            totals: the BOM totals; receives water_supply_length and water_fitting_count.
        """
        self._totals = totals

    def block(self, water_supply: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Return {runs, loops, penetrations, parts, stock, cuts} or None without drinking water."""
        if not water_supply:
            return None
        self._totals["water_supply_length"] += water_supply["length"]
        self._totals["water_fitting_count"] += sum(s["count"] for s in water_supply["stock"] if s["kind"] != "pipe")
        runs = [{"run": r["id"], "name": r["name"], "component": r["component"], "component_name": r["component_name"],
                 "dn": r["dn"], "line": r["line"], "medium": r["medium"], "medium_name": r["medium_name"],
                 "length": r["length"], "estimated": r["estimated"]} for r in water_supply["runs"]]
        return {"runs": runs, "loops": water_supply["loops"],
                "penetrations": [p for p in water_supply["penetrations"] if p["kind"] == "through"],
                "parts": water_supply["parts"], "stock": water_supply["stock"], "cuts": water_supply["cuts"]}
