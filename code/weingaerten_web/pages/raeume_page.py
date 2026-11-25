"""Page /raeume: rooms with number, usage and height, floor and wall coverings and shafts (`raum.js`)."""
import logging
from typing import Optional

from ..catalog_enums import FORM_ENUMS
from ..rendering.html_tools import HtmlTools
from ..rendering.page_context import PageContext
from ..rendering.storey_selector import StoreySelector

logger = logging.getLogger(__name__)

TITLE, URL = "Räume", "/raeume"
# element types the covering forms need (assemblies of category covering and their materials)
EMBEDDED_TYPES = ("material", "assembly")
TABS = (("floor", "Bodenbeläge"), ("wall", "Wandbeläge"), ("shaft", "Schächte"), ("furniture", "Möblierung"))


class RaeumePage:
    """Renders the room page; plan, tables and forms are built in the browser."""

    def __init__(self, context: PageContext) -> None:
        """Args:
            context: shared page services.
        """
        self._context = context

    def render(self, storey_id: Optional[str] = None) -> str:
        """Return the page HTML with house and elements embedded as `raumdata` (storey `storey_id` first)."""
        context = self._context
        if not context.core.available:
            return context.core_missing_page(TITLE, URL, TITLE)
        house = StoreySelector.view(context.core.ask("HOUSE"), storey_id)
        elements = context.all_elements()
        data = {"house": house,
                "elements": {ref: e for ref, e in elements.items() if ref.split(":")[0] in EMBEDDED_TYPES},
                "enums": FORM_ENUMS}
        tabs = "".join('<button class="btn2 rtab" data-tab="%s"%s>%s</button>'
                       % (key, ' disabled title="später"' if key == "furniture" else "", label) for key, label in TABS)
        assets = context.assets
        # same master-detail frame as the wall page (katgrid/katside/katsplit/katmain, KatLayout splitter)
        body = ['<h1>Räume</h1><p class="sub">Raumdaten, Bodenbeläge (ganzer Raum oder Teilflächen), Wandbeläge '
                '(Fliesenspiegel, Sockelleiste) und Schächte – Maße in cm; die Raumform wird im Grundriss bearbeitet</p>',
                '<div id="katgrid"><div id="katside"><div id="kattool">'
                '<label>Geschoss <select id="rfloor"></select></label>'
                '<input id="rsearch" type="search" placeholder="Suchen …" style="padding:5px 8px;flex:1;min-width:100px">'
                '<span id="katcount" class="note"></span></div>'
                '<div id="katlist"><div id="roomlist"></div></div></div>'
                '<div id="katsplit" title="Breite ändern"></div><div id="katmain"><div id="kathead">'
                '<b id="katname"></b><span class="note" id="rtitle"></span><span id="katbtns">'
                '<button class="btn" id="redmode">Bearbeiten</button>'
                '<button class="btn" id="rsave" style="display:none">Speichern und zurück</button>'
                '<button class="btn2" id="rcancel" style="display:none">Abbrechen</button></span></div>'
                '<div id="katdetail" class="wmain"><div id="rsaveerr" style="color:#C62828;margin:.4rem 0"></div>'
                '<div id="rdata" class="wpanel" style="margin-top:0"></div>'
                '<div style="margin:.5rem 0"><a id="redit" href="/grundriss#edit">Raumform im Grundriss bearbeiten</a></div>'
                '<svg id="roomsvg" style="width:100%;background:#fff;border:1px solid #ddd;touch-action:none;user-select:none"></svg>'
                '<div id="rtabs" style="display:flex;gap:.4rem;margin:.8rem 0 .2rem">' + tabs + '</div>'
                '<div id="rbar"></div><div class="wpanel" id="rpanel" style="display:none"></div><table id="rtable"></table>'
                '</div><div id="katvsplit"></div><div id="katphotos"></div></div></div><div id="kattoast"></div>',
                '<script type="application/json" id="raumdata">%s</script>' % HtmlTools.embed_json(data),
                '<script>%s</script>' % (assets.text("tip.js") + assets.text("common.js")
                                         + assets.text("katalog_layout.js") + assets.text("raum.js"))]
        return context.model_page(TITLE, URL, "".join(body), house)
