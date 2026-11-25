"""Section `Installation (Einzelteile)` of the page /mengen: parts per component, sticks, cables, slots, penetrations."""
import logging
from typing import Any, Dict, List

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

escape = HtmlTools.escape
decimal = GermanFormat.decimal
TRADE_NAMES = {"electrical": "Elektro", "waste_water": "Abwasser", "water_supply": "Zuwasser"}
DIRECTION_NAMES = {"vertical": "senkrecht", "horizontal": "waagerecht", "oblique": "schräg", "hole": "Loch"}
EST = " (geschätzt)"


class InstallationTables:
    """Renders the `installation` block of the BOM."""

    @staticmethod
    def render(block: Dict[str, Any], totals: Dict[str, Any]) -> str:
        """Return the section of the installed parts."""
        open_note = (' – <b style="color:#C62828">%d offene Anschlüsse</b>' % block["open_ports"]
                     if block["open_ports"] else "")
        return ('<h2>Installation (Einzelteile in den Wänden)</h2><p>%d Teile, Rohr %s m, Schlitze %s m³, '
                '%d Durchbrüche, Material ca. %s €%s. Eingebaut auf der Seite <a href="/waende">Wände</a>.</p>%s%s%s%s%s'
                % (totals.get("installation_part_count", 0), decimal(totals.get("installation_pipe_length", 0), 2),
                   decimal(totals.get("installation_slot_volume", 0), 4),
                   totals.get("installation_penetration_count", 0), decimal(totals.get("installation_price", 0), 2),
                   open_note, InstallationTables._components(block["components"]),
                   InstallationTables._stock(block["stock"]), InstallationTables._cables(block["cables"]),
                   InstallationTables._slots(block["slots"]), InstallationTables._penetrations(block["penetrations"])))

    @staticmethod
    def _components(rows: List[Dict[str, Any]]) -> str:
        body = "".join('<tr><td>%s</td><td>%s</td><td class=n>%d</td><td class=n>%s</td><td class=n>%s</td>'
                       '<td class=n>%s</td></tr>' % (
                           TRADE_NAMES.get(r["trade"], r["trade"] or ""), escape((r["name"] or r["component"])
                                                                                 + (EST if r["estimated"] else "")),
                           r["count"], "" if r["length"] is None else decimal(r["length"], 2),
                           "" if r["unit_price"] is None else decimal(r["unit_price"], 2),
                           "" if r["price"] is None else decimal(r["price"], 2)) for r in rows)
        return ('<h3>Teile</h3><table><tr><th>Gewerk</th><th>Komponente</th><th class=n>Stück</th>'
                '<th class=n>Länge m</th><th class=n>Preis €</th><th class=n>Summe €</th></tr>%s</table>' % body)

    @staticmethod
    def _stock(stock: List[Dict[str, Any]]) -> str:
        if not stock:
            return ""
        body = "".join('<tr><td>%s</td><td class=n>%d × %s m</td><td>%s</td></tr>' % (
            escape(s["name"] + (EST if s["estimated"] else "")), s["count"], decimal(s["length"], 2),
            escape(s.get("note") or "")) for s in stock)
        return ('<h3>Stangen (Zuschnitt der geraden Rohre)</h3><table><tr><th>Rohr</th><th class=n>Stangen</th>'
                '<th>Hinweis</th></tr>%s</table>' % body)

    @staticmethod
    def _cables(cables: List[Dict[str, Any]]) -> str:
        if not cables:
            return ""
        body = "".join('<tr><td>%s</td><td class=n>%d</td><td class=n>%s</td></tr>' % (
            escape(c["name"] or c["cable"]), c["parts"], decimal(c["length"], 2)) for c in cables)
        return ('<h3>Kabel in Leerrohren</h3><table><tr><th>Kabel</th><th class=n>Rohrstücke</th>'
                '<th class=n>Länge m</th></tr>%s</table>' % body)

    @staticmethod
    def _slots(slots: List[Dict[str, Any]]) -> str:
        if not slots:
            return ""
        body = "".join('<tr%s><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class=n>%s</td><td class=n>%s</td>'
                       '<td class=n>%s</td><td class=n>%s</td><td>%s</td></tr>' % (
                           ' style="color:#C62828"' if s["over_limit"] else "", escape(s["wall_name"] or s["wall"]),
                           escape(s["part"]), "Aussparung" if s["kind"] == "cutout" else "Schlitz",
                           DIRECTION_NAMES.get(s["direction"], s["direction"]), decimal(s["length"] * 100, 1),
                           decimal(s["width"] * 100, 1), decimal(s["depth"] * 100, 1), decimal(s["volume"] * 1000, 2),
                           "Richtwert %s cm überschritten" % decimal(s["limit"] * 100, 1) if s["over_limit"] else "")
                       for s in slots)
        return ('<h3>Schlitze und Aussparungen (geschätzt)</h3><table><tr><th>Wand</th><th>Teil</th><th>Art</th>'
                '<th>Richtung</th><th class=n>Länge cm</th><th class=n>Breite cm</th><th class=n>Tiefe cm</th>'
                '<th class=n>Volumen l</th><th>Hinweis</th></tr>%s</table>' % body)

    @staticmethod
    def _penetrations(items: List[Dict[str, Any]]) -> str:
        if not items:
            return ""
        body = "".join('<tr><td>%s</td><td>%s</td><td class=n>%s</td></tr>' % (
            escape(p["element_name"]), escape(p["run_name"]), decimal(p["core_drill"] * 100, 0)) for p in items)
        return ('<h3>Durchbrüche</h3><table><tr><th>Bauteil</th><th>Teil</th><th class=n>Bohrung Ø cm</th></tr>'
                '%s</table>' % body)
