"""Electrical (Elektrik KG 440): TGA runs whose component is a cable, laid in a conduit with push-fit bends,
sleeves and clamps; boxes as terminals, open ends (connection later), cutting list and penetrations."""
import logging
import math
import re
from typing import Any, Dict, List, Optional

from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from ..model.tga_products import TgaProducts
from .penetration_builder import PenetrationBuilder

logger = logging.getLogger(__name__)

CABLE_KIND = "cable"
DEFAULT_RESERVE = 0.5          # cable reserve at a box in m
DEFAULT_OPEN_RESERVE = 1.5     # cable reserve at an open end in m
DEFAULT_CLAMP_SPACING = 0.5
DEFAULT_STOCK_LENGTH = 3.0
DEFAULT_CABLE_DIAMETER = 0.009
STRAIGHT = 0.002               # max. deviation of a "straight" segment from an axis in m
AT_TERMINAL = 0.10             # the end point lies at most 10 cm from its box
FILL_LIMIT = 0.8               # a single cable may fill at most 80 % of the inner diameter
CORE_COLOR = {3: "#E53935", 5: "#8E24AA"}
OTHER_COLOR = "#FB8C00"
CONDUIT_COLOR = "#C9CDD2"
RING_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*m\b")


class ElectricalBuilder:
    """Builds model["electrical"] = {runs, terminals, penetrations, parts, stock, cuts, length, cable_length} or None."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the computed model with model["tga"] from TgaLoader and storeys_out.
            issues: receives electrical errors and warnings.
        """
        self._model = model
        self._issues = issues
        self._tga = model.get("tga") or {"elements": {}, "terminals": {}, "runs": {}, "penetrations": []}
        self._elements = self._tga["elements"]

    def build(self) -> Optional[Dict[str, Any]]:
        """Compute all cable runs; None when the house has none."""
        runs = [r for r in (self._raw(ref, run) for ref, run in sorted(self._tga["runs"].items())) if r]
        if not runs:
            return None
        terminals = self._terminals(runs)
        by_ref = {t["ref"]: t for t in terminals}
        parts: List[Dict[str, Any]] = []
        cuts: List[Dict[str, Any]] = []
        for run in runs:
            self._finish(run)
            self._check_ends(run, by_ref)
            parts.extend(self._parts(run))
            cuts.extend(self._cuts(run))
        return {"runs": runs, "terminals": terminals,
                "penetrations": PenetrationBuilder(self._model, self._issues).build(runs),
                "parts": parts, "stock": self._stock(runs, parts, cuts, terminals), "cuts": cuts,
                "length": sum(r["length"] for r in runs), "cable_length": sum(r["cable_length"] for r in runs)}

    # --- runs -----------------------------------------------------------------------------------------------

    def _is_cable(self, component: Optional[Dict[str, Any]]) -> bool:
        cls = self._elements.get((component or {}).get("class")) or {}
        return cls.get("kind") == CABLE_KIND

    def _raw(self, ref: str, run: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        component = self._elements.get(run.get("component"))
        if not self._is_cable(component):
            return None
        points = run.get("points")
        if not (isinstance(points, list) and len(points) >= 2 and all(
                isinstance(p, list) and len(p) == 3 and all(JsonValues.is_number(v) for v in p) for p in points)):
            self._issues.error(ref, "points: mindestens 2 Punkte [x, y, z]")
            return None
        params = component.get("params") or {}
        cores = params.get("cores")
        cable_d = float(params.get("outer_diameter") or DEFAULT_CABLE_DIAMETER)
        conduit = self._conduit(ref, run.get("conduit"))
        open_end = run.get("open_end") if isinstance(run.get("open_end"), dict) else None
        return {"id": run["id"], "ref": ref, "name": run.get("name") or run["id"], "component": run["component"],
                "component_name": component.get("name"), "cable_type": params.get("cable_type"),
                "cores": cores, "cross_section": params.get("cross_section_mm2"),
                "label": "%s %sx%s" % (params.get("cable_type") or "Kabel", cores or "?",
                                       str(params.get("cross_section_mm2") or "?").replace(".", ",")),
                "cable_diameter": cable_d, "color": CORE_COLOR.get(cores, OTHER_COLOR),
                "conduit": conduit, "conduit_color": CONDUIT_COLOR,
                "outer_diameter": conduit["outer_diameter"] if conduit else cable_d,
                "dn": None, "line": (conduit or {}).get("size") or "Kabel",
                "installation": run.get("installation"), "system": run.get("system"),
                "estimated": bool(run.get("estimated") or component.get("estimated")), "note": run.get("note"),
                "points": [[float(v) for v in p] for p in points], "from": run.get("from"), "to": run.get("to"),
                "open_end": None if open_end is None else {
                    "reserve": float(open_end.get("reserve", DEFAULT_OPEN_RESERVE)), "note": open_end.get("note")},
                "reserve": float(run.get("reserve", DEFAULT_RESERVE))}

    def _conduit(self, ref: str, spec: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(spec, dict):
            return None
        pipe = self._elements.get(spec.get("pipe"))
        if pipe is None:
            self._issues.error(ref + ".conduit.pipe", "Schutzrohr unbekannt: %s" % spec.get("pipe"))
            return None
        params = pipe.get("params") or {}
        if params.get("part_type") != "conduit":
            self._issues.warning(ref + ".conduit.pipe", "%s ist kein Schutzrohr (part_type conduit)" % spec["pipe"])
        result = {"pipe": spec["pipe"], "pipe_name": pipe.get("name"), "size": params.get("size"),
                  "outer_diameter": float(params.get("outer_diameter") or 0.02),
                  "inner_diameter": float(params.get("inner_diameter") or 0.0),
                  "stock_length": float(params.get("stock_length") or DEFAULT_STOCK_LENGTH),
                  "clamp_spacing": float(spec.get("clamp_spacing") or DEFAULT_CLAMP_SPACING)}
        for key in ("bend", "sleeve", "clamp"):
            part = spec.get(key)
            if part and part not in self._elements:
                self._issues.error("%s.conduit.%s" % (ref, key), "Teil unbekannt: %s" % part)
                part = None
            result[key] = part
        return result

    def _finish(self, run: Dict[str, Any]) -> None:
        points = run["points"]
        segments = []
        for index in range(len(points) - 1):
            p0, p1 = points[index], points[index + 1]
            length = math.dist(p0, p1)
            plan = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            where = "%s.points.%d" % (run["ref"], index)
            if length < 0.001:
                self._issues.error(where, "doppelter Punkt")
            elif sorted(abs(p1[i] - p0[i]) for i in range(3))[1] > STRAIGHT:
                self._issues.warning(where, "Strecke nicht achsparallel (schräg im Rohr)")
            segments.append({"from": p0, "to": p1, "length": length, "plan_length": plan, "slope": None,
                             "vertical": plan < 0.001})
        run["segments"] = segments
        run["length"] = sum(s["length"] for s in segments)
        conduit = run["conduit"]
        if conduit and conduit["inner_diameter"] and run["cable_diameter"] > FILL_LIMIT * conduit["inner_diameter"]:
            self._issues.error(run["ref"] + ".conduit", "Kabel Ø %.1f mm passt nicht in %s (innen %.1f mm, max. %d %%)"
                               % (run["cable_diameter"] * 1000, conduit["size"] or "Rohr",
                                  conduit["inner_diameter"] * 1000, FILL_LIMIT * 100))
        ends = (run["open_end"]["reserve"] if run["open_end"] else 0.0) + (run["reserve"] if run["to"] else 0.0)
        run["cable_length"] = run["length"] + ends

    def _check_ends(self, run: Dict[str, Any], terminals: Dict[str, Dict[str, Any]]) -> None:
        if not run["to"] and not run["open_end"]:
            self._issues.warning(run["ref"], "Leitung ohne Endstelle und ohne offenes Ende")
        for key, point in (("from", run["points"][0]), ("to", run["points"][-1])):
            terminal = terminals.get(run[key]) if run[key] else None
            if terminal and terminal.get("position") and math.dist(point, terminal["position"]) > AT_TERMINAL:
                self._issues.warning("%s.%s" % (run["ref"], key), "Leitungsende %.0f cm von %s entfernt"
                                     % (math.dist(point, terminal["position"]) * 100, terminal["name"]))

    # --- conduit parts and cutting ----------------------------------------------------------------------------

    def _part(self, run: Dict[str, Any], ref: Optional[str], kind: str, position: List[float],
              direction: List[float]) -> Dict[str, Any]:
        element = self._elements.get(ref) or {}
        return {"run": run["id"], "run_name": run["name"], "component": ref, "name": element.get("name"),
                "fitting_type": kind, "position": position, "direction": direction,
                "outer_diameter": run["outer_diameter"], "estimated": run["estimated"]}

    def _parts(self, run: Dict[str, Any]) -> List[Dict[str, Any]]:
        conduit = run["conduit"]
        if not conduit:
            return []
        parts = []
        segments = [s for s in run["segments"] if s["length"] >= 0.001]
        for a, b in zip(segments, segments[1:]):
            da, db = _unit(a), _unit(b)
            if sum(x * y for x, y in zip(da, db)) < 0.999:
                angle = round(math.degrees(math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(da, db)))))))
                part = self._part(run, conduit["bend"], "bend", a["to"], da)
                part["angle"] = angle
                parts.append(part)
        for segment in segments:
            direction = _unit(segment)
            stock = conduit["stock_length"]
            for k in range(1, int(math.ceil(segment["length"] / stock - 1e-9))):
                parts.append(self._part(run, conduit["sleeve"], "sleeve", _along(segment, k * stock), direction))
            count = max(1, int(math.ceil(segment["length"] / conduit["clamp_spacing"] - 1e-9)))
            for k in range(count):
                parts.append(self._part(run, conduit["clamp"], "clamp",
                                        _along(segment, (k + 0.5) * segment["length"] / count), direction))
        return parts

    @staticmethod
    def _cuts(run: Dict[str, Any]) -> List[Dict[str, Any]]:
        conduit = run["conduit"]
        if not conduit:
            return []
        stock = conduit["stock_length"]
        cuts = []
        for index, segment in enumerate(run["segments"]):
            rest, pieces = segment["length"], []
            while rest > 1e-6:
                pieces.append(round(min(stock, rest), 3))
                rest -= stock
            cuts.append({"run": run["id"], "run_name": run["name"], "segment": index, "pipe": conduit["pipe"],
                         "net_length": round(segment["length"], 3), "pieces": pieces})
        return cuts

    # --- terminals and stock ----------------------------------------------------------------------------------

    def _terminals(self, runs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        used = {r[key] for r in runs for key in ("from", "to") if r[key]}
        result = []
        for ref in sorted(used):
            terminal = self._tga["terminals"].get(ref)
            if terminal is None:
                self._issues.error(ref, "Endstelle unbekannt")
                continue
            component = self._elements.get(terminal.get("component")) or {}
            params = component.get("params") or {}
            result.append({"id": terminal["id"], "ref": ref, "name": terminal.get("name") or terminal["id"],
                           "component": terminal.get("component"), "component_name": component.get("name"),
                           "terminal_type": params.get("part_type") or params.get("terminal_type"),
                           "size": params.get("size"), "storey": terminal.get("storey"), "room": terminal.get("room"),
                           "wall": terminal.get("wall"), "position": terminal.get("position"),
                           "estimated": bool(terminal.get("estimated"))})
        return result

    def _stock(self, runs: List[Dict[str, Any]], parts: List[Dict[str, Any]], cuts: List[Dict[str, Any]],
               terminals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        rows: Dict[str, Dict[str, Any]] = {}

        def row(ref: str, kind: str, fitting_type: Optional[str]) -> Dict[str, Any]:
            element = self._elements.get(ref) or {}
            return rows.setdefault(ref, {"component": ref, "name": element.get("name") or ref, "kind": kind,
                                         "fitting_type": fitting_type, "length": None, "count": 0, "packs": None,
                                         "pack_size": (element.get("params") or {}).get("pack_size"),
                                         "estimated": False, "note": None})

        for run in runs:
            cable = row(run["component"], "cable", None)
            cable["length"] = (cable["length"] or 0.0) + run["cable_length"]
            cable["estimated"] = cable["estimated"] or run["estimated"]
            ring = _ring_length(cable["name"])
            cable["note"] = "inkl. Vorrat; %s" % (("Ring %s m" % _num(ring)) if ring else "Meterware")
        for pipe, pieces in _group_pieces(cuts).items():
            stock = next(r["conduit"]["stock_length"] for r in runs if r["conduit"] and r["conduit"]["pipe"] == pipe)
            entry = row(pipe, "pipe", None)
            entry["length"] = stock
            entry["count"] = _bars(pieces, stock)
            entry["note"] = "%s m Rohr netto in %d Stücken" % (_num(round(sum(pieces), 2)), len(pieces))
        for part in parts:
            if part["component"]:
                entry = row(part["component"], "fitting", part["fitting_type"])
                entry["count"] += 1
        for terminal in terminals:
            if terminal["component"]:
                entry = row(terminal["component"], "box", "box")
                entry["count"] += 1
        for entry in rows.values():
            if entry["pack_size"] and entry["kind"] == "fitting":
                entry["packs"] = int(math.ceil(entry["count"] / float(entry["pack_size"])))
            entry["unit_price"], entry["price_note"] = self._price(entry)
            entry["price"] = self._total(entry)
        order = {"cable": 0, "pipe": 1, "fitting": 2, "box": 3}
        return sorted(rows.values(), key=lambda r: (order[r["kind"]], r["name"]))

    def _price(self, entry: Dict[str, Any]) -> tuple:
        # lowest EUR offer; cables per m (offers "je m" or ring price / ring length)
        offers = [o for o in TgaProducts(self._model).offers_of(entry["component"])
                  if o.get("currency", "EUR") == "EUR" and JsonValues.is_number(o.get("price"))]
        if not offers:
            return None, None
        if entry["kind"] != "cable":
            best = min(offers, key=lambda o: o["price"])
            return best["price"], best.get("price_basis")
        ring = _ring_length(entry["name"])
        per_m = [(o["price"] if "je m" in (o.get("source") or "") else (o["price"] / ring if ring else None), o)
                 for o in offers]
        per_m = [(p, o) for p, o in per_m if p]
        if not per_m:
            return None, None
        best = min(per_m, key=lambda item: item[0])
        return round(best[0], 4), "%s je m" % (best[1].get("price_basis") or "")

    @staticmethod
    def _total(entry: Dict[str, Any]) -> Optional[float]:
        if entry["unit_price"] is None:
            return None
        if entry["kind"] == "cable":
            return round(entry["unit_price"] * entry["length"], 2)
        return round(entry["unit_price"] * (entry["packs"] if entry["packs"] is not None else entry["count"]), 2)


def _unit(segment: Dict[str, Any]) -> List[float]:
    a, b = segment["from"], segment["to"]
    length = segment["length"] or 1.0
    return [(b[i] - a[i]) / length for i in range(3)]


def _along(segment: Dict[str, Any], distance: float) -> List[float]:
    direction = _unit(segment)
    return [segment["from"][i] + direction[i] * distance for i in range(3)]


def _ring_length(name: str) -> Optional[float]:
    match = RING_RE.search(name or "")
    return float(match.group(1).replace(",", ".")) if match else None


def _num(value: float) -> str:
    return ("%g" % value).replace(".", ",")


def _group_pieces(cuts: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    result: Dict[str, List[float]] = {}
    for cut in cuts:
        result.setdefault(cut["pipe"], []).extend(cut["pieces"])
    return result


def _bars(pieces: List[float], stock: float) -> int:
    # first fit decreasing: how many stock bars the pieces need
    bars: List[float] = []
    for piece in sorted(pieces, reverse=True):
        for i, free in enumerate(bars):
            if free >= piece - 1e-9:
                bars[i] = free - piece
                break
        else:
            bars.append(stock - piece)
    return len(bars)
