"""Node page of /techdoku for a browser script: facts, function table and the highlighted source popup."""
import logging
from typing import Any, Dict, List

from ..rendering.html_tools import HtmlTools
from .python_source_html import PYGMENTS_AVAILABLE, PythonSourceHtml

logger = logging.getLogger(__name__)

try:
    from pygments import lex
    from pygments.lexers import JavascriptLexer
    from pygments.token import Punctuation
except ImportError:
    JavascriptLexer = None


class ScriptPage:
    """Renders the facts of one JS file collected by CodeInspector; every value is escaped."""

    @staticmethod
    def page(script: Dict[str, Any], folder: str, source: str) -> str:
        """Return the HTML of a browser script node.

        Args:
            script: the script facts (`CodeInspector.scripts`).
            folder: the folder shown in the row `Datei`, e.g. `weingaerten_web/static`.
            source: the source text of the file (shown in the popup).
        """
        escape = HtmlTools.escape
        rows = [("Datei", '<a href="#" data-src="jsdlg"><code>%s/%s</code></a>' % (escape(folder), escape(script["file"]))),
                ("Zeilen", str(script["lines"])), ("Beschreibung", escape(script["doc"])),
                ("Objekte", ScriptPage._codes(script["objects"])),
                ("Öffentliche Mitglieder", ScriptPage._codes(script["members"]))]
        html = ["<table>%s</table>" % "".join("<tr><th>%s</th><td>%s</td></tr>" % row for row in rows)]
        html.append(ScriptPage._functions(script["function_docs"]))
        html.append(ScriptPage._dialog(script["file"], source))
        return "".join(html)

    @staticmethod
    def _functions(functions: List[Dict[str, Any]]) -> str:
        escape = HtmlTools.escape
        if not functions:
            return '<h2>Funktionen</h2><p class="note">Keine benannten Funktionen.</p>'
        rows = "".join("<tr><td><code>%s</code></td><td>%d</td><td>%s</td></tr>" % (escape(f["name"]), f["line"], escape(f["doc"]))
                       for f in functions)
        return ("<h2>Funktionen</h2><table><tr><th>Funktion</th><th>Zeile</th><th>Beschreibung</th></tr>%s</table>"
                % rows)

    @staticmethod
    def _codes(names: List[str]) -> str:
        return ", ".join("<code>%s</code>" % HtmlTools.escape(n) for n in names) or "–"

    @staticmethod
    def _dialog(file: str, source: str) -> str:
        text = source.replace("\r\n", "\n")
        lexer = JavascriptLexer(stripnl=False, ensurenl=False) if PYGMENTS_AVAILABLE and JavascriptLexer else None
        body = PythonSourceHtml.lines_html(PythonSourceHtml.coloured_lines(text, lexer), ScriptPage._blocks(text, lexer))
        return ('<dialog id="jsdlg" class="tdsrc"><div class="tdsrchead"><b>%s</b>'
                '<button type="button" class="btn2" data-expand="1">Alle aufklappen</button>'
                '<button type="button" class="btn2" data-expand="0">Alle zuklappen</button>'
                '<form method="dialog"><button class="btn">Schließen</button></form></div>'
                '<style>%s</style><div class="tdsrcbody">%s</div></dialog>'
                % (HtmlTools.escape(file), PythonSourceHtml.style(), body))

    @staticmethod
    def _blocks(text: str, lexer: Any) -> Dict[int, int]:
        # braces from the Pygments tokens (strings, comments and regexes are separate tokens);
        # a block is foldable when its opening line defines a function (`function` or `=>`)
        if lexer is None:
            return {}
        lines = text.split("\n")
        starts: Dict[int, int] = {}
        stack: List[int] = []
        number = 1
        for kind, value in lex(text, lexer):
            if kind in Punctuation and value == "{":
                stack.append(number)
            elif kind in Punctuation and value == "}" and stack:
                first = stack.pop()
                if number > first and ("function" in lines[first - 1] or "=>" in lines[first - 1]):
                    starts[first] = max(starts.get(first, 0), number)
            number += value.count("\n")
        return ScriptPage._nested(starts)

    @staticmethod
    def _nested(starts: Dict[int, int]) -> Dict[int, int]:
        # keeps only properly nested ranges: a block starting on the last line of an open one would cross it
        kept: Dict[int, int] = {}
        ends: List[int] = []
        for first in sorted(starts):
            while ends and ends[-1] < first:
                ends.pop()
            last = starts[first]
            if ends and (first >= ends[-1] or last > ends[-1]):
                continue
            kept[first] = last
            ends.append(last)
        return kept
