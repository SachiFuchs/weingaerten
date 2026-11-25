"""Answer of the RESOLVE command: an element with all references replaced by the referenced elements."""
import logging
from typing import Any, Dict, Set

from ..compute.assembly_info import AssemblyInfo
from ..constants import REF_RE

logger = logging.getLogger(__name__)

# guards against reference cycles in the data
MAX_DEPTH = 20


class ReferenceResolver:
    """Resolves references recursively; assemblies additionally get thickness and layer offsets."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the loaded model.
        """
        self._model = model
        # refs being resolved on the current path: a reference back to one of them stays a ref string (cycles
        # such as material -> offer document -> item material would otherwise grow exponentially)
        self._path: Set[str] = set()

    def resolve_element(self, ref: str, element: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
        """Return `{ref, ...element}` with every nested reference resolved."""
        self._path.add(ref)
        try:
            out = {"ref": ref}
            out.update({key: self._resolve(value, depth) for key, value in element.items()})
        finally:
            self._path.discard(ref)
        if ref.startswith("assembly:"):
            info = AssemblyInfo.of(self._model, ref)
            if info:
                out["thickness"] = info["thickness"]
                for layer, layer_info in zip(out.get("layers", []), info["layers"]):
                    if isinstance(layer, dict):
                        layer["offset"] = layer_info["offset"]
        return out

    def _resolve(self, value: Any, depth: int) -> Any:
        if depth > MAX_DEPTH:
            return value
        if isinstance(value, str) and REF_RE.match(value):
            if value in self._path:
                return value
            element = self._model["elements"].get(value)
            if element is None and value in self._model["storeys"]:
                element = self._model["storeys"][value]
            return value if element is None else self.resolve_element(value, element, depth + 1)
        if isinstance(value, list):
            return [self._resolve(item, depth) for item in value]
        if isinstance(value, dict):
            return {key: self._resolve(item, depth) for key, item in value.items()}
        return value
