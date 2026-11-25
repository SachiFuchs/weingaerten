"""Section `Elektrik` of the page /mengen: runs, penetrations, parts list with prices and cutting list."""
import logging
from typing import Any, Dict, List

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

escape = HtmlTools.escape
decimal = GermanFormat.decimal
KIND_NAMES = {"cable": "Kabel", "pipe": "Schutzrohr", "box": "Dose"}
PART_NAMES = {"bend": "Steckbogen", "sleeve": "Steckmuffe", "clamp": "Klemmschelle"}
EST = " (geschätzt)"


class ElectricalTables:
    """Renders the electrical block of the BOM."""

    @staticmethod
    def render(block: Dict[str, Any], totals: Dict[str, Any]) -> str:
        """Return the section `Elektrik`."""
        return ('<h2>Elektrik</h2><p>Schutzrohr %s m, Kabel %s m (inkl. Vorrat), Material ca. %s €. '
                'Version 1, Leitungsbahnen vorläufig; offene Enden im Keller (Anschluss Sicherungskasten später).</p>'
                '%s%s%s%s'
                % (decimal(totals.get("electrical_conduit_length", 0), 2),
                   decimal(totals.get("electrical_cable_length", 0), 2), decimal(totals.get("electrical_price", 0), 2),
                   ElectricalTables._runs(block["runs"]), ElectricalTables._penetrations(block["penetrations"]),
                   ElectricalTables._stock(block["stock"]), ElectricalTables._cuts(block["cuts"])))

    @staticmethod
    def _runs(runs: List[Dict[str, Any]]) -> str:
        rows = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td class=n>%s</td><td class=n>%s</td><td>%s</td></tr>' % (
            escape(r["name"] + (EST if r["estimated"] else "")), escape(r["label"]), escape(r["conduit"] or "–"),
            decimal(r["length"], 2), decimal(r["cable_length"], 2),
            escape("offen: " + (r["open_end"]["note"] or "") if r["open_end"] else "")) for r in runs)
        return ('<h3>Leitungen</h3><table><tr><th>Leitung</th><th>Kabel</th><th>Rohr</th><th class=n>Rohr m</th>'
                '<th class=n>Kabel m</th><th>Anfang</th></tr>%s<tr class="sum"><td>Summe</td><td></td><td></td>'
                '<td class=n>%s</td><td class=n>%s</td><td></td></tr></table>'
                % (rows, decimal(sum(r["length"] for r in runs), 2), decimal(sum(r["cable_length"] for r in runs), 2)))

    @staticmethod
    def _penetrations(through: List[Dict[str, Any]]) -> str:
        if not through:
            return ""
        rows = "".join('<tr><td>%s</td><td>%s</td><td class=n>%s</td></tr>' % (
            escape(p["element_name"]), escape(p["run_name"]), decimal(p["core_drill"] * 100, 0)) for p in through)
        return ('<h3>Durchführungen</h3><table><tr><th>Bauteil</th><th>Leitung</th><th class=n>Bohrung Ø cm</th></tr>'
                '%s</table>' % rows)

    @staticmethod
    def _stock(stock: List[Dict[str, Any]]) -> str:
        def amount(s: Dict[str, Any]) -> str:
            if s["kind"] == "cable":
                return decimal(s["length"], 2) + " m"
            if s["kind"] == "pipe":
                return "%d × %s m" % (s["count"], decimal(s["length"], 1))
            if s.get("packs") is not None:
                return "%d Stk = %d Pck à %d" % (s["count"], s["packs"], s["pack_size"])
            return "%d Stk" % s["count"]
        rows = "".join('<tr><td>%s</td><td>%s</td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>'
                       '<td>%s</td></tr>' % (
                           escape(s["name"] + (EST if s["estimated"] else "")),
                           KIND_NAMES.get(s["kind"]) or PART_NAMES.get(s.get("fitting_type"), "Zubehör"),
                           amount(s), "" if s["unit_price"] is None else decimal(s["unit_price"], 2),
                           "" if s["price"] is None else decimal(s["price"], 2), escape(s.get("note") or ""))
                       for s in stock)
        return ('<h3>Stückliste (aus vorhandenem Material)</h3><table><tr><th>Artikel</th><th>Art</th>'
                '<th class=n>Menge</th><th class=n>Preis €</th><th class=n>Summe €</th><th>Hinweis</th></tr>%s<tr class="sum">'
                '<td>Summe</td><td></td><td></td><td></td><td class=n>%s</td><td></td></tr></table>'
                % (rows, decimal(sum(s["price"] or 0 for s in stock), 2)))

    @staticmethod
    def _cuts(cuts: List[Dict[str, Any]]) -> str:
        rows = "".join('<tr><td>%s</td><td class=n>%d</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
            escape(c["run_name"]), c["segment"] + 1, decimal(c["net_length"], 3),
            " + ".join(decimal(p, 3) for p in c["pieces"])) for c in cuts)
        return ('<h3>Zuschnitt Schutzrohr je gerader Strecke</h3><table><tr><th>Leitung</th><th class=n>Strecke</th>'
                '<th class=n>Länge m</th><th class=n>Stücke m</th></tr>%s</table>' % rows)
