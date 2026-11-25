"""BOM rows of the waste water system: pipe lengths, penetrations, fittings and stock pipes."""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class WasteWaterTally:
    """Builds the `waste_water` BOM block and adds its totals."""

    def __init__(self, totals: Dict[str, Any]) -> None:
        """Args:
            totals: the BOM totals; receives waste_water_length, penetration_count and fitting_count.
        """
        self._totals = totals

    def block(self, waste_water: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Return {pipes, penetrations, embedded, parts, stock, cuts} or None without waste water."""
        if not waste_water:
            return None
        through = [p for p in waste_water["penetrations"] if p["kind"] == "through"]
        self._totals["waste_water_length"] += waste_water["length"]
        self._totals["penetration_count"] += len(through)
        self._totals["fitting_count"] += sum(s["count"] for s in waste_water["stock"] if s["kind"] == "fitting")
        runs = [{"run": r["id"], "name": r["name"], "component": r["component"], "component_name": r["component_name"],
                 "dn": r["dn"], "line": r["line"], "length": r["length"],
                 "min_slope": r["min_slope"], "slopes": [s["slope"] for s in r["segments"] if s["slope"] is not None],
                 "estimated": r["estimated"]} for r in waste_water["runs"]]
        return {"runs": runs, "pipes": waste_water["by_component"], "penetrations": through,
                "embedded": [p for p in waste_water["penetrations"] if p["kind"] == "embedded"],
                "parts": waste_water["parts"], "stock": waste_water["stock"], "cuts": waste_water["cuts"]}
