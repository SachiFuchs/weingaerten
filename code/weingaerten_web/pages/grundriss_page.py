"""Page /grundriss: plan section at 1.0 m, plan editor (`plan.js`) and the corner detail."""
import logging
from typing import Any, Dict, Optional

from ..plan.corner_detail import CornerDetail
from ..plan.plan_svg import PlanSvg
from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools
from ..rendering.page_context import PageContext
from ..rendering.storey_selector import StoreySelector

logger = logging.getLogger(__name__)

TITLE, URL = "Grundriss", "/grundriss"
WALL_CATEGORIES = ("exterior_wall", "interior_wall")
FALLBACK_WALL_COLOR = "#C9A88A"
DEFAULT_CUT = 1.0  # m above the storey floor


class GrundrissPage:
    """Renders the floor plan page."""

    def __init__(self, context: PageContext) -> None:
        """Args:
            context: shared page services.
        """
        self._context = context

    def render(self, storey_id: Optional[str] = None, cut_cm: Optional[str] = None) -> str:
        """Return the page HTML for the storey `storey_id` (default the first storey) cut at `cut_cm` cm."""
        context = self._context
        house = context.house_or_none()
        if house is None:
            return context.core_missing_page(TITLE, URL, TITLE)
        house = StoreySelector.view(house, storey_id)
        storey = (house.get("storeys") or [None])[0]
        if not storey or not house.get("bbox"):
            body = '<h1>Grundriss</h1><p class="note">Kein Geschoss vorhanden.</p>'
            return context.model_page(TITLE, URL, body, house)
        cut = self._cut_height(cut_cm, storey)
        assets = context.assets
        hatch_defs = assets.text("hatch_defs.svg")
        body = ['<h1>Grundriss</h1><p class="sub">Horizontalschnitt bei %s m – alle Schichten und Öffnungen</p>'
                % GermanFormat.decimal(cut, 2), self._toolbar(house, cut)]
        body.append('<div class="planlay"><div id="planbox"><div id="planview">'
                    + PlanSvg(house, storey, hatch_defs, cut).render() + '</div>'
                    '<div id="planarea" style="display:none"><svg id="planedsvg" '
                    'style="width:100%;background:#fff;touch-action:none;user-select:none"></svg></div></div>'
                    '<div id="plansplit" style="display:none"></div><div id="planpanel" style="display:none"></div></div>'
                    '<div id="kattoast"></div>')
        plan_data = {"house": house, "assemblies": self._wall_assemblies()}
        body.append('<script type="application/json" id="plandata">%s</script>' % HtmlTools.embed_json(plan_data))
        body.append('<script>%s</script>' % (assets.text("common.js") + assets.text("plan_zoom.js") + assets.text("plan.js")))
        body.append(CornerDetail(house, storey).render())
        body.append('<style>#tip.live{pointer-events:auto}.tiplinks a{display:inline-block;margin:4px 8px 0 0;'
                    'color:#1C69D4;cursor:pointer}</style>')
        body.append("<script>%s\n%s</script>" % (assets.text("tip.js"), assets.text("plan_tooltips.js")))
        return context.model_page(TITLE, URL, "".join(body), house)

    @staticmethod
    def _cut_height(cut_cm: Optional[str], storey: Dict[str, Any]) -> float:
        # storey-local cut height in m from `?cut=<cm>`, clamped to the storey height
        try:
            cut = float(cut_cm) / 100 if cut_cm not in (None, "") else DEFAULT_CUT
        except ValueError:
            cut = DEFAULT_CUT
        return min(max(cut, 0.0), storey.get("height") or DEFAULT_CUT)

    @staticmethod
    def _toolbar(house: Dict[str, Any], cut: float) -> str:
        return ('<div id="plantools"><label>Geschoss %s</label>'
                '<label>Schnitthöhe cm <input id="plancut" type="number" step="1" min="0" value="%d"></label>'
                '<label><input type="checkbox" id="planroomnames" checked> Raumnamen</label>'
                '<label><input type="checkbox" id="planwallnames" checked> Wandnamen</label>'
                '<span class="zoombtns"><button class="btn2" id="zoomin" title="Vergrößern">+</button>'
                '<button class="btn2" id="zoomout" title="Verkleinern">−</button>'
                '<button class="btn2" id="zoomfit">Einpassen</button></span>'
                '<button class="btn" id="planedit">Bearbeiten</button>'
                '<span class="note">Wände verschieben, verlängern, drehen, teilen, Versprung, Räume und Geschosshöhe'
                ' · Mausrad = Zoom, rechte Maustaste ziehen = Verschieben, Slider bei Überstand</span></div>'
                % (StoreySelector.select(house), round(cut * 100)))

    def _wall_assemblies(self) -> Dict[str, Dict[str, Any]]:
        # wall assemblies for the editor; the colour of the thickest layer stands for the wall
        core = self._context.core
        assemblies = {}
        for entry in core.ask("CATALOG", type="assembly").get("elements", []):
            resolved = core.ask("RESOLVE", ref=entry["ref"])
            if resolved.get("category") in WALL_CATEGORIES:
                layers = resolved.get("layers") or []
                thickest = max(layers, key=lambda layer: layer.get("thickness", 0)) if layers else {}
                color = ((thickest.get("material") or {}).get("appearance") or {}).get("color", FALLBACK_WALL_COLOR)
                assemblies[entry["ref"]] = {"name": resolved.get("name"), "category": resolved.get("category"),
                                            "thickness": resolved.get("thickness"), "color": color}
        return assemblies
