"""Rules for components (parameter values and material roles of their class, product)."""
import logging
from typing import Any, Dict, List, Optional

from .class_validator import ClassValidator
from .parameter_rules import ParameterRules
from .product_validator import ProductValidator

logger = logging.getLogger(__name__)


class ComponentValidator:
    """Checks a `component:` element against its class."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the loaded model with classes, materials and companies.
        """
        self._model = model

    def errors(self, element: Dict[str, Any], component_class: Optional[Dict[str, Any]] = None) -> List[str]:
        """Return the errors of a component.

        Args:
            element: the component.
            component_class: class to check against instead of the referenced one (used before saving a class).
        """
        if component_class is None:
            class_ref = element.get("class", "")
            component_class = self._model["elements"].get(class_ref) if str(class_ref).startswith("class:") else None
        if not isinstance(component_class, dict):
            return ["unbekannt: %s" % element.get("class")]
        errors = self._parameter_errors(element, component_class)
        errors += self._material_errors(element, component_class)
        errors += ProductValidator(self._model).errors(element)
        return errors

    @staticmethod
    def _parameter_errors(element: Dict[str, Any], component_class: Dict[str, Any]) -> List[str]:
        parameters = {p.get("key"): p for p in component_class.get("parameters") or [] if isinstance(p, dict)}
        values = element.get("params") if isinstance(element.get("params"), dict) else {}
        errors = []
        for key, parameter in parameters.items():
            if key not in values:
                if parameter.get("required"):
                    errors.append("Parameter %s fehlt" % key)
                continue
            problem = ParameterRules.problem(parameter, values[key])
            if problem:
                errors.append("Parameter %s (%s): %s" % (key, parameter.get("name", key), problem))
        errors += ["unbekannter Parameter %s" % key for key in values if key not in parameters]
        return errors

    def _material_errors(self, element: Dict[str, Any], component_class: Dict[str, Any]) -> List[str]:
        roles = {r.get("key") for r in component_class.get("material_roles") or [] if isinstance(r, dict)}
        materials = element.get("materials") if isinstance(element.get("materials"), dict) else {}
        errors = []
        for key in roles:
            if key not in materials:
                errors.append("Materialrolle %s fehlt" % key)
            elif not ClassValidator.is_material(self._model, materials[key]):
                errors.append("Materialrolle %s: unbekannt: %s" % (key, materials[key]))
        errors += ["unbekannte Materialrolle %s" % key for key in materials if key not in roles]
        return errors
