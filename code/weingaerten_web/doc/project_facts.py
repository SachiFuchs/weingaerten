"""Project-wide facts for /techdoku: the exception lists of the specifications and all imported modules."""
import importlib
import logging
import os
import platform
import re
import sys
from typing import Any, Dict, List

from ..rendering.html_tools import HtmlTools
from .inline_markup import InlineMarkup

logger = logging.getLogger(__name__)

SPECIFICATIONS = ("weingaerten-core.md", "weingaerten-web.md")
EXCEPTION_SECTION_RE = re.compile(r"(?ms)^## Exception list.*?$(.*?)(?=^## )")
INTERNAL = ("weingaerten_core", "weingaerten_web")
# third-party Python code that the specifications allow (Exception #4 of weingaerten-web.md)
VENDORED = {"pygments": "Fremdbibliothek (Exception #4, vendor)"}
SHOWN_USERS = 8


class ProjectFacts:
    """Builds the tables from the specification files and the CodeInspector module facts."""

    def __init__(self, home: str) -> None:
        """Args:
            home: WEINGAERTEN_HOME (contains the specifications).
        """
        self._home = home

    def exceptions(self) -> str:
        """Return one table row per row of the `## Exception list` of every specification."""
        rows = []
        for name in SPECIFICATIONS:
            path = os.path.join(self._home, name)
            if not os.path.isfile(path):
                continue
            with open(path, encoding="utf-8") as handle:
                match = EXCEPTION_SECTION_RE.search(handle.read().replace("\r\n", "\n"))
            for cells in self._table_rows(match.group(1) if match else ""):
                rows.append("<tr><td><code>%s</code></td>%s</tr>"
                            % (HtmlTools.escape(name), "".join("<td>%s</td>" % InlineMarkup.render(c) for c in cells[:5])))
        if not rows:
            return '<p class="note">Keine Ausnahmeliste gefunden.</p>'
        return ("<table><tr><th>Spezifikation</th><th>#</th><th>Ausnahme</th><th>Begründung</th><th>Erzeugt aus</th>"
                "<th>Code</th></tr>%s</table>" % "".join(rows))

    @staticmethod
    def imports(modules: List[Dict[str, Any]], links: Dict[str, str]) -> str:
        """Return the table of all absolutely imported top-level modules with their kind and users.

        Args:
            modules: the module facts of both packages (with `externals`).
            links: module file -> url of its node.
        """
        users: Dict[str, List[Dict[str, Any]]] = {}
        for module in modules:
            for name in module["externals"]:
                users.setdefault(name, []).append(module)
        rows = []
        for name in sorted(users, key=lambda n: (ProjectFacts._kind(n), n)):
            shown = ", ".join(ProjectFacts._user_link(m, links) for m in users[name][:SHOWN_USERS])
            more = " … (+%d)" % (len(users[name]) - SHOWN_USERS) if len(users[name]) > SHOWN_USERS else ""
            rows.append("<tr><td><code>%s</code></td><td>%s</td><td>%s</td><td>%d</td><td>%s%s</td></tr>"
                        % (HtmlTools.escape(name), ProjectFacts._kind(name), HtmlTools.escape(ProjectFacts._version(name)),
                           len(users[name]), shown, more))
        return ("<p>%d Module werden importiert.</p><table><tr><th>Modul</th><th>Art</th><th>Version</th><th>Anzahl</th>"
                "<th>Verwendet in</th></tr>"
                "%s</table>" % (len(users), "".join(rows)))

    @staticmethod
    def _kind(name: str) -> str:
        if name in INTERNAL:
            return "intern (eigenes Paket)"
        if name in VENDORED:
            return VENDORED[name]
        if name in sys.stdlib_module_names:
            return "Standardbibliothek"
        return "unbekannt – prüfen"

    @staticmethod
    def _version(name: str) -> str:
        # stdlib = running Python; vendored = its __version__; own packages have no version of their own
        if name in VENDORED:
            return str(getattr(importlib.import_module(name), "__version__", "?"))
        if name in sys.stdlib_module_names:
            return "Python " + platform.python_version()
        return "–"

    @staticmethod
    def _user_link(module: Dict[str, Any], links: Dict[str, str]) -> str:
        label = "<code>%s</code>" % HtmlTools.escape(module["package"] + "." + module["module"])
        url = links.get(module["file"])
        return '<a href="%s">%s</a>' % (HtmlTools.escape(url), label) if url else label

    @staticmethod
    def _table_rows(text: str) -> List[List[str]]:
        rows = []
        for line in text.split("\n"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            # header and rule rows are skipped; data rows start with the exception number
            if line.startswith("|") and cells and cells[0].isdigit():
                rows.append(cells)
        return rows
