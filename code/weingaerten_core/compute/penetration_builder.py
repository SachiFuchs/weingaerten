"""Penetrations (Durchbrüche) of TGA runs through walls, ceilings, floors and the foundation slab."""
import logging
import math
from typing import Any, Dict, List, Optional

from ..geometry.segment_prism import SegmentPrism
from ..model.issue_log import IssueLog

logger = logging.getLogger(__name__)

MIN_HIT = 0.005          # shorter hits are touches, not penetrations
EMBEDDED_FACTOR = 3.0    # a hit longer than 3 x element thickness runs inside the element
DRILL_MARGIN = 0.02      # core drill = outer diameter + 2 cm, rounded up to cm
OVERRIDE_KEYS = ("fire_stop_type", "sealing", "done", "note")


class PenetrationBuilder:
    """Intersects run segments with the computed building elements."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the computed model (storeys_out, foundation, foundation_spec, tga.penetrations).
            issues: receives warnings for orphaned overrides.
        """
        self._model = model
        self._issues = issues

    def build(self, runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return every penetration and embedded stretch of the runs, with the stored overrides merged."""
        result = self.hits(runs)
        self._merge_overrides(result)
        return result

    def hits(self, runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return the penetrations and embedded stretches of the runs without the overrides of penetrations.json."""
        bodies = self._bodies()
        result = []
        for run in runs:
            counter: Dict[str, int] = {}
            for hit in self._run_hits(run, bodies):
                if hit["kind"] == "through":
                    hit["index"] = counter.get(hit["element"], 0)
                    counter[hit["element"]] = hit["index"] + 1
                result.append(hit)
        return result

    def _bodies(self) -> List[Dict[str, Any]]:
        bodies = []
        for storey in self._model.get("storeys_out") or []:
            sid = storey["id"]
            for wall in storey.get("walls") or []:
                bodies.append(self._body("wall:%s/%s" % (sid, wall["id"]), wall.get("name") or wall["id"], "wall",
                                         wall["footprint"], wall["z0"], wall["z1"], wall["thickness"],
                                         wall.get("category") == "exterior_wall", storey))
            for ceiling in storey.get("ceilings") or []:
                joists = ceiling.get("joists") or {}
                top = ceiling["z_top"] + float(joists.get("height") or 0.0)
                bodies.append(self._body("ceiling:%s/%s" % (sid, ceiling["id"]), ceiling.get("name") or ceiling["id"],
                                         "ceiling", ceiling["polygon"], ceiling["z_bottom"], top,
                                         top - ceiling["z_bottom"], "dach" in (ceiling.get("name") or "").lower(),
                                         storey))
            for floor in storey.get("floors") or []:
                for room in floor.get("rooms") or []:
                    for x, y, w, h in room.get("rects") or []:
                        bodies.append(self._body("floor:%s/%s" % (sid, floor["id"]), floor.get("name") or floor["id"],
                                                 "floor", [(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
                                                 floor["z_bottom"], floor["z_top"], floor["thickness"], False, storey))
        slab = self._foundation_body()
        if slab:
            bodies.append(slab)
        return bodies

    @staticmethod
    def _body(element: str, name: str, kind: str, polygon: Any, z0: float, z1: float, thickness: float,
              exterior: bool, storey: Dict[str, Any]) -> Dict[str, Any]:
        return {"element": element, "name": name, "kind": kind, "polygon": [tuple(p) for p in polygon],
                "z0": float(z0), "z1": float(z1), "thickness": float(thickness), "exterior": exterior,
                "storey": storey["id"], "cutouts": []}

    def _foundation_body(self) -> Optional[Dict[str, Any]]:
        spec = self._model.get("foundation_spec")
        if not spec:
            return None
        built = self._model.get("foundation")
        polygon = built["polygon"] if built else (spec.get("poly") or self._ground_bbox())
        if not polygon:
            return None
        thickness = float(spec["info"]["thickness"])
        return {"element": "foundation:main", "name": spec.get("name") or "Bodenplatte", "kind": "foundation",
                "polygon": [tuple(p) for p in polygon], "z0": spec["top"] - thickness, "z1": spec["top"],
                "thickness": thickness, "exterior": True, "storey": None, "cutouts": spec.get("cutouts") or []}

    def _ground_bbox(self) -> Optional[List[tuple]]:
        # the foundation follows the outline; when the outline is not closed the exterior walls give its extent
        top = self._model["foundation_spec"]["top"]
        points = [p for s in self._model.get("storeys_out") or [] if abs(s.get("elevation", 0) - top) < 1e-6
                  for w in s.get("walls") or [] if w.get("category") == "exterior_wall" for p in w["footprint"]]
        if not points:
            return None
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        return [(min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))]

    def _run_hits(self, run: Dict[str, Any], bodies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        points = run["points"]
        pieces = []
        for index in range(len(points) - 1):
            p0, p1 = points[index], points[index + 1]
            for body in bodies:
                for t0, t1 in SegmentPrism.intervals(p0, p1, body["polygon"], body["z0"], body["z1"]):
                    pieces.append((index, t0, t1, body))
        pieces.sort(key=lambda piece: (piece[0], piece[1]))
        merged: List[list] = []
        for piece in pieces:
            same = [m for m in merged if m[3]["element"] == piece[3]["element"] and self._continues(m, piece)]
            if same:
                same[-1][4].append(piece)
            else:
                merged.append([piece[0], piece[1], piece[2], piece[3], [piece]])
        return [h for h in (self._hit(run, m) for m in merged) if h]

    @staticmethod
    def _continues(group: list, piece: tuple) -> bool:
        last = group[4][-1]
        return (last[0] == piece[0] and abs(last[2] - piece[1]) < 1e-6) or \
            (last[0] + 1 == piece[0] and last[2] > 1 - 1e-6 and piece[1] < 1e-6)

    def _hit(self, run: Dict[str, Any], group: list) -> Optional[Dict[str, Any]]:
        body, pieces = group[3], group[4]
        points = run["points"]
        length, plan, rise = 0.0, 0.0, 0.0
        for index, t0, t1, _ in pieces:
            a = SegmentPrism.point(points[index], points[index + 1], t0)
            b = SegmentPrism.point(points[index], points[index + 1], t1)
            length += math.dist(a, b)
            plan += math.hypot(b[0] - a[0], b[1] - a[1])
            rise += abs(b[2] - a[2])
        if length < MIN_HIT:
            return None
        first, last = pieces[0], pieces[-1]
        start = SegmentPrism.point(points[first[0]], points[first[0] + 1], first[1])
        end = SegmentPrism.point(points[last[0]], points[last[0] + 1], last[2])
        middle = [(start[i] + end[i]) / 2.0 for i in range(3)]
        if any(_inside(middle, cutout) for cutout in body["cutouts"]):
            return None
        kind = "embedded" if length > EMBEDDED_FACTOR * body["thickness"] or self._along(body, plan, rise) else "through"
        direction = "vertical" if plan < 0.2 * length else ("horizontal" if rise < 0.2 * length else "oblique")
        od = run["outer_diameter"]
        return {"element": body["element"], "element_name": body["name"], "element_kind": body["kind"],
                "storey": body["storey"], "source": "tga-run:" + run["id"], "run": run["id"], "run_name": run["name"],
                "kind": kind, "dn": run["dn"], "outer_diameter": od, "line": run["line"],
                "core_drill": math.ceil(round((od + DRILL_MARGIN) * 100, 6)) / 100.0, "position": middle,
                "length": length, "direction": direction, "airtight": body["exterior"],
                "estimated": bool(run.get("estimated"))}

    @staticmethod
    def _along(body: Dict[str, Any], plan: float, rise: float) -> bool:
        # a pipe lying in a slab or standing in a wall runs along the element instead of crossing its thickness
        if body["kind"] == "wall":
            return plan < rise
        return rise < plan

    def _merge_overrides(self, hits: List[Dict[str, Any]]) -> None:
        by_key = {(h["element"], h["source"], h.get("index")): h for h in hits if h["kind"] == "through"}
        for number, item in enumerate((self._model.get("tga") or {}).get("penetrations") or []):
            hit = by_key.get((item.get("element"), item.get("source"), item.get("index")))
            if hit is None:
                self._issues.warning("house/penetrations.json.items.%d" % number,
                                     "verwaist: %s / %s #%s" % (item.get("element"), item.get("source"),
                                                                item.get("index")))
                continue
            for key in OVERRIDE_KEYS:
                if key in item:
                    hit[key] = item[key]


def _inside(point: List[float], rect_polygon: List[tuple]) -> bool:
    xs, ys = [p[0] for p in rect_polygon], [p[1] for p in rect_polygon]
    return min(xs) <= point[0] <= max(xs) and min(ys) <= point[1] <= max(ys)
