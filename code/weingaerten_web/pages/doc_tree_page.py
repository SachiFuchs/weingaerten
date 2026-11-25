"""Pages /techdoku and /handbuch: tree view of a Markdown document left, the selected node right."""
import logging
import os
from typing import List, Optional

from ..doc.code_inspector import CodeInspector
from ..doc.code_pages import CodePages
from ..doc.doc_node import DocNode
from ..doc.doc_tree import DocTree
from ..doc.markdown_renderer import MarkdownRenderer
from ..rendering.html_tools import HtmlTools
from ..rendering.page_context import PageContext

logger = logging.getLogger(__name__)


class DocTreePage:
    """Renders one document as tree + page; document and code are read again on every request."""

    def __init__(self, context: PageContext, url: str, title: str, doc_file: str) -> None:
        """Args:
            context: shared page services.
            url: page url (also the menu entry), e.g. `/techdoku`.
            title: menu label, used in the tab title.
            doc_file: Markdown file in WEINGAERTEN_HOME.
        """
        self._context = context
        self._url = url
        self._title = title
        self._doc_file = doc_file
        self._store = url.strip("/")
        self._inspector = CodeInspector()

    def render(self, node_id: Optional[str] = None) -> str:
        """Return the page of one node (unknown or missing id = first node)."""
        home = self._context.settings.home()
        path = os.path.join(home, self._doc_file)
        if not home or not os.path.isfile(path):
            return self._page(self._title, "<p>%s fehlt – %s anlegen</p>" % (HtmlTools.escape(self._title), HtmlTools.escape(self._doc_file)))
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        pages = CodePages(self._inspector, self._context.settings.code_dir, home, self._url + "?node=")
        tree = DocTree(text, pages.generate)
        node = tree.node(node_id)
        if node is None:
            return self._page(self._title, "<p>%s ist leer.</p>" % HtmlTools.escape(self._title))
        body = ('<div id="tdgrid" data-store="%s"><div id="tdtree"><div class="tdtitle">%s</div>%s</div><div id="tdsplit"></div>'
                '<div id="tdmain" class="doc">%s</div></div><script>%s</script>'
                % (self._store, HtmlTools.escape(tree.title), self._tree(tree.roots, node), self._content(node),
                   self._context.assets.text("techdoku.js")))
        return self._page(self._title + " – " + node.title, body)

    def _page(self, title: str, body: str) -> str:
        return self._context.layout.render(title, self._url, body)

    def _link(self, node: DocNode) -> str:
        return self._url + "?node=" + node.node_id

    def _tree(self, nodes: List[DocNode], current: DocNode) -> str:
        path = {n.node_id for n in current.ancestors()}
        items = []
        for node in nodes:
            link = '<a href="%s" data-node="%s"%s>%s</a>' % (self._link(node), node.node_id,
                                                              ' class="on"' if node is current else "",
                                                              HtmlTools.escape(node.title))
            if node.children:
                opened = " open" if node.node_id in path or node is current else ""
                items.append('<li><details data-node="%s"%s><summary>%s</summary>%s</details></li>'
                             % (node.node_id, opened, link, self._tree(node.children, current)))
            else:
                items.append('<li class="leaf">%s</li>' % link)
        return "<ul>%s</ul>" % "".join(items)

    def _content(self, node: DocNode) -> str:
        crumbs = " › ".join('<a href="%s">%s</a>' % (self._link(n), HtmlTools.escape(n.title)) for n in node.ancestors())
        html = ['<div class="tdcrumb">%s</div>' % crumbs if crumbs else "", "<h1>%s</h1>" % HtmlTools.escape(node.title)]
        for kind, value in node.blocks:
            # lazy blocks (module pages) are built only for the shown node
            html.append(MarkdownRenderer().render(value) if kind == "md" else value() if kind == "lazy" else value)
        if node.children:
            html.append("<h2>Unterseiten</h2><ul>%s</ul>" % "".join(
                '<li><a href="%s">%s</a></li>' % (self._link(c), HtmlTools.escape(c.title)) for c in node.children))
        return "".join(html)
