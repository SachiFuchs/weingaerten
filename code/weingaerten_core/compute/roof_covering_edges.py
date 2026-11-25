"""Edge lengths of a roof covering (ridge, verge, eaves) and the per-edge invoice items derived from them."""
import logging
import math
from typing import Any, Dict, List

from ..json_values import JsonValues
from ..model.issue_log import IssueLog

logger = logging.getLogger(__name__)

MEASURES = ("ridge", "verge", "eaves", "invoice")
SAME = 1e-6


class RoofCoveringEdges:
    """Measures the edges of the covering faces and quantifies the `items`."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the loaded model (components).
            issues: receives item errors.
        """
        self._model = model
        self._issues = issues

    @staticmethod
    def measure(faces: List[Dict[str, Any]], ridge: float, cos: float) -> Dict[str, float]:
        """Return `{ridge, verge, eaves}` in m.

        eaves = along length of every face; ridge = along overlap of west and east faces both ending at the ridge;
        verge = sloped length of the exposed across part of every face end (not covered by an adjoining face of the
        same side).
        """
        eaves = sum(f["along"][1] - f["along"][0] for f in faces)
        at_ridge = lambda side: [f for f in faces if f["side"] == side and abs(f["end"] - ridge) < SAME]
        ridge_length = sum(max(0.0, min(w["along"][1], e["along"][1]) - max(w["along"][0], e["along"][0]))
                           for w in at_ridge("west") for e in at_ridge("east"))
        verge = 0.0
        for face in faces:
            for index in (0, 1):
                y = face["along"][index]
                neighbours = [n for n in faces if n is not face and n["side"] == face["side"]
                              and abs(n["along"][1 - index] - y) < 1e-3]
                verge += RoofCoveringEdges._exposed(face["across"], [n["across"] for n in neighbours]) / cos
        return {"ridge": ridge_length, "verge": verge, "eaves": eaves}

    @staticmethod
    def _exposed(span: tuple, covers: List[tuple]) -> float:
        # length of `span` not covered by any of `covers`
        length = span[1] - span[0]
        for c in covers:
            length -= max(0.0, min(span[1], c[1]) - max(span[0], c[0]))
        return max(0.0, length)

    def items(self, where: str, items: Any, edges: Dict[str, float]) -> List[Dict[str, Any]]:
        """Return `[{component, name, measure, per_m, quantity, unit, invoice_quantity, invoice_unit}]`;
        unknown components or measures are reported and skipped."""
        result = []
        for item in items or []:
            ref = item.get("component") if isinstance(item, dict) else None
            component = self._model["elements"].get(ref)
            if component is None:
                self._issues.error(where, "unbekannt: %s" % ref)
                continue
            measure = item.get("measure")
            if measure not in MEASURES:
                self._issues.error(where, "Messart ungültig: %s" % measure)
                continue
            params = component.get("params") or {}
            invoice = params.get("quantity") if JsonValues.is_number(params.get("quantity")) else None
            per_m = item.get("per_m")
            if measure == "invoice":
                quantity, unit = invoice, params.get("unit")
            elif JsonValues.is_number(per_m):
                quantity, unit = float(math.ceil(edges[measure] * per_m - 1e-9)), "pcs"
            else:
                quantity, unit = edges[measure], "m"
            result.append({"component": ref, "name": component.get("name"), "measure": measure,
                           "per_m": per_m if JsonValues.is_number(per_m) else None, "quantity": quantity,
                           "unit": unit, "invoice_quantity": invoice, "invoice_unit": params.get("unit")})
        return result
