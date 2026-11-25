"""Answer of the HOUSE command: computed storeys plus the used materials, assemblies and components."""
import logging
from typing import Any, Dict, List, Optional, Set

from ..compute.assembly_info import AssemblyInfo

logger = logging.getLogger(__name__)


class HouseSummary:
    """Builds the HOUSE answer from a computed model."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the computed model.
        """
        self._model = model

    def build(self) -> Dict[str, Any]:
        """Return `{id, name, unit, valid, errors, bbox, foundation, storeys, materials, assemblies, components}`."""
        model = self._model
        house = model["house"] if isinstance(model["house"], dict) else {}
        used_materials, used_assemblies, used_components = self._used_refs()
        return {"id": house.get("id"), "name": house.get("name"), "unit": "m", "valid": not model["errors"],
                "errors": model["errors"], "bbox": self._bbox(), "foundation": model["foundation"],
                "storeys": model["storeys_out"], "materials": self._materials(used_materials),
                "assemblies": self._assemblies(used_assemblies), "components": self._components(used_components),
                "waste_water": model.get("waste_water"), "water_supply": model.get("water_supply"),
                "electrical": model.get("electrical"), "installation": model.get("installation"),
                "shafts": model.get("shafts") or []}

    def _bbox(self) -> Optional[List[float]]:
        points = [p for storey in self._model["storeys_out"] for wall in storey["walls"] for p in wall["footprint"]]
        foundation = self._model["foundation"]
        if foundation:
            x, y, w, h = foundation["rect"]
            points += [[x, y], [x + w, y + h]]
        if not points:
            return None
        return [min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points),
                max(p[1] for p in points)]

    def _used_refs(self) -> tuple:
        materials: Set[str] = set()
        assemblies: Set[str] = set()
        components: Set[str] = set()
        foundation = self._model["foundation"]
        if foundation:
            assemblies.add(foundation["assembly"])
            materials.update(layer["material"] for layer in foundation["layers"])
        for storey in self._model["storeys_out"]:
            for floor in storey["floors"]:
                assemblies.add(floor["assembly"])
                materials.update(layer["material"] for layer in floor["layers"])
            for ceiling in storey["ceilings"]:
                assemblies.add(ceiling["assembly"])
                materials.update(layer["material"] for layer in ceiling["layers"])
                if ceiling["joists"]:
                    materials.add(ceiling["joists"]["material"])
            materials.update(element["material"] for element in storey["structure"])
            materials.update(stair["material"] for stair in storey["stairs"])
            materials.update(part["material"] for well in storey.get("light_wells") or [] for part in well["parts"])
            if storey.get("roof_structure"):
                materials.add(storey["roof_structure"]["material"])
            facade = storey.get("facade")
            if facade:
                materials.update(ref for ref in (facade["material"], facade["paint"]) if ref)
            for lining in storey.get("linings") or []:
                assemblies.add(lining["assembly"])
                materials.update(layer["material"] for layer in lining["layers"])
            for room in storey["rooms"]:
                for room_covering in room.get("coverings") or []:
                    assemblies.add(room_covering["assembly"])
                    materials.update(layer["material"] for layer in room_covering["layers"])
            covering = storey.get("roof_covering")
            if covering:
                assemblies.add(covering["assembly"])
                materials.update(layer["material"] for face in covering["faces"] for layer in face["layers"])
                for opening in covering["openings"]:
                    components.update(ref for ref in [opening["component"], opening["flashing"]] + opening["parts"]
                                      if ref)
                    if opening["component"]:
                        materials.update(m for m in ((self._model["elements"].get(opening["component"]) or {})
                                                     .get("materials") or {}).values() if isinstance(m, str))
            for wall in storey["walls"]:
                assemblies.add(wall["assembly"])
                materials.update(layer["material"] for layer in wall["layers"])
                for opening in wall["openings"]:
                    components.add(opening["component"])
                    materials.update(part["material"] for part in opening["parts"] if part["material"])
                    if opening["reveal_material"]:
                        materials.add(opening["reveal_material"])
        return materials, assemblies, components

    def _materials(self, refs: Set[str]) -> Dict[str, Any]:
        elements = self._model["elements"]
        return {ref: {"name": elements[ref].get("name"), "category": elements[ref].get("category"),
                      "appearance": elements[ref].get("appearance"), "conductivity": elements[ref].get("conductivity")}
                for ref in sorted(refs) if ref in elements}

    def _assemblies(self, refs: Set[str]) -> Dict[str, Any]:
        elements = self._model["elements"]
        result = {}
        for ref in sorted(refs):
            info = AssemblyInfo.of(self._model, ref)
            if ref in elements and info:
                element = elements[ref]
                result[ref] = {"name": element.get("name"), "category": element.get("category"),
                               "layer_order": element.get("layer_order"), "thickness": info["thickness"],
                               "visualization": element.get("visualization")}
        return result

    def _components(self, refs: Set[str]) -> Dict[str, Any]:
        elements = self._model["elements"]
        result = {}
        for ref in sorted(refs):
            component = elements.get(ref)
            if component:
                result[ref] = {"name": component.get("name"), "class": component.get("class"),
                               "geometry": (elements.get(component.get("class")) or {}).get("geometry"),
                               "params": component.get("params"), "materials": component.get("materials")}
        return result
