"""BOM rows of the rooms (DIN 277), their coverings (Beläge) and the shafts."""
import logging
from typing import Any, Dict, List

from .material_tally import MaterialTally

logger = logging.getLogger(__name__)

LAYER_KEYS = ("material", "thickness", "area", "volume")


class CoveringTally:
    """Adds the covering layers to the materials and the totals; returns the `rooms`, `coverings` and `shafts` rows."""

    def __init__(self, materials: MaterialTally, totals: Dict[str, Any]) -> None:
        """Args:
            materials: the material tally of the BOM.
            totals: the BOM totals (`room_area`, `room_volume`, `covering_floor_area`, `covering_wall_area`,
                `covering_wall_length`, `covering_volume`, `shaft_cut_area` are added up).
        """
        self._materials = materials
        self._totals = totals

    def room(self, storey: Dict[str, Any], room: Dict[str, Any]) -> Dict[str, Any]:
        """Return the BOM row of a room (area and volume per DIN 277 usage are summed by the web page)."""
        self._totals["room_area"] += room["area"]
        self._totals["room_volume"] += room["volume"]
        return {"room": room["id"], "storey": storey["id"], "number": room["number"], "name": room["name"],
                "usage": room["usage"], "usage_name": room["usage_name"], "floor_area": room["area"],
                "perimeter": room["perimeter"], "height": room["height"], "volume": room["volume"],
                "wall_area": room["wall_area"]}

    def rows(self, storey: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return one row per covering of the rooms of the storey."""
        return [self._row(storey, room, covering) for room in storey["rooms"] for covering in room.get("coverings") or []]

    def _row(self, storey: Dict[str, Any], room: Dict[str, Any], covering: Dict[str, Any]) -> Dict[str, Any]:
        # every layer counts with its volume and its net area (laid flat on the floor or the wall)
        for layer in covering["layers"]:
            self._materials.add(layer["material"], "volume", layer["volume"])
            self._materials.add(layer["material"], "area_inside", layer["area"])
        floor = covering["surface"] == "floor"
        self._totals["covering_floor_area" if floor else "covering_wall_area"] += covering["area"]
        if not floor:
            self._totals["covering_wall_length"] += covering["length"]
        self._totals["covering_volume"] += covering["volume"]
        return {"storey": storey["id"], "room": room["id"], "room_number": room["number"], "room_name": room["name"],
                "covering": covering["id"], "name": covering["name"], "surface": covering["surface"],
                "scope": covering["scope"], "assembly": covering["assembly"],
                "assembly_name": covering["assembly_name"], "area": covering["area"],
                "length": None if floor else covering["length"], "thickness": covering["thickness"],
                "volume": covering["volume"], "estimated": covering["estimated"],
                "layers": [{key: layer[key] for key in LAYER_KEYS} for layer in covering["layers"]]}

    def shafts(self, shafts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return one row per shaft with its cut areas."""
        rows = []
        for shaft in shafts:
            self._totals["shaft_cut_area"] += shaft["cut_area"]
            rows.append({"shaft": shaft["id"], "name": shaft["name"], "purpose": shaft["purpose"],
                         "from_storey": shaft["from_storey"], "to_storey": shaft["to_storey"], "area": shaft["area"],
                         "cuts": shaft["cuts"], "cut_area": shaft["cut_area"], "penetrations": shaft["penetrations"],
                         "estimated": shaft["estimated"]})
        return rows
