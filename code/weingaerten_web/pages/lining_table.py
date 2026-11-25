"""Table "Innendämmung" of the page /mengen: lined areas per wall face and the sums per layer material."""
import logging
from typing import Any, Dict, List

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

escape = HtmlTools.escape
decimal = GermanFormat.decimal
FACE_NAMES = {"inside": "innen", "left": "links", "right": "rechts"}


class LiningTable:
    """Renders the interior linings of the BOM."""

    @staticmethod
    def render(linings: List[Dict[str, Any]]) -> str:
        """Return the HTML of the section (one row per lined area, then one row per layer material)."""
        rows = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td><code>%s</code></td><td class=n>%s – %s</td>'
                       '<td class=n>%s – %s</td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>'
                       '<td class=n>%s</td></tr>' % (
                           escape(l["lining"]), escape(l.get("wall_name") or l["wall"]),
                           FACE_NAMES.get(l["face"], escape(l["face"])), escape(l["assembly"]),
                           decimal(l["u0"] * 100, 0), decimal(l["u1"] * 100, 0), decimal(l["z0"] * 100, 0),
                           decimal(l["z1"] * 100, 0), decimal(l["gross_area"]), decimal(l["opening_area"]),
                           decimal(l["area"]), decimal(l["volume"])) for l in linings)
        layers: Dict[str, Dict[str, float]] = {}
        for lining in linings:
            for layer in lining["layers"]:
                row = layers.setdefault(layer["material"], {"thickness": layer["thickness"], "area": 0.0, "volume": 0.0})
                row["area"] += layer["area"]
                row["volume"] += layer["volume"]
        layer_rows = "".join('<tr><td><code>%s</code></td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
            escape(ref), decimal(v["thickness"] * 100, 1), decimal(v["area"]), decimal(v["volume"], 3))
            for ref, v in layers.items())
        return ('<h2>Innendämmung</h2><table><tr><th>Bereich</th><th>Wand</th><th>Seite</th><th>Aufbau</th>'
                '<th class=n>von – bis cm</th><th class=n>Höhe cm</th><th class=n>brutto m²</th>'
                '<th class=n>Öffnungen m²</th><th class=n>netto m²</th><th class=n>Volumen m³</th></tr>%s'
                '<tr class="sum"><td>Summe</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td>'
                '<td class=n>%s</td><td class=n>%s</td></tr></table>'
                '<table><tr><th>Schicht (Material)</th><th class=n>Dicke cm</th><th class=n>Fläche m²</th>'
                '<th class=n>Volumen m³</th></tr>%s</table>' % (
                    rows, decimal(sum(l["area"] for l in linings)), decimal(sum(l["volume"] for l in linings)),
                    layer_rows))
