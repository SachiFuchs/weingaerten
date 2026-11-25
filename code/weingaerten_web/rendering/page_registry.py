"""Maps the page urls to their page objects."""
import logging
from typing import Dict, List, Optional

from ..constants import CATALOG_PAGES
from ..pages.about_page import AboutPage
from ..pages.grundriss_page import GrundrissPage
from ..pages.haus3d_page import Haus3dPage
from ..pages.katalog_page import KatalogPage
from ..pages.mengen_page import MengenPage
from ..pages.doc_tree_page import DocTreePage
from ..pages.raeume_page import RaeumePage
from ..pages.tga_katalog_page import TgaKatalogPage
from ..pages.waende_page import WaendePage
from .page_context import PageContext

logger = logging.getLogger(__name__)

# pages that show one storey, chosen by `?storey=<id>`
STOREY_PAGES = ("/grundriss", "/waende", "/raeume")
# pages with a document tree, node chosen by `?node=<id>`
DOC_PAGES = ("/handbuch", "/techdoku")


class PageRegistry:
    """All GET pages of the server."""

    def __init__(self, context: PageContext) -> None:
        """Args:
            context: shared page services.
        """
        self._context = context
        self._pages = {"/haus3d": Haus3dPage(context), "/grundriss": GrundrissPage(context),
                       "/waende": WaendePage(context), "/raeume": RaeumePage(context), "/mengen": MengenPage(context),
                       "/handbuch": DocTreePage(context, "/handbuch", "Benutzerhandbuch", "weingaerten-handbuch.md"),
                       "/techdoku": DocTreePage(context, "/techdoku", "Tech.Doku", "weingaerten-techdoku.md"),
                       "/about": AboutPage(context), "/katalog/tga": TgaKatalogPage(context)}
        for slug in CATALOG_PAGES:
            self._pages["/katalog/" + slug] = KatalogPage(context, slug)

    def paths(self) -> List[str]:
        """Return every page url."""
        return list(self._pages)

    def has(self, path: str) -> bool:
        """Return True if path is a page url."""
        return path in self._pages

    def render(self, path: str, query: Optional[Dict[str, str]] = None) -> str:
        """Render the page of a url (see `has`); pages in STOREY_PAGES get the `storey` query value."""
        page = self._pages[path]
        query = query or {}
        if path == "/grundriss":
            return page.render(query.get("storey"), query.get("cut"))
        if path in STOREY_PAGES:
            return page.render(query.get("storey"))
        if path in DOC_PAGES:
            return page.render(query.get("node"))
        return page.render()

    def render_not_found(self) -> str:
        """Render the 404 page."""
        return self._context.layout.render("404", "", "<h1>404</h1><p>Seite nicht gefunden.</p>")
