"""Placement of an installed part: its local frame (x, y in the wall plane, w out of the wall) in world coordinates."""
import logging
import math
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

Vector = List[float]
FIRST_FACES = ("outside", "left")      # t = 0 side of the wall (outside of exterior, left of interior walls)
FACES = {"exterior_wall": ("outside", "inside"), "interior_wall": ("left", "right")}


class PartFrame:
    """World origin and axes of a part; the same formula is used by the wall view in the browser (install.js)."""

    def __init__(self, origin: Vector, x: Vector, y: Vector, w: Vector) -> None:
        """Args:
            origin: world point of the local origin.
            x, y, w: world unit vectors of the local axes.
        """
        self.origin = origin
        self.x = x
        self.y = y
        self.w = w

    def point(self, local: Vector) -> Vector:
        """Return the world point of a local point."""
        return [self.origin[i] + local[0] * self.x[i] + local[1] * self.y[i] + local[2] * self.w[i] for i in range(3)]

    def vector(self, local: Vector) -> Vector:
        """Return the world direction of a local direction."""
        return [local[0] * self.x[i] + local[1] * self.y[i] + local[2] * self.w[i] for i in range(3)]

    @staticmethod
    def face_depth(wall: Dict[str, Any], face: str) -> tuple:
        """Return (t of the face plane along normal_in, sign of the outward normal) of a wall face."""
        start, n = wall["start"], wall["normal_in"]
        ts = [(p[0] - start[0]) * n[0] + (p[1] - start[1]) * n[1] for p in wall["footprint"]]
        return (min(ts), -1.0) if face in FIRST_FACES else (max(ts), 1.0)

    @staticmethod
    def direction(wall: Dict[str, Any]) -> Vector:
        """Return the unit plan direction of the wall reference line."""
        dx, dy = wall["end"][0] - wall["start"][0], wall["end"][1] - wall["start"][1]
        length = math.hypot(dx, dy)
        return [dx / length, dy / length]

    @staticmethod
    def rotated(local: Vector, rot: Dict[str, Any]) -> Vector:
        """Apply flip (x -> -x), plane rotation (about w), tilt (about the wall's horizontal x) and turn (about the
        vertical y) to a local vector: tilt and turn point a part into or out of the wall."""
        x, y, w = local
        if rot.get("flip"):
            x = -x
        plane, tilt, turn = (math.radians(float(rot.get(k) or 0.0)) for k in ("plane", "tilt", "turn"))
        x, y = x * math.cos(plane) - y * math.sin(plane), x * math.sin(plane) + y * math.cos(plane)
        y, w = y * math.cos(tilt) - w * math.sin(tilt), y * math.sin(tilt) + w * math.cos(tilt)
        x, w = x * math.cos(turn) + w * math.sin(turn), -x * math.sin(turn) + w * math.cos(turn)
        return [x, y, w]

    @classmethod
    def on_wall(cls, wall: Dict[str, Any], part: Dict[str, Any]) -> "PartFrame":
        """Frame of a part hosted on a wall face: u along the wall, z above the storey floor, depth out of the face."""
        d, n = cls.direction(wall), wall["normal_in"]
        t, sign = cls.face_depth(wall, part["host"]["face"])
        e_u, e_z, e_out = [d[0], d[1], 0.0], [0.0, 0.0, 1.0], [sign * n[0], sign * n[1], 0.0]
        start = wall["start"]
        u, depth = float(part["u"]), float(part["depth"])
        origin = [start[0] + d[0] * u + n[0] * t + e_out[0] * depth,
                  start[1] + d[1] * u + n[1] * t + e_out[1] * depth, float(wall["z0"]) + float(part["z"])]
        rot = part.get("rot") or {}
        axes = []
        for local in ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]):
            r = cls.rotated(local, rot)
            axes.append([r[0] * e_u[i] + r[1] * e_z[i] + r[2] * e_out[i] for i in range(3)])
        return cls(origin, *axes)

    @classmethod
    def free(cls, part: Dict[str, Any]) -> Optional["PartFrame"]:
        """Frame of a free part from `position` and `axes {x, y}` (y is made orthogonal to x); None if degenerate."""
        x, y = cls._unit(part["axes"]["x"]), part["axes"]["y"]
        if x is None:
            return None
        dot = sum(x[i] * y[i] for i in range(3))
        y = cls._unit([y[i] - dot * x[i] for i in range(3)])
        if y is None:
            return None
        w = [x[1] * y[2] - x[2] * y[1], x[2] * y[0] - x[0] * y[2], x[0] * y[1] - x[1] * y[0]]
        return cls([float(v) for v in part["position"]], x, y, w)

    @staticmethod
    def _unit(vector: Any) -> Optional[Vector]:
        length = math.sqrt(sum(float(v) ** 2 for v in vector))
        return [float(v) / length for v in vector] if length > 1e-9 else None
