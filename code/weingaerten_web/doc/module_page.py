"""HTML of one generated /techdoku node: a Python module with its classes, or a browser script."""
import logging
from typing import Any, Dict, List

from ..rendering.html_tools import HtmlTools
from .class_diagram_svg import ClassDiagramSvg
from .python_source_html import PythonSourceHtml

logger = logging.getLogger(__name__)


class ModulePage:
    """Renders the facts collected by CodeInspector; every value is escaped."""

    @staticmethod
    def python(module: Dict[str, Any], links: Dict[str, str], used_by: List[str], source: str) -> str:
        """Return the HTML of a Python module node.

        Args:
            module: the module facts.
            links: module name -> url of its node (modules without a node are missing).
            used_by: names of the modules that import this one.
            source: the source text of the module (shown in the popup).
        """
        escape = HtmlTools.escape
        html = ['<table><tr><th>Datei</th><td><a href="#" data-src="srcdlg"><code>%s</code></a></td></tr>'
                '<tr><th>Zeilen</th><td>%d</td></tr><tr><th>Beschreibung</th><td>%s</td></tr>'
                % (escape(module["file"]), module["lines"], escape(module["doc"]))]
        imports = ClassDiagramSvg.resolve(module["module"], module["imports"])
        if imports:
            html.append("<tr><th>Verwendet</th><td>%s</td></tr>" % ModulePage.module_links(imports, links))
        if used_by:
            html.append("<tr><th>Wird verwendet von</th><td>%s</td></tr>" % ModulePage.module_links(used_by, links))
        if module["constants"]:
            html.append("<tr><th>Konstanten</th><td>%s</td></tr>"
                        % ", ".join("<code>%s</code>" % escape(c) for c in module["constants"]))
        html.append("</table>")
        for cls in module["classes"]:
            html.append(ModulePage._class(cls))
        html.append(ModulePage._dialog(module["file"], source))
        return "".join(html)

    @staticmethod
    def script(script: Dict[str, Any], folder: str, source: str) -> str:
        """Return the HTML of a script node of `scripts\\`: facts, functions, classes and the source popup.

        Args:
            script: the script facts (`CodeInspector.scripts` with `.py`).
            folder: the folder shown in the row `Datei`, e.g. `scripts`.
            source: the source text of the script (shown in the popup).
        """
        escape = HtmlTools.escape
        paragraphs = "".join("<p>%s</p>" % escape(" ".join(p.split())) for p in script["doc_full"].split("\n\n") if p.strip())
        html = ['<table><tr><th>Datei</th><td><a href="#" data-src="srcdlg"><code>%s/%s</code></a></td></tr>'
                '<tr><th>Zeilen</th><td>%d</td></tr><tr><th>Beschreibung</th><td>%s</td></tr>'
                % (escape(folder), escape(script["file"]), script["lines"], paragraphs)]
        if script["externals"]:
            html.append("<tr><th>Importiert</th><td>%s</td></tr>" % ", ".join("<code>%s</code>" % escape(n) for n in script["externals"]))
        if script["constants"]:
            html.append("<tr><th>Konstanten</th><td>%s</td></tr>" % ", ".join("<code>%s</code>" % escape(c) for c in script["constants"]))
        html.append("</table><h2>Funktionen</h2>")
        if script["functions"]:
            html.append("<table><tr><th>Funktion</th><th>Zeile</th><th>Signatur</th><th>Beschreibung</th></tr>%s</table>"
                        % "".join("<tr><td><code>%s</code></td><td>%d</td><td><code>%s</code></td><td>%s</td></tr>"
                                  % (escape(f["name"]), f["line"], escape(f["signature"]), escape(f["doc"]))
                                  for f in script["functions"]))
        else:
            html.append('<p class="note">Keine Funktionen.</p>')
        for cls in script["classes"]:
            html.append(ModulePage._class(cls))
        html.append(ModulePage._dialog(script["file"], source))
        return "".join(html)

    @staticmethod
    def module_links(names: List[str], links: Dict[str, str]) -> str:
        """Return the module names as links to their nodes (plain code when a module has no node)."""
        parts = []
        for name in names:
            code = "<code>%s</code>" % HtmlTools.escape(name)
            parts.append('<a href="%s">%s</a>' % (HtmlTools.escape(links[name]), code) if name in links else code)
        return ", ".join(parts)

    @staticmethod
    def _dialog(file: str, source: str) -> str:
        # modal popup; only the close button (form method=dialog) and Esc end it
        return ('<dialog id="srcdlg" class="tdsrc"><div class="tdsrchead"><b>%s</b>'
                '<button type="button" class="btn2" data-expand="1">Alle aufklappen</button>'
                '<button type="button" class="btn2" data-expand="0">Alle zuklappen</button>'
                '<form method="dialog"><button class="btn">Schließen</button></form></div>'
                '<style>%s</style><div class="tdsrcbody">%s</div></dialog>'
                % (HtmlTools.escape(file), PythonSourceHtml.style(), PythonSourceHtml.render(source)))

    @staticmethod
    def _class(cls: Dict[str, Any]) -> str:
        escape = HtmlTools.escape
        bases = " (%s)" % escape(", ".join(cls["bases"])) if cls["bases"] else ""
        html = ["<h2>Klasse <code>%s</code>%s</h2><p>%s</p>" % (escape(cls["name"]), bases, escape(cls["doc"]))]
        if cls["attributes"]:
            html.append("<p><b>Öffentliche Variablen:</b> %s</p>"
                        % ", ".join("<code>%s</code>" % escape(a) for a in cls["attributes"]))
        if cls["methods"]:
            html.append("<table><tr><th>Methode</th><th>Signatur</th><th>Beschreibung</th></tr>%s</table>"
                        % "".join("<tr><td><code>%s</code></td><td><code>%s</code></td><td>%s</td></tr>"
                                  % (escape(m["name"]), escape(m["signature"]), escape(m["doc"])) for m in cls["methods"]))
        else:
            html.append('<p class="note">Keine öffentlichen Methoden.</p>')
        return "".join(html)

    @staticmethod
    def group_list(members: List[Dict[str, Any]], links: Dict[str, str]) -> str:
        """Return the foldable content list of a sub package: one `<details>` per module."""
        escape = HtmlTools.escape
        items = []
        for module in members:
            title = ", ".join(c["name"] for c in module["classes"]) or module["module"].split(".")[-1] + ".py"
            methods = "".join("<li><code>%s</code> – %s</li>" % (escape(m["name"]), escape(m["doc"]))
                              for c in module["classes"] for m in c["methods"])
            items.append('<details class="tdmod"><summary><b>%s</b> <span class="note">%d Zeilen</span> – %s</summary>'
                         '<p>%s</p><ul>%s</ul></details>'
                         % (escape(title), module["lines"], escape(module["doc"]),
                            ModulePage.module_links([module["module"]], links), methods or "<li>keine öffentlichen Methoden</li>"))
        return ('<h2>Inhalt</h2><p><button type="button" class="btn2" data-expand="1">Alle aufklappen</button> '
                '<button type="button" class="btn2" data-expand="0">Alle zuklappen</button></p><div class="tdlist">%s</div>'
                % "".join(items))
