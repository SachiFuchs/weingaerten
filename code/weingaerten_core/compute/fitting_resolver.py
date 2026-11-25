"""Resolves waste water runs into fittings (bends, branches, adapters, plugs) and cut pipe pieces (stage 2)."""
import logging
import math
from typing import Any, Dict, List, Optional

from ..model.issue_log import IssueLog
from .fitting_catalog import FittingCatalog
from .pipe_cutter import PipeCutter

logger = logging.getLogger(__name__)

MIN_ANGLE = 2.0   # direction changes below 2° (slope changes) need no bend
EPS = 1e-9


def _direction(segment: Dict[str, Any]) -> List[float]:
    d = [segment["to"][i] - segment["from"][i] for i in range(3)]
    n = math.sqrt(sum(v * v for v in d)) or 1.0
    return [v / n for v in d]


def _angle(a: List[float], b: List[float]) -> float:
    return math.degrees(math.acos(max(-1.0, min(1.0, sum(a[i] * b[i] for i in range(3))))))


class FittingResolver:
    """Builds {parts, stock, cuts} from the computed runs and the fitting catalog."""

    def __init__(self, elements: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            elements: model["tga"]["elements"].
            issues: receives warnings for angles or connections the stock cannot build.
        """
        self._catalog = FittingCatalog(elements)
        self._issues = issues
        self._parts: List[Dict[str, Any]] = []
        self._deduct: Dict[tuple, float] = {}       # (run, segment, end 0|1) -> length taken by fittings
        self._splits: Dict[tuple, List[tuple]] = {}  # (run, segment) -> [(t, z_length)] branch fittings on it

    def resolve(self, runs: List[Dict[str, Any]], by_id: Dict[str, Dict[str, Any]],
                stubs: List[str]) -> Dict[str, Any]:
        """Return parts, stock rows (fittings + sticks) and the cut list per straight stretch."""
        continued = {str(r["into"]["run"]).split(":", 1)[-1] for r in runs if r["into"] and r["into"]["kind"] == "continue"}
        for run in runs:
            self._bends(run)
            if run["id"] not in continued and (not run["from"] or run["from"] in stubs):
                self._plug(run)
            if run.get("to") in stubs:
                self._plug(run, end=True)
            if run["into"]:
                target = by_id.get(str(run["into"]["run"]).split(":", 1)[-1])
                if target and run["into"]["kind"] == "continue":
                    self._adapter(run, target)
                elif target:
                    self._branch(run, target)
        cutter = PipeCutter(self._catalog.pipes)
        cuts = [cut for run in runs for cut in self._cuts(run, cutter)]
        return {"parts": self._parts, "stock": self._fitting_stock() + cutter.stock(), "cuts": cuts}

    def _part(self, run: Dict[str, Any], fitting: Dict[str, Any], position: List[float], direction: List[float],
              at: Any, angle: Optional[float] = None, wanted: Optional[float] = None, od: Optional[float] = None) -> None:
        self._parts.append({"run": run["id"], "run_name": run["name"], "component": fitting["component"],
                            "name": fitting["name"], "fitting_type": fitting["fitting_type"], "at": at,
                            "angle": angle, "wanted": wanted, "position": list(position), "direction": direction,
                            "outer_diameter": od or run["outer_diameter"], "estimated": fitting["estimated"]})

    def _take(self, run_id: str, segment: int, end: int, length: float) -> None:
        key = (run_id, segment, end)
        self._deduct[key] = self._deduct.get(key, 0.0) + length

    def _bends(self, run: Dict[str, Any]) -> None:
        segments = run["segments"]
        for k in range(1, len(segments)):
            before, after = _direction(segments[k - 1]), _direction(segments[k])
            wanted = _angle(before, after)
            if wanted < MIN_ANGLE:
                continue
            bends, exact = self._catalog.bends(run["line"], run["dn"], wanted)
            if not bends:
                self._issues.warning("%s.points.%d" % (run["ref"], k), "kein Bogen %s DN %s im Sortiment" %
                                     (run["line"].upper(), run["dn"]))
                continue
            if not exact:
                self._issues.warning("%s.points.%d" % (run["ref"], k), "Winkel %.1f° nicht im Sortiment (gewählt %s°)"
                                     % (wanted, " + ".join("%g" % b["angle"] for b in bends)))
            middle = [before[i] + after[i] for i in range(3)]
            norm = math.sqrt(sum(v * v for v in middle)) or 1.0
            for bend in bends:
                self._part(run, bend, run["points"][k], [v / norm for v in middle], k, bend["angle"], wanted)
                self._take(run["id"], k - 1, 1, bend["z_length"])
                self._take(run["id"], k, 0, bend["z_length"])

    def _plug(self, run: Dict[str, Any], end: bool = False) -> None:
        plug = self._catalog.plug(run["line"], run["dn"])
        if plug is None:
            self._issues.warning(run["ref"], "kein Stopfen %s DN %s im Sortiment" % (run["line"].upper(), run["dn"]))
            return
        last = len(run["segments"]) - 1
        self._part(run, plug, run["points"][-1 if end else 0], _direction(run["segments"][last if end else 0]),
                   "end" if end else "start")
        self._take(run["id"], last if end else 0, 1 if end else 0, plug["z_length"])

    def _adapter(self, run: Dict[str, Any], target: Dict[str, Any]) -> None:
        if (run["line"], run["dn"]) == (target["line"], target["dn"]):
            return
        adapter = self._catalog.adapter(run["line"], run["dn"], target["line"], target["dn"])
        if adapter is None:
            self._issues.warning(run["ref"] + ".into", "kein Übergang %s DN %s auf %s DN %s im Sortiment" % (
                run["line"].upper(), run["dn"], target["line"].upper(), target["dn"]))
            return
        last = len(run["segments"]) - 1
        self._part(run, adapter, run["points"][-1], _direction(run["segments"][last]), "end",
                   od=max(run["outer_diameter"], target["outer_diameter"]))
        self._take(run["id"], last, 1, adapter["z_length"])
        self._take(target["id"], 0, 0, adapter["z_length"])

    def _branch(self, run: Dict[str, Any], target: Dict[str, Any]) -> None:
        end = run["points"][-1]
        index, t = self._on_axis(end, target)
        main = _direction(target["segments"][index])
        angle = _angle(_direction(run["segments"][-1]), main)
        fitting, exact = self._catalog.branch(target["line"], target["dn"], run["dn"], angle)
        where = run["ref"] + ".into"
        if fitting is None:
            self._issues.warning(where, "kein Abzweig %s DN %s/%s im Sortiment" % (target["line"].upper(), target["dn"],
                                                                                  run["dn"]))
            return
        if not exact:
            self._issues.warning(where, "Abzweigwinkel %.0f° nicht im Sortiment (gewählt %g°)" % (angle, fitting["angle"]))
        self._part(run, fitting, end, main, "end", fitting["angle"], angle, target["outer_diameter"])
        self._take(run["id"], len(run["segments"]) - 1, 1, fitting["z_length"])
        self._splits.setdefault((target["id"], index), []).append((t, fitting["z_length"]))

    @staticmethod
    def _on_axis(point: List[float], target: Dict[str, Any]) -> tuple:
        best = (float("inf"), 0, 0.0)
        for index, segment in enumerate(target["segments"]):
            a, b = segment["from"], segment["to"]
            d = [b[i] - a[i] for i in range(3)]
            t = max(0.0, min(1.0, sum((point[i] - a[i]) * d[i] for i in range(3)) / (sum(v * v for v in d) or EPS)))
            distance = math.dist(point, [a[i] + d[i] * t for i in range(3)])
            if distance < best[0]:
                best = (distance, index, t)
        return best[1], best[2]

    def _cuts(self, run: Dict[str, Any], cutter: PipeCutter) -> List[Dict[str, Any]]:
        # every segment is split at the branch fittings on it; each stretch loses the fitting lengths at both ends
        rows = []
        for index, segment in enumerate(run["segments"]):
            marks = [(0.0, self._deduct.get((run["id"], index, 0), 0.0))]
            marks += sorted(self._splits.get((run["id"], index), []))
            marks.append((1.0, self._deduct.get((run["id"], index, 1), 0.0)))
            for (t0, z0), (t1, z1) in zip(marks, marks[1:]):
                length = (t1 - t0) * segment["length"]
                deduction = min(length, z0 + z1)
                pieces = cutter.cut(run["component"], length - deduction)
                if length - (z0 + z1) < -1e-6:
                    self._issues.warning("%s.points.%d" % (run["ref"], index), "Abschnitt zu kurz für die Formteile")
                rows.append({"run": run["id"], "run_name": run["name"], "component": run["component"],
                             "name": run["component_name"], "segment": index, "length": length,
                             "net_length": length - deduction, "pieces": pieces, "deduction": deduction})
        return rows

    def _fitting_stock(self) -> List[Dict[str, Any]]:
        rows: Dict[str, Dict[str, Any]] = {}
        for part in self._parts:
            fitting = next(f for f in self._catalog.fittings if f["component"] == part["component"])
            row = rows.setdefault(part["component"], {"component": part["component"], "name": part["name"],
                                                      "kind": "fitting", "fitting_type": part["fitting_type"],
                                                      "length": None, "count": 0, "estimated": part["estimated"],
                                                      "note": fitting["note"] if part["estimated"] else None})
            row["count"] += 1
        return [rows[key] for key in sorted(rows)]
