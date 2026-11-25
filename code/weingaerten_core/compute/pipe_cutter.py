"""Cuts the straight pipe stretches of the waste water runs from the stock lengths (greedy, offcuts reused)."""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

EPS = 1e-6


class PipeCutter:
    """Keeps the bought sticks and the offcuts per pipe component over all runs."""

    def __init__(self, pipes: Dict[str, Dict[str, Any]]) -> None:
        """Args:
            pipes: FittingCatalog.pipes (component ref -> {name, lengths, estimated, note}).
        """
        self._pipes = pipes
        self._sticks: Dict[str, Dict[float, int]] = {}
        self._offcuts: Dict[str, List[float]] = {}

    def cut(self, component: str, length: float) -> List[float]:
        """Return the pieces (sum = length) for one stretch: offcut, else one cut stick, else full longest sticks."""
        lengths = (self._pipes.get(component) or {}).get("lengths") or []
        if not lengths or length <= EPS:
            return [length] if length > EPS else []
        pieces, remaining = [], length
        while remaining > EPS:
            offcuts = sorted(o for o in self._offcuts.get(component, []) if o >= remaining - EPS)
            longer = [s for s in lengths if s >= remaining - EPS]
            if offcuts:
                # rest of an earlier stick first
                self._offcuts[component].remove(offcuts[0])
                self._offcuts[component].append(offcuts[0] - remaining)
            elif longer:
                # one cut from the shortest stick that is long enough: fewest joints
                stick = min(longer)
                self._buy(component, stick)
                self._offcuts.setdefault(component, []).append(stick - remaining)
            else:
                stick = max(lengths)
                self._buy(component, stick)
                pieces.append(stick)
                remaining -= stick
                continue
            pieces.append(remaining)
            remaining = 0.0
        return pieces

    def _buy(self, component: str, stick: float) -> None:
        counts = self._sticks.setdefault(component, {})
        counts[stick] = counts.get(stick, 0) + 1

    def stock(self) -> List[Dict[str, Any]]:
        """Return one row per bought stick length: {component, name, kind pipe, length, count, estimated, note, waste}."""
        rows = []
        for component in sorted(self._sticks):
            pipe = self._pipes[component]
            waste = sum(o for o in self._offcuts.get(component, []))
            for stick in sorted(self._sticks[component], reverse=True):
                rows.append({"component": component, "name": pipe["name"], "kind": "pipe", "fitting_type": None,
                             "length": stick, "count": self._sticks[component][stick], "estimated": pipe["estimated"],
                             "note": "Verschnitt gesamt %.2f m" % waste if waste > EPS else None})
        return rows
