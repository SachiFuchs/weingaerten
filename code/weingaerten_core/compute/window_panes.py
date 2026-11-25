"""Effective opening type of every pane of a window."""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class WindowPanes:
    """Derives the pane opening types from the component parameters."""

    @staticmethod
    def opening_types(params: Dict[str, Any]) -> List[str]:
        """Return the opening type per pane, counted from the left seen from inside.

        Without sashes the window is one fixed pane. Defaults follow the usual hinge layout:
        the last of several panes opens to the right, all others to the left.
        """
        sashes = params.get("sashes", 0) or 0
        if sashes < 1:
            return ["fixed"]
        types = []
        for i in range(sashes):
            default = "tilt_turn_right" if (sashes > 1 and i == sashes - 1) else "tilt_turn_left"
            types.append(params.get("opening_%d" % (i + 1)) or default)
        return types
