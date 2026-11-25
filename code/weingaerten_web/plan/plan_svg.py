"""The main plan SVG of /grundriss: rooms, outdoor areas, layers, openings, structure, foundation outline, labels and
dimensions."""
import logging
import math
from typing import Any, Dict

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools
from .dimension_svg import DimensionSvg
from .layer_svg import LayerSvg
from .opening_svg import OpeningSvg
from .outdoor_area_svg import OutdoorAreaSvg
from .light_well_svg import LightWellSvg
from .stair_svg import StairSvg
from .structure_svg import StructureSvg
from .waste_water_svg import WasteWaterSvg
from .water_supply_svg import WaterSupplySvg
from .electrical_svg import ElectricalSvg

logger = logging.getLogger(__name__)

SCALE = 60.0     # px per metre
MARGIN = 70.0    # px around the house for the dimension lines
CUT_HEIGHT = 1.0  # default storey-local height of the section in m
TWO_METRES = 2.0  # clear height of the dashed roof slope line
decimal = GermanFormat.decimal


class PlanSvg:
    """Renders the plan section of the first storey."""

    def __init__(self, house: Dict[str, Any], storey: Dict[str, Any], hatch_defs: str,
                 cut_height: float = CUT_HEIGHT) -> None:
        """Args:
            house: the HOUSE answer (with `bbox`).
            storey: its first storey.
            hatch_defs: the SVG `<defs>` with the hatch patterns.
            cut_height: storey-local height of the section in m.
        """
        self._cut = cut_height
        self._house = house
        self._storey = storey
        self._hatch_defs = hatch_defs
        x0, y0, x1, y1 = house["bbox"]
        foundation = house.get("foundation")
        if foundation:
            fx, fy, fw, fh = foundation["rect"]
            x0, y0, x1, y1 = min(x0, fx), min(y0, fy), max(x1, fx + fw), max(y1, fy + fh)
        self._origin = (x0, y0)
        self._size = ((x1 - x0) * SCALE + 2 * MARGIN, (y1 - y0) * SCALE + 2 * MARGIN)

    def to_x(self, x: float) -> float:
        """Plan x → SVG x."""
        return MARGIN + (x - self._origin[0]) * SCALE

    def to_y(self, y: float) -> float:
        """Plan y → SVG y."""
        return MARGIN + (y - self._origin[1]) * SCALE

    def render(self) -> str:
        """Return the complete `<svg>` element."""
        house, storey = self._house, self._storey
        svg = ['<svg viewBox="0 0 %.0f %.0f" style="width:100%%;background:#fff" '
               'font-family="Arial, Helvetica, sans-serif">' % self._size, self._hatch_defs]
        for room in storey["rooms"]:
            svg.append('<polygon points="%s" fill="#F7F3EA"/>' % self._points(room["polygon"]))
        svg.append(self._shafts())
        svg.append(OutdoorAreaSvg.render(storey, self.to_x, self.to_y, SCALE))
        svg.append(StairSvg(self.to_x, self.to_y).render(storey))
        cut = self._cut
        svg.append(LayerSvg.render(house, self.to_x, self.to_y, "layer", storey["elevation"] + cut))
        svg.append(OpeningSvg(house, self.to_x, self.to_y, SCALE).render(cut))
        svg.append(StructureSvg(house, self.to_x, self.to_y).render(storey, storey["elevation"] + cut))
        svg.append(LightWellSvg(self.to_x, self.to_y).render(storey))
        ground = abs(storey["elevation"] - (house.get("foundation") or {}).get("top", 0.0)) < 1e-6
        svg.append(WasteWaterSvg(self.to_x, self.to_y, SCALE).render(house.get("waste_water"), storey, ground))
        svg.append(WaterSupplySvg(self.to_x, self.to_y, SCALE).render(house.get("water_supply"), storey))
        svg.append(ElectricalSvg(self.to_x, self.to_y, SCALE).render(house.get("electrical"), storey))
        svg.append(self._foundation_outline())
        svg.append(self._two_metre_lines())
        for room in storey["rooms"]:
            svg.append(self._room_labels(room))
        for wall in storey["walls"]:
            svg.append(self._wall_label(wall))
        bx0, by0, bx1, by1 = house["bbox"]
        svg.append(DimensionSvg.horizontal(self.to_x(bx0), MARGIN - 45, self.to_x(bx1), MARGIN - 45,
                                           decimal(bx1 - bx0, 2), "#000"))
        svg.append(DimensionSvg.vertical(MARGIN - 45, self.to_y(by0), MARGIN - 45, self.to_y(by1),
                                         decimal(by1 - by0, 2), "#000"))
        svg.append("</svg>")
        return "".join(svg)

    def _two_metre_lines(self) -> str:
        # roof slope: dashed lines where the roof underside (storey.roof) is 2 m above the floor, on both sides of the
        # ridge, across the extent of the storey's walls
        storey = self._storey
        roof = storey.get("roof")
        if not roof or roof["knee_wall_height"] >= TWO_METRES or roof["ridge_height"] <= TWO_METRES:
            return ""
        distance = (TWO_METRES - roof["knee_wall_height"]) / math.tan(math.radians(roof["pitch"]))
        points = [p for wall in storey["walls"] for p in wall["footprint"]]
        if not points:
            return ""
        along = 1 if roof["ridge_direction"] == "south_north" else 0
        low, high = min(p[along] for p in points), max(p[along] for p in points)
        lines = []
        for c in (roof["eaves"][0] + distance, roof["eaves"][1] - distance):
            (ax, ay), (bx, by) = ((c, low), (c, high)) if along == 1 else ((low, c), (high, c))
            lines.append('<line class="line2m" x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#555" '
                         'stroke-dasharray="8 4" pointer-events="none"/>'
                         % (self.to_x(ax), self.to_y(ay), self.to_x(bx), self.to_y(by)))
            lines.append('<text x="%.1f" y="%.1f" font-size="11" fill="#555">2 m</text>'
                         % (self.to_x((ax + bx) / 2) + 4, self.to_y((ay + by) / 2) - 4))
        return "".join(lines)

    def _foundation_outline(self) -> str:
        foundation = self._house.get("foundation")
        if not foundation:
            return ""
        x, y, w, h = foundation["rect"]
        polygon = foundation.get("polygon") or [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
        return '<polygon points="%s" fill="none" stroke="#888" stroke-dasharray="6 4" pointer-events="none"/>' % " ".join(
            "%.2f,%.2f" % (self.to_x(p[0]), self.to_y(p[1])) for p in polygon)

    def _points(self, polygon: Any) -> str:
        return " ".join("%.2f,%.2f" % (self.to_x(p[0]), self.to_y(p[1])) for p in polygon)

    def _shafts(self) -> str:
        # shafts opening a floor or a ceiling of this storey: hatched, with their name
        parts = []
        for shaft in self._house.get("shafts") or []:
            if self._storey["ref"] not in shaft["floor_storeys"] + shaft["ceiling_storeys"]:
                continue
            xs, ys = [p[0] for p in shaft["polygon"]], [p[1] for p in shaft["polygon"]]
            parts.append('<g class="shaft"><title>%s</title><polygon points="%s" fill="url(#hatch-shaft)" stroke="#6A1B9A" '
                         'stroke-width="1.5" stroke-dasharray="5 3"/><line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" '
                         'stroke="#6A1B9A"/><line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="#6A1B9A"/></g>'
                         % (HtmlTools.escape("Schacht %s (%s)" % (shaft["name"], shaft["id"])), self._points(shaft["polygon"]),
                            self.to_x(min(xs)), self.to_y(min(ys)), self.to_x(max(xs)), self.to_y(max(ys)),
                            self.to_x(min(xs)), self.to_y(max(ys)), self.to_x(max(xs)), self.to_y(min(ys))))
        if not parts:
            return ""
        return ('<defs><pattern id="hatch-shaft" width="6" height="6" patternUnits="userSpaceOnUse">'
                '<rect width="6" height="6" fill="#F3E5F5"/><path d="M0,6 L6,0" stroke="#AB47BC" stroke-width="1"/>'
                '</pattern></defs>' + "".join(parts))

    def _room_labels(self, room: Dict[str, Any]) -> str:
        polygon = room["polygon"]
        xs, ys = [p[0] for p in polygon], [p[1] for p in polygon]
        # the label sits in the largest rect of the decomposition, so it stays inside L-shaped rooms
        x, y, w, h = max(room["rects"], key=lambda r: r[2] * r[3])
        center_x, center_y = self.to_x(x + w / 2), self.to_y(y + h / 2)
        title = room["name"] if not room.get("number") else "%s %s" % (room["number"], room["name"])
        parts = ['<g class="roomlabel" pointer-events="none">'
                 '<text x="%.1f" y="%.1f" text-anchor="middle" font-size="16" font-weight="bold">%s</text>'
                 % (center_x, center_y - 10, HtmlTools.escape(title))]
        if len(polygon) == 4:
            parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="13">%s × %s m</text>'
                         % (center_x, center_y + 8, decimal(max(xs) - min(xs), 2), decimal(max(ys) - min(ys), 2)))
        parts.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="13">%s m²</text></g>'
                     % (center_x, center_y + (26 if len(polygon) == 4 else 8), decimal(room["area"], 2)))
        if len(polygon) == 4:
            x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
            parts += [DimensionSvg.horizontal(self.to_x(x0), self.to_y(y0) + 40, self.to_x(x1), self.to_y(y0) + 40,
                                              decimal(x1 - x0, 2), "#777"),
                      DimensionSvg.vertical(self.to_x(x0) + 40, self.to_y(y0), self.to_x(x0) + 40, self.to_y(y1),
                                            decimal(y1 - y0, 2), "#777")]
        return "".join(parts)

    def _wall_label(self, wall: Dict[str, Any]) -> str:
        # wall name in the middle of the footprint, along the wall and kept upright
        footprint = wall.get("footprint") or []
        if not footprint or not wall.get("name"):
            return ""
        center_x = self.to_x(sum(p[0] for p in footprint) / len(footprint))
        center_y = self.to_y(sum(p[1] for p in footprint) / len(footprint))
        (sx, sy), (ex, ey) = wall["start"], wall["end"]
        angle = math.degrees(math.atan2(ey - sy, ex - sx))
        if angle > 90 or angle <= -90:
            angle -= 180 if angle > 0 else -180
        return ('<text class="walllabel" x="%.1f" y="%.1f" text-anchor="middle" dominant-baseline="central" '
                'font-size="11" fill="#1C69D4" stroke="#fff" stroke-width="3" paint-order="stroke" '
                'pointer-events="none" transform="rotate(%.1f %.1f %.1f)">%s</text>'
                % (center_x, center_y, angle, center_x, center_y, HtmlTools.escape(wall["name"])))
