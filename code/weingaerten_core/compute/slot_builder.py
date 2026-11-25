"""Slots (Schlitze) and box cutouts of parts that lie inside their host wall, with the removed volume per layer."""
import logging
import math
from typing import Any, Dict, List, Optional

from ..model.issue_log import IssueLog
from .part_frame import FIRST_FACES, PartFrame

logger = logging.getLogger(__name__)

SLOT_MARGIN = 0.01   # the slot is 1 cm wider than the pipe (mortar bed)
# reference depths for slots without static proof in the load-bearing layer (DIN EN 1996-1-1/NA, simplified, estimated)
LIMITS = {"vertical": 0.03, "horizontal": 0.015, "oblique": 0.015, "hole": 0.03}


class SlotBuilder:
    """Turns the parts below the face of their host wall into slot rows."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the computed model (storeys_out).
            issues: receives the warnings for too deep slots.
        """
        self._model = model
        self._issues = issues
        self._walls = {(s["id"], w["id"]): w for s in model.get("storeys_out") or [] for w in s["walls"]}

    def slots(self, parts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return one row per pipe leg or box that reaches into its host wall (through-going pieces excluded)."""
        rows = []
        for part in parts:
            host = part["host"]
            wall = self._walls.get((part["storey"], host["wall"])) if host else None
            if wall is None:
                continue
            for piece in self._pieces(part, wall):
                row = self._row(part, wall, piece)
                if row:
                    rows.append(row)
        return rows

    def _pieces(self, part: Dict[str, Any], wall: Dict[str, Any]) -> List[Dict[str, Any]]:
        depth_of = self._depth_function(wall, part["host"]["face"])
        if part["shape"] in ("box", "insert"):
            width, height, box_depth = part["size"] or (0.0, 0.0, 0.0)
            front = depth_of(part["origin"])
            if part["shape"] == "insert" or front - box_depth >= 0:
                return []
            return [{"kind": "cutout", "direction": "hole", "length": height, "width": width,
                     "depth": min(-(front - box_depth), float(wall["thickness"]))}]
        radius = (part["outer_diameter"] or 0.02) / 2.0
        pieces = []
        for a, b in part["legs"]:
            inner = min(depth_of(a), depth_of(b)) - radius
            if inner >= 0:
                continue
            du = abs(self._along(wall, a, b))
            dz = abs(b[2] - a[2])
            plane = math.hypot(du, dz)
            direction = "hole" if plane < 2 * radius else ("vertical" if dz >= du else
                                                             ("horizontal" if dz < 0.2 * du else "oblique"))
            pieces.append({"kind": "slot", "direction": direction, "length": plane + 2 * radius,
                           "width": 2 * radius + SLOT_MARGIN, "depth": min(-inner, float(wall["thickness"]))})
        return pieces

    @staticmethod
    def _along(wall: Dict[str, Any], a: List[float], b: List[float]) -> float:
        d = PartFrame.direction(wall)
        return (b[0] - a[0]) * d[0] + (b[1] - a[1]) * d[1]

    @staticmethod
    def _depth_function(wall: Dict[str, Any], face: str) -> Any:
        t_face, sign = PartFrame.face_depth(wall, face)
        start, n = wall["start"], wall["normal_in"]
        return lambda p: ((p[0] - start[0]) * n[0] + (p[1] - start[1]) * n[1] - t_face) * sign

    def _row(self, part: Dict[str, Any], wall: Dict[str, Any], piece: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        thickness, depth = float(wall["thickness"]), piece["depth"]
        if depth >= thickness - 0.002:
            return None  # through the whole wall: a penetration, not a slot
        first = part["host"]["face"] in FIRST_FACES
        low, high = (0.0, depth) if first else (thickness - depth, thickness)
        area = piece["length"] * piece["width"]
        layers, bearing = [], self._bearing_layer(wall)
        bearing_depth = 0.0
        for layer in wall["layers"]:
            a, b = float(layer["offset"]), float(layer["offset"]) + float(layer["thickness"])
            overlap = min(b, high) - max(a, low)
            if overlap <= 1e-6:
                continue
            layers.append({"index": layer["index"], "material": layer["material"], "depth": overlap,
                           "volume": area * overlap})
            if layer["index"] == bearing:
                bearing_depth = overlap
        limit = LIMITS[piece["direction"]] if piece["kind"] == "slot" else None
        over = limit is not None and bearing_depth > limit + 1e-6
        if over:
            self._issues.warning("tga-part:" + part["id"], "Schlitz %.1f cm tief in der tragenden Schicht von %s "
                                 "(Richtwert %.1f cm, geschätzt)" % (bearing_depth * 100, wall.get("name") or wall["id"],
                                                                   limit * 100))
        return {"part": part["id"], "component": part["component"], "component_name": part["component_name"],
                "storey": part["storey"], "wall": wall["id"], "wall_name": wall.get("name"), "face": part["host"]["face"],
                "kind": piece["kind"], "direction": piece["direction"], "length": piece["length"],
                "width": piece["width"], "depth": depth, "volume": area * depth, "bearing_depth": bearing_depth,
                "limit": limit, "over_limit": over, "layers": layers, "estimated": True}

    @staticmethod
    def _bearing_layer(wall: Dict[str, Any]) -> Optional[int]:
        # assumption: the thickest layer carries the load
        layers = wall.get("layers") or []
        return max(layers, key=lambda l: float(l["thickness"]))["index"] if layers else None
