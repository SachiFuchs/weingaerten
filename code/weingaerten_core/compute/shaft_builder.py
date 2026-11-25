"""Shafts (Schächte) of the house: rectangular openings through the floors and ceilings of several storeys."""
import logging
from typing import Any, Dict, List

from ..constants import ID_RE, TOLERANCE
from ..geometry.ortho_polygon import OrthoPolygon
from ..json_values import JsonValues
from ..model.issue_log import IssueLog

logger = logging.getLogger(__name__)

# a pipe point within 1 cm of the shaft counts as running in it
RUN_IN_SHAFT_LIMIT = 0.01
NO_CUTS: Dict[str, List[List[float]]] = {"floor": [], "ceiling": []}


class ShaftBuilder:
    """`plan` before the storeys (which floors / ceilings each shaft opens), `finish` after them (cut areas)."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the model; `plan` sets `shaft_specs` and `shaft_cuts`, `finish` sets `shafts`.
            issues: receives shaft errors and warnings.
        """
        self._model = model
        self._issues = issues

    def plan(self) -> None:
        """Parse `house.shafts` and store per storey ref the shaft rects that open its floor / its ceilings."""
        house = self._model["house"] if isinstance(self._model["house"], dict) else {}
        specs, cuts, seen = [], {}, set()
        for shaft in house.get("shafts") or []:
            if not isinstance(shaft, dict):
                continue
            where = "house.shafts.%s" % shaft.get("id")
            if shaft.get("id") in seen or not isinstance(shaft.get("id"), str) or not ID_RE.match(shaft["id"]):
                self._issues.error(where, "Schacht-id ungültig oder doppelt")
                continue
            seen.add(shaft["id"])
            spec = self._spec(where, shaft)
            if spec is None:
                continue
            specs.append(spec)
            for kind in ("floor", "ceiling"):
                for ref in spec[kind + "_storeys"]:
                    cuts.setdefault(ref, {"floor": [], "ceiling": []})[kind].extend(spec["rects"])
        self._model["shaft_specs"] = specs
        self._model["shaft_cuts"] = cuts

    @staticmethod
    def cuts_of(model: Dict[str, Any], storey_ref: str) -> Dict[str, List[List[float]]]:
        """Return `{floor: rects, ceiling: rects}` of the shafts through this storey."""
        return (model.get("shaft_cuts") or {}).get(storey_ref, NO_CUTS)

    def _spec(self, where: str, shaft: Dict[str, Any]) -> Any:
        points, error = OrthoPolygon.parse(shaft.get("polygon"))
        if error:
            self._issues.error(where, error)
            return None
        storeys = self._model["storeys"]
        top, bottom = shaft.get("from_storey"), shaft.get("to_storey")
        for ref in (top, bottom):
            if ref not in storeys:
                self._issues.error(where, "unbekannt: %s" % ref)
                return None
        elevation = {ref: float(s["elevation"]) if JsonValues.is_number(s.get("elevation")) else 0.0
                     for ref, s in storeys.items()}
        if elevation[top] <= elevation[bottom]:
            self._issues.error(where, "oberstes Geschoss liegt nicht über dem untersten")
            return None
        low, high = elevation[bottom], elevation[top]
        floors = [ref for ref, z in elevation.items() if low < z <= high]
        ceilings = [ref for ref, z in elevation.items() if low <= z < high]
        return {"id": shaft["id"], "name": shaft.get("name"), "purpose": shaft.get("purpose"),
                "from_storey": top, "to_storey": bottom, "polygon": OrthoPolygon.to_json(points),
                "rects": OrthoPolygon.rects(points), "area": OrthoPolygon.area(points),
                "floor_storeys": sorted(floors, key=lambda r: -elevation[r]),
                "ceiling_storeys": sorted(ceilings, key=lambda r: -elevation[r]),
                "penetrations": [p for p in shaft.get("penetrations") or [] if isinstance(p, str)],
                "estimated": bool(shaft.get("estimated")), "note": shaft.get("note"), "source": shaft}

    def finish(self) -> None:
        """Compute the cut areas per storey element and check the listed runs; sets `model["shafts"]`."""
        result = []
        storeys = {s["ref"]: s for s in self._model["storeys_out"]}
        for spec in self._model.get("shaft_specs") or []:
            where = "house.shafts.%s" % spec["id"]
            cuts = []
            for ref in spec["floor_storeys"]:
                cuts += self._floor_cuts(where, spec, storeys.get(ref))
            for ref in spec["ceiling_storeys"]:
                cuts += self._ceiling_cuts(where, spec, storeys.get(ref))
            self._check_runs(where, spec)
            result.append(dict(spec, cuts=cuts, cut_area=sum(c["area"] for c in cuts)))
        self._model["shafts"] = result

    def _floor_cuts(self, where: str, spec: Dict[str, Any], storey: Any) -> List[Dict[str, Any]]:
        if storey is None:
            return []
        cuts = []
        for floor in storey["floors"]:
            area = sum(OrthoPolygon.overlap_area(r["rects"], spec["rects"]) for r in floor["rooms"])
            if area > TOLERANCE * TOLERANCE:
                cuts.append({"storey": storey["id"], "kind": "floor", "element": floor["id"], "name": floor["name"],
                             "area": area})
        if sum(c["area"] for c in cuts) < spec["area"] - TOLERANCE:
            self._issues.warning(where, "Schacht liegt in %s nicht vollständig in einem Boden" % storey["id"])
        heating = storey.get("heating") or {}
        for circuit in heating.get("circuits") or []:
            if OrthoPolygon.overlap_area([circuit["rect"]], spec["rects"]) > TOLERANCE * TOLERANCE:
                self._issues.warning(where, "Heizkreis %s liegt im Schacht" % circuit["id"])
        return cuts

    def _ceiling_cuts(self, where: str, spec: Dict[str, Any], storey: Any) -> List[Dict[str, Any]]:
        if storey is None:
            return []
        cuts = []
        for ceiling in storey["ceilings"]:
            polygon = [tuple(p) for p in ceiling["polygon"]]
            area = OrthoPolygon.polygon_overlap(polygon, spec["rects"])
            if area <= TOLERANCE * TOLERANCE:
                continue
            cuts.append({"storey": storey["id"], "kind": "ceiling", "element": ceiling["id"], "name": ceiling["name"],
                         "area": area})
            beams = (ceiling.get("joists") or {}).get("beams") or []
            if any(OrthoPolygon.polygon_overlap([tuple(p) for p in b["polygon"]], spec["rects"]) > 1e-6 for b in beams):
                self._issues.warning(where, "Deckenbalken von %s im Schacht – Wechsel nötig" % ceiling["id"])
        return cuts

    def _check_runs(self, where: str, spec: Dict[str, Any]) -> None:
        runs = {}
        for system in ("waste_water", "water_supply", "electrical"):
            for run in (self._model.get(system) or {}).get("runs") or []:
                runs[run["ref"]] = run
        for ref in spec["penetrations"]:
            run = runs.get(ref)
            if run is None:
                self._issues.error(where, "Leitung unbekannt: %s" % ref)
            elif not any(self._in_rects(p, spec["rects"]) for p in run["points"]):
                self._issues.error(where, "Leitung %s verläuft nicht im Schacht" % ref)

    @staticmethod
    def _in_rects(point: List[float], rects: List[List[float]]) -> bool:
        limit = RUN_IN_SHAFT_LIMIT
        return any(x - limit <= point[0] <= x + w + limit and y - limit <= point[1] <= y + h + limit
                   for x, y, w, h in rects)
