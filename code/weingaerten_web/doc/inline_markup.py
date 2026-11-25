"""Inline Markdown (`code`, **bold**, *italic*) and heading slugs."""
import logging
import re

from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)


class InlineMarkup:
    """Converts inline Markdown of one text run; the text is escaped first, so no raw HTML gets through."""

    @staticmethod
    def render(text: str) -> str:
        """Return escaped HTML with `<code>`, `<b>` and `<i>`."""
        html = HtmlTools.escape(text)
        html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)
        html = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", html)
        html = re.sub(r"(?<![*\w])\*([^*]+)\*(?![*\w])", r"<i>\1</i>", html)
        return html

    @staticmethod
    def slug(text: str) -> str:
        """Return the anchor of a heading: umlauts spelled out, lowercase letters and digits, everything else `-`."""
        text = text.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
        return re.sub(r"[^a-z0-9]+", "-", text).strip("-")
