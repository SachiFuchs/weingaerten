"""Component parts (frame, mullions, sashes, glass, door leaf) of an opening as oriented boxes."""
import logging
from typing import Any, Dict, List

from .opening_data import OpeningData
from .wall_data import WallData
from .window_panes import WindowPanes

logger = logging.getLogger(__name__)

GLASS_THICKNESS = 0.024
# sash bars are slimmer and thinner than the frame
SASH_WIDTH_FACTOR = 0.6
SASH_DEPTH_FACTOR = 0.8
LEAF_DEPTH_FACTOR = 0.6


class OpeningPartsBuilder:
    """Places the parts of a window or door in the clear opening of one wall opening."""

    def __init__(self, wall: WallData, opening: OpeningData, z0: float) -> None:
        """Args:
            wall: the wall of the opening.
            opening: the opening.
            z0: storey elevation.
        """
        self._wall = wall
        self._opening = opening
        self._z0 = z0
        self._materials = opening.component.get("materials") or {}
        self._direction = wall.degrees
        self._depth_middle = opening.inset + opening.depth / 2.0
        self._parts: List[Dict[str, Any]] = []

    def build(self) -> List[Dict[str, Any]]:
        """Return the parts `{kind, material, center, size, direction, volume}` in drawing order (none for a passage)."""
        opening = self._opening
        if opening.geometry == "passage":
            return self._parts
        joint, frame, depth = opening.joint, opening.frame_width, opening.depth
        left, right = opening.u0 + joint, opening.u1 - joint
        bottom, top = opening.z_bottom + joint, opening.z_top - joint
        self._box("frame", "frame", left, left + frame, bottom, top, depth)
        self._box("frame", "frame", right - frame, right, bottom, top, depth)
        self._box("frame", "frame", left + frame, right - frame, top - frame, top, depth)
        if opening.geometry == "window":
            self._box("frame", "frame", left + frame, right - frame, bottom, bottom + frame, depth)
            self._window_panes(left + frame, right - frame, bottom + frame, top - frame)
        else:
            self._box("leaf", "leaf", left + frame, right - frame, bottom, top - frame, LEAF_DEPTH_FACTOR * depth)
        return self._parts

    def _window_panes(self, inner_left: float, inner_right: float, inner_bottom: float, inner_top: float) -> None:
        opening = self._opening
        frame, depth = opening.frame_width, opening.depth
        sashes = opening.params.get("sashes", 0) or 0
        pane_types = WindowPanes.opening_types(opening.params)
        count = len(pane_types)
        pane_width = (inner_right - inner_left - (count - 1) * frame) / count
        panes = []
        for k in range(count):
            pane_left = inner_left + k * (pane_width + frame)
            panes.append((pane_left, pane_left + pane_width))
            if k < count - 1:
                self._box("mullion", "frame", pane_left + pane_width, pane_left + pane_width + frame,
                          inner_bottom, inner_top, depth)
        for (pane_left, pane_right), pane_type in zip(panes, pane_types):
            glass = (pane_left, pane_right, inner_bottom, inner_top)
            if sashes >= 1 and pane_type != "fixed":
                glass = self._sash(pane_left, pane_right, inner_bottom, inner_top)
            self._box("glass", "glazing", glass[0], glass[1], glass[2], glass[3], GLASS_THICKNESS)

    def _sash(self, pane_left: float, pane_right: float, bottom: float, top: float) -> tuple:
        # four sash bars around the pane; returns the remaining glass rectangle
        bar = SASH_WIDTH_FACTOR * self._opening.frame_width
        depth = SASH_DEPTH_FACTOR * self._opening.depth
        self._box("sash", "frame", pane_left, pane_left + bar, bottom, top, depth)
        self._box("sash", "frame", pane_right - bar, pane_right, bottom, top, depth)
        self._box("sash", "frame", pane_left + bar, pane_right - bar, top - bar, top, depth)
        self._box("sash", "frame", pane_left + bar, pane_right - bar, bottom, bottom + bar, depth)
        return (pane_left + bar, pane_right - bar, bottom + bar, top - bar)

    def _box(self, kind: str, role: str, u_a: float, u_b: float, z_a: float, z_b: float, depth: float) -> None:
        # every part is centred in the depth of the component
        center = self._wall.point_3d((u_a + u_b) / 2.0, self._depth_middle, (z_a + z_b) / 2.0, self._z0)
        size = [u_b - u_a, depth, z_b - z_a]
        self._parts.append({"kind": kind, "material": self._materials.get(role), "center": center, "size": size,
                            "direction": self._direction, "volume": size[0] * size[1] * size[2]})
