"""Checks one parameter value against its parameter definition."""
import logging
from typing import Any, Dict, Optional

from ..json_values import JsonValues

logger = logging.getLogger(__name__)


class ParameterRules:
    """Validation of class parameter values (length, number, choice, bool)."""

    @staticmethod
    def problem(parameter: Dict[str, Any], value: Any) -> Optional[str]:
        """Check a value against a parameter definition.

        Args:
            parameter: definition with type and optional min / max / options.
            value: the value given by a component (or the parameter default).

        Returns:
            A German message describing the problem, or None if the value is valid.
        """
        kind = parameter.get("type")
        if kind in ("length", "number"):
            return ParameterRules._number_problem(parameter, value, kind)
        if kind == "choice":
            if value not in (parameter.get("options") or []):
                return "nicht in der Auswahl %s" % parameter.get("options")
        elif kind == "bool":
            if not isinstance(value, bool):
                return "muss ja/nein sein"
        return None

    @staticmethod
    def _number_problem(parameter: Dict[str, Any], value: Any, kind: str) -> Optional[str]:
        if not JsonValues.is_number(value):
            return "muss eine Zahl sein"
        if JsonValues.is_number(parameter.get("min")) and value < parameter["min"]:
            return "kleiner als Minimum %s" % parameter["min"]
        if JsonValues.is_number(parameter.get("max")) and value > parameter["max"]:
            return "größer als Maximum %s" % parameter["max"]
        if kind == "length" and value <= 0:
            return "muss > 0 sein"
        return None
