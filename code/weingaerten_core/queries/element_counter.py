"""Answer of the VALIDATE command: number of elements and house parts."""
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

COUNT_KEYS = {"material": "materials", "assembly": "assemblies",
              "class": "classes", "component": "components", "company": "companies",
              "document": "documents"}


class ElementCounter:
    """Counts catalog elements per type and the computed walls, openings, rooms, ceilings, structure and outdoor areas."""

    @staticmethod
    def counts(model: Dict[str, Any]) -> Dict[str, int]:
        """Return the `counts` object of VALIDATE."""
        counts = {key: 0 for key in COUNT_KEYS.values()}
        for ref in model["elements"]:
            counts[COUNT_KEYS[ref.split(":")[0]]] += 1
        storeys = model["storeys_out"]
        counts["storeys"] = len(model["storeys"])
        counts["walls"] = sum(len(s["walls"]) for s in storeys)
        counts["openings"] = sum(len(w["openings"]) for s in storeys for w in s["walls"])
        counts["rooms"] = sum(len(s["rooms"]) for s in storeys)
        counts["ceilings"] = sum(len(s["ceilings"]) for s in storeys)
        counts["structure"] = sum(len(s["structure"]) for s in storeys)
        counts["outdoor_areas"] = sum(len(s["outdoor_areas"]) for s in storeys)
        counts["roof_structure"] = sum(len(s["roof_structure"]["members"]) for s in storeys if s.get("roof_structure"))
        counts["roof_covering"] = sum(len(s["roof_covering"]["faces"]) for s in storeys if s.get("roof_covering"))
        counts["stairs"] = sum(len(s["stairs"]) for s in storeys)
        counts["floors"] = sum(len(s["floors"]) for s in storeys)
        counts["heating_circuits"] = sum(len(s["heating"]["circuits"]) for s in storeys if s.get("heating"))
        counts["wall_heating_circuits"] = sum(len(s["wall_heating"]["circuits"]) for s in storeys if s.get("wall_heating"))
        counts["light_wells"] = sum(len(s.get("light_wells") or []) for s in storeys)
        counts["facade_parts"] = sum(len(s["facade"]["parts"]) for s in storeys if s.get("facade"))
        counts["linings"] = sum(len(s.get("linings") or []) for s in storeys)
        counts["coverings"] = sum(len(r.get("coverings") or []) for s in storeys for r in s["rooms"])
        counts["shafts"] = len(model.get("shafts") or [])
        counts["parts"] = len((model.get("installation") or {}).get("parts") or [])
        return counts
