"""Node pages of /techdoku for the project's *.md files: sections, description and the highlighted source popup."""
import logging
import os
import re
from typing import Any, Dict, List

from ..rendering.html_tools import HtmlTools
from .python_source_html import PYGMENTS_AVAILABLE, PythonSourceHtml

logger = logging.getLogger(__name__)

try:
    from pygments.lexers import MarkdownLexer
except ImportError:
    MarkdownLexer = None

MD_FOLDERS = ("", "skills", "people")
HEADING_RE = re.compile(r"^(#{1,4})\s+(.*\S)\s*$")
MAX_DESCRIPTION = 200
NO_DESCRIPTION = "(keine Beschreibung)"


class MarkdownFilePage:
    """Lists the Markdown files of WEINGAERTEN_HOME and renders one node page per file."""

    def __init__(self, home: str) -> None:
        """Args:
            home: WEINGAERTEN_HOME; only its fixed folders `MD_FOLDERS` are listed.
        """
        self._home = home

    def files(self) -> List[Dict[str, Any]]:
        """Return file (relative, `/`), path, lines, title, description and sections of every *.md file."""
        found = []
        for folder in MD_FOLDERS:
            directory = os.path.join(self._home, folder)
            if not os.path.isdir(directory):
                continue
            for name in sorted(os.listdir(directory)):
                path = os.path.join(directory, name)
                if name.endswith(".md") and os.path.isfile(path):
                    with open(path, encoding="utf-8", errors="replace") as handle:
                        text = handle.read().replace("\r\n", "\n")
                    found.append(dict(self._facts(text), file=(folder + "/" if folder else "") + name, path=path))
        return found

    @staticmethod
    def _facts(text: str) -> Dict[str, Any]:
        lines = text.split("\n")
        sections = MarkdownFilePage._sections(lines)
        title = next((s["title"] for s in sections if s["level"] == 1), "")
        return {"lines": len(lines), "title": title, "sections": sections,
                "doc": MarkdownFilePage._description(lines)}

    @staticmethod
    def _sections(lines: List[str]) -> List[Dict[str, Any]]:
        # headings outside ``` fences; a section ends before the next heading of the same or a higher level
        sections: List[Dict[str, Any]] = []
        fenced = False
        for number, line in enumerate(lines, start=1):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            match = None if fenced else HEADING_RE.match(line)
            if match:
                sections.append({"level": len(match.group(1)), "title": match.group(2), "start": number, "end": len(lines)})
        for index, section in enumerate(sections):
            following = [s for s in sections[index + 1:] if s["level"] <= section["level"]]
            if following:
                section["end"] = following[0]["start"] - 1
        return sections

    @staticmethod
    def _description(lines: List[str]) -> str:
        if lines and lines[0].strip() == "---":
            for line in lines[1:]:
                if line.strip() == "---":
                    break
                if line.startswith("description:"):
                    return MarkdownFilePage._short(line[len("description:"):].strip().strip("'\""))
        paragraph: List[str] = []
        started = False
        for line in lines:
            if line.startswith("# "):
                started = True
            elif started and line.strip() and not line.startswith(("#", "|", "{{", "```")):
                paragraph.append(line.strip())
            elif paragraph:
                break
        return MarkdownFilePage._short(" ".join(paragraph))

    @staticmethod
    def _short(text: str) -> str:
        text = text.replace("**", "").replace("`", "")
        if not text:
            return NO_DESCRIPTION
        return text if len(text) <= MAX_DESCRIPTION else text[:MAX_DESCRIPTION - 1].rstrip() + "…"

    @staticmethod
    def overview(files: List[Dict[str, Any]], links: Dict[str, str]) -> str:
        """Return the table of all files; links maps a file to the url of its node."""
        escape = HtmlTools.escape
        rows = "".join('<tr><td><a href="%s"><code>%s</code></a></td><td>%d</td><td>%d</td><td>%s</td></tr>'
                       % (escape(links[f["file"]]), escape(f["file"]), f["lines"], len(f["sections"]), escape(f["doc"]))
                       for f in files)
        return ("<p>%d Markdown-Dateien; je Datei ein Unterknoten mit Abschnitten und Quelltext.</p><table><tr><th>Datei</th>"
                "<th>Zeilen</th><th>Abschnitte</th><th>Beschreibung</th></tr>%s</table>" % (len(files), rows))

    @staticmethod
    def page(info: Dict[str, Any], source: str) -> str:
        """Return the HTML of one file node: facts, section table and the source popup."""
        escape = HtmlTools.escape
        html = ['<table><tr><th>Datei</th><td><a href="#" data-src="mddlg"><code>%s</code></a></td></tr>'
                '<tr><th>Zeilen</th><td>%d</td></tr><tr><th>Titel</th><td>%s</td></tr><tr><th>Beschreibung</th><td>%s</td></tr>'
                '</table>' % (escape(info["file"]), info["lines"], escape(info["title"]) or "–", escape(info["doc"]))]
        if info["sections"]:
            rows = "".join('<tr><td>%s</td><td style="padding-left:%.1fem">%s</td><td>%d–%d</td><td>%d</td></tr>'
                           % ("#" * s["level"], 0.4 + 1.2 * (s["level"] - 1), escape(s["title"]), s["start"], s["end"],
                              s["end"] - s["start"] + 1) for s in info["sections"])
            html.append("<h2>Abschnitte</h2><table><tr><th>Ebene</th><th>Abschnitt</th><th>Zeilen</th><th>Umfang</th></tr>%s</table>"
                        % rows)
        else:
            html.append('<p class="note">Keine Überschriften.</p>')
        html.append(MarkdownFilePage._dialog(info, source))
        return "".join(html)

    @staticmethod
    def _dialog(info: Dict[str, Any], source: str) -> str:
        text = source.replace("\r\n", "\n")
        lexer = MarkdownLexer(stripnl=False, ensurenl=False) if PYGMENTS_AVAILABLE and MarkdownLexer else None
        starts = {s["start"]: s["end"] for s in info["sections"] if s["end"] > s["start"]}
        body = PythonSourceHtml.lines_html(PythonSourceHtml.coloured_lines(text, lexer), starts)
        return ('<dialog id="mddlg" class="tdsrc"><div class="tdsrchead"><b>%s</b>'
                '<button type="button" class="btn2" data-expand="1">Alle aufklappen</button>'
                '<button type="button" class="btn2" data-expand="0">Alle zuklappen</button>'
                '<form method="dialog"><button class="btn">Schließen</button></form></div>'
                '<style>%s</style><div class="tdsrcbody">%s</div></dialog>'
                % (HtmlTools.escape(info["file"]), PythonSourceHtml.style(), body))
