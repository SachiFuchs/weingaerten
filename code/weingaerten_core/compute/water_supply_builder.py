"""Drinking water (Zuwasser): TGA runs with medium cold_water | hot_water | circulation, their terminals,
crossing loops, fittings, cut pipes and penetrations."""
import logging
import math
from typing import Any, Dict, List, Optional

from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from .crossing_loop import CrossingLoop
from .fitting_resolver import FittingResolver
from .penetration_builder import PenetrationBuilder
from .waste_water_builder import ON_AXIS, WasteWaterBuilder

logger = logging.getLogger(__name__)


def _edge_distance(point: tuple, polygon: List[Any]) -> float:
    """Plan distance from a point to the edges of a polygon."""
    best = float("inf")
    for i, a in enumerate(polygon):
        b = polygon[(i + 1) % len(polygon)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        t = max(0.0, min(1.0, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / ((dx * dx + dy * dy) or 1e-12)))
        best = min(best, math.hypot(point[0] - a[0] - dx * t, point[1] - a[1] - dy * t))
    return best

MEDIA = ("cold_water", "hot_water", "circulation")
MEDIUM_NAMES = {"cold_water": "Kaltwasser", "hot_water": "Warmwasser", "circulation": "Zirkulation"}
MEDIUM_COLOR = {"cold_water": "#1B7F3B", "hot_water": "#8BC34A", "circulation": "#4CAF7A"}


class WaterSupplyBuilder:
    """Builds model["water_supply"] = {runs, terminals, loops, penetrations, parts, stock, cuts, length} or None."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the computed model with model["tga"] from TgaLoader and storeys_out.
            issues: receives drinking water errors and warnings.
        """
        self._model = model
        self._issues = issues
        self._tga = model.get("tga") or {"elements": {}, "terminals": {}, "runs": {}, "penetrations": []}

    def build(self) -> Optional[Dict[str, Any]]:
        """Compute all drinking water runs; None when the house has none."""
        runs = [r for r in (self._raw(ref, run) for ref, run in sorted(self._tga["runs"].items())) if r]
        if not runs:
            return None
        loops, problems = CrossingLoop(self._side).apply(runs)
        for problem in problems:
            self._issues.warning("tga-run:" + problem["run"], "Kreuzung mit %s ohne Platz für die Schleife (%.0f cm frei)"
                                 % (problem["other"], problem["room"] * 100))
        for run in runs:
            self._finish(run)
        by_id = {run["id"]: run for run in runs}
        for run in runs:
            self._check_into(run, by_id)
        terminals = self._terminals(runs)
        transfers = [t["ref"] for t in terminals if t["terminal_type"] in ("transfer", "stub")]
        fittings = FittingResolver(self._tga["elements"], self._issues).resolve(runs, by_id, transfers)
        return {"runs": runs, "terminals": terminals, "loops": loops,
                "penetrations": PenetrationBuilder(self._model, self._issues).build(runs),
                "parts": fittings["parts"], "stock": fittings["stock"] + self._terminal_stock(terminals),
                "cuts": fittings["cuts"], "length": sum(run["length"] for run in runs)}

    def _raw(self, ref: str, run: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        component = self._tga["elements"].get(run.get("component"))
        params = (component or {}).get("params") or {}
        medium = run.get("medium") or params.get("medium")
        if component is None or medium not in MEDIA:
            return None
        points = run.get("points")
        if not (isinstance(points, list) and len(points) >= 2 and all(
                isinstance(p, list) and len(p) == 3 and all(JsonValues.is_number(v) for v in p) for p in points)):
            self._issues.error(ref, "points: mindestens 2 Punkte [x, y, z]")
            return None
        line = params.get("system_line") or "ppr"
        return {"id": run["id"], "ref": ref, "name": run.get("name") or run["id"], "component": run["component"],
                "component_name": component.get("name"), "line": line, "dn": params.get("nominal_size_dn"),
                "outer_diameter": float(params.get("outer_diameter") or 0.02), "medium": medium,
                "medium_name": MEDIUM_NAMES[medium], "color": MEDIUM_COLOR[medium],
                "installation": run.get("installation"), "system": run.get("system"),
                "estimated": bool(run.get("estimated") or component.get("estimated")), "note": run.get("note"),
                "points": [[float(v) for v in p] for p in points], "from": run.get("from"), "to": run.get("to"),
                "into": run.get("into") if isinstance(run.get("into"), dict) else None}

    def _check_into(self, run: Dict[str, Any], by_id: Dict[str, Dict[str, Any]]) -> None:
        # drinking water joins only as branch (T-piece): the first point lies on the axis of the feeding run
        into = run["into"]
        if not into:
            return
        target = by_id.get(str(into.get("run", "")).split(":", 1)[-1])
        if target is None:
            self._issues.error(run["ref"] + ".into", "Leitung unbekannt: %s" % into.get("run"))
            run["into"] = None
        elif WasteWaterBuilder.axis_distance(run["points"][-1], target)[0] > ON_AXIS:
            self._issues.error(run["ref"] + ".into", "Ende liegt nicht auf der Achse von %s" % target["id"])

    def _finish(self, run: Dict[str, Any]) -> None:
        points = run["points"]
        segments = []
        for index in range(len(points) - 1):
            p0, p1 = points[index], points[index + 1]
            length = math.dist(p0, p1)
            plan = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            if length < 0.001:
                self._issues.error("%s.points.%d" % (run["ref"], index), "doppelter Punkt")
            segments.append({"from": p0, "to": p1, "length": length, "plan_length": plan, "slope": None,
                             "vertical": plan < 0.001})
        run["segments"] = segments
        run["length"] = sum(s["length"] for s in segments)

    def _side(self, point: List[float], direction: List[float]) -> List[float]:
        # of the two offset directions take the one that ends farther from the wall faces near the point
        def clearance(sign: float) -> float:
            probe = (point[0] + sign * direction[0] * 0.03, point[1] + sign * direction[1] * 0.03)
            return min([_edge_distance(probe, w["footprint"]) for s in self._model.get("storeys_out") or []
                        for w in s.get("walls") or [] if w["z0"] - 0.5 <= point[2] <= w["z1"] + 0.5] or [1.0])
        return direction if clearance(1.0) >= clearance(-1.0) else [-v for v in direction]

    def _terminals(self, runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        used = {r[key] for r in runs for key in ("from", "to") if r[key]}
        result = []
        for ref in sorted(used):
            terminal = self._tga["terminals"].get(ref)
            if terminal is None:
                self._issues.error(ref, "Endstelle unbekannt")
                continue
            component = self._tga["elements"].get(terminal.get("component")) or {}
            result.append({"id": terminal["id"], "ref": ref, "name": terminal.get("name") or terminal["id"],
                           "component": terminal.get("component"), "component_name": component.get("name"),
                           "terminal_type": (component.get("params") or {}).get("terminal_type"),
                           "storey": terminal.get("storey"), "room": terminal.get("room"), "wall": terminal.get("wall"),
                           "position": terminal.get("position"), "estimated": bool(terminal.get("estimated"))})
        return result

    @staticmethod
    def _terminal_stock(terminals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # wall plates are bought parts; transfers are only open ends
        rows: Dict[str, Dict[str, Any]] = {}
        for terminal in terminals:
            if terminal["terminal_type"] != "wall_plate":
                continue
            row = rows.setdefault(terminal["component"], {"component": terminal["component"],
                                                          "name": terminal["component_name"], "kind": "terminal",
                                                          "fitting_type": "wall_plate", "length": None, "count": 0,
                                                          "estimated": False, "note": None})
            row["count"] += 1
        return [rows[key] for key in sorted(rows)]
