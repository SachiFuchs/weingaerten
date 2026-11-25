"""BOM rows of the interior linings (Innendämmung) of a storey."""
import logging
from typing import Any, Dict, List

from .material_tally import MaterialTally

logger = logging.getLogger(__name__)

LAYER_KEYS = ("material", "thickness", "area", "volume")
ROW_KEYS = ("wall", "wall_name", "face", "assembly", "u0", "u1", "z0", "z1", "gross_area", "opening_area", "area",
            "thickness", "volume", "openings")


class LiningTally:
    """Adds the lining layers to the materials and the totals and returns the `linings` rows."""

    def __init__(self, materials: MaterialTally, totals: Dict[str, Any]) -> None:
        """Args:
            materials: the material tally of the BOM.
            totals: the BOM totals (`lining_area`, `lining_volume` are added up).
        """
        self._materials = materials
        self._totals = totals

    def rows(self, storey: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return one row per lining of the storey."""
        return [self._row(storey, lining) for lining in storey.get("linings") or []]

    def _row(self, storey: Dict[str, Any], lining: Dict[str, Any]) -> Dict[str, Any]:
        # every layer counts with its volume and its net area (glue, boards, plaster and paint are laid flat)
        for layer in lining["layers"]:
            self._materials.add(layer["material"], "volume", layer["volume"])
            self._materials.add(layer["material"], "area_inside", layer["area"])
        self._totals["lining_area"] += lining["area"]
        self._totals["lining_volume"] += lining["volume"]
        row = {"storey": storey["id"], "lining": lining["id"]}
        row.update({key: lining[key] for key in ROW_KEYS})
        row["layers"] = [{key: layer[key] for key in LAYER_KEYS} for layer in lining["layers"]]
        return row
