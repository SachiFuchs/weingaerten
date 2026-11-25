"""Openings of a roof covering: roof windows (in the roof plane) and chimneys (vertical, plan rectangle)."""
import logging
import math
from typing import Any, Dict, List, Optional

from ..json_values import JsonValues
from ..model.issue_log import IssueLog

logger = logging.getLogger(__name__)

OVERLAP = 1e-6


class RoofCoveringOpenings:
    """Places the `openings` of `roof_covering` on their faces."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the loaded model (components).
            issues: receives opening errors and the trimmer warnings.
        """
        self._model = model
        self._issues = issues

    def build(self, where: str, openings: Any, faces: Dict[str, Dict[str, Any]], roof: Any,
              rafters: List[Dict[str, Any]], ridge_top: float) -> List[Dict[str, Any]]:
        """Return the placed openings `{id, kind, name, component, flashing, parts, slope, side, across, along,
        size, area, sill?, z0?, z1?}` (across/along in plan, area in the roof plane).

        Args:
            where: `<storey>.roof_covering`.
            openings: the `openings` JSON.
            faces: faces by slope id (`across`, `along`, `side`).
            roof: the storey RoofProfile.
            rafters: the rafter members of the roof structure (trimmer check), may be empty.
            ridge_top: absolute height of the covering top at the ridge (chimney top = +0.5 m).
        """
        result = []
        for spec in openings or []:
            if not isinstance(spec, dict):
                continue
            here = "%s.%s" % (where, spec.get("id"))
            face = faces.get(spec.get("slope"))
            if face is None:
                self._issues.error(here, "Dachfläche unbekannt: %s" % spec.get("slope"))
                continue
            placed = (self._chimney(here, spec, face, roof, ridge_top) if spec.get("kind") == "chimney"
                      else self._window(here, spec, face, roof))
            if placed is None:
                continue
            if not self._inside(placed, face):
                self._issues.error(here, "Öffnung außerhalb der Dachfläche")
                continue
            cut = [r["id"] for r in rafters if r["id"].startswith(face["id"] + "-s") and self._hits(placed, r, 1 - roof.axis)]
            if cut:
                self._issues.warning(here, "Sparren geschnitten (%s) – Balkenwechsel nötig" % ", ".join(cut))
            placed["rafters_cut"] = cut
            result.append(placed)
        return result

    def _known(self, here: str, refs: List[Any]) -> bool:
        for ref in refs:
            if ref is not None and ref not in self._model["elements"]:
                self._issues.error(here, "unbekannt: %s" % ref)
                return False
        return True

    def _window(self, here: str, spec: Dict[str, Any], face: Dict[str, Any], roof: Any) -> Optional[Dict[str, Any]]:
        ref, flashing = spec.get("component"), spec.get("flashing")
        if not self._known(here, [ref, flashing]) or ref is None:
            if ref is None:
                self._issues.error(here, "Bauteil fehlt")
            return None
        params = self._model["elements"][ref].get("params") or {}
        if not all(JsonValues.is_number(v) for v in (params.get("width"), params.get("height"), spec.get("y"),
                                                       spec.get("sill"))):
            self._issues.error(here, "Maße ungültig")
            return None
        width, height, sill = float(params["width"]), float(params["height"]), float(spec["sill"])
        if sill < roof.knee:
            self._issues.error(here, "Unterkante unter dem Kniestock")
            return None
        # sill = storey-local height of the lower edge on the roof underside; the window rises along the slope
        cos = math.cos(math.radians(roof.pitch))
        distance = (sill - roof.knee) / roof.slope
        if face["side"] == "west":
            across = (roof.eaves[0] + distance, roof.eaves[0] + distance + height * cos)
        else:
            across = (roof.eaves[1] - distance - height * cos, roof.eaves[1] - distance)
        y = float(spec["y"])
        frame = float(params.get("frame_width") or 0.0)
        return {"id": spec.get("id"), "kind": "window", "name": self._model["elements"][ref].get("name"),
                "component": ref, "flashing": flashing, "parts": [], "slope": face["id"], "side": face["side"],
                "across": list(across), "along": [y - width / 2.0, y + width / 2.0], "size": [width, height],
                "area": width * height, "glass_area": max(0.0, width - 2 * frame) * max(0.0, height - 2 * frame),
                "sill": sill}

    def _chimney(self, here: str, spec: Dict[str, Any], face: Dict[str, Any], roof: Any,
                 ridge_top: float) -> Optional[Dict[str, Any]]:
        parts = [p for p in spec.get("parts") or []]
        if not self._known(here, parts):
            return None
        rect = spec.get("rect_plan")
        if not (isinstance(rect, list) and len(rect) == 4 and all(JsonValues.is_number(v) for v in rect)
                and rect[2] > 0 and rect[3] > 0):
            self._issues.error(here, "Maße ungültig")
            return None
        x, y, w, h = (float(v) for v in rect)
        across, along = ((x, x + w), (y, y + h)) if roof.axis == 0 else ((y, y + h), (x, x + w))
        cos = math.cos(math.radians(roof.pitch))
        return {"id": spec.get("id"), "kind": "chimney", "name": spec.get("name") or "Kamin", "component": None,
                "flashing": None, "parts": parts, "slope": face["id"], "side": face["side"],
                "across": list(across), "along": list(along), "size": [w, h],
                "area": (across[1] - across[0]) * (along[1] - along[0]) / cos, "glass_area": 0.0,
                "z1": ridge_top + 0.5}

    @staticmethod
    def _inside(placed: Dict[str, Any], face: Dict[str, Any]) -> bool:
        return all(face[key][0] - OVERLAP <= placed[key][0] and placed[key][1] <= face[key][1] + OVERLAP
                   for key in ("across", "along"))

    @staticmethod
    def _hits(placed: Dict[str, Any], rafter: Dict[str, Any], along_index: int) -> bool:
        # the rafter footprint gives its interval along the ridge
        values = [p[along_index] for p in rafter["footprint"]]
        lo, hi = min(values), max(values)
        return placed["along"][0] < hi - OVERLAP and lo + OVERLAP < placed["along"][1]
