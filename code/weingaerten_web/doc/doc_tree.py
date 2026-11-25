"""Splits `weingaerten-techdoku.md` into the node tree of /techdoku (`##`, `###`, `####` = tree levels)."""
import logging
import re
from typing import Callable, Dict, List, Optional

from .doc_node import DocNode
from .inline_markup import InlineMarkup

logger = logging.getLogger(__name__)

NODE_HEADING_RE = re.compile(r"^(#{2,4})\s+(.*)$")
GENERATED_RE = re.compile(r"^\{\{code:([a-z]+)(?:\s+([a-z]+))?\}\}$")

# fills a node for a `{{code:<kind> <argument>}}` line and returns its HTML
Generator = Callable[[DocNode, str, str], str]


class DocTree:
    """The parsed tree; every node can be looked up by its id."""

    def __init__(self, text: str, generate: Generator) -> None:
        """Parse the document.

        Args:
            text: the Markdown document.
            generate: builds the generated parts (may add child nodes).
        """
        self.title = "Technische Dokumentation"
        self.roots: List[DocNode] = []
        self._generate = generate
        self._by_id: Dict[str, DocNode] = {}
        self._parse(text.replace("\r\n", "\n").split("\n"))
        self._index(self.roots)

    def node(self, node_id: Optional[str]) -> Optional[DocNode]:
        """Return the node of an id, else the first node (None for an empty document)."""
        if node_id in self._by_id:
            return self._by_id[node_id]
        return self.roots[0] if self.roots else None

    def _parse(self, lines: List[str]) -> None:
        stack: List[DocNode] = []
        text: List[str] = []
        for line in lines:
            heading = NODE_HEADING_RE.match(line)
            generated = GENERATED_RE.match(line.strip())
            if line.startswith("# ") and not stack:
                self.title = line[2:].strip()
            elif heading:
                self._flush(stack, text)
                stack = self._open(stack, len(heading.group(1)) - 1, heading.group(2).strip())
            elif generated and stack:
                self._flush(stack, text)
                stack[-1].blocks.append(("html", self._generate(stack[-1], generated.group(1), generated.group(2) or "")))
            else:
                text.append(line)
        self._flush(stack, text)

    def _open(self, stack: List[DocNode], depth: int, title: str) -> List[DocNode]:
        # a heading deeper than one level below its parent is attached to the deepest open node
        stack = stack[:depth - 1]
        slug = InlineMarkup.slug(title)
        if stack:
            stack.append(stack[-1].add_child(stack[-1].node_id + "-" + slug, title))
        else:
            node = DocNode(slug, title)
            self.roots.append(node)
            stack.append(node)
        return stack

    @staticmethod
    def _flush(stack: List[DocNode], text: List[str]) -> None:
        if stack and "\n".join(text).strip():
            stack[-1].blocks.append(("md", "\n".join(text)))
        text.clear()

    def _index(self, nodes: List[DocNode]) -> None:
        for node in nodes:
            if node.node_id in self._by_id:
                logger.warning("duplicate techdoku node id %s", node.node_id)
            self._by_id.setdefault(node.node_id, node)
            self._index(node.children)
