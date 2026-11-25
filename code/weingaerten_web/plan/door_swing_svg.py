"""The door leaf and its swing arc in the plan section."""
import logging
from typing import Any, Callable, Dict

from .plan_geometry import PlanGeometry

logger = logging.getLogger(__name__)

Transform = Callable[[float], float]


class DoorSwingSvg:
    """Draws an open door leaf (perpendicular to the wall) and the dashed quarter circle it sweeps."""

    @staticmethod
    def render(opening: Dict[str, Any], frame: PlanGeometry, to_x: Transform, to_y: Transform, scale: float,
               colour: Callable[[Any], str]) -> str:
        """Return the leaf line and the arc.

        Args:
            opening: a door opening of the HOUSE answer.
            frame: plan frame of its wall.
            to_x, to_y: plan → SVG transforms.
            scale: SVG pixels per metre (arc radius).
            colour: material ref → escaped fill colour.
        """
        rough, params = opening["rough"], opening["params"]
        joint, frame_width, depth = opening["joint"], params["frame_width"], params["depth"]
        clear_width = rough["u1"] - rough["u0"] - 2 * joint - 2 * frame_width
        hinge_left = (opening.get("swing") or "left") == "left"
        hinge_u = rough["u0"] + joint + frame_width if hinge_left else rough["u1"] - joint - frame_width
        # the leaf opens to the inside, hinged at the inner edge of the component
        hinge = frame.point(hinge_u, opening["inset"] + depth)
        normal = frame.normal
        leaf_end = (hinge[0] + normal[0] * clear_width, hinge[1] + normal[1] * clear_width)
        towards_latch = frame.direction if hinge_left else (-frame.direction[0], -frame.direction[1])
        closed_end = (hinge[0] + towards_latch[0] * clear_width, hinge[1] + towards_latch[1] * clear_width)
        leaf_material = (opening.get("parts") and next((x["material"] for x in opening["parts"] if x["kind"] == "leaf"), None))
        out = ['<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="3"/>' % (
            to_x(hinge[0]), to_y(hinge[1]), to_x(leaf_end[0]), to_y(leaf_end[1]), colour(leaf_material))]
        # the sign of the cross product picks the SVG sweep flag
        cross = (leaf_end[0] - hinge[0]) * (closed_end[1] - hinge[1]) - (leaf_end[1] - hinge[1]) * (closed_end[0] - hinge[0])
        out.append('<path d="M %.2f %.2f A %.2f %.2f 0 0 %d %.2f %.2f" fill="none" stroke="#555" stroke-width="0.8" '
                   'stroke-dasharray="5 3"/>' % (to_x(leaf_end[0]), to_y(leaf_end[1]), clear_width * scale,
                                                 clear_width * scale, 1 if cross > 0 else 0,
                                                 to_x(closed_end[0]), to_y(closed_end[1])))
        return "".join(out)
