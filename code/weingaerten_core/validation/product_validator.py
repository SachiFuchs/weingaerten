"""Rules for the optional product data of a component or material (manufacturer, supplier offers)."""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ProductValidator:
    """Checks that the companies named in a product have the required roles."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the loaded model with the companies.
        """
        self._model = model

    def errors(self, element: Dict[str, Any], companies: Optional[Dict[str, Any]] = None) -> List[str]:
        """Return the product errors of a component.

        Args:
            element: the component.
            companies: companies that override the loaded ones (used to test a company before it is saved).
        """
        product = element.get("product")
        if not isinstance(product, dict):
            return []
        errors = []
        manufacturer = product.get("manufacturer")
        if manufacturer is not None:
            has_role = self.company_has_role(manufacturer, "manufacturer", companies)
            if has_role is None:
                errors.append("product.manufacturer: unbekannt: %s" % manufacturer)
            elif not has_role:
                errors.append("Firma ist kein Hersteller: %s" % manufacturer)
        for i, offer in enumerate(product.get("offers") or []):
            if not isinstance(offer, dict):
                continue
            has_role = self.company_has_role(offer.get("supplier"), "supplier", companies)
            if has_role is None:
                errors.append("product.offers[%d].supplier: unbekannt: %s" % (i, offer.get("supplier")))
            elif not has_role:
                errors.append("Firma ist kein Lieferant: %s" % offer.get("supplier"))
            document = offer.get("document")
            if document is not None and document not in self._model["elements"]:
                errors.append("product.offers[%d].document: unbekannt: %s" % (i, document))
        return errors

    def company_has_role(self, ref: Any, role: str, companies: Optional[Dict[str, Any]] = None) -> Optional[bool]:
        """Return whether the company has the role, or None if ref is not a known company."""
        company = None
        if isinstance(ref, str) and ref.startswith("company:"):
            company = (companies or {}).get(ref) or self._model["elements"].get(ref)
        if not isinstance(company, dict):
            return None
        return role in (company.get("roles") or [])
