"""BOM rows of the installed parts: count and length per component, stock sticks, cables, slots and penetrations."""
import logging
from typing import Any, Dict, List, Optional

from ..compute.pipe_cutter import PipeCutter
from ..json_values import JsonValues
from ..model.tga_products import TgaProducts

logger = logging.getLogger(__name__)


class PartTally:
    """Builds the `installation` BOM block and adds its totals."""

    # appended last to the BOM totals (in this order)
    ZERO_TOTALS = {"installation_part_count": 0, "installation_pipe_length": 0.0, "installation_slot_volume": 0.0,
                   "installation_penetration_count": 0, "installation_price": 0.0}

    def __init__(self, totals: Dict[str, Any], model: Dict[str, Any]) -> None:
        """Args:
            totals: the BOM totals; receives the installation_* totals.
            model: the computed model (TGA catalog for stock lengths, linked materials for prices).
        """
        self._totals = totals
        self._elements = (model.get("tga") or {}).get("elements") or {}
        self._products = TgaProducts(model)

    def block(self, installation: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Return {components, stock, cables, slots, penetrations} or None without parts."""
        if not installation or not installation["parts"]:
            return None
        parts = installation["parts"]
        cutter = PipeCutter(self._pipes(parts))
        rows: Dict[str, Dict[str, Any]] = {}
        cables: Dict[str, Dict[str, Any]] = {}
        for part in parts:
            # an assembly is bought as its main object plus its parts (clamps below, other parts as extras)
            key = part.get("assembly_main") or part["component"]
            row = rows.setdefault(key, {
                "component": key, "name": self._name(key) if part.get("assembly_main") else part["component_name"],
                "trade": part["trade"], "shape": part["shape"], "count": 0, "length": None,
                "unit_price": self._price(key), "price": None, "estimated": False})
            row["count"] += 1
            row["estimated"] = row["estimated"] or part["estimated"]
            if part["length"] is not None:
                row["length"] = (row["length"] or 0.0) + part["length"]
                cutter.cut(part["component"], part["length"])
                if part["cable"]:
                    cable = cables.setdefault(part["cable"], {"cable": part["cable"], "name": self._name(part["cable"]),
                                                              "length": 0.0, "parts": 0})
                    cable["length"] += part["length"]
                    cable["parts"] += 1
            self._assembly_rows(rows, part)
            for clamp in part.get("clamp_list") or []:
                # one clamp per conductor and box (the wires share it)
                row = rows.setdefault(clamp["clamp"], {
                    "component": clamp["clamp"], "name": clamp["name"], "trade": "electrical", "shape": "clamp",
                    "count": 0, "length": None, "unit_price": self._price(clamp["clamp"]), "price": None,
                    "estimated": False})
                row["count"] += 1
        stock = cutter.stock()
        self._prices(rows, stock)
        slots = installation["slots"]
        self._totals["installation_part_count"] += len(parts)
        self._totals["installation_pipe_length"] += sum(p["length"] or 0.0 for p in parts)
        self._totals["installation_slot_volume"] += sum(s["volume"] for s in slots)
        self._totals["installation_penetration_count"] += len(installation["penetrations"])
        self._totals["installation_price"] += sum(r["price"] or 0.0 for r in rows.values())
        return {"components": [rows[k] for k in sorted(rows)], "stock": stock,
                "cables": [cables[k] for k in sorted(cables)], "slots": slots,
                "penetrations": installation["penetrations"], "open_ports": installation["open_ports"]}

    def _assembly_rows(self, rows: Dict[str, Dict[str, Any]], part: Dict[str, Any]) -> None:
        # parts of an assembly without a conductor role (the clamps come from clamp_list)
        for extra in part.get("assembly_extras") or []:
            row = rows.setdefault(extra["ref"], {
                "component": extra["ref"], "name": self._name(extra["ref"]), "trade": part["trade"], "shape": "part",
                "count": 0, "length": None, "unit_price": self._price(extra["ref"]), "price": None, "estimated": False})
            row["count"] += extra["count"]

    def _pipes(self, parts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        # stock lengths: the pipe's `stock.lengths`, else a conduit's `stock_length` parameter
        pipes = {}
        for ref in {p["component"] for p in parts if p["length"] is not None}:
            element = self._elements.get(ref) or {}
            lengths = (element.get("stock") or {}).get("lengths")
            if not lengths and JsonValues.is_number((element.get("params") or {}).get("stock_length")):
                lengths = [float(element["params"]["stock_length"])]
            if lengths:
                pipes[ref] = {"name": element.get("name"), "lengths": lengths,
                              "estimated": bool(element.get("estimated")), "note": element.get("note")}
        return pipes

    def _prices(self, rows: Dict[str, Dict[str, Any]], stock: List[Dict[str, Any]]) -> None:
        # pieces are priced per part; straight pipes per bought stick (offer = price of one stick)
        sticks: Dict[str, int] = {}
        for row in stock:
            sticks[row["component"]] = sticks.get(row["component"], 0) + row["count"]
        for row in rows.values():
            if row["unit_price"] is None:
                continue
            count = sticks.get(row["component"]) if row["length"] is not None else row["count"]
            row["price"] = row["unit_price"] * count if count is not None else None

    def _price(self, ref: str) -> Optional[float]:
        offers = self._products.offers_of(ref)
        prices = [o["price"] for o in offers if isinstance(o, dict) and JsonValues.is_number(o.get("price"))
                  and (o.get("currency") or "EUR") == "EUR"]
        return min(prices) if prices else None

    def _name(self, ref: str) -> Optional[str]:
        return (self._elements.get(ref) or {}).get("name")
