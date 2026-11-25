"""Page /haus3d: the three.js view of the house."""
import logging
import os
from typing import Any, Dict

from ..constants import LIBRARY_FILES
from ..rendering.html_tools import HtmlTools
from ..rendering.page_context import PageContext

logger = logging.getLogger(__name__)

TITLE, URL = "Haus 3D", "/haus3d"
# short checkbox labels of the storeys
SHORT_NAMES = {"Erdgeschoss": "EG", "Dachgeschoss": "DG", "Obergeschoss": "OG", "Kellergeschoss": "KG"}
IMPORT_MAP = ('<script type="importmap">{"imports":{"three":"/lib/three.module.js",'
              '"three/addons/OrbitControls.js":"/lib/OrbitControls.js"}}</script>')
# the 3D page is a flex row: 3D column | splitter | detail panel (full height, sticky)
WIDE_MAIN = ('<style>main{max-width:none;padding:0}'
             '#row3d{display:flex;flex-wrap:nowrap;align-items:flex-start}'
             '#view3d{flex:1;min-width:320px;padding:2rem}'
             '.opt3d{display:inline-block;vertical-align:top;border:1px solid #ccc;margin:0 .6rem .6rem 0;padding:.2rem .7rem .4rem}'
             '.opt3d legend{font-size:.85em;color:#666;padding:0 .3rem}.opt3d label{margin-right:.6rem;white-space:nowrap}'
             '#split3d{flex:none;width:16px;align-self:stretch;cursor:col-resize;background:#E0E0E0;display:none}'
             '#detailtoggle{position:sticky;top:45vh;width:16px;padding:8px 0;border:0;background:#1C69D4;color:#fff;'
             'font-size:11px;line-height:1.1;cursor:pointer;white-space:normal;word-break:break-all}'
             '#detail3d{flex:none;position:sticky;top:0;height:100vh;overflow:hidden;display:none;background:#fff}'
             '#detail3d iframe{width:100%;height:100%;border:0}'
             '#below3d{display:flex;gap:1rem;align-items:flex-start;margin-top:1rem}'
             '.box3d{flex:1;min-width:0;border:1px solid #ccc;padding:.3rem .8rem}'
             '.box3d summary{cursor:pointer;font-weight:bold;padding:.2rem 0}'
             '.box3d table{border-collapse:collapse}.box3d td{padding:.15rem .8rem .15rem 0;vertical-align:top}'
             '#tip.live{pointer-events:auto}.tiplinks a{display:inline-block;margin:4px 8px 0 0;color:#1C69D4;cursor:pointer}</style>')
# user guide of the 3D view (expandable box right of the legend)
GUIDE_ROWS = (("Linke Maustaste ziehen", "drehen"), ("Rechte Maustaste ziehen", "verschieben (seitlich / hoch / runter)"),
              ("Mausrad", "zoomen, jede Raste ±10 %"),
              ("Strg + Mausrad", "vorwärts / rückwärts in Blickrichtung, 0,5 m je Raste, ohne Zoom"),
              ("Alt + linke Maustaste ziehen", "umschauen: um die eigene Position drehen"),
              ("Maus über Objekt", "Hinweisfeld; kurz stehen lassen = Feld friert ein, Links klickbar"),
              ("Link im Hinweisfeld", "öffnet das Objekt im Detailfenster rechts"),
              ("Doppelklick auf Fenster / Tür", "öffnet das Bauteil im Katalog"),
              ("Esc", "schließt das Hinweisfeld"),
              ("Ecke unten rechts ziehen", "Höhe der Ansicht ändern"))
GUIDE = ('<details class="box3d" id="guide3d" open><summary>Bedienung 3D-Ansicht</summary><table>%s</table></details>'
         % "".join('<tr><td><b>%s</b></td><td>%s</td></tr>' % row for row in GUIDE_ROWS))
# technical systems of the box "Technik": (checkbox id, label, storey or house key)
TECHNIK = (("heizung3d", "Heizung", "heating"), ("wandheizung3d", "Wandheizung", "wall_heating"),
           ("abwasser3d", "Abwasser", "waste_water"),
           ("zuwasser3d", "Zuwasser", "water_supply"), ("elektrik3d", "Elektrik", "electrical"),
           ("einbau3d", "Einbauteile", "installation"))


class Haus3dPage:
    """Renders the 3D page; the scene itself is built in the browser by `haus3d.js`."""

    def __init__(self, context: PageContext) -> None:
        """Args:
            context: shared page services.
        """
        self._context = context

    def render(self) -> str:
        """Return the page HTML (a hint instead of the canvas if three.js is missing)."""
        context = self._context
        house = context.house_or_none()
        if house is None:
            return context.core_missing_page(TITLE, URL, TITLE)
        body = ['<div id="row3d"><div id="view3d"><h1>Haus 3D</h1><p class="sub">Maus: drehen (links ziehen), verschieben (rechts), zoomen (Rad), vorwärts/rückwärts (Strg + Rad), umschauen (Alt + links ziehen) – '
                'Höhe der Ansicht: Ecke unten rechts ziehen</p>',
                '<div>%s%s%s</div>' % (self._storey_fieldset(house), self._technik_fieldset(house), self._details_fieldset())]
        if not self._libraries_present():
            body.append('<p class="bad">three.js fehlt – weingaerten-web ausführen</p></div></div>')
            return context.model_page(TITLE, URL, "".join(body), house)
        body.append('<div id="scene3d" style="position:relative;width:100%;resize:vertical;overflow:hidden;'
                    'min-height:240px;max-height:129vh;background:#EEF2F6;border:1px solid #ccc">'
                    '</div>')
        body.append('<div id="below3d"><details class="box3d" open><summary>Legende Materialien</summary>'
                    '<div id="legend3d"></div></details>%s</div></div>' % GUIDE)
        body.append('<div id="split3d"><button id="detailtoggle" type="button" title="Details ein-/ausklappen">&lt;|&gt;</button></div>'
                    '<div id="detail3d"><iframe id="detailframe" title="Details" '
                    'srcdoc="&lt;p style=&quot;font-family:sans-serif;color:#666;padding:1rem&quot;&gt;Objekt anklicken&lt;/p&gt;">'
                    '</iframe></div></div>')
        body.append('<script type="application/json" id="house">%s</script>' % HtmlTools.embed_json(house))
        body.append('<script>%s</script>' % context.assets.text("tip.js"))
        body.append('<script>%s</script>' % context.assets.text("detail3d.js"))
        body.append('<script>%s</script>' % context.assets.text("waste3d.js"))
        body.append('<script>%s</script>' % context.assets.text("water3d.js"))
        body.append('<script>%s</script>' % context.assets.text("electric3d.js"))
        body.append('<script>%s</script>' % context.assets.text("parts3d.js"))
        body.append('<script>%s</script>' % context.assets.text("room3d.js"))
        body.append('<script>%s</script>' % context.assets.text("wallheat3d.js"))
        body.append('<script type="module">%s</script>' % context.assets.text("haus3d.js"))
        return context.model_page(TITLE, URL, "".join(body), house, IMPORT_MAP + WIDE_MAIN)

    @staticmethod
    def _storey_fieldset(house: Dict[str, Any]) -> str:
        return ('<fieldset class="opt3d"><legend>Stockwerke</legend>%s'
                '<label><input type="checkbox" id="decke3d"> Decke</label>%s%s%s%s%s</fieldset>'
                % (Haus3dPage._storey_boxes(house), Haus3dPage._roof_structure_box(house),
                   Haus3dPage._roof_covering_box(house), Haus3dPage._lining_box(house),
                   Haus3dPage._optional_box(any(r.get("coverings") for s in house.get("storeys") or [] for r in s["rooms"]),
                                            "belag3d", "Beläge"),
                   Haus3dPage._optional_box(bool(house.get("shafts")), "schacht3d", "Schächte")))

    @staticmethod
    def _optional_box(present: bool, box_id: str, label: str) -> str:
        # active only when the house has such elements
        if present:
            return '<label><input type="checkbox" id="%s" checked> %s</label>' % (box_id, label)
        return '<label title="noch nicht vorhanden"><input type="checkbox" disabled> %s</label>' % label

    @staticmethod
    def _lining_box(house: Dict[str, Any]) -> str:
        # active only when a storey has interior linings
        if any(s.get("linings") for s in house.get("storeys") or []):
            return '<label><input type="checkbox" id="daemmung3d" checked> Innendämmung</label>'
        return '<label title="noch nicht vorhanden"><input type="checkbox" disabled> Innendämmung</label>'

    @staticmethod
    def _technik_fieldset(house: Dict[str, Any]) -> str:
        # one checkbox per technical system, active only when a storey has it
        storeys = house.get("storeys") or []
        boxes = []
        for box_id, label, key in TECHNIK:
            if any(s.get(key) for s in storeys) or Haus3dPage._present(house.get(key)):
                boxes.append('<label><input type="checkbox" id="%s" checked> %s</label>' % (box_id, label))
            else:
                boxes.append('<label title="noch nicht vorhanden"><input type="checkbox" disabled> %s</label>' % label)
        return '<fieldset class="opt3d"><legend>Technik</legend>%s</fieldset>' % "".join(boxes)

    @staticmethod
    def _present(value: Any) -> bool:
        # the installation block always exists; it counts only with placed parts
        if isinstance(value, dict) and "parts" in value and "catalog" in value:
            return bool(value["parts"])
        return bool(value)

    @staticmethod
    def _details_fieldset() -> str:
        return ('<fieldset class="opt3d"><legend>Details</legend>'
                '<label><input type="checkbox" id="transp3d"> transparent</label>'
                '<label><input type="checkbox" id="beschr3d"> Beschriftungen</label>'
                '<label><input type="checkbox" id="details3d"> Details</label></fieldset>')

    @staticmethod
    def _storey_boxes(house: Dict[str, Any]) -> str:
        # one checkbox per storey (bottom up), label = short name (EG, DG) with the full name as title
        storeys = sorted(house.get("storeys") or [], key=lambda s: s.get("elevation") or 0)
        boxes = []
        for storey in storeys:
            storey_id = HtmlTools.escape(str(storey.get("id")))
            name = str(storey.get("name") or storey.get("id"))
            boxes.append('<label title="%s"><input type="checkbox" id="geschoss3d-%s" checked> %s</label>'
                         % (HtmlTools.escape(name), storey_id, HtmlTools.escape(SHORT_NAMES.get(name, name))))
        return "".join(boxes)

    @staticmethod
    def _roof_structure_box(house: Dict[str, Any]) -> str:
        # active only when a storey has a roof structure
        if any(s.get("roof_structure") for s in house.get("storeys") or []):
            return '<label><input type="checkbox" id="dachstuhl3d" checked> Dachstuhl</label>'
        return '<label title="noch nicht vorhanden"><input type="checkbox" disabled> Dachstuhl</label>'

    @staticmethod
    def _roof_covering_box(house: Dict[str, Any]) -> str:
        # active only when a storey has a roof covering
        if any(s.get("roof_covering") for s in house.get("storeys") or []):
            return '<label><input type="checkbox" id="dach3d" checked> Dach</label>'
        return ('<label title="noch nicht vorhanden"><input type="checkbox" disabled> Dach</label>'
                '<span class="note">(Dach noch nicht vorhanden)</span>')

    def _libraries_present(self) -> bool:
        lib_dir = self._context.settings.lib_dir
        return all(os.path.isfile(os.path.join(lib_dir, name)) for name in LIBRARY_FILES)
