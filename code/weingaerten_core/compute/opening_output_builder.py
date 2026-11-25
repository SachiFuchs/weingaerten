"""Output of the openings of a wall: rough opening, plan points, reveals and component parts."""
import logging
import math
from typing import Any, Dict, List

from ..constants import TOLERANCE
from .opening_data import OpeningData
from .opening_parts_builder import OpeningPartsBuilder
from .wall_data import WallData
from .window_panes import WindowPanes

logger = logging.getLogger(__name__)


class OpeningOutputBuilder:
    """Builds the HOUSE answer of every opening of a wall."""

    def __init__(self, z0: float) -> None:
        """Args:
            z0: storey elevation.
        """
        self._z0 = z0

    def build(self, wall: WallData) -> List[Dict[str, Any]]:
        """Return the opening objects of the wall in order."""
        return [self._opening(wall, opening) for opening in wall.openings]

    def _opening(self, wall: WallData, opening: OpeningData) -> Dict[str, Any]:
        u0, u1, z_bottom, z_top = opening.u0, opening.u1, opening.z_bottom, opening.z_top
        thickness = wall.thickness
        reveals = self._reveals(wall, opening) if opening.reveal_material else []
        parts = OpeningPartsBuilder(wall, opening, self._z0).build()
        params = opening.params
        return {"id": opening.id, "component": opening.component_ref, "name": opening.component.get("name"),
                "class": opening.component.get("class"), "geometry": opening.geometry, "params": params,
                "offset": opening.source.get("offset"), "offset_right": wall.length - u1,
                "sill": opening.source.get("sill"), "joint": opening.joint, "inset": opening.inset,
                "reveal_material": opening.reveal_material,
                "rough": {"u0": u0, "u1": u1, "zb": z_bottom, "zt": z_top, "width": u1 - u0,
                          "height": z_top - z_bottom, "area": (u1 - u0) * (z_top - z_bottom)},
                "plan": {"outside": [self._plan_point(wall, u0, 0.0), self._plan_point(wall, u1, 0.0)],
                         "inside": [self._plan_point(wall, u0, thickness), self._plan_point(wall, u1, thickness)]},
                "swing": params.get("swing"), "sashes": params.get("sashes"),
                "pane_openings": WindowPanes.opening_types(params) if opening.geometry == "window" else None,
                "reveals": reveals, "parts": parts}

    @staticmethod
    def _plan_point(wall: WallData, u: float, t: float) -> List[float]:
        point = wall.base(t)
        return [point[0] + wall.direction[0] * u, point[1] + wall.direction[1] * u]

    def _reveals(self, wall: WallData, opening: OpeningData) -> List[Dict[str, Any]]:
        # reveals cover the wall depth in front of and behind the component
        u0, u1, z_bottom, z_top = opening.u0, opening.u1, opening.z_bottom, opening.z_top
        thickness = wall.thickness
        zones = [(0.0, opening.inset), (opening.inset + opening.depth, thickness)]
        sides = [("left", [(u0, z_bottom), (u0, z_top)]), ("right", [(u1, z_bottom), (u1, z_top)]),
                 ("top", [(u0, z_top), (u1, z_top)])]
        if z_bottom > TOLERANCE:
            sides.append(("bottom", [(u0, z_bottom), (u1, z_bottom)]))
        reveals = []
        for name, ((u_a, z_a), (u_b, z_b)) in sides:
            quads = []
            for t0, t1 in zones:
                if t1 - t0 > 1e-6:
                    quads.append([wall.point_3d(u_a, t0, z_a, self._z0), wall.point_3d(u_b, t0, z_b, self._z0),
                                  wall.point_3d(u_b, t1, z_b, self._z0), wall.point_3d(u_a, t1, z_a, self._z0)])
            side_length = math.hypot(u_b - u_a, z_b - z_a)
            reveals.append({"side": name, "material": opening.reveal_material,
                            "area": side_length * (thickness - opening.depth), "quads": quads})
        return reveals
