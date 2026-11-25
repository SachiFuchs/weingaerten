"""Pages /katalog/<slug>: one catalog type, edited in the browser by `katalog.js`."""
import logging

from ..catalog_enums import FORM_ENUMS
from ..constants import CATALOG_PAGES
from ..rendering.html_tools import HtmlTools
from ..rendering.page_context import PageContext

logger = logging.getLogger(__name__)


class KatalogPage:
    """Renders the catalog page of one element type."""

    def __init__(self, context: PageContext, slug: str) -> None:
        """Args:
            context: shared page services.
            slug: key of CATALOG_PAGES (e.g. `materialien`).
        """
        self._context = context
        self._slug = slug

    def render(self) -> str:
        """Return the page HTML; all elements and their usage are embedded as `katdata`."""
        context = self._context
        element_type, title, new_label = CATALOG_PAGES[self._slug]
        page_title, url = "Katalog – " + title, "/katalog/" + self._slug
        if not context.core.available:
            return context.core_missing_page(page_title, url, "Katalog – %s" % HtmlTools.escape(title))
        house = context.core.ask("HOUSE")
        elements = context.all_elements()
        # every element is embedded because the forms need materials and classes of other types
        usage = context.core.ask("USAGE", all=True).get("usage", {})
        data = {"page": element_type, "elements": elements,
                "usage": {ref: usage.get(ref, []) for ref in elements},
                "enums": FORM_ENUMS}
        assets = context.assets
        new_button = '<button class="btn" id="katnew">%s</button>' % HtmlTools.escape(new_label) if new_label else ""
        body = ['<h1>Katalog – %s</h1>' % HtmlTools.escape(title),
                '<div id="katgrid"><div id="katside"><div id="kattool">%s'
                '<input id="katsearch" type="search" placeholder="Suchen …">'
                '<span id="katcount" class="note"></span></div><div id="katlist" tabindex="0"></div></div>'
                '<div id="katsplit" title="Breite ändern"></div>'
                '<div id="katmain"><div id="kathead"><b id="katname"></b><span id="katbtns">'
                '<button class="btn" id="katedit">Bearbeiten</button></span></div>'
                '<div id="katdetail"></div><div id="katvsplit" title="Höhe ändern"></div><div id="katphotos"></div></div></div>'
                '<div id="kattoast"></div>' % new_button,
                '<script type="application/json" id="katdata">%s</script>' % HtmlTools.embed_json(data),
                '<script>%s</script>' % (assets.text("tip.js") + assets.text("common.js") + assets.text("front.js")
                                         + assets.text("katalog_layout.js") + assets.text("katalog_ifc.js")
                                         + assets.text("katalog_docs.js") + assets.text("katalog.js"))]
        return context.model_page(page_title, url, "".join(body), house)
