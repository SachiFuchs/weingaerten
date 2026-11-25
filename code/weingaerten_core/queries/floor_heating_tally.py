"""BOM rows of the floor build-ups and the floor heating."""
import logging
from typing import Any, Dict, List

from .material_tally import MaterialTally

logger = logging.getLogger(__name__)


class FloorHeatingTally:
    """Turns the computed floors and heating of the storeys into BOM rows and adds their quantities."""

    def __init__(self, materials: MaterialTally, totals: Dict[str, float]) -> None:
        """Args:
            materials: receives the layer volumes and the visible floor area (top layer).
            totals: receives `floor_area`, `floor_volume` and `pipe_length`.
        """
        self._materials = materials
        self._totals = totals

    def floors(self, storey: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return one row per floor of the storey."""
        rows = []
        for floor in storey["floors"]:
            volume = 0.0
            for layer in floor["layers"]:
                self._materials.add(layer["material"], "volume", layer["volume"])
                volume += layer["volume"]
            if floor["layers"]:
                # the top of the first (top_down) layer is the walking surface until a covering is chosen
                self._materials.add(floor["layers"][0]["material"], "area_inside", floor["area"])
            self._totals["floor_area"] += floor["area"]
            self._totals["floor_volume"] += volume
            rows.append({"storey": storey["id"], "floor": floor["id"], "name": floor["name"],
                         "assembly": floor["assembly"], "area": floor["area"], "edge_length": floor["edge_length"],
                         "thickness": floor["thickness"], "volume": volume,
                         "rooms": [{"name": r["name"], "area": r["area"], "edge_length": r["edge_length"]}
                                   for r in floor["rooms"]],
                         "layers": [{"index": layer["index"], "material": layer["material"],
                                     "thickness": layer["thickness"], "area": layer["area"], "volume": layer["volume"],
                                     "heated": layer["heated"]} for layer in floor["layers"]],
                         "offer": floor["offer"]})
        return rows

    def heating(self, storey: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return one row for the heating of the storey (empty without heating)."""
        heating = storey.get("heating")
        if not heating:
            return []
        self._totals["pipe_length"] += heating["length"]
        return [{"storey": storey["id"], "name": heating["name"], "pipe": heating["pipe"],
                 "pipe_diameter": heating["pipe_diameter"], "estimated": heating["estimated"],
                 "area": heating["area"], "length": heating["length"],
                 "circuits": [{"id": c["id"], "name": c["name"], "room": c["room"], "pattern": c["pattern"],
                               "spacing": c["spacing"], "area": c["area"], "length_field": c["length_field"],
                               "length_feed": c["length_feed"], "length": c["length"]}
                              for c in heating["circuits"]]}]
