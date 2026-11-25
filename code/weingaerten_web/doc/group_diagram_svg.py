"""Class diagram of one sub package for /techdoku: module boxes in a grid, arrows for the imports between them."""
import logging
from typing import Any, Callable, Dict, List, Tuple

from ..rendering.html_tools import HtmlTools
from .class_diagram_svg import ClassDiagramSvg

logger = logging.getLogger(__name__)

COLUMNS = 4
BOX_WIDTH = 210
BOX_HEIGHT = 40
GAP_X = 60
GAP_Y = 46
MARGIN = 20
Point = Tuple[float, float]


class GroupDiagramSvg:
    """Draws the modules of a sub package; used modules of other sub packages appear dashed on the right."""

    def __init__(self, link: Callable[[str], str]) -> None:
        """Args:
            link: module name -> url of its node ("" when it has none).
        """
        self._link = link

    def render(self, members: List[Dict[str, Any]], all_modules: List[Dict[str, Any]]) -> str:
        """Return the SVG markup of the sub package `members`."""
        names = [m["module"] for m in members]
        known = {m["module"]: m for m in all_modules}
        edges, external = self._edges(members, set(names), known)
        boxes: Dict[str, Point] = {}
        for index, name in enumerate(names):
            boxes[name] = (MARGIN + (index % COLUMNS) * (BOX_WIDTH + GAP_X), MARGIN + (index // COLUMNS) * (BOX_HEIGHT + GAP_Y))
        right = MARGIN + COLUMNS * (BOX_WIDTH + GAP_X) + GAP_X
        for index, name in enumerate(external):
            boxes[name] = (right, MARGIN + index * (BOX_HEIGHT + 14))
        width = right + BOX_WIDTH + MARGIN if external else right - GAP_X
        height = max(y for _, y in boxes.values()) + BOX_HEIGHT + MARGIN if boxes else 2 * MARGIN
        parts = ['<svg xmlns="http://www.w3.org/2000/svg" class="tdgroup" width="%d" height="%d" viewBox="0 0 %d %d" '
                 'font-family="Consolas,monospace" font-size="12">' % (width, height, width, height),
                 '<defs><marker id="tdgarrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                 'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#1C69D4"/></marker></defs>']
        parts.extend(self._arrow(boxes[a], boxes[b], a, b) for a, b in edges)
        parts.extend(self._box(name, boxes[name], known.get(name), name in external) for name in boxes)
        return "".join(parts) + "</svg>"

    @staticmethod
    def _edges(members: List[Dict[str, Any]], inside: set, known: Dict[str, Any]) -> Tuple[List[Tuple[str, str]], List[str]]:
        edges, external = [], []
        for module in members:
            for target in ClassDiagramSvg.resolve(module["module"], module["imports"]):
                if target not in known or target == module["module"]:
                    continue
                edges.append((module["module"], target))
                if target not in inside and target not in external:
                    external.append(target)
        return edges, sorted(external)

    def _box(self, name: str, origin: Point, module: Any, dashed: bool) -> str:
        x, y = origin
        label = ", ".join(c["name"] for c in module["classes"]) if module else ""
        label = label or name.split(".")[-1] + ".py"
        detail = name if dashed else "%d Zeilen" % module["lines"]
        box = ('<g data-mod="%s"><rect x="%d" y="%d" width="%d" height="%d" fill="%s" stroke="#262626"%s/>'
               '<text x="%d" y="%d" fill="#1C69D4" font-weight="bold">%s</text><text x="%d" y="%d" fill="#666" font-size="10">%s</text></g>'
               % (HtmlTools.escape(name), x, y, BOX_WIDTH, BOX_HEIGHT, "#F7F7F7" if dashed else "#fff",
                  ' stroke-dasharray="4 3"' if dashed else "", x + 8, y + 17, HtmlTools.escape(label[:28]),
                  x + 8, y + 32, HtmlTools.escape(detail)))
        url = self._link(name)
        return '<a href="%s">%s</a>' % (HtmlTools.escape(url), box) if url else box

    @staticmethod
    def _arrow(source: Point, target: Point, source_name: str, target_name: str) -> str:
        start = GroupDiagramSvg._edge_point(source, target)
        end = GroupDiagramSvg._edge_point(target, source)
        return ('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#1C69D4" stroke-opacity="0.35" '
                'marker-end="url(#tdgarrow)" data-from="%s" data-to="%s"/>'
                % (start[0], start[1], end[0], end[1], HtmlTools.escape(source_name), HtmlTools.escape(target_name)))

    @staticmethod
    def _edge_point(origin: Point, toward: Point) -> Point:
        # where the line from the centre of the origin box to the centre of the other box leaves the origin box
        cx, cy = origin[0] + BOX_WIDTH / 2, origin[1] + BOX_HEIGHT / 2
        dx, dy = toward[0] + BOX_WIDTH / 2 - cx, toward[1] + BOX_HEIGHT / 2 - cy
        if dx == 0 and dy == 0:
            return cx, cy
        scale = min(BOX_WIDTH / 2 / abs(dx) if dx else float("inf"), BOX_HEIGHT / 2 / abs(dy) if dy else float("inf"))
        return cx + dx * scale, cy + dy * scale
