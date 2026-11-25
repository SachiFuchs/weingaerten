"""Waste water (Abwasser): TGA runs with medium waste_water, their terminals, slope checks and penetrations."""
import logging
import math
from typing import Any, Dict, List, Optional

from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from .fitting_resolver import FittingResolver
from .penetration_builder import PenetrationBuilder

logger = logging.getLogger(__name__)

MEDIUM = "waste_water"
LINE_SLOPE = {"ht": 0.02, "kg": 0.01}
LINE_COLOR = {"ht": "#9AA0A6", "kg": "#C0602A"}
ON_AXIS = 0.01       # a branch end must lie within 1 cm of the target axis
SLOPE_TOLERANCE = 0.0005


class WasteWaterBuilder:
    """Builds model["waste_water"] = {runs, terminals, penetrations, parts, stock, length} or None."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the computed model with model["tga"] from TgaLoader.
            issues: receives waste water errors and warnings.
        """
        self._model = model
        self._issues = issues
        self._tga = model.get("tga") or {"elements": {}, "terminals": {}, "runs": {}, "penetrations": []}

    def build(self) -> Optional[Dict[str, Any]]:
        """Compute all waste water runs; None when the house has none."""
        runs = [r for r in (self._run(ref, run) for ref, run in sorted(self._tga["runs"].items())) if r]
        if not runs:
            return None
        by_id = {run["id"]: run for run in runs}
        for run in runs:
            self._check_into(run, by_id)
        terminals = self._terminals(runs)
        stubs = [t["ref"] for t in terminals if t["terminal_type"] == "stub"]
        fittings = FittingResolver(self._tga["elements"], self._issues).resolve(runs, by_id, stubs)
        return {"runs": runs, "terminals": terminals,
                "penetrations": PenetrationBuilder(self._model, self._issues).build(runs),
                "parts": fittings["parts"], "stock": fittings["stock"], "cuts": fittings["cuts"],
                "length": sum(run["length"] for run in runs), "by_component": self._by_component(runs)}

    def _run(self, ref: str, run: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        component = self._tga["elements"].get(run.get("component"))
        params = (component or {}).get("params") or {}
        if params.get("medium") != MEDIUM:
            if component is None:
                self._issues.error(ref, "Komponente unbekannt: %s" % run.get("component"))
            return None
        points = run.get("points")
        if not (isinstance(points, list) and len(points) >= 2 and all(
                isinstance(p, list) and len(p) == 3 and all(JsonValues.is_number(v) for v in p) for p in points)):
            self._issues.error(ref, "points: mindestens 2 Punkte [x, y, z]")
            return None
        line = params.get("system_line") or "ht"
        min_slope = float(run.get("min_slope", LINE_SLOPE.get(line, 0.01)))
        points = [[float(v) for v in p] for p in points]
        segments = [self._segment(ref, i, points[i], points[i + 1], min_slope) for i in range(len(points) - 1)]
        into = run.get("into") if isinstance(run.get("into"), dict) else None
        return {"id": run["id"], "ref": ref, "name": run.get("name") or run["id"], "component": run["component"],
                "component_name": component.get("name"), "line": line, "dn": params.get("nominal_size_dn"),
                "outer_diameter": float(params.get("outer_diameter") or 0.1), "color": LINE_COLOR.get(line, "#888888"),
                "installation": run.get("installation"), "system": run.get("system"),
                "estimated": bool(run.get("estimated") or component.get("estimated")), "note": run.get("note"),
                "min_slope": min_slope, "points": points, "segments": segments,
                "length": sum(s["length"] for s in segments), "from": run.get("from"), "to": run.get("to"),
                "into": into}

    def _segment(self, ref: str, index: int, p0: List[float], p1: List[float], min_slope: float) -> Dict[str, Any]:
        length = math.dist(p0, p1)
        plan = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        fall = p0[2] - p1[2]
        vertical = plan < 0.01 * max(length, 1e-9) or plan < 0.001
        slope = None if vertical else fall / plan
        where = "%s.points.%d" % (ref, index)
        if length < 0.001:
            self._issues.error(where, "doppelter Punkt")
        elif fall < -0.001:
            self._issues.error(where, "Gegengefälle (%.1f cm steigend)" % (-fall * 100))
        elif slope is not None and slope + SLOPE_TOLERANCE < min_slope:
            self._issues.warning(where, "Gefälle %.1f %% < %.1f %%" % (slope * 100, min_slope * 100))
        return {"from": p0, "to": p1, "length": length, "plan_length": plan, "slope": slope, "vertical": vertical}

    def _check_into(self, run: Dict[str, Any], by_id: Dict[str, Dict[str, Any]]) -> None:
        into = run["into"]
        if not into:
            if not run["to"]:
                self._issues.warning(run["ref"], "Leitung ohne Ziel (to / into)")
            return
        target = by_id.get(str(into.get("run", "")).split(":", 1)[-1])
        if target is None:
            self._issues.error(run["ref"] + ".into", "Leitung unbekannt: %s" % into.get("run"))
            run["into"] = None
            return
        end = run["points"][-1]
        if into.get("kind") == "continue":
            if math.dist(end, target["points"][0]) > ON_AXIS:
                self._issues.error(run["ref"] + ".into", "Ende trifft nicht den Anfang von %s" % target["id"])
        else:
            if self.axis_distance(end, target)[0] > ON_AXIS:
                self._issues.error(run["ref"] + ".into", "Ende liegt nicht auf der Achse von %s" % target["id"])
            if (run["dn"] or 0) > (target["dn"] or 0):
                self._issues.warning(run["ref"] + ".into", "Abzweig DN %s größer als Leitung DN %s" %
                                     (run["dn"], target["dn"]))

    @staticmethod
    def axis_distance(point: List[float], target: Dict[str, Any]) -> tuple:
        """Return (distance, segment index, t) of the nearest point on the target axis."""
        best = (float("inf"), 0, 0.0)
        for index, segment in enumerate(target["segments"]):
            a, b = segment["from"], segment["to"]
            d = [b[i] - a[i] for i in range(3)]
            dd = sum(v * v for v in d) or 1e-12
            t = max(0.0, min(1.0, sum((point[i] - a[i]) * d[i] for i in range(3)) / dd))
            distance = math.dist(point, [a[i] + d[i] * t for i in range(3)])
            if distance < best[0]:
                best = (distance, index, t)
        return best

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
                           "storey": terminal.get("storey"), "room": terminal.get("room"),
                           "position": terminal.get("position"), "estimated": bool(terminal.get("estimated"))})
        return result

    @staticmethod
    def _by_component(runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        totals: Dict[str, Dict[str, Any]] = {}
        for run in runs:
            row = totals.setdefault(run["component"], {"component": run["component"], "name": run["component_name"],
                                                       "dn": run["dn"], "line": run["line"], "length": 0.0})
            row["length"] += run["length"]
        return list(totals.values())
