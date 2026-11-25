"""Source popup of /techdoku: Python highlighted by the vendored Pygments, classes and functions foldable."""
import ast
import logging
from typing import Any, Dict, List

from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

try:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import PythonLexer
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False
    logger.warning("Pygments not found in vendor – the source popup is shown without colours")

MISSING_NOTE = "Pygments fehlt – weingaerten-web ausführen"


class PythonSourceHtml:
    """Renders a module as numbered lines; every class and function is an open `<details>` block."""

    @staticmethod
    def style() -> str:
        """Return the Pygments colours scoped to the popup (empty without Pygments)."""
        return HtmlFormatter().get_style_defs(".tdsrc") if PYGMENTS_AVAILABLE else ""

    @staticmethod
    def render(text: str) -> str:
        """Return the HTML of the source text."""
        text = text.replace("\r\n", "\n")
        lexer = PythonLexer(stripnl=False, ensurenl=False) if PYGMENTS_AVAILABLE else None
        return PythonSourceHtml.lines_html(PythonSourceHtml.coloured_lines(text, lexer), PythonSourceHtml._blocks(text))

    @staticmethod
    def lines_html(lines: List[str], starts: Dict[int, int]) -> str:
        """Return numbered lines; starts maps the first line of a foldable block to its last line."""
        html: List[str] = [] if PYGMENTS_AVAILABLE else ['<p class="note">%s</p>' % MISSING_NOTE]
        open_ends: List[int] = []
        for number, line in enumerate(lines, start=1):
            row = '<div class="sl"><span class="ln">%d</span>%s</div>' % (number, line)
            if number in starts:
                html.append("<details open><summary>%s</summary>" % row)
                open_ends.append(starts[number])
            else:
                html.append(row)
            while open_ends and open_ends[-1] <= number:
                open_ends.pop()
                html.append("</details>")
        html.extend("</details>" for _ in open_ends)
        return "".join(html)

    @staticmethod
    def coloured_lines(text: str, lexer: Any) -> List[str]:
        """Return the highlighted HTML lines of text (escaped only when Pygments is missing)."""
        if not PYGMENTS_AVAILABLE or lexer is None:
            return [HtmlTools.escape(line) for line in text.split("\n")]
        # HtmlFormatter closes and reopens its spans at every line break, so the result can be split by lines
        coloured = highlight(text, lexer, HtmlFormatter(nowrap=True))
        lines = coloured.split("\n")
        return lines + [""] * (text.count("\n") + 1 - len(lines))

    @staticmethod
    def _blocks(text: str) -> Dict[int, int]:
        # first line (incl. decorators) of every class / function -> its last line
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return {}
        starts: Dict[int, int] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.end_lineno:
                first = min([node.lineno] + [d.lineno for d in node.decorator_list])
                if node.end_lineno > first:
                    starts[first] = max(starts.get(first, 0), node.end_lineno)
        return starts
