"""Layer info of an assembly: thickness and the offset of every layer from the first face."""
import logging
from typing import Any, Dict, Optional

from ..json_values import JsonValues

logger = logging.getLogger(__name__)


class AssemblyInfo:
    """Derives the layer offsets of an assembly."""

    @staticmethod
    def of(model: Dict[str, Any], ref: Any) -> Optional[Dict[str, Any]]:
        """Return the layer info of an assembly.

        Args:
            model: the loaded model.
            ref: the assembly reference.

        Returns:
            `{ref, el, thickness, layers: [{index, material, offset, thickness}]}`, or None if the
            assembly is unknown or has no valid layers (missing or non-positive thickness).
        """
        assembly = model["elements"].get(ref)
        if not isinstance(assembly, dict) or not isinstance(assembly.get("layers"), list) or not assembly["layers"]:
            return None
        layers, offset = [], 0.0
        for i, layer in enumerate(assembly["layers"]):
            if not isinstance(layer, dict) or not JsonValues.is_number(layer.get("thickness")) or layer["thickness"] <= 0:
                return None
            layers.append({"index": i, "material": layer.get("material"), "offset": offset,
                           "thickness": float(layer["thickness"])})
            offset += layer["thickness"]
        return {"ref": ref, "el": assembly, "thickness": offset, "layers": layers}
