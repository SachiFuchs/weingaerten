"""Fills the `{{code:<kind> <package>}}` lines of /techdoku: diagrams, class tables, scripts and their nodes."""
import logging
import os
from typing import Any, Callable, Dict, List

from ..rendering.html_tools import HtmlTools
from .class_diagram_svg import ROOT_GROUP, ClassDiagramSvg
from .code_inspector import CodeInspector
from .doc_node import DocNode
from .group_diagram_svg import GroupDiagramSvg
from .inline_markup import InlineMarkup
from .markdown_file_page import MarkdownFilePage
from .markdown_renderer import MarkdownRenderer
from .module_page import ModulePage
from .project_facts import ProjectFacts
from .script_page import ScriptPage
from .test_catalog_page import TestCatalogPage
from .test_history_page import TestHistoryPage
from .test_results_page import TestResultsPage

logger = logging.getLogger(__name__)

PACKAGES = {"core": "weingaerten_core", "web": "weingaerten_web"}
USER_DOC_FILE = "weingaerten-doku.md"


class CodePages:
    """Generator for DocTree; module facts come from one shared CodeInspector (cached per file)."""

    def __init__(self, inspector: CodeInspector, code_dir: str, home: str, node_url: str) -> None:
        """Args:
            inspector: reads the source files.
            code_dir: the `code` folder with both packages.
            home: WEINGAERTEN_HOME (contains `scripts`).
            node_url: link prefix of a node of the page, e.g. `/techdoku?node=`.
        """
        self._inspector = inspector
        self._code_dir = code_dir
        self._home = home
        self._node_url = node_url
        self._module_ids: Dict[str, str] = {}

    def generate(self, node: DocNode, kind: str, argument: str) -> str:
        """Return the HTML of one generated part; `classes` and `js` add child nodes to node."""
        if kind == "scripts":
            return self._scripts(node)
        if kind == "userdoc":
            return self._user_doc()
        if kind == "mdfiles":
            return self._markdown_files(node)
        if kind == "tests":
            return TestResultsPage(self._home).render()
        if kind == "testcases":
            return TestCatalogPage(self._inspector, self._home, self._node_url).generate(node)
        if kind == "testhistory":
            return TestHistoryPage(self._home).render()
        if kind == "exceptions":
            return ProjectFacts(self._home).exceptions()
        if kind == "imports":
            modules = [m for package in PACKAGES.values() for m in self._inspector.package(os.path.join(self._code_dir, package))]
            return ProjectFacts.imports(modules, {f: self._node_url + n for f, n in self._module_ids.items()})
        if kind == "js" and argument == "web":
            return self._javascript(node)
        if argument not in PACKAGES or kind not in ("diagram", "classes"):
            return '<p class="note">Unbekannter Platzhalter code:%s %s</p>' % (HtmlTools.escape(kind), HtmlTools.escape(argument))
        modules = self._inspector.package(os.path.join(self._code_dir, PACKAGES[argument]))
        if kind == "classes":
            return self._classes(node, modules)
        # the diagram usually comes before the class nodes, so the ids are predicted the same way as in _classes
        return '<div class="tdsvg">%s</div>' % ClassDiagramSvg(self._predicted_link(node, argument)).render(modules)

    def _predicted_link(self, node: DocNode, argument: str) -> Any:
        prefix = node.node_id + "-klassen-"

        def link(module: Dict[str, Any]) -> str:
            known = self._module_ids.get(module["file"])
            return self._node_url + (known or prefix + self._group_slug(module) + "-" + InlineMarkup.slug(self._title(module)))
        return link

    def _classes(self, node: DocNode, modules: List[Dict[str, Any]]) -> str:
        # pass 1: every node, so all links are known; pass 2 (lazy, only for the shown node): the page contents
        groups: Dict[str, DocNode] = {}
        members: Dict[str, List[Dict[str, Any]]] = {}
        links: Dict[str, str] = {}
        children = []
        for module in modules:
            group_title = module["group"] or ROOT_GROUP
            if group_title not in groups:
                groups[group_title] = node.add_child(node.node_id + "-" + self._group_slug(module), group_title)
                members[group_title] = []
            group = groups[group_title]
            child = group.add_child(group.node_id + "-" + InlineMarkup.slug(self._title(module)), self._title(module))
            self._module_ids[module["file"]] = child.node_id
            links[module["module"]] = self._node_url + child.node_id
            members[group_title].append(module)
            children.append((child, module))
        used_by = self._used_by(modules)
        for child, module in children:
            child.blocks.append(("lazy", self._module_page(module, links, used_by.get(module["module"], []))))
        for title, group in groups.items():
            group.blocks.append(("lazy", self._group_page(members[title], modules, links)))
        rows = "".join("<tr><td>%s</td><td><code>%s</code></td><td><a href=\"%s\">%s</a></td><td>%d</td><td>%s</td></tr>"
                       % (HtmlTools.escape(m["group"] or ROOT_GROUP), HtmlTools.escape(m["module"]), links[m["module"]],
                          HtmlTools.escape(self._title(m)), m["lines"], HtmlTools.escape(m["doc"])) for m in modules)
        total = sum(m["lines"] for m in modules)
        return ("<p>%d Module, %d Klassen, %d Zeilen.</p><table><tr><th>Paket</th><th>Modul</th><th>Klasse</th>"
                "<th>Zeilen</th><th>Beschreibung</th></tr>%s</table>"
                % (len(modules), sum(len(m["classes"]) for m in modules), total, rows))

    @staticmethod
    def _used_by(modules: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        # reverse index of the imports inside the package
        index: Dict[str, List[str]] = {}
        for module in modules:
            for target in ClassDiagramSvg.resolve(module["module"], module["imports"]):
                if module["module"] not in index.setdefault(target, []):
                    index[target].append(module["module"])
        return index

    def _module_page(self, module: Dict[str, Any], links: Dict[str, str], used_by: List[str]) -> Callable[[], str]:
        return lambda: ModulePage.python(module, links, sorted(used_by), self._inspector.source(module["path"]))

    @staticmethod
    def _group_page(members: List[Dict[str, Any]], modules: List[Dict[str, Any]], links: Dict[str, str]) -> Callable[[], str]:
        def render() -> str:
            svg = GroupDiagramSvg(lambda name: links.get(name, "")).render(members, modules)
            return ("<p>Klassendiagramm: Pfeile = Importe; gestrichelt = Module anderer Unterpakete. "
                    "Maus über einem Kasten hebt seine Pfeile hervor.</p><div class=\"tdsvg\">%s</div>%s"
                    % (svg, ModulePage.group_list(members, links)))
        return render

    def _javascript(self, node: DocNode) -> str:
        folder = os.path.join(self._code_dir, PACKAGES["web"], "static")
        rows = []
        for script in self._inspector.scripts(folder, ".js"):
            child = node.add_child(node.node_id + "-" + InlineMarkup.slug(script["file"]), script["file"])
            child.blocks.append(("lazy", self._script_page(script, os.path.join(folder, script["file"]))))
            names = script["objects"] + script["functions"]
            rows.append("<tr><td><a href=\"%s%s\">%s</a></td><td>%d</td><td>%s</td><td>%s</td></tr>"
                        % (self._node_url, child.node_id, HtmlTools.escape(script["file"]), script["lines"],
                           HtmlTools.escape(script["doc"]), HtmlTools.escape(", ".join(names[:12]) + (" …" if len(names) > 12 else ""))))
        return ("<table><tr><th>Datei</th><th>Zeilen</th><th>Beschreibung</th><th>Funktionen</th></tr>%s</table>"
                % "".join(rows))

    def _script_page(self, script: Dict[str, Any], path: str) -> Callable[[], str]:
        return lambda: ScriptPage.page(script, PACKAGES["web"] + "/static", self._inspector.source(path))

    def _markdown_files(self, node: DocNode) -> str:
        files = MarkdownFilePage(self._home).files()
        links = {}
        for info in files:
            child = node.add_child(node.node_id + "-" + InlineMarkup.slug(info["file"]), info["file"])
            child.blocks.append(("lazy", self._markdown_page(info)))
            links[info["file"]] = self._node_url + child.node_id
        return MarkdownFilePage.overview(files, links)

    def _markdown_page(self, info: Dict[str, Any]) -> Callable[[], str]:
        return lambda: MarkdownFilePage.page(info, self._inspector.source(info["path"]))

    def _scripts(self, node: DocNode) -> str:
        folder = os.path.join(self._home, "scripts")
        rows = []
        scripts = self._inspector.scripts(folder, ".py")
        for script in scripts:
            child = node.add_child(node.node_id + "-" + InlineMarkup.slug(script["file"]), script["file"])
            child.blocks.append(("lazy", self._python_script_page(script, os.path.join(folder, script["file"]))))
            rows.append("<tr><td><a href=\"%s%s\"><code>%s</code></a></td><td>%d</td><td>%s</td></tr>"
                        % (self._node_url, child.node_id, HtmlTools.escape(script["file"]), script["lines"],
                           HtmlTools.escape(script["doc"])))
        return "<p>%d Skripte in <code>scripts\\</code>.</p><table><tr><th>Datei</th><th>Zeilen</th><th>Beschreibung</th></tr>%s</table>" % (
            len(scripts), "".join(rows))

    def _python_script_page(self, script: Dict[str, Any], path: str) -> Callable[[], str]:
        return lambda: ModulePage.script(script, "scripts", self._inspector.source(path))

    def _user_doc(self) -> str:
        path = os.path.join(self._home, USER_DOC_FILE)
        if not os.path.isfile(path):
            return "<p>Doku fehlt – weingaerten-doku.md anlegen</p>"
        with open(path, encoding="utf-8") as handle:
            lines = handle.read().replace("\r\n", "\n").split("\n")
        # the node title is the h1 of the page, so the document's own first `#` heading is left out
        titles = [i for i, line in enumerate(lines) if line.startswith("# ")]
        if titles:
            del lines[titles[0]]
        return MarkdownRenderer().render("\n".join(lines))

    @staticmethod
    def _title(module: Dict[str, Any]) -> str:
        return ", ".join(c["name"] for c in module["classes"]) or module["module"].split(".")[-1] + ".py"

    @staticmethod
    def _group_slug(module: Dict[str, Any]) -> str:
        return InlineMarkup.slug(module["group"] or ROOT_GROUP)
