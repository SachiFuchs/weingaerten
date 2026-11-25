"""One opening of a wall, parsed and checked, in wall coordinates."""
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class OpeningData:
    """Rough opening and component dimensions of one wall opening.

    `u0`/`u1` run along the wall from its start, `z_bottom`/`z_top` are storey-local heights;
    the rough opening includes the joint on every side.
    """

    def __init__(self, source: Dict[str, Any], where: str, component_ref: str, component: Dict[str, Any],
                 component_class: Dict[str, Any], sizes: Dict[str, float],
                 reveal_material: Optional[str]) -> None:
        """Args:
            source: the opening JSON of the storey file.
            where: location for messages (`<storey>.<wall>.<opening>`).
            component_ref: the component reference.
            component: the component element.
            component_class: its class element.
            sizes: width, height, depth, frame_width, offset, sill, joint, inset (floats).
            reveal_material: material ref of the reveals, or None.
        """
        self.source = source
        self.id = source.get("id")
        self.where = where
        self.component_ref = component_ref
        self.component = component
        self.component_class = component_class
        self.geometry = component_class.get("geometry")
        self.params = component.get("params") or {}
        self.width = sizes["width"]
        self.height = sizes["height"]
        self.depth = sizes["depth"]
        self.frame_width = sizes["frame_width"]
        self.joint = sizes["joint"]
        self.inset = sizes["inset"]
        self.reveal_material = reveal_material
        self.u0 = sizes["offset"]
        self.u1 = sizes["offset"] + self.width + 2 * self.joint
        self.z_bottom = sizes["sill"]
        self.z_top = sizes["sill"] + self.height + 2 * self.joint

    @property
    def rough_area(self) -> float:
        """Area of the rough opening in the wall plane."""
        return (self.u1 - self.u0) * (self.z_top - self.z_bottom)
