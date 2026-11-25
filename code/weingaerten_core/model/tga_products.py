"""Product data of a tga-component: the linked material (catalog_material) is the single source of product and offers."""
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TgaProducts:
    """Resolves the effective product of a tga-component and the reverse links material -> tga-components."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the loaded model (main catalog in model["elements"], TGA catalog in model["tga"]).
        """
        self._model = model

    def material_of(self, element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Return the material named by `catalog_material`, or None."""
        ref = element.get("catalog_material")
        if not isinstance(ref, str) or not ref.startswith("material:"):
            return None
        material = self._model["elements"].get(ref)
        return material if isinstance(material, dict) else None

    def product_of(self, element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Return the product of the linked material, else the component's own product (placeholders)."""
        product = (self.material_of(element) or {}).get("product")
        if isinstance(product, dict):
            return product
        own = element.get("product")
        return own if isinstance(own, dict) else None

    def offers_of(self, ref: str) -> List[Dict[str, Any]]:
        """Return the offers of a tga-component ref (empty if unknown or without product)."""
        element = ((self._model.get("tga") or {}).get("elements") or {}).get(ref)
        if not isinstance(element, dict):
            return []
        offers = [o for o in (self.product_of(element) or {}).get("offers") or [] if isinstance(o, dict)]
        # `material_offer` picks one offer of the shared material (e.g. price per panel type)
        index = element.get("material_offer")
        if isinstance(index, int) and self.material_of(element) is not None:
            return offers[index:index + 1]
        return offers

    def double_offers(self, element: Dict[str, Any]) -> bool:
        """Return whether component and linked material both carry offers (the component's are ignored)."""
        own = (element.get("product") or {}).get("offers") if isinstance(element.get("product"), dict) else None
        material = ((self.material_of(element) or {}).get("product") or {}).get("offers")
        return bool(own) and bool(material)
