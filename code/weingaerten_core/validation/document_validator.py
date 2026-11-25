"""Rules for documents (invoices, quotes): supplier, item references, related documents and sums."""
import logging
from typing import Any, Dict, List

from ..json_values import JsonValues
from .product_validator import ProductValidator

logger = logging.getLogger(__name__)

SUM_TOLERANCE = 0.05


class DocumentValidator:
    """Checks one document; references are errors, sums that do not add up are warnings."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the loaded model with companies, materials, components and documents.
        """
        self._model = model

    def errors(self, element: Dict[str, Any]) -> List[str]:
        """Return the reference errors of a document."""
        errors = []
        has_role = ProductValidator(self._model).company_has_role(element.get("supplier"), "supplier")
        if has_role is None:
            errors.append("supplier: unbekannt: %s" % element.get("supplier"))
        elif not has_role:
            errors.append("Firma ist kein Lieferant: %s" % element.get("supplier"))
        elements = self._model["elements"]
        tga_elements = (self._model.get("tga") or {}).get("elements") or {}
        for i, item in enumerate(element.get("items") or []):
            ref = item.get("ref") if isinstance(item, dict) else None
            if ref is not None and ref not in elements and ref not in tga_elements:
                errors.append("items[%d].ref: unbekannt: %s" % (i, ref))
        for i, ref in enumerate(element.get("related") or []):
            if ref not in elements:
                errors.append("related[%d]: unbekannt: %s" % (i, ref))
        return errors

    def warnings(self, element: Dict[str, Any]) -> List[str]:
        """Return `Belegsumme weicht ab: …` when items, subtotal, net and gross do not add up."""
        value = lambda key: float(element.get(key) or 0.0)
        items = [i for i in element.get("items") or [] if isinstance(i, dict)]
        found = []
        item_sum = sum(float(i["total_price"]) for i in items if JsonValues.is_number(i.get("total_price")))
        if element.get("items_gross") and JsonValues.is_number(element.get("vat_rate")):
            item_sum /= 1 + float(element["vat_rate"]) / 100.0
        if JsonValues.is_number(element.get("subtotal_net")) and abs(item_sum - value("subtotal_net")) > SUM_TOLERANCE:
            found.append("Positionen %.2f ≠ Zwischensumme %.2f" % (item_sum, value("subtotal_net")))
        net = value("subtotal_net") - value("discount_net") + value("shipping_net") - value("deductions_net")
        if JsonValues.is_number(element.get("total_net")) and abs(net - value("total_net")) > SUM_TOLERANCE:
            found.append("Netto %.2f ≠ %.2f" % (net, value("total_net")))
        if JsonValues.is_number(element.get("total_gross")) and \
                abs(value("total_net") + value("vat_amount") - value("total_gross")) > SUM_TOLERANCE:
            found.append("Brutto %.2f ≠ %.2f" % (value("total_net") + value("vat_amount"), value("total_gross")))
        return ["Belegsumme weicht ab: " + text for text in found]
