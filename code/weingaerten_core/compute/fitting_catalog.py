"""Index of the pipe fittings and pipes of the TGA catalog with the selection rules of stage 2."""
import itertools
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

BEND_TOLERANCE = 2.0     # degrees a bend combination may differ from the wanted angle
BRANCH_TOLERANCE = 10.0  # degrees between the real junction angle and a branch fitting
MAX_BENDS = 3            # bends combined at one corner


class FittingCatalog:
    """Fittings grouped by type, system line (ht|kg) and DN; pipes with their stock lengths."""

    def __init__(self, elements: Dict[str, Any]) -> None:
        """Args:
            elements: model["tga"]["elements"] (tga-class and tga-component refs).
        """
        self.fittings: List[Dict[str, Any]] = []
        self.pipes: Dict[str, Dict[str, Any]] = {}
        for ref, element in sorted(elements.items()):
            if not ref.startswith("tga-component:"):
                continue
            params = element.get("params") or {}
            item = {"component": ref, "name": element.get("name") or ref, "estimated": bool(element.get("estimated")),
                    "note": element.get("note")}
            if element.get("class") == "tga-class:pipe-fitting":
                item.update({"fitting_type": params.get("fitting_type"), "line": params.get("system_line"),
                             "dn": params.get("dn"), "angle": params.get("angle"), "dn_branch": params.get("dn_branch"),
                             "line_to": params.get("line_to"), "dn_to": params.get("dn_to"),
                             "z_length": float(params.get("z_length") or 0.0)})
                self.fittings.append(item)
            elif element.get("class") == "tga-class:pipe" and element.get("stock"):
                item["lengths"] = sorted(float(v) for v in element["stock"].get("lengths") or [])
                self.pipes[ref] = item

    def _of(self, kind: str, line: str, dn: Any) -> List[Dict[str, Any]]:
        return [f for f in self.fittings if f["fitting_type"] == kind and f["line"] == line and f["dn"] == dn]

    def bends(self, line: str, dn: Any, angle: float) -> Tuple[List[Dict[str, Any]], bool]:
        """Return (bends whose angles add up to `angle`, exact) - the closest combination if none fits."""
        bends = [b for b in self._of("bend", line, dn) if b["angle"]]
        best: Tuple[float, List[Dict[str, Any]]] = (float("inf"), [])
        for count in range(1, MAX_BENDS + 1):
            for combo in itertools.combinations_with_replacement(bends, count):
                error = abs(sum(b["angle"] for b in combo) - angle)
                # fewer parts win at the same error
                if error < best[0] - 1e-6:
                    best = (error, list(combo))
            if best[0] <= BEND_TOLERANCE:
                return best[1], True
        return best[1], False

    def branch(self, line: str, dn: Any, dn_branch: Any, angle: float) -> Tuple[Optional[Dict[str, Any]], bool]:
        """Return (branch fitting with the nearest angle, within tolerance)."""
        candidates = [b for b in self._of("branch", line, dn) if b["dn_branch"] == dn_branch and b["angle"]]
        if not candidates:
            return None, False
        best = min(candidates, key=lambda b: abs(b["angle"] - angle))
        return best, abs(best["angle"] - angle) <= BRANCH_TOLERANCE

    def adapter(self, line: str, dn: Any, line_to: str, dn_to: Any) -> Optional[Dict[str, Any]]:
        """Return the adapter between two pipe systems (either orientation)."""
        for f in self.fittings:
            if f["fitting_type"] != "adapter":
                continue
            if (f["line"], f["dn"], f["line_to"], f["dn_to"]) in ((line, dn, line_to, dn_to), (line_to, dn_to, line, dn)):
                return f
        return None

    def plug(self, line: str, dn: Any) -> Optional[Dict[str, Any]]:
        """Return the plug (Muffenstopfen) of a pipe system."""
        plugs = self._of("plug", line, dn)
        return plugs[0] if plugs else None
