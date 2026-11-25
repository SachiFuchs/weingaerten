"""Conductor roles (L, N, PE ...) and colours of a cable: own list or derived from the number of cores."""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# DIN VDE 0293-308, cables with protective conductor (G); index = number of cores
STANDARD_ROLES = {1: ["L"], 2: ["L", "N"], 3: ["L", "N", "PE"], 4: ["L1", "L2", "L3", "PE"], 5: ["L1", "L2", "L3", "N", "PE"]}
COLORS = {"L": "#7B4A2A", "L1": "#7B4A2A", "L2": "#222222", "L3": "#8A8A8A", "N": "#1E5AA8", "PE": "#9ACD32"}
PHASES = ("L", "L1", "L2", "L3")


class ConductorRoles:
    """Answers which conductors a cable has and whether two conductors may share a clamp."""

    @staticmethod
    def of(component: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return `[{role, color, derived}]` of a cable component (empty list for anything else)."""
        connection = component.get("connection") if isinstance(component.get("connection"), dict) else {}
        own = connection.get("conductors")
        if isinstance(own, list) and own:
            return [{"role": c.get("role"), "color": c.get("color") or COLORS.get(c.get("role")), "derived": False}
                    for c in own if isinstance(c, dict)]
        cores = (component.get("params") or {}).get("cores")
        if not isinstance(cores, (int, float)) or isinstance(cores, bool) or cores < 1:
            return []
        cores = int(cores)
        if connection.get("line") == "power" and cores in STANDARD_ROLES:
            return [{"role": r, "color": COLORS[r], "derived": True} for r in STANDARD_ROLES[cores]]
        return [{"role": "C%d" % (i + 1), "color": None, "derived": True} for i in range(cores)]

    @staticmethod
    def same_kind(a: str, b: str) -> bool:
        """True when a clamp may join the two conductors (same role; a phase L meets L1/L2/L3)."""
        if a == b:
            return True
        return a in PHASES and b in PHASES and "L" in (a, b)
