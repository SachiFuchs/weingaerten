"""TGA_CATALOG: every tga-class and tga-component with derived conductors and the connection issues."""
import logging
from typing import Any, Dict

from ..compute.tga_assembly import TgaAssembly
from ..compute.tga_tree import TgaTree
from ..model.tga_products import TgaProducts
from ..validation.conductor_roles import ConductorRoles

logger = logging.getLogger(__name__)

TGA_FILES = {"tga-class": "catalog/tga-classes/%s.json", "tga-component": "catalog/tga-components/%s.json",
             "tga-tree": "catalog/tga-trees/%s.json"}


class TgaCatalog:
    """Answer of TGA_CATALOG (the TGA catalog page loads everything with one call)."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the computed model.
        """
        self._model = model

    def build(self) -> Dict[str, Any]:
        """Return `{elements, conductors, issues, abstracts, assemblies, trees, placement}`; `material_product` = product
        taken from catalog_material, `abstracts` = concretisations per abstract TGA object (deprecated, shown read-only),
        `assemblies` = main object, parts and capacity per TGA assembly, `placement` = effective suitability."""
        tga = self._model.get("tga") or {}
        products = TgaProducts(self._model)
        elements, conductors = {}, {}
        for ref, element in sorted((tga.get("elements") or {}).items()):
            kind, eid = ref.split(":", 1)
            elements[ref] = dict(element, ref=ref, type=kind, file=TGA_FILES[kind] % eid)
            material_product = (products.material_of(element) or {}).get("product")
            if isinstance(material_product, dict):
                elements[ref]["material_product"] = material_product
            if (tga["elements"].get(element.get("class")) or {}).get("kind") == "cable":
                conductors[ref] = ConductorRoles.of(element)
        issues = [dict(i, level=level) for level in ("errors", "warnings") for i in self._model[level]
                  if str(i.get("where", "")).startswith(("tga-", "catalog/tga-"))]
        tree = TgaTree(tga.get("elements") or {})
        assembly = TgaAssembly(tga.get("elements") or {})
        abstracts = {ref: tree.abstract_of(ref) for ref, e in (tga.get("elements") or {}).items() if e.get("abstract")}
        assemblies = {ref: assembly.summary(e) for ref, e in (tga.get("elements") or {}).items()
                      if TgaAssembly.is_assembly(e)}
        return {"elements": elements, "conductors": conductors, "issues": issues, "abstracts": abstracts,
                "assemblies": assemblies, "trees": tree.trees(),
                "placement": {r: TgaTree.placement_of(assembly.effective(tga["elements"][r])) for r in elements
                              if r.startswith("tga-component:")}}
