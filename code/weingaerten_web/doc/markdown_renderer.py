"""The Markdown subset of /doku: headings, paragraphs, lists, pipe tables, fenced code."""
import logging
import re
from typing import List, Optional, Tuple

from ..rendering.html_tools import HtmlTools
from .inline_markup import InlineMarkup

logger = logging.getLogger(__name__)

HEADING_RE = re.compile(r"^(#{1,3})\s+(.*)$")
BULLET_RE = re.compile(r"^- ")
NUMBERED_RE = re.compile(r"^\d+\. ")
TABLE_RULE_RE = re.compile(r"^\|[\s:|-]+\|?$")


class MarkdownRenderer:
    """Renders a document to HTML with a table of contents of the `##`/`###` headings below the `h1`."""

    def __init__(self) -> None:
        self._out: List[str] = []
        self._paragraph: List[str] = []
        self._toc: List[Tuple[int, str, str]] = []
        self._h1_index: Optional[int] = None

    def render(self, text: str) -> str:
        """Return the HTML of the document."""
        lines = text.replace("\r\n", "\n").split("\n")
        i = 0
        while i < len(lines):
            i = self._block(lines, i)
        self._flush_paragraph()
        if self._toc:
            toc = "<ul>%s</ul>" % "".join('<li style="margin-left:%drem"><a href="#%s">%s</a></li>'
                                           % ((level - 2) * 1.2, slug, HtmlTools.escape(title))
                                           for level, title, slug in self._toc)
            self._out.insert((self._h1_index + 1) if self._h1_index is not None else 0, toc)
        return "".join(self._out)

    def _block(self, lines: List[str], i: int) -> int:
        # renders the block starting at line i and returns the index of the next unread line
        line = lines[i]
        if line.startswith("```"):
            self._flush_paragraph()
            return self._code_block(lines, i)
        heading = HEADING_RE.match(line)
        if heading:
            self._flush_paragraph()
            self._heading(len(heading.group(1)), heading.group(2).strip())
            return i + 1
        if line.startswith("|"):
            self._flush_paragraph()
            return self._table(lines, i)
        if BULLET_RE.match(line) or NUMBERED_RE.match(line):
            self._flush_paragraph()
            return self._list(lines, i)
        if not line.strip():
            self._flush_paragraph()
        else:
            self._paragraph.append(line.strip())
        return i + 1

    def _flush_paragraph(self) -> None:
        if self._paragraph:
            self._out.append("<p>%s</p>" % InlineMarkup.render(" ".join(self._paragraph)))
            self._paragraph.clear()

    def _code_block(self, lines: List[str], i: int) -> int:
        end = i + 1
        code = []
        while end < len(lines) and not lines[end].startswith("```"):
            code.append(lines[end])
            end += 1
        self._out.append("<pre>%s</pre>" % HtmlTools.escape("\n".join(code)))
        return end + 1

    def _heading(self, level: int, title: str) -> None:
        slug = InlineMarkup.slug(title)
        if level == 1 and self._h1_index is None:
            self._h1_index = len(self._out)
        if level > 1:
            self._toc.append((level, title, slug))
        self._out.append('<h%d id="%s">%s</h%d>' % (level, slug, InlineMarkup.render(title), level))

    def _table(self, lines: List[str], i: int) -> int:
        rows = []
        while i < len(lines) and lines[i].startswith("|"):
            rows.append(lines[i])
            i += 1
        html = "<table><tr>%s</tr>" % "".join("<th>%s</th>" % InlineMarkup.render(c) for c in self._cells(rows[0]))
        for row in rows[1:]:
            if TABLE_RULE_RE.match(row.strip()):
                continue
            html += "<tr>%s</tr>" % "".join("<td>%s</td>" % InlineMarkup.render(c) for c in self._cells(row))
        self._out.append(html + "</table>")
        return i

    @staticmethod
    def _cells(row: str) -> List[str]:
        return [cell.strip() for cell in row.strip().strip("|").split("|")]

    def _list(self, lines: List[str], i: int) -> int:
        ordered = bool(NUMBERED_RE.match(lines[i]))
        item_re = NUMBERED_RE if ordered else BULLET_RE
        items = []
        while i < len(lines) and item_re.match(lines[i]):
            items.append(re.sub(r"^(- |\d+\. )", "", lines[i]))
            i += 1
        tag = "ol" if ordered else "ul"
        self._out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % InlineMarkup.render(x) for x in items), tag))
        return i
