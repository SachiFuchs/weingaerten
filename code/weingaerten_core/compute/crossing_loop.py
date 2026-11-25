"""Crossing loops (Kreuzungsschleifen): where two pressure pipes cross in front of a wall, one of them bends
around the other with four 45° bends (out, along, back)."""
import logging
import math
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

CLEARANCE = 0.01       # gap between the pipe surfaces at the loop
MIN_CROSS_ANGLE = 30.0  # nearly parallel pipes do not cross
FREE_END = 0.02        # straight pipe kept between loop and the next corner (fittings need room)
EPS = 1e-9

Vec = List[float]


def _sub(a: Vec, b: Vec) -> Vec:
    return [a[i] - b[i] for i in range(3)]


def _dot(a: Vec, b: Vec) -> float:
    return sum(a[i] * b[i] for i in range(3))


def _cross(a: Vec, b: Vec) -> Vec:
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def _unit(a: Vec) -> Vec:
    n = math.sqrt(_dot(a, a)) or 1.0
    return [v / n for v in a]


def closest(p0: Vec, p1: Vec, q0: Vec, q1: Vec) -> Tuple[float, float, float]:
    """Return (distance, s, t) of the closest points p0 + s (p1 - p0) and q0 + t (q1 - q0), s, t in [0, 1]."""
    d1, d2, r = _sub(p1, p0), _sub(q1, q0), _sub(p0, q0)
    a, e, f = _dot(d1, d1), _dot(d2, d2), _dot(d2, r)
    c, b = _dot(d1, r), _dot(d1, d2)
    denom = a * e - b * b
    s = max(0.0, min(1.0, (b * f - c * e) / denom)) if denom > EPS else 0.0
    t = (b * s + f) / e if e > EPS else 0.0
    if t < 0.0 or t > 1.0:
        t = max(0.0, min(1.0, t))
        s = max(0.0, min(1.0, (b * t - c) / a)) if a > EPS else 0.0
    pa = [p0[i] + d1[i] * s for i in range(3)]
    pb = [q0[i] + d2[i] * t for i in range(3)]
    return math.dist(pa, pb), s, t


class CrossingLoop:
    """Finds crossings between runs and inserts the loop points into the run with more room around it."""

    def __init__(self, side: Callable[[Vec, Vec], Vec]) -> None:
        """Args:
            side: (crossing point, offset direction) -> the direction or its opposite; loops bend away from the wall.
        """
        self._side = side

    def apply(self, runs: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Change run["points"] in place; return (loops, problems) - problems are crossings without room."""
        loops, problems = [], []
        for i, a in enumerate(runs):
            for b in runs[i + 1:]:
                found = self._crossing(a, b)
                while found:
                    result = self._loop(a, b, *found, runs)
                    (loops if result.get("points") else problems).append(result)
                    if not result.get("points"):
                        break
                    found = self._crossing(a, b)
        return loops, problems

    @staticmethod
    def _crossing(a: Dict[str, Any], b: Dict[str, Any]) -> Optional[tuple]:
        need = (a["outer_diameter"] + b["outer_diameter"]) / 2 + CLEARANCE / 2
        for ia in range(len(a["points"]) - 1):
            for ib in range(len(b["points"]) - 1):
                pa0, pa1, pb0, pb1 = a["points"][ia], a["points"][ia + 1], b["points"][ib], b["points"][ib + 1]
                da, db = _unit(_sub(pa1, pa0)), _unit(_sub(pb1, pb0))
                angle = math.degrees(math.acos(min(1.0, abs(_dot(da, db)))))
                if angle < MIN_CROSS_ANGLE:
                    continue
                distance, s, t = closest(pa0, pa1, pb0, pb1)
                if distance < need and 0.0 < s < 1.0 and 0.0 < t < 1.0:
                    return ia, s, ib, t
        return None

    def _loop(self, a: Dict[str, Any], b: Dict[str, Any], ia: int, s: float, ib: int, t: float,
              runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        # the run with more straight pipe on both sides of the crossing (corners and branch points) makes the loop
        room_a, room_b = self._room(a, ia, s, runs), self._room(b, ib, t, runs)
        mover, other, index, u, room = (a, b, ia, s, room_a) if room_a >= room_b else (b, a, ib, t, room_b)
        p0, p1 = mover["points"][index], mover["points"][index + 1]
        d = _unit(_sub(p1, p0))
        q0, q1 = (other["points"][ib], other["points"][ib + 1]) if mover is a else (other["points"][ia],
                                                                                       other["points"][ia + 1])
        centre = [p0[i] + (p1[i] - p0[i]) * u for i in range(3)]
        n = self._side(centre, _unit(_cross(d, _unit(_sub(q1, q0)))))
        offset = (mover["outer_diameter"] + other["outer_diameter"]) / 2 + CLEARANCE
        along = mover["outer_diameter"] / 2
        info = {"run": mover["id"], "run_name": mover["name"], "other": other["id"], "other_name": other["name"],
                "position": [round(v, 4) for v in centre], "offset": offset, "segment": index}
        if room < offset + along + FREE_END:
            info["room"] = room
            return info
        at = lambda k, side: [centre[i] + d[i] * k + n[i] * side for i in range(3)]  # noqa: E731
        points = [at(-(offset + along), 0.0), at(-along, offset), at(along, offset), at(offset + along, 0.0)]
        mover["points"][index + 1:index + 1] = [[round(v, 4) for v in p] for p in points]
        info["points"] = mover["points"][index + 1:index + 5]
        return info

    @staticmethod
    def _room(run: Dict[str, Any], index: int, u: float, runs: List[Dict[str, Any]]) -> float:
        # free length from the crossing to the segment ends or to the nearest branch end of another run on it
        p0, p1 = run["points"][index], run["points"][index + 1]
        length = math.dist(p0, p1)
        d = _sub(p1, p0)
        marks = [0.0, 1.0]
        for other in runs:
            if other is not run:
                end = other["points"][-1]
                t = max(0.0, min(1.0, _dot(_sub(end, p0), d) / (_dot(d, d) or EPS)))
                if math.dist(end, [p0[i] + d[i] * t for i in range(3)]) < 0.01:
                    marks.append(t)
        return min(abs(u - m) for m in marks) * length
