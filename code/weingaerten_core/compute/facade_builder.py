"""Board facade (Stülpschalung) on the exterior walls of a storey: rows, joints, cuts at the roof and openings."""
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from ..geometry.polygon import Polygon
from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from ..validation.class_validator import ClassValidator
from .facade_cutting import FacadeCutting

logger = logging.getLogger(__name__)

SIZE_KEYS = ("board_length", "board_width", "board_thickness")
SHIFTS = {"outside_face": 0.0, "center": 0.5, "inside_face": 1.0}
# visible shadow joint between two rows (3D only, quantities use the full board)
SHADOW = 0.004
EPS = 1e-6


class FacadeBuilder:
    """Builds `facade` of a storey from the serialized walls whose assembly has an outermost layer with
    `cladding`; a wall with an invalid cladding is reported and left out."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the loaded model (materials).
            issues: receives the facade errors and warnings.
        """
        self._model = model
        self._issues = issues

    def build(self, storey_ref: str, z0: float, walls: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Return the facade or None (no wall with a cladding layer).

        Args:
            storey_ref: storey reference.
            z0: storey elevation.
            walls: the serialized walls (profile storey-local, openings with `rough`).
        """
        self._z0 = z0
        first, rows_out, parts, lengths = None, [], [], []
        for wall in walls:
            spec = self._cladding("%s.%s" % (storey_ref, wall["id"]), wall)
            if spec is None:
                continue
            self._spec = spec
            first = first or spec
            summary, wall_parts, wall_lengths = self._wall(wall)
            rows_out.append(summary)
            parts.extend(wall_parts)
            lengths.extend(wall_lengths)
        return self._result(first, rows_out, parts, lengths) if first else None

    def _cladding(self, where: str, wall: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # the board facade is the first layer with `cladding` (layer_order outside_in); thin layers in front of
        # it (paint) are its coating: they give the colour and push the boards inwards by their thickness
        if wall["category"] != "exterior_wall":
            return None
        layers = [l for l in (self._model["elements"].get(wall["assembly"]) or {}).get("layers") or []
                  if isinstance(l, dict)]
        index = next((i for i, l in enumerate(layers) if isinstance(l.get("cladding"), dict)), None)
        if index is None:
            return None
        layer, coats = layers[index], layers[:index]
        paint = layer["cladding"].get("paint") or (coats[0].get("material") if coats else None)
        spec = dict(layer["cladding"], material=layer.get("material"), board_thickness=layer.get("thickness"),
                    assembly=wall["assembly"], paint=paint, layer=index,
                    depth=sum(float(l.get("thickness") or 0.0) for l in coats))
        return spec if self._checked(where, spec) else None

    def _checked(self, where: str, spec: Dict[str, Any]) -> bool:
        refs = [spec.get("material")] + ([spec["paint"]] if spec.get("paint") is not None else [])
        for ref in refs:
            if not ClassValidator.is_material(self._model, ref):
                self._issues.error(where, "unbekannt: %s" % ref)
                return False
        sizes = [spec.get(k) for k in SIZE_KEYS]
        overlap, bottom = spec.get("overlap"), spec.get("bottom", 0.0)
        if not (all(JsonValues.is_number(s) and s > 0 for s in sizes) and JsonValues.is_number(overlap)
                and 0 <= overlap < spec["board_width"] and JsonValues.is_number(bottom)):
            self._issues.error(where, "Maße ungültig")
            return False
        return True

    def _result(self, spec: Dict[str, Any], walls: List[Dict[str, Any]], parts: List[Dict[str, Any]],
                lengths: List[float]) -> Dict[str, Any]:
        width, thickness = float(spec["board_width"]), float(spec["board_thickness"])
        cover = width - float(spec["overlap"])
        area = sum(w["area"] for w in walls)
        cutting = FacadeCutting.plan(lengths, float(spec["board_length"]))
        board_area = area * width / cover
        return {"kind": spec.get("kind", "lap_siding"), "assembly": spec["assembly"], "material": spec["material"],
                "paint": spec.get("paint"), "estimated": bool(spec.get("estimated")),
                "board": {"length": float(spec["board_length"]), "width": width, "thickness": thickness},
                "overlap": float(spec["overlap"]), "cover": cover, "bottom": float(spec.get("bottom", 0.0)),
                "walls": walls, "parts": parts, "pieces": len(lengths), "length": cutting["used_length"],
                "area": area, "board_area": board_area, "volume": board_area * thickness,
                "boards": cutting["boards"], "stock_length": cutting["stock_length"],
                "waste_length": cutting["waste_length"], "waste_share": cutting["waste_share"],
                "paint_area": board_area if spec.get("paint") else 0.0}

    def _wall(self, wall: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[float]]:
        spec = self._spec
        cover, width = float(spec["board_width"]) - float(spec["overlap"]), float(spec["board_width"])
        bottom, board_length = float(spec.get("bottom", 0.0)), float(spec["board_length"])
        self._frame(wall)
        u_a, u_b = wall["u_range"]["outside"]
        profile = [(float(u), float(z)) for u, z in wall["profile"]]
        top = max(z for _, z in profile)
        holes = [(o["rough"]["u0"], o["rough"]["u1"], o["rough"]["zb"], o["rough"]["zt"]) for o in wall["openings"]]
        parts, lengths, area, rows = [], [], 0.0, 0
        k = 0
        while bottom + k * cover < top - 1e-3:
            z_lo = bottom + k * cover
            z_hi = z_lo + cover
            free = self._minus([(u_a, u_b)], [(h[0], h[1]) for h in holes if h[2] < z_lo + width and h[3] > z_lo])
            offset = 0.0 if k % 2 == 0 else board_length / 2.0
            row_used = False
            for a, b in self._split(free, u_a + offset, board_length):
                pieces = self._clip(a, b, z_lo, z_hi, profile)
                if not pieces:
                    continue
                row_used = True
                lengths.append(max(p[1] for p in pieces) - min(p[0] for p in pieces))
                for piece in pieces:
                    part, part_area = self._part(wall, k, len(parts), piece, z_lo, z_hi)
                    parts.append(part)
                    area += part_area
            rows += 1 if row_used else 0
            k += 1
        summary = {"wall": wall["id"], "name": wall.get("name"), "rows": rows, "pieces": len(lengths),
                   "length": sum(lengths), "area": area}
        return summary, parts, lengths

    def _frame(self, wall: Dict[str, Any]) -> None:
        start, end = wall["start"], wall["end"]
        length = math.hypot(end[0] - start[0], end[1] - start[1])
        d = ((end[0] - start[0]) / length, (end[1] - start[1]) / length)
        shift = SHIFTS.get(wall.get("reference"), 0.0) * wall["thickness"]
        self._geo = (start, d, tuple(wall["normal_in"]), shift)

    def _point(self, u: float, t: float) -> Tuple[float, float]:
        start, d, n, shift = self._geo
        return (start[0] + u * d[0] + (t - shift) * n[0], start[1] + u * d[1] + (t - shift) * n[1])

    @staticmethod
    def _minus(intervals: List[Tuple[float, float]], cuts: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        for c0, c1 in cuts:
            result = []
            for a, b in intervals:
                if c1 <= a or c0 >= b:
                    result.append((a, b))
                    continue
                if c0 > a + EPS:
                    result.append((a, c0))
                if c1 < b - EPS:
                    result.append((c1, b))
            intervals = result
        return intervals

    @staticmethod
    def _split(intervals: List[Tuple[float, float]], origin: float, step: float) -> List[Tuple[float, float]]:
        # butt joints on a grid; every second row shifted by half a board so the joints are staggered
        result = []
        for a, b in intervals:
            cuts = [origin + m * step for m in range(int(math.floor((a - origin) / step)) + 1,
                                                    int(math.ceil((b - origin) / step)))]
            edges = [a] + [c for c in cuts if a + EPS < c < b - EPS] + [b]
            result.extend((edges[i], edges[i + 1]) for i in range(len(edges) - 1))
        return result

    @staticmethod
    def _roof(profile: List[Tuple[float, float]], u: float) -> float:
        for (u0, z0), (u1, z1) in zip(profile, profile[1:]):
            if u0 - EPS <= u <= u1 + EPS:
                return z0 if u1 - u0 < EPS else z0 + (z1 - z0) * (u - u0) / (u1 - u0)
        return profile[0][1] if u < profile[0][0] else profile[-1][1]

    def _clip(self, a: float, b: float, z_lo: float, z_hi: float,
              profile: List[Tuple[float, float]]) -> List[Tuple[float, float, float, float]]:
        # pieces (u0, u1, top0, top1) of the row strip below the roof line; tops are storey-local
        edges = {a, b}
        edges.update(u for u, _ in profile if a < u < b)
        for (u0, r0), (u1, r1) in zip(profile, profile[1:]):
            if abs(r1 - r0) > EPS:
                for level in (z_lo, z_hi):
                    u = u0 + (level - r0) * (u1 - u0) / (r1 - r0)
                    if a < u < b and u0 < u < u1:
                        edges.add(u)
        ordered = sorted(edges)
        pieces = []
        for u0, u1 in zip(ordered, ordered[1:]):
            if u1 - u0 < 1e-4:
                continue
            t0, t1 = min(z_hi, self._roof(profile, u0)), min(z_hi, self._roof(profile, u1))
            if (t0 + t1) / 2.0 > z_lo + 1e-3:
                pieces.append((u0, u1, max(t0, z_lo), max(t1, z_lo)))
        return pieces

    def _part(self, wall: Dict[str, Any], row: int, index: int, piece: Tuple[float, float, float, float],
              z_lo: float, z_hi: float) -> Tuple[Dict[str, Any], float]:
        u0, u1, t0, t1 = piece
        thickness = float(self._spec["board_thickness"]) + float(self._spec["depth"])
        # the boards (with their coating) are the wall's outer layers: t [0, coat + board] from the outside face
        corners = [(u0, 0.0), (u1, 0.0), (u1, thickness), (u0, thickness)]
        footprint = Polygon.counter_clockwise([self._point(u, t) for u, t in corners])
        z_top = max(t0, t1)
        part = {"id": "%s-r%d-%d" % (wall["id"], row + 1, index + 1), "wall": wall["id"], "row": row + 1,
                "layer": self._spec["layer"],
                "material": self._spec["material"], "footprint": [list(p) for p in footprint],
                "z0": self._z0 + z_lo, "z1": self._z0 + (z_top - SHADOW if z_top >= z_hi - EPS else z_top),
                "top_plane": None, "length": u1 - u0, "color": self._color()}
        if abs(t1 - t0) > EPS:
            # the roof cut: plane through the two top points along the wall
            start, d, _, _ = self._geo
            s = (t1 - t0) / (u1 - u0)
            base = start[0] * d[0] + start[1] * d[1]
            part["top_plane"] = [s * d[0], s * d[1], self._z0 + t0 - s * u0 - s * base]
        return part, (u1 - u0) * ((t0 + t1) / 2.0 - z_lo)

    def _color(self) -> Optional[str]:
        ref = self._spec.get("paint") or self._spec["material"]
        return ((self._model["elements"].get(ref) or {}).get("appearance") or {}).get("color")
