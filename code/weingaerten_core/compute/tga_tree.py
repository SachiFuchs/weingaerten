"""TGA trees: resolved nodes (concrete objects and assemblies; abstract objects are deprecated) and the placement."""
import logging
from typing import Any, Dict, List, Optional

from ..json_values import JsonValues
from ..validation.tga_tree_validator import TgaTreeValidator
from .tga_assembly import TgaAssembly

logger = logging.getLogger(__name__)

MOUNTING_MODES = {"surface": ["on"], "flush": ["in"], "hollow_wall": ["in"]}
HOSTS = ["wall", "floor", "ceiling", "roof"]


class TgaTree:
    """Builds the trees of catalog/tga-trees for the palette and checks the placement of installed parts."""

    def __init__(self, elements: Dict[str, Any]) -> None:
        """Args:
            elements: model["tga"]["elements"].
        """
        self._elements = elements
        self._assemblies = TgaAssembly(elements)

    def trees(self) -> List[Dict[str, Any]]:
        """Return `[{ref, id, name, nodes}]` sorted by order/name; object nodes carry name, `assembly` (bool),
        `placement` and `deprecated` (abstract object, never offered)."""
        trees = [(ref, e) for ref, e in self._elements.items() if ref.startswith("tga-tree:")]
        trees.sort(key=lambda t: (t[1].get("order", 0), t[1].get("name") or ""))
        return [{"ref": ref, "id": tree.get("id"), "name": tree.get("name"), "nodes": self._nodes(tree.get("nodes"))}
                for ref, tree in trees]

    def _nodes(self, nodes: Any) -> List[Dict[str, Any]]:
        out = []
        for node in nodes if isinstance(nodes, list) else []:
            if not isinstance(node, dict):
                continue
            ref = node.get("ref")
            if ref is None:
                out.append({"id": node.get("id"), "name": node.get("name"), "nodes": self._nodes(node.get("nodes"))})
                continue
            element = self._elements.get(ref) or {}
            row = {"id": node.get("id"), "name": node.get("name") or element.get("name") or ref, "ref": ref,
                   "missing": not element, "assembly": TgaAssembly.is_assembly(element),
                   "placement": self.placement_of(self._assemblies.effective(element))}
            if element.get("abstract"):
                row["deprecated"] = True
            out.append(row)
        return out

    def abstract_of(self, ref: str) -> Optional[Dict[str, Any]]:
        """Deprecated: axes, fixed params, candidates [{ref, name, values}] and default of an abstract TGA object."""
        element = self._elements.get(ref) or {}
        abstract = element.get("abstract")
        if not isinstance(abstract, dict):
            return None
        axes = [dict(a) for a in abstract.get("axes") or [] if isinstance(a, dict)]
        candidates = []
        for cref, candidate in sorted(self._elements.items()):
            if cref.startswith("tga-component:") and TgaTreeValidator.concretises(element, candidate):
                params = candidate.get("params") or {}
                candidates.append({"ref": cref, "name": candidate.get("name"),
                                   "values": {a["param"]: params.get(a["param"]) for a in axes},
                                   "placement": self.placement_of(candidate)})
        candidates.sort(key=lambda c: (tuple(self._sort_key(c["values"].get(a["param"])) for a in axes),
                                       len(c["ref"]), c["ref"]))
        default = abstract.get("default") or (candidates[0]["ref"] if candidates else None)
        return {"axes": axes, "fixed": dict(element.get("params") or {}), "candidates": candidates, "default": default}

    @staticmethod
    def _sort_key(value: Any) -> tuple:
        return (0, float(value), "") if JsonValues.is_number(value) else (1, 0.0, str(value))

    @staticmethod
    def placement_of(element: Dict[str, Any]) -> Dict[str, Any]:
        """Effective placement {hosts, modes, derived, none}: own block, else modes from connection.mounting (walls,
        ceilings ...), else `none` = no suitability (empty hosts/modes, never offered in a palette tree)."""
        own = element.get("placement")
        if isinstance(own, dict) and (own.get("hosts") or own.get("modes")):
            return {"hosts": list(own.get("hosts") or HOSTS), "modes": list(own.get("modes") or ["in", "on"]),
                    "derived": False, "none": False}
        mounting = (element.get("connection") or {}).get("mounting")
        if mounting in MOUNTING_MODES:
            return {"hosts": list(HOSTS), "modes": list(MOUNTING_MODES[mounting]), "derived": True, "none": False}
        return {"hosts": [], "modes": [], "derived": False, "none": True}

    def placement_warning(self, part: Dict[str, Any]) -> Optional[str]:
        """German warning if a wall-hosted part is not suited for walls or for its mode (depth < 0 = in the wall)."""
        if not part.get("host") or not JsonValues.is_number(part.get("depth")):
            return None
        element = self._assemblies.effective(self._elements.get(part.get("component")) or {})
        placement = self.placement_of(element)
        if placement["none"]:
            return None
        # boxes / inserts: front at the wall face (depth 0) = in, body in front of it (depth = box depth) = on;
        # pipes and cables: axis behind the face (depth < 0) = in
        size = part.get("size")
        own = float(size[2]) if part.get("shape") in ("box", "insert") and isinstance(size, list) and len(size) == 3 else 0.0
        mode = "in" if part["depth"] < own - 1e-6 else "on"
        if "wall" not in placement["hosts"]:
            return "TGA-Teil nicht für Wände geeignet"
        if mode not in placement["modes"]:
            return "TGA-Teil nicht geeignet für %s der Wand" % ("Einbau in" if mode == "in" else "Montage auf")
        return None
