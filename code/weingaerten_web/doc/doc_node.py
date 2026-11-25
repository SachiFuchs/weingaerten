"""One node of the /techdoku tree: title, id, content blocks and child nodes."""
import logging
from typing import Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DocNode:
    """A page of the documentation; `blocks` are ("md", text), ("html", markup) or ("lazy", function returning markup)."""

    def __init__(self, node_id: str, title: str, parent: Optional["DocNode"] = None) -> None:
        """Args:
            node_id: unique id (slug path), used in `?node=`.
            title: shown in the tree and as `h1`.
            parent: the enclosing node, None for a top node.
        """
        self.node_id = node_id
        self.title = title
        self.parent = parent
        self.blocks: List[Tuple[str, Any]] = []
        self.children: List["DocNode"] = []

    def add_child(self, node_id: str, title: str) -> "DocNode":
        """Create, append and return a child node."""
        child = DocNode(node_id, title, self)
        self.children.append(child)
        return child

    def ancestors(self) -> List["DocNode"]:
        """Return the parent nodes from the top node down (without this node)."""
        chain = []
        node = self.parent
        while node is not None:
            chain.insert(0, node)
            node = node.parent
        return chain
