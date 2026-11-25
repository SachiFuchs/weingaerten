"""The `{{code:testcases}}` part of /techdoku: one node per test level and per test script, with its single checks."""
import ast
import logging
import os
from typing import Any, Callable, Dict, List, Tuple

from ..rendering.html_tools import HtmlTools
from .code_inspector import CodeInspector
from .doc_node import DocNode
from .inline_markup import InlineMarkup
from .test_results_page import LEVELS, TestResultsPage

logger = logging.getLogger(__name__)

CHECK_NAMES = ("check", "chk", "ok", "expect", "test")
PREREQUISITES = {"struktur": "keine", "daten": "WEINGAERTEN_HOME", "web": "laufender Server auf Port 8008",
                 "fachlich": "WEINGAERTEN_HOME", "szenario": "keine (eigene Sandbox aus tests/fixtures/testhaus)"}
MAX_CHECK_TEXT = 160


class TestCatalogPage:
    """Builds the level nodes and the lazy test nodes; checks come from the `check(...)` calls of each script."""

    def __init__(self, inspector: CodeInspector, home: str, node_url: str) -> None:
        """Args:
            inspector: reads the scripts.
            home: WEINGAERTEN_HOME (contains `scripts`).
            node_url: link prefix of a node, e.g. `/techdoku?node=`.
        """
        self._inspector = inspector
        self._folder = os.path.join(home, "scripts")
        self._results = TestResultsPage(home)
        self._node_url = node_url

    def generate(self, node: DocNode) -> str:
        """Add the level and test nodes below node and return the overview table."""
        scripts = [s for s in self._inspector.scripts(self._folder, ".py") if TestResultsPage.is_test(s["file"])]
        rows = []
        for level, title in LEVELS:
            members = [s for s in scripts if TestResultsPage.level_of(s["file"]) == level]
            if not members:
                continue
            level_node = node.add_child(node.node_id + "-" + level, title)
            links = {}
            for script in members:
                child = level_node.add_child(level_node.node_id + "-" + InlineMarkup.slug(script["file"]), script["file"][:-3])
                child.blocks.append(("lazy", self._test_page(script, level)))
                links[script["file"]] = self._node_url + child.node_id
            level_node.blocks.append(("lazy", self._level_page(members, links, level)))
            rows.append("<tr><td><a href=\"%s%s\">%s</a></td><td>%d</td><td>%s</td></tr>"
                        % (self._node_url, level_node.node_id, title, len(members), HtmlTools.escape(PREREQUISITES[level])))
        return ("<p>%d Testskripte in <code>scripts\\</code>.</p><table><tr><th>Ebene</th><th>Tests</th><th>Voraussetzung</th></tr>"
                "%s</table>" % (len(scripts), "".join(rows)))

    def _level_page(self, members: List[Dict[str, Any]], links: Dict[str, str], level: str) -> Callable[[], str]:
        def render() -> str:
            last = self._results.last()
            rows = "".join("<tr><td><a href=\"%s\"><code>%s</code></a></td><td>%d</td><td>%s</td><td>%s</td></tr>"
                           % (links[s["file"]], HtmlTools.escape(s["file"]), len(self.checks(self._source(s))),
                              TestResultsPage.status_html(last.get(s["file"], {}).get("status", "–")), HtmlTools.escape(s["doc"]))
                           for s in members)
            return ("<p>Voraussetzung: %s.</p><table><tr><th>Test</th><th>Prüfungen</th><th>Letzter Lauf</th><th>Beschreibung</th>"
                    "</tr>%s</table>" % (HtmlTools.escape(PREREQUISITES[level]), rows))
        return render

    def _test_page(self, script: Dict[str, Any], level: str) -> Callable[[], str]:
        def render() -> str:
            checks = self.checks(self._source(script))
            entry = self._results.last().get(script["file"], {})
            facts = ("<table><tr><th>Datei</th><td><code>scripts\\%s</code></td></tr><tr><th>Ebene</th><td>%s</td></tr>"
                     "<tr><th>Voraussetzung</th><td>%s</td></tr><tr><th>Aufruf</th><td><code>python scripts\\run_tests.py --only %s</code></td></tr>"
                     "<tr><th>Letzter Lauf</th><td>%s %s</td></tr></table>"
                     % (HtmlTools.escape(script["file"]), HtmlTools.escape(dict(LEVELS)[level]), HtmlTools.escape(PREREQUISITES[level]),
                        HtmlTools.escape(script["file"][:-3]), TestResultsPage.status_html(entry.get("status", "–")),
                        HtmlTools.escape(str(entry.get("message", "")))))
            doc = "<p>%s</p>" % HtmlTools.escape(script.get("doc_full", script["doc"])).replace("\n\n", "</p><p>")
            if not checks:
                return doc + facts + "<p>Keine einzelnen Prüfungen erkannt (Bestanden = Exit-Code 0).</p>"
            rows = "".join("<tr><td>%d</td><td>%d</td><td>%s</td></tr>" % (i + 1, line, HtmlTools.escape(text))
                           for i, (line, text) in enumerate(checks))
            return (doc + facts + "<h3>Prüfungen (%d)</h3><table><tr><th>Nr.</th><th>Zeile</th><th>Was geprüft wird</th></tr>%s</table>"
                    % (len(checks), rows))
        return render

    def _source(self, script: Dict[str, Any]) -> str:
        return self._inspector.source(os.path.join(self._folder, script["file"]))

    @staticmethod
    def checks(source: str) -> List[Tuple[int, str]]:
        """Return (line, text) of every `check(...)`-like call; text = its first string argument."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return []
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in CHECK_NAMES:
                text = next((TestCatalogPage._text(arg) for arg in node.args if TestCatalogPage._text(arg)), "")
                if text:
                    found.append((node.lineno, text[:MAX_CHECK_TEXT]))
        return sorted(found)

    @staticmethod
    def _text(arg: ast.expr) -> str:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
        if isinstance(arg, ast.BinOp) and isinstance(arg.left, ast.Constant) and isinstance(arg.left.value, str):
            return arg.left.value
        if isinstance(arg, ast.JoinedStr):
            return ast.unparse(arg)[2:-1]
        return ""
