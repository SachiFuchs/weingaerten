"""Class diagram of a package for /techdoku: one box per sub package, arcs for the imports between them."""
import logging
from typing import Any, Callable, Dict, List, Tuple

from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

BOX_WIDTH = 210
BOX_GAP = 46
HEADER_HEIGHT = 26
ROW_HEIGHT = 17
ARC_UNIT = 26
ROOT_GROUP = "(Wurzel)"


class ClassDiagramSvg:
    """Draws the diagram; the class names link to their module nodes."""

    def __init__(self, link: Callable[[Dict[str, Any]], str]) -> None:
        """Args:
            link: returns the url of a module's node.
        """
        self._link = link

    def render(self, modules: List[Dict[str, Any]]) -> str:
        """Return the SVG markup (escaped, no scripts)."""
        groups = self._groups(modules)
        names = list(groups)
        edges = self._edges(modules)
        arc_space = ARC_UNIT * (max([abs(names.index(a) - names.index(b)) for a, b in edges] or [0]) + 1) + 20
        height = arc_space + HEADER_HEIGHT + ROW_HEIGHT * max(len(g) for g in groups.values()) + 20
        width = len(names) * (BOX_WIDTH + BOX_GAP)
        parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
                 'font-family="Consolas,monospace" font-size="12">' % (width, height, width, height),
                 '<defs><marker id="tdarrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                 'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#1C69D4"/></marker></defs>']
        for index, name in enumerate(names):
            parts.append(self._box(index, arc_space, name, groups[name]))
        for (source, target), count in sorted(edges.items()):
            parts.append(self._arc(names.index(source), names.index(target), arc_space, count))
        return "".join(parts) + "</svg>"

    @staticmethod
    def _groups(modules: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for module in modules:
            groups.setdefault(module["group"] or ROOT_GROUP, []).append(module)
        return groups

    @staticmethod
    def _edges(modules: List[Dict[str, Any]]) -> Dict[Tuple[str, str], int]:
        known = {m["module"]: m["group"] or ROOT_GROUP for m in modules}
        edges: Dict[Tuple[str, str], int] = {}
        for module in modules:
            source = module["group"] or ROOT_GROUP
            for target in ClassDiagramSvg.resolve(module["module"], module["imports"]):
                group = known.get(target)
                if group and group != source:
                    edges[(source, group)] = edges.get((source, group), 0) + 1
        return edges

    @staticmethod
    def resolve(module: str, imports: List[Tuple[int, str]]) -> List[str]:
        """Return the absolute module names (inside the package) of relative imports."""
        parts = module.split(".")
        return [".".join(parts[:len(parts) - level] + ([name] if name else [])) for level, name in imports]

    def _box(self, index: int, top: int, name: str, modules: List[Dict[str, Any]]) -> str:
        x = index * (BOX_WIDTH + BOX_GAP) + BOX_GAP // 2
        height = HEADER_HEIGHT + ROW_HEIGHT * len(modules) + 6
        rows = ['<rect x="%d" y="%d" width="%d" height="%d" fill="#fff" stroke="#262626"/>' % (x, top, BOX_WIDTH, height),
                '<rect x="%d" y="%d" width="%d" height="%d" fill="#262626"/>' % (x, top, BOX_WIDTH, HEADER_HEIGHT),
                '<text x="%d" y="%d" fill="#fff" font-weight="bold">%s</text>' % (x + 8, top + 17, HtmlTools.escape(name))]
        for row, module in enumerate(modules):
            label = ", ".join(c["name"] for c in module["classes"]) or module["module"].split(".")[-1] + ".py"
            rows.append('<a href="%s"><text x="%d" y="%d" fill="#1C69D4">%s</text></a>'
                        % (HtmlTools.escape(self._link(module)), x + 8, top + HEADER_HEIGHT + 14 + row * ROW_HEIGHT,
                           HtmlTools.escape(label)))
        return "".join(rows)

    @staticmethod
    def _arc(source: int, target: int, top: int, count: int) -> str:
        # arcs start right of the box centre and end left of it, so both directions of a pair stay apart
        sx = source * (BOX_WIDTH + BOX_GAP) + BOX_GAP // 2 + BOX_WIDTH // 2 + 12
        tx = target * (BOX_WIDTH + BOX_GAP) + BOX_GAP // 2 + BOX_WIDTH // 2 - 12
        lift = ARC_UNIT * abs(source - target)
        middle = (sx + tx) // 2
        return ('<path d="M%d,%d Q%d,%d %d,%d" fill="none" stroke="#1C69D4" stroke-opacity="0.55" marker-end="url(#tdarrow)"/>'
                '<text x="%d" y="%d" fill="#1C69D4" text-anchor="middle" font-size="10">%d</text>'
                % (sx, top, middle, top - 2 * lift, tx, top, middle, top - lift - 3, count))
