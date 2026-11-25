"""Rules for component classes (parameters, drawing recipe, material roles)."""
import logging
from typing import Any, Dict, List

from ..constants import PANE_OPENING_TYPES, RECIPE_PARAMETERS
from ..json_values import JsonValues
from .parameter_rules import ParameterRules

logger = logging.getLogger(__name__)


class ClassValidator:
    """Checks a `class:` element against the parameter, recipe and role rules."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the loaded model (role defaults must resolve to its materials).
        """
        self._model = model

    def errors(self, element: Dict[str, Any]) -> List[str]:
        """Return the German error messages of a class element (empty if valid)."""
        parameters = [p for p in element.get("parameters") or [] if isinstance(p, dict)]
        errors = self._parameter_errors(parameters)
        by_key = {p.get("key"): p for p in parameters}
        for key, kind in RECIPE_PARAMETERS.get(element.get("geometry"), []):
            if key not in by_key or by_key[key].get("type") != kind:
                errors.append("Rezept %s braucht Parameter %s (%s)" % (element.get("geometry"), key, kind))
        if element.get("geometry") == "window" and "sashes" in by_key:
            errors += self._window_errors(by_key)
        errors += self._role_errors(element)
        return errors

    @staticmethod
    def _duplicates(keys: List[Any]) -> List[Any]:
        return [key for key in set(keys) if keys.count(key) > 1]

    def _parameter_errors(self, parameters: List[Dict[str, Any]]) -> List[str]:
        errors = ["Parameter %s doppelt" % key for key in self._duplicates([p.get("key") for p in parameters])]
        for parameter in parameters:
            key = parameter.get("key")
            if parameter.get("type") == "choice" and not parameter.get("options"):
                errors.append("Parameter %s: Auswahl braucht Werte" % key)
            if JsonValues.is_number(parameter.get("min")) and JsonValues.is_number(parameter.get("max")) \
                    and parameter["min"] > parameter["max"]:
                errors.append("Parameter %s: Minimum > Maximum" % key)
            if "default" in parameter and parameter["default"] is not None:
                problem = ParameterRules.problem(parameter, parameter["default"])
                if problem:
                    errors.append("Parameter %s: Default %s" % (key, problem))
        return errors

    @staticmethod
    def _window_errors(by_key: Dict[Any, Dict[str, Any]]) -> List[str]:
        errors = []
        if not set(by_key["sashes"].get("options") or []) <= {0, 1, 2, 3}:
            errors.append("Parameter sashes: nur 0, 1, 2, 3 erlaubt")
        for i in (1, 2, 3):
            pane = by_key.get("opening_%d" % i)
            if pane and (pane.get("type") != "choice" or not set(pane.get("options") or []) <= PANE_OPENING_TYPES):
                errors.append("Parameter opening_%d: Auswahl aus %s" % (i, ", ".join(sorted(PANE_OPENING_TYPES))))
        return errors

    def _role_errors(self, element: Dict[str, Any]) -> List[str]:
        roles = [r for r in element.get("material_roles") or [] if isinstance(r, dict)]
        errors = ["Materialrolle %s doppelt" % key for key in self._duplicates([r.get("key") for r in roles])]
        for role in roles:
            default = role.get("default")
            if default is not None and not self.is_material(self._model, default):
                errors.append("Materialrolle %s: unbekannt: %s" % (role.get("key"), default))
        return errors

    @staticmethod
    def is_material(model: Dict[str, Any], ref: Any) -> bool:
        """Return True if ref is a `material:` reference of a loaded material."""
        return isinstance(ref, str) and ref.startswith("material:") and ref in model["elements"]
