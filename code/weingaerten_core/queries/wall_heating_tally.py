"""BOM rows of the wall heating: panels per type with prices, fittings, pipes and the layers of its assembly."""
import logging
from typing import Any, Dict, List, Optional

from ..json_values import JsonValues
from ..model.tga_products import TgaProducts
from .material_tally import MaterialTally

logger = logging.getLogger(__name__)

ZERO_TOTALS = {"wall_heating_area": 0.0, "wall_heating_panels": 0, "wall_heating_pipe_length": 0.0,
               "wall_heating_feed_length": 0.0, "wall_heating_price": 0.0}


class WallHeatingTally:
    """Turns the computed wall heating of the storeys into BOM rows and adds their quantities."""

    def __init__(self, model: Dict[str, Any], materials: MaterialTally, totals: Dict[str, Any]) -> None:
        """Args:
            model: the computed model (TGA catalog and linked materials for the prices).
            materials: receives the layer volumes and the plaster area (last layer).
            totals: receives the `wall_heating_*` totals.
        """
        self._model = model
        self._tga = (model.get("tga") or {}).get("elements") or {}
        self._products = TgaProducts(model)
        self._materials = materials
        self._totals = totals

    def rows(self, storey: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return one row for the wall heating of the storey (empty without wall heating)."""
        heating = storey.get("wall_heating")
        if not heating:
            return []
        area = heating["area"]
        layers = []
        for layer in heating["layers"]:
            volume = area * layer["thickness"]
            self._materials.add(layer["material"], "volume", volume)
            layers.append({"material": layer["material"], "thickness": layer["thickness"], "area": area,
                           "volume": volume, "heated": layer["heated"]})
        if heating["layers"]:
            self._materials.add(heating["layers"][-1]["material"], "area_inside", area)
        items = self._items(heating)
        price = sum(i["price"] or 0.0 for i in items)
        self._totals["wall_heating_area"] += area
        self._totals["wall_heating_panels"] += heating["panel_count"]
        self._totals["wall_heating_pipe_length"] += heating["pipe_length"]
        self._totals["wall_heating_feed_length"] += heating["feed_length"]
        self._totals["wall_heating_price"] += price
        return [{"storey": storey["id"], "name": heating["name"], "assembly": heating["assembly"],
                 "estimated": heating["estimated"], "supply_temperature": heating["supply_temperature"],
                 "return_temperature": heating["return_temperature"], "area": area,
                 "panel_count": heating["panel_count"], "pipe_length": heating["pipe_length"],
                 "feed_length": heating["feed_length"], "couplings": heating["couplings"],
                 "adapters": heating["adapters"], "price": price, "layers": layers, "items": items,
                 "distributor": {"name": heating["distributor"]["name"],
                                 "component": heating["distributor"]["component"],
                                 "outlets": heating["distributor"]["outlets"]},
                 "circuits": [{"id": c["id"], "name": c["name"], "room": c["room"], "panel_count": c["panel_count"],
                               "area": c["area"], "design_area": c["design_area"],
                               "design_output": c["design_output"], "pipe_length": c["pipe_length"],
                               "feed_length": c["feed_length"], "couplings": c["couplings"],
                               "adapters": c["adapters"]} for c in heating["circuits"]],
                 "fields": [{"id": f["id"], "name": f["name"], "circuit": f["circuit"], "room": f["room"],
                             "wall": f["wall"], "wall_name": f["wall_name"],
                             "panels": "".join(p["type"] for p in f["panels"]), "area": f["area"]}
                            for f in heating["fields"]]}]

    def _items(self, heating: Dict[str, Any]) -> List[Dict[str, Any]]:
        # panels per type, couplings (panel to panel) and adapters (panel to feed line)
        counts: Dict[str, Dict[str, Any]] = {}
        for f in heating["fields"]:
            for panel in f["panels"]:
                row = counts.setdefault(panel["component"], {"kind": "panel", "type": panel["type"], "count": 0,
                                                             "area": 0.0})
                row["count"] += 1
                row["area"] += panel["area"]
        if heating["coupling"]:
            counts[heating["coupling"]] = {"kind": "coupling", "type": None, "count": heating["couplings"], "area": None}
        if heating["adapter"]:
            counts[heating["adapter"]] = {"kind": "adapter", "type": None, "count": heating["adapters"], "area": None}
        items = []
        for ref, row in sorted(counts.items(), key=lambda kv: (kv[1]["kind"] != "panel", kv[1]["type"] or "", kv[0])):
            unit = self._price(ref)
            items.append({"component": ref, "name": (self._tga.get(ref) or {}).get("name"), "kind": row["kind"],
                          "type": row["type"], "count": row["count"], "area": row["area"], "unit_price": unit,
                          "price": unit * row["count"] if unit is not None else None})
        return items

    def _price(self, ref: str) -> Optional[float]:
        prices = [o["price"] for o in self._products.offers_of(ref) if JsonValues.is_number(o.get("price"))
                  and (o.get("currency") or "EUR") == "EUR"]
        return min(prices) if prices else None
