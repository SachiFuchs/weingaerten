"""HTML escaping and safe JSON embedding."""
import html
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class HtmlTools:
    """Escaping helpers; every dynamic value in a page goes through them."""

    @staticmethod
    def escape(value: Any) -> str:
        """HTML-escape text (quotes included)."""
        return html.escape(value)

    @staticmethod
    def embed_json(value: Any) -> str:
        """Return JSON for a `<script type="application/json">` block.

        `<` is escaped so the data can never close the script element.
        """
        return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c")
