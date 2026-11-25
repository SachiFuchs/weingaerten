"""Single-element rules: schema, layer order, references and the type-specific rules."""
import logging
from typing import Any, Dict, List

from ..compute.tga_assembly import TgaAssembly
from ..constants import LAYER_ORDER_BY_CATEGORY
from .class_validator import ClassValidator
from .component_validator import ComponentValidator
from .connection_validator import ConnectionValidator
from .document_validator import DocumentValidator
from .product_validator import ProductValidator
from .schema_validator import SchemaValidator
from .tga_tree_validator import TgaTreeValidator

logger = logging.getLogger(__name__)


class ElementValidator:
    """Checks one catalog element of any type (used by VALIDATE and before every SAVE)."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the loaded model with schemas and elements.
        """
        self._model = model

    def errors(self, ref: str, element: Dict[str, Any]) -> List[str]:
        """Return the German error messages of an element.

        Args:
            ref: the element reference (its type selects schema and rules).
            element: the element JSON.
        """
        element_type = ref.split(":")[0]
        errors = []
        schema = self._model["schemas"].get(element_type)
        if schema:
            errors += ["%s: %s" % (where, text) for where, text in SchemaValidator(schema).check(element, ref)]
        if element_type == "assembly":
            errors += self._assembly_errors(element)
        elif element_type == "class":
            errors += ClassValidator(self._model).errors(element)
        elif element_type == "component":
            errors += ComponentValidator(self._model).errors(element)
        elif element_type == "material":
            errors += ProductValidator(self._model).errors(element)
        elif element_type == "company":
            errors += self._company_errors(element)
        elif element_type == "document":
            errors += DocumentValidator(self._model).errors(element)
        elif element_type == "tga-tree":
            errors += TgaTreeValidator(self._model).tree_errors(element)
        elif element_type == "tga-component":
            if element.get("class") not in ((self._model.get("tga") or {}).get("elements") or {}):
                errors.append("class: unbekannt: %s" % element.get("class"))
            if element.get("abstract"):
                return errors + TgaTreeValidator(self._model).abstract_errors(element)
            if TgaAssembly.is_assembly(element):
                tga = (self._model.get("tga") or {}).get("elements") or {}
                return errors + TgaAssembly(tga).errors(element) + ProductValidator(self._model).errors(element)
            errors += TgaTreeValidator.install_errors(element)
            errors += ConnectionValidator(self._model).errors(ref, element)
            material = element.get("catalog_material")
            if material is not None and not (isinstance(material, str) and material.startswith("material:")
                                             and material in self._model["elements"]):
                errors.append("catalog_material: unbekannt: %s" % material)
            offer = element.get("material_offer")
            if offer is not None:
                offers = ((self._model["elements"].get(material) or {}).get("product") or {}).get("offers") or []
                if not isinstance(offer, int) or isinstance(offer, bool) or not 0 <= offer < len(offers):
                    errors.append("material_offer: kein Angebot %s am Material" % offer)
            errors += ProductValidator(self._model).errors(element)
        return errors

    def _assembly_errors(self, element: Dict[str, Any]) -> List[str]:
        errors = []
        category, layer_order = element.get("category"), element.get("layer_order")
        if category in LAYER_ORDER_BY_CATEGORY and layer_order != LAYER_ORDER_BY_CATEGORY[category]:
            errors.append("layer_order '%s' passt nicht zu category '%s' (erwartet %s)"
                          % (layer_order, category, LAYER_ORDER_BY_CATEGORY[category]))
        for i, layer in enumerate(element.get("layers", []) or []):
            if isinstance(layer, dict) and not ClassValidator.is_material(self._model, layer.get("material")):
                errors.append("layers[%d]: unbekannt: %s" % (i, layer.get("material")))
        return errors

    @staticmethod
    def _company_errors(element: Dict[str, Any]) -> List[str]:
        roles = element.get("roles") if isinstance(element.get("roles"), list) else []
        if len(set(map(str, roles))) != len(roles):
            return ["roles: doppelte Rolle"]
        return []
