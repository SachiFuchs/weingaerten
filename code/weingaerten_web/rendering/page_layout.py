"""The BMW-style page frame: header with roundel, collapsible menu, banner, content."""
import logging

from ..constants import MENU
from ..static_assets import StaticAssets
from .html_tools import HtmlTools

logger = logging.getLogger(__name__)


class PageLayout:
    """Wraps page content into the frame of `static/page.html`."""

    def __init__(self, assets: StaticAssets) -> None:
        """Args:
            assets: provides the frame, the CSS and the roundel.
        """
        self._template = assets.text("page.html")
        self._css = assets.text("style.css")
        self._roundel = assets.text("roundel.svg")

    def render(self, title: str, active: str, body: str, house_valid: bool = True, error_count: int = 0,
               head: str = "") -> str:
        """Return the complete HTML page.

        Args:
            title: page name (tab title `Weingärten – <title>`).
            active: url of the current menu entry.
            body: the page content (already HTML).
            house_valid: False shows the red "Modell ungültig" banner.
            error_count: number of model errors shown in the banner.
            head: extra elements for `<head>` (e.g. the import map).
        """
        banner = "" if house_valid else '<div class="banner">Modell ungültig – %d Fehler, siehe Mengen</div>' % error_count
        return self._template % (HtmlTools.escape(title), self._css, head, self._roundel, self._menu(active), banner, body)

    @staticmethod
    def _menu(active: str) -> str:
        return "".join('<a href="%s"%s>%s</a>' % (url, PageLayout._menu_class(url, active, sub), HtmlTools.escape(label))
                       for label, url, sub in MENU)

    @staticmethod
    def _menu_class(url: str, active: str, sub: int) -> str:
        classes = []
        if url == active:
            classes.append("on")
        elif url == "/katalog" and active.startswith("/katalog/"):
            # the group heading is highlighted while one of its sub pages is open
            classes.append("grp")
        if sub:
            classes.append("msub")
        return ' class="%s"' % " ".join(classes) if classes else ""
