"""Openings in the plan section: wall outline broken at the openings, opening symbols, dimension chains."""
import logging
from typing import Any, Callable, Dict, List

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools
from .dimension_svg import DimensionSvg
from .door_swing_svg import DoorSwingSvg
from .plan_geometry import PlanGeometry

logger = logging.getLogger(__name__)

Transform = Callable[[float], float]
LINE = '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%s"/>'
# the two glass lines of a pane, 6 mm to each side of its centre
GLASS_LINE_OFFSETS = (-0.006, 0.006)
escape = HtmlTools.escape


class OpeningSvg:
    """Draws the openings of the first storey cut at a given height."""

    def __init__(self, house: Dict[str, Any], to_x: Transform, to_y: Transform, scale: float) -> None:
        """Args:
            house: the HOUSE answer.
            to_x, to_y: plan → SVG transforms.
            scale: SVG pixels per metre.
        """
        self._house = house
        self._to_x, self._to_y = to_x, to_y
        self._scale = scale
        self._materials = house.get("materials", {})

    def _colour(self, ref: Any) -> str:
        return escape(((self._materials.get(ref) or {}).get("appearance") or {}).get("color", "#ccc"))

    def _xy(self, p: tuple) -> str:
        return "%.2f,%.2f" % (self._to_x(p[0]), self._to_y(p[1]))

    def render(self, cut_height: float) -> str:
        """Return the SVG of all walls; cut_height is storey-local (1.0 m)."""
        storey = (self._house.get("storeys") or [{}])[0]
        out = []
        for wall in storey.get("walls", []):
            frame = PlanGeometry(wall)
            out += self._outline(wall, frame, cut_height)
            out += [self._opening(wall, frame, opening, cut_height) for opening in wall.get("openings", [])]
            if wall.get("openings"):
                out.append(DimensionSvg.wall_chain(wall, frame, self._to_x, self._to_y))
        return "".join(out)

    @staticmethod
    def _is_cut(rough: Dict[str, Any], cut_height: float) -> bool:
        return rough["zb"] - 1e-6 <= cut_height <= rough["zt"] + 1e-6

    def _outline(self, wall: Dict[str, Any], frame: PlanGeometry, cut_height: float) -> List[str]:
        # the black wall outline is interrupted where the section cuts through an opening
        cuts = sorted((o["rough"]["u0"], o["rough"]["u1"]) for o in wall.get("openings", [])
                      if self._is_cut(o["rough"], cut_height))
        bounds = [None] + [x for cut in cuts for x in cut] + [None]
        direction = frame.direction
        out = []
        for k in range(0, len(bounds) - 1, 2):
            low, high = bounds[k], bounds[k + 1]
            polygon = [tuple(p) for p in wall["footprint"]]
            if low is not None:
                polygon = PlanGeometry.clip_half_plane(polygon, frame.along(low), direction)
            if high is not None and polygon:
                polygon = PlanGeometry.clip_half_plane(polygon, frame.along(high), (-direction[0], -direction[1]))
            if len(polygon) >= 3:
                out.append('<polygon points="%s" fill="none" stroke="#000" stroke-width="1.5" pointer-events="none"/>'
                           % " ".join(self._xy(p) for p in polygon))
        return out

    def _opening(self, wall: Dict[str, Any], frame: PlanGeometry, opening: Dict[str, Any], cut_height: float) -> str:
        rough = opening["rough"]
        group = ['<g class="opening" data-name="%s" data-id="%s" data-wall="%s" data-size="%s × %s cm" data-sill="%s">' % (
            escape(opening.get("name") or opening["component"]), escape(opening["id"]), escape(wall.get("name") or wall["id"]),
            escape(GermanFormat.decimal(rough["width"] * 100, 0)), escape(GermanFormat.decimal(rough["height"] * 100, 0)),
            escape(GermanFormat.centimetres(opening["sill"] or 0)))]
        thickness = frame.thickness
        rough_polygon = " ".join(self._xy(frame.point(u, t)) for u, t in
                                 ((rough["u0"], 0), (rough["u1"], 0), (rough["u1"], thickness), (rough["u0"], thickness)))
        if not self._is_cut(rough, cut_height):
            # openings above or below the section are shown dashed
            group.append('<polygon points="%s" fill="rgba(191,227,247,.25)" stroke="#1C69D4" stroke-width="1" '
                         'stroke-dasharray="4 3"/>' % rough_polygon)
        else:
            group.append('<polygon points="%s" fill="#fff" stroke="none"/>' % rough_polygon)
            group += self._cut_opening(wall, frame, opening, cut_height)
            if opening["geometry"] == "passage":
                # a passage has no frame: only the thin outline of the hole
                group.append('<polygon points="%s" fill="none" stroke="#888" stroke-width="0.6"/>' % rough_polygon)
        group.append("</g>")
        return "".join(group)

    def _cut_opening(self, wall: Dict[str, Any], frame: PlanGeometry, opening: Dict[str, Any],
                     cut_height: float) -> List[str]:
        rough, thickness = opening["rough"], frame.thickness
        to_x, to_y = self._to_x, self._to_y
        out = []
        if opening.get("reveal_material"):
            for u in (rough["u0"], rough["u1"]):
                out.append(LINE % (to_x(frame.point(u, 0)[0]), to_y(frame.point(u, 0)[1]), to_x(frame.point(u, thickness)[0]),
                                   to_y(frame.point(u, thickness)[1]), self._colour(opening["reveal_material"]), "2"))
        for part in opening["parts"]:
            out += self._part(wall, frame, part, cut_height)
        if opening["geometry"] == "door":
            out.append(DoorSwingSvg.render(opening, frame, to_x, to_y, self._scale, self._colour))
        return out

    def _part(self, wall: Dict[str, Any], frame: PlanGeometry, part: Dict[str, Any], cut_height: float) -> List[str]:
        center_z = part["center"][2] - wall["z0"]
        if not (center_z - part["size"][2] / 2 - 1e-6 <= cut_height <= center_z + part["size"][2] / 2 + 1e-6):
            return []
        center_x, center_y = part["center"][0], part["center"][1]
        half_along, half_across = part["size"][0] / 2, part["size"][1] / 2
        d, n = frame.direction, frame.normal
        if part["kind"] == "glass":
            out = []
            for offset in GLASS_LINE_OFFSETS:
                q0 = (center_x - d[0] * half_along + n[0] * offset, center_y - d[1] * half_along + n[1] * offset)
                q1 = (center_x + d[0] * half_along + n[0] * offset, center_y + d[1] * half_along + n[1] * offset)
                out.append(LINE % (self._to_x(q0[0]), self._to_y(q0[1]), self._to_x(q1[0]), self._to_y(q1[1]),
                                   "#2A7FB8", "1"))
            return out
        if part["kind"] == "leaf":
            # the leaf is drawn open by DoorSwingSvg
            return []
        corners = [(center_x + d[0] * sa * half_along + n[0] * sb * half_across,
                    center_y + d[1] * sa * half_along + n[1] * sb * half_across)
                   for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        return ['<polygon points="%s" fill="%s" stroke="#333" stroke-width="0.6"/>'
                % (" ".join(self._xy(c) for c in corners), self._colour(part["material"]))]
