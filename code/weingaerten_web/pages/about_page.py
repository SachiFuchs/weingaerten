"""Page /about: host, port, start time and data folder."""
import logging

from ..rendering.html_tools import HtmlTools
from ..rendering.page_context import PageContext

logger = logging.getLogger(__name__)


class AboutPage:
    """Renders the About page."""

    def __init__(self, context: PageContext) -> None:
        """Args:
            context: shared page services.
        """
        self._context = context

    def render(self) -> str:
        """Return the page HTML."""
        settings = self._context.settings
        body = ("<h1>About</h1><p>Haus Weingärten – a local experiment web server generated from a non-code prompt.</p>"
                "<dl><dt>Host</dt><dd>localhost</dd><dt>Port</dt><dd>%d</dd><dt>Started</dt><dd>%s</dd>"
                "<dt>Daten</dt><dd>%s</dd></dl>" % (settings.port, HtmlTools.escape(settings.started),
                                                     HtmlTools.escape(settings.home("–"))))
        return self._context.layout.render("About", "/about", body)
