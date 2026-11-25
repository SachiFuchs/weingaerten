"""Tables `Boden` and `Fußbodenheizung` of the page /mengen."""
import logging
from typing import Any, Dict, List

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

PATTERN_NAMES = {"spiral": "Schnecke", "meander": "Mäander"}
MEASURE_NAMES = {"area": "Bodenfläche", "edge": "Randlänge", "offer": "lt. Angebot"}

escape = HtmlTools.escape
decimal = GermanFormat.decimal
money = GermanFormat.money


class FloorHeatingTables:
    """Renders the floor build-ups (rooms, layers, offer comparison) and the heating circuits of the BOM."""

    @staticmethod
    def floors(floors: List[Dict[str, Any]]) -> str:
        """Return the section `Boden` (one block per floor)."""
        return "".join(FloorHeatingTables._floor(f) for f in floors)

    @staticmethod
    def _floor(f: Dict[str, Any]) -> str:
        rooms = "".join('<tr><td>%s</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
            escape(r["name"]), decimal(r["area"], 2), decimal(r["edge_length"], 2)) for r in f["rooms"])
        layers = "".join('<tr><td>%d</td><td><code>%s</code></td><td class=n>%s</td><td class=n>%s</td><td>%s</td></tr>' % (
            layer["index"] + 1, escape(layer["material"]), decimal(layer["thickness"] * 100, 1), decimal(layer["volume"]),
            "Rohrebene" if layer["heated"] else "") for layer in f["layers"])
        return ('<h2>Boden</h2><p>%s – Aufbau <code>%s</code>, Dicke %s cm, Fläche %s m², Randlänge %s m, Volumen %s m³</p>'
                '<table><tr><th>Raum</th><th class=n>Fläche m²</th><th class=n>Randlänge m</th></tr>%s'
                '<tr class="sum"><td>Summe</td><td class=n>%s</td><td class=n>%s</td></tr></table>'
                '<table><tr><th>Schicht (oben → unten)</th><th>Material</th><th class=n>Dicke cm</th>'
                '<th class=n>Volumen m³</th><th></th></tr>%s</table>%s' % (
                    escape(f.get("name") or f["floor"]), escape(f["assembly"]), decimal(f["thickness"] * 100, 1),
                    decimal(f["area"], 2), decimal(f["edge_length"], 2), decimal(f["volume"]), rooms,
                    decimal(f["area"], 2), decimal(f["edge_length"], 2), layers, FloorHeatingTables._offer(f.get("offer"))))

    @staticmethod
    def _document(offer: Dict[str, Any]) -> str:
        # a catalog document ref becomes a link to its card, other text is shown as is
        document = offer.get("document") or ""
        if document.startswith("document:"):
            return '<a href="/katalog/dokumente#%s">%s</a>' % (escape(document),
                                                                escape(offer.get("document_name") or document))
        return escape(document)

    @staticmethod
    def _offer(offer: Any) -> str:
        if not offer:
            return ""
        rows = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td class=n>%s %s</td><td class=n>%s %s</td>'
                       '<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
                           escape(i["pos"] or ""), escape(i["name"] or ""), MEASURE_NAMES.get(i["measure"], i["measure"]),
                           decimal(i["quantity"], 2), escape(i["unit"] or ""), decimal(i["model_quantity"], 2),
                           escape(i["unit"] or ""), money(i["unit_price"], "EUR"), money(i["offer_total"], "EUR"),
                           money(i["model_total"], "EUR")) for i in offer["items"])
        return ('<h3>Angebot %s %s (%s)</h3><table><tr><th>Pos.</th><th>Leistung</th><th>Modellmenge</th>'
                '<th class=n>Angebot</th><th class=n>Modell</th><th class=n>EP netto</th><th class=n>GP Angebot</th>'
                '<th class=n>GP Modell</th></tr>%s<tr class="sum"><td>Summe</td><td></td><td></td><td></td><td></td>'
                '<td></td><td class=n>%s</td><td class=n>%s</td></tr></table>' % (
                    escape(offer.get("company_name") or offer["company"]), FloorHeatingTables._document(offer),
                    escape(offer.get("date") or ""), rows, money(offer["offer_total"], "EUR"),
                    money(offer["model_total"], "EUR")))

    @staticmethod
    def heating(rows_in: List[Dict[str, Any]]) -> str:
        """Return the section `Fußbodenheizung` (one table per storey heating)."""
        parts = []
        for x in rows_in:
            rows = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td class=n>%s</td><td class=n>%s</td>'
                           '<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
                               escape(c.get("name") or c["id"]), escape(c["room"]),
                               PATTERN_NAMES.get(c["pattern"], c["pattern"]), decimal(c["spacing"] * 100, 1),
                               decimal(c["area"], 2), decimal(c["length_field"], 1), decimal(c["length_feed"], 1),
                               decimal(c["length"], 1)) for c in x["circuits"])
            parts.append('<h2>Fußbodenheizung</h2><p>%s – Rohr <code>%s</code> Ø %s mm%s</p>'
                         '<table><tr><th>Heizkreis</th><th>Raum</th><th>Verlegung</th><th class=n>Abstand cm</th>'
                         '<th class=n>Fläche m²</th><th class=n>Rohr Fläche m</th><th class=n>Anbindung m</th>'
                         '<th class=n>Rohr gesamt m</th></tr>%s<tr class="sum"><td>Summe</td><td></td><td></td><td></td>'
                         '<td class=n>%s</td><td></td><td></td><td class=n>%s</td></tr></table>' % (
                             escape(x.get("name") or ""), escape(x.get("pipe") or ""),
                             decimal(x["pipe_diameter"] * 1000, 0), " (geschätzt)" if x["estimated"] else "", rows,
                             decimal(x["area"], 2), decimal(x["length"], 1)))
        return "".join(parts)
