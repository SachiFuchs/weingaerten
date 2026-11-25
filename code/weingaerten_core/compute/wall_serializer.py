"""Converts a computed wall into its HOUSE answer object."""
import logging
from typing import Any, Dict

from .wall_data import WallData

logger = logging.getLogger(__name__)


class WallSerializer:
    """Builds the `walls[]` entries of a storey."""

    @staticmethod
    def to_json(wall: WallData, z0: float) -> Dict[str, Any]:
        """Return the wall object (keys in answer order).

        Args:
            wall: the computed wall.
            z0: storey elevation (the wall's own height gives z1).
        """
        first_range, second_range = wall.u_ranges[0.0], wall.u_ranges[wall.thickness]
        if wall.is_exterior:
            u_range = {"outside": list(first_range), "inside": list(second_range)}
        else:
            u_range = {"left": list(first_range), "right": list(second_range)}
        source = wall.source
        return {"id": wall.id, "name": source.get("name"), "assembly": wall.info["ref"], "category": wall.category,
                "start": list(wall.start), "end": list(wall.end), "reference": source.get("reference"), "shape": source.get("shape") or {"kind": "rect"},
                "outside": source.get("outside"), "free_ends": list(source.get("free_ends") or []), "length": wall.length, "ref_length": wall.length,
                "direction": wall.degrees, "normal_in": list(wall.normal), "thickness": wall.thickness,
                "height": wall.height, "z0": z0, "z1": z0 + wall.height, "profile": wall.profile(*first_range),
                "footprint": [list(p) for p in wall.footprint],
                "u_range": u_range, "layers": wall.layers, "faces": wall.faces, "openings": wall.openings_out}
