"""Page /waende: wall elevations with interactive openings (`wand.js`)."""
import logging
from typing import Optional

from ..catalog_enums import FORM_ENUMS
from ..rendering.html_tools import HtmlTools
from ..rendering.page_context import PageContext
from ..rendering.storey_selector import StoreySelector
from .haus3d_page import IMPORT_MAP

logger = logging.getLogger(__name__)

TITLE, URL = "Wände", "/waende"
# element types the opening and lining forms need
EMBEDDED_TYPES = ("material", "assembly", "class", "component")
# palette and port menu of the installation mode (install.js)
INSTALL_STYLE = ('<style>#instpal{display:block;flex:1;min-height:0;overflow:auto;padding:.4rem}.instgrp{border:1px solid #ddd;padding:.2rem .4rem}'
                 '.insttree details{margin-left:1rem}.insttree>details{margin-left:0}.insttree summary{cursor:pointer;font-size:.9em;padding:1px 0}'
                 '.insttree summary.off{color:#aaa}.insttree .cnt{color:#888;font-size:.85em}.insttree .items{margin-left:1rem}'
                 '.instgrp b{display:block;font-size:.8em;color:#666}.instbtn{margin:2px;font-size:.85em;cursor:pointer;background:#fff;'
                 'border:1px solid #bbb;padding:2px 6px}.instbtn.on{border-color:#1C69D4;background:#F2F7FD}'
                 '.instmenu{background:#fff;border:1px solid #999;box-shadow:0 2px 6px rgba(0,0,0,.2);z-index:50;font-size:.9em}'
                 '.institem{padding:4px 10px;cursor:pointer}.institem:hover{background:#F2F7FD}.insttab td,.insttab th{padding:2px 8px}</style>')


class WaendePage:
    """Renders the wall page; the elevation is drawn in the browser."""

    def __init__(self, context: PageContext) -> None:
        """Args:
            context: shared page services.
        """
        self._context = context

    def render(self, storey_id: Optional[str] = None) -> str:
        """Return the page HTML with house and elements embedded as `wanddata` (storey `storey_id` first)."""
        context = self._context
        if not context.core.available:
            return context.core_missing_page(TITLE, URL, TITLE)
        house = StoreySelector.view(context.core.ask("HOUSE"), storey_id)
        elements = context.all_elements()
        data = {"house": house,
                "elements": {ref: e for ref, e in elements.items() if ref.split(":")[0] in EMBEDDED_TYPES},
                "enums": FORM_ENUMS}
        assets = context.assets
        # four panes: list | wall view over parts table | installation tree over 3D preview (WaendeLayout splitters)
        body = ['<h1>Wände</h1><p class="sub">Öffnungen, Innendämmung und Einbauteile (Elektro, Abwasser, Zuwasser) einfügen, verschieben, ändern und löschen – Maße in cm</p>',
                '<div id="katgrid"><div id="katside"><div id="kattool">'
                '<label>Geschoss <select id="wfloor"></select></label>'
                '<input id="wsearch" type="search" placeholder="Suchen …" style="padding:5px 8px;flex:1;min-width:100px">'
                '<span id="katcount" class="note"></span></div>'
                '<div id="katlist"><div id="wallist"></div></div></div>'
                '<div id="katsplit" title="Breite ändern"></div><div id="katmain"><div id="kathead">'
                '<b id="katname"></b><span class="note" id="wtitle"></span><span id="katbtns">'
                '<button class="btn" id="wedmode">Bearbeiten</button>'
                '<button class="btn2" id="opnew" style="display:none">+ Öffnung</button>'
                '<button class="btn" id="opsave" style="display:none">Speichern und zurück</button>'
                '<button class="btn2" id="wcancel" style="display:none">Abbrechen</button></span></div><div id="katdetail" class="wmain">'
                '<div style="display:flex;gap:.5rem;align-items:center;flex-wrap:wrap">'
                '<label><input type="radio" name="wview" value="outside" checked> Außenansicht</label>'
                '<label><input type="radio" name="wview" value="inside"> Innenansicht</label>'
                '<a id="wedit" href="/grundriss#edit">Wand im Grundriss bearbeiten</a></div>'
                '<div id="instbar" style="margin-top:.5rem"></div>'
                '<svg id="wallsvg" style="width:100%;background:#fff;border:1px solid #ddd;margin-top:.5rem;touch-action:none;user-select:none"></svg>'
                '<svg id="instsec" style="display:none;width:100%;height:70px;background:#FAFAFA;border:1px solid #ddd;touch-action:none"></svg>'
                '<div class="wpanel" id="instpanel" style="display:none"></div>'
                '<div class="wpanel" id="oppanel" style="display:none"></div>'
                '<table id="optable"></table>'
                '<h3>Innendämmung</h3><div id="linbar"></div><div class="wpanel" id="linpanel" style="display:none"></div>'
                '<table id="lintable"></table></div>'
                '<div id="wcsplit" class="hsplit" title="Höhe ändern"></div>'
                '<div id="wbottom"><h3>Einbauteile dieser Wandseite</h3><table id="insttable"></table></div></div>'
                '<div id="wrsplit" class="vsplit" title="Breite ändern"></div><div id="wright"><div id="instpal"></div>'
                '<div id="prevsplit" title="Höhe der 3D-Vorschau ändern"></div>'
                '<div id="prev3dbox"><b>3D-Vorschau</b>'
                '<div id="prev3d" style="flex:1;min-height:0;overflow:hidden;position:relative"></div>'
                '<button class="btn2" id="prev3dreset" type="button">Ansicht zurücksetzen</button></div></div></div>'
                '<div id="kattoast"></div>' + INSTALL_STYLE,
                '<script type="application/json" id="wanddata">%s</script>' % HtmlTools.embed_json(data),
                '<script>%s</script>' % (assets.text("tip.js") + assets.text("common.js") + assets.text("front.js")
                                         + assets.text("katalog_layout.js") + assets.text("waende_layout.js") + assets.text("wand.js") + assets.text("lining.js")
                                         + assets.text("install_tree.js") + assets.text("install.js") + assets.text("parts3d.js")),
                '<script type="module">%s</script>' % assets.text("install3d.js")]
        return context.model_page(TITLE, URL, "".join(body), house, IMPORT_MAP)
