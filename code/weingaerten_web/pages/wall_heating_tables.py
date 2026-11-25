"""Table `Wandheizung` of the page /mengen: heating circuits, panel fields, bill of panels and fittings, layers."""
import logging
from typing import Any, Dict, List

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

KIND_NAMES = {"panel": "Platte", "coupling": "Presskupplung Platte–Platte", "adapter": "Übergang auf Anbindeleitung"}

escape = HtmlTools.escape
decimal = GermanFormat.decimal
money = GermanFormat.money


class WallHeatingTables:
    """Renders the wall heating rows of the BOM (one block per storey)."""

    @staticmethod
    def render(rows_in: List[Dict[str, Any]]) -> str:
        """Return the section `Wandheizung`."""
        return "".join(WallHeatingTables._block(x) for x in rows_in)

    @staticmethod
    def _block(x: Dict[str, Any]) -> str:
        design = ""
        if x.get("supply_temperature") is not None:
            design = ", Auslegung %s/%s °C" % (decimal(x["supply_temperature"], 0), decimal(x["return_temperature"], 0))
        head = ('<h2>Wandheizung</h2><p>%s – Aufbau <code>%s</code>, %d Platten, Heizfläche %s m², Rohr in Platten %s m, '
                'Anbindung %s m%s%s</p>' % (
                    escape(x.get("name") or x["storey"]), escape(x["assembly"]), x["panel_count"], decimal(x["area"], 2),
                    decimal(x["pipe_length"], 1), decimal(x["feed_length"], 1), design,
                    " (geschätzt)" if x["estimated"] else ""))
        return head + WallHeatingTables._circuits(x) + WallHeatingTables._fields(x) + WallHeatingTables._items(x) \
            + WallHeatingTables._layers(x)

    @staticmethod
    def _circuits(x: Dict[str, Any]) -> str:
        rows = "".join('<tr><td>%s</td><td>%s</td><td class=n>%d</td><td class=n>%s</td><td class=n>%s</td>'
                       '<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
                           escape(c.get("name") or c["id"]), escape(c["room"]), c["panel_count"], decimal(c["area"], 2),
                           decimal(c["design_area"], 2) if c["design_area"] is not None else "–",
                           decimal(c["design_output"], 0) if c["design_output"] is not None else "–",
                           decimal(c["pipe_length"], 1), decimal(c["feed_length"], 1)) for c in x["circuits"])
        output = sum(c["design_output"] or 0 for c in x["circuits"])
        distributor = x.get("distributor") or {}
        return ('<p>Verteiler: %s%s</p><table><tr><th>Heizkreis</th><th>Raum</th><th class=n>Platten</th>'
                '<th class=n>Fläche m²</th><th class=n>Auslegung m²</th><th class=n>Leistung W</th>'
                '<th class=n>Rohr Platten m</th><th class=n>Anbindung m</th></tr>%s'
                '<tr class="sum"><td>Summe</td><td></td><td class=n>%d</td><td class=n>%s</td><td></td>'
                '<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr></table>' % (
                    escape(distributor.get("name") or "–"),
                    (' (<code>%s</code>, %s Abgänge)' % (escape(distributor["component"]), distributor.get("outlets") or "?"))
                    if distributor.get("component") else "", rows, x["panel_count"], decimal(x["area"], 2),
                    decimal(output, 0), decimal(x["pipe_length"], 1), decimal(x["feed_length"], 1)))

    @staticmethod
    def _fields(x: Dict[str, Any]) -> str:
        rows = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><code>%s</code></td><td class=n>%s</td></tr>' % (
            escape(f.get("name") or f["id"]), escape(f["circuit"]), escape(f["room"]),
            escape(f.get("wall_name") or f.get("wall") or ""), escape(f["panels"]), decimal(f["area"], 2))
            for f in x["fields"])
        return ('<h3>Plattenfelder</h3><table><tr><th>Feld</th><th>Heizkreis</th><th>Raum</th><th>Wand</th>'
                '<th>Platten</th><th class=n>Fläche m²</th></tr>%s</table>' % rows)

    @staticmethod
    def _items(x: Dict[str, Any]) -> str:
        rows = "".join('<tr><td>%s</td><td>%s</td><td><code>%s</code></td><td class=n>%d</td><td class=n>%s</td>'
                       '<td class=n>%s</td><td class=n>%s</td></tr>' % (
                           KIND_NAMES.get(i["kind"], i["kind"]) + (" " + i["type"] if i["type"] else ""),
                           escape(i.get("name") or ""), escape(i["component"]), i["count"],
                           decimal(i["area"], 2) if i["area"] is not None else "",
                           money(i["unit_price"], "EUR"), money(i["price"], "EUR")) for i in x["items"])
        return ('<h3>Stückliste (Modell)</h3><table><tr><th>Art</th><th>Artikel</th><th>Bauteil</th><th class=n>Anzahl</th>'
                '<th class=n>Fläche m²</th><th class=n>EP netto</th><th class=n>GP netto</th></tr>%s'
                '<tr class="sum"><td>Summe</td><td></td><td></td><td></td><td></td><td></td><td class=n>%s</td></tr></table>'
                '<p class="note">Kupplungen = Plattenstöße je Feld, Übergänge = Vor- und Rücklauf je Feld; Rechnung mit '
                'Reserve (Kupplungen 11,6 gerade/90°, Übergänge 11,6/16 gerade/90°).</p>' % (rows, money(x["price"], "EUR")))

    @staticmethod
    def _layers(x: Dict[str, Any]) -> str:
        rows = "".join('<tr><td><code>%s</code></td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td><td>%s</td></tr>' % (
            escape(layer["material"]), decimal(layer["thickness"] * 1000, 0), decimal(layer["area"], 2),
            decimal(layer["volume"], 3), "Plattenebene" if layer["heated"] else "") for layer in x["layers"])
        return ('<h3>Schichten (Wand → Raum)</h3><table><tr><th>Material</th><th class=n>Dicke mm</th>'
                '<th class=n>Fläche m²</th><th class=n>Volumen m³</th><th></th></tr>%s</table>' % rows)
