"""Page /katalog/tga: TGA classes and components with their connection rules, edited by `katalog_tga.js`."""
import logging

from ..catalog_enums import FORM_ENUMS
from ..catalog_labels import CatalogLabels
from ..rendering.html_tools import HtmlTools
from ..rendering.page_context import PageContext

logger = logging.getLogger(__name__)

TITLE = "Katalog – TGA"
URL = "/katalog/tga"
INTRO = ("Technische Gebäudeausrüstung (TGA, KG 400): Elektro, Abwasser, Zuwasser und Heizung – Klassen, Bauteile, "
         "Anschluss- und Verbindungsregeln sowie die Darstellung für die Planung in den Wänden.")


class TgaKatalogPage:
    """Renders the TGA catalog (classes, components, connection data and issues)."""

    def __init__(self, context: PageContext) -> None:
        """Args:
            context: shared page services.
        """
        self._context = context

    def render(self) -> str:
        """Return the page HTML; the TGA_CATALOG answer is embedded as `katdata`."""
        context = self._context
        if not context.core.available:
            return context.core_missing_page(TITLE, URL, HtmlTools.escape(TITLE))
        house = context.core.ask("HOUSE")
        catalog = context.core.ask("TGA_CATALOG")
        # companies and materials are needed for the product block and the material link
        names = {ref: {"name": e.get("name"), "roles": e.get("roles")} for ref, e in context.all_elements().items()
                 if ref.startswith(("company:", "material:"))}
        data = {"page": "tga", "elements": catalog.get("elements", {}), "conductors": catalog.get("conductors", {}),
                "issues": catalog.get("issues", []), "names": names, "enums": FORM_ENUMS,
                "abstracts": catalog.get("abstracts", {}), "assemblies": catalog.get("assemblies", {}),
                "trees": catalog.get("trees", []), "placement": catalog.get("placement", {}),
                "labels": CatalogLabels.load(context.settings.home())}
        body = ['<h1>%s (Technische Gebäudeausrüstung)</h1>' % HtmlTools.escape(TITLE),
                '<p class="note" style="margin:-4px 0 8px">%s</p>' % HtmlTools.escape(INTRO),
                '<div id="kattabs" style="display:flex;gap:4px;margin:0 0 6px">'
                '<button class="btn2" data-tab="list">Liste</button><button class="btn2" data-tab="tree">Baum</button></div>',
                '<div id="katgrid"><div id="katside"><div id="kattool">'
                '<button class="btn" id="katnew">+ TGA-Bauteil</button>'
                '<button class="btn" id="katnewasm">+ Baugruppe</button>'
                '<button class="btn" id="katnewtree">+ Baum</button>'
                '<input id="katsearch" type="search" placeholder="Suchen …">'
                '<span id="katcount" class="note"></span></div>'
                '<div id="tgafilter" style="display:flex;gap:6px;flex-wrap:wrap;margin:4px 0">'
                '<select id="tgafilter-kind"></select>'
                '<label><input type="checkbox" id="tgafilter-issues"> nur mit Hinweisen</label></div>'
                '<div id="katlist" tabindex="0"></div><div id="kattree" style="display:none;flex:1;overflow:auto;padding:4px 6px"></div></div>'
                '<div id="katsplit" title="Breite ändern"></div>'
                '<div id="katmain"><div id="kathead"><b id="katname"></b><span id="katbtns">'
                '<button class="btn" id="katedit">Bearbeiten</button></span></div>'
                '<div id="katdetail"></div><div id="katvsplit" title="Höhe ändern"></div><div id="katphotos"></div>'
                '</div></div><div id="kattoast"></div>',
                '<script type="application/json" id="katdata">%s</script>' % HtmlTools.embed_json(data),
                '<script>%s</script>' % (context.assets.text("tip.js") + context.assets.text("common.js")
                                         + context.assets.text("katalog_layout.js")
                                         + context.assets.text("katalog_tga_tree.js")
                                         + context.assets.text("katalog_tga_draw.js")
                                         + context.assets.text("katalog_tga.js"))]
        return context.model_page(TITLE, URL, "".join(body), house)
