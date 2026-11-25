"""Section `Abwasser` of the page /mengen: runs, penetrations, fittings and stock pipes with cutting list."""
import logging
from typing import Any, Dict, List

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

escape = HtmlTools.escape
decimal = GermanFormat.decimal
LINE_NAMES = {"ht": "HT", "kg": "KG"}
DIRECTION_NAMES = {"vertical": "senkrecht", "horizontal": "waagerecht", "oblique": "schräg"}
FITTING_NAMES = {"bend": "Bogen", "branch": "Abzweig", "adapter": "Übergang", "plug": "Stopfen"}
EST = " (geschätzt)"


class WasteWaterTables:
    """Renders the waste water block of the BOM."""

    @staticmethod
    def render(block: Dict[str, Any], totals: Dict[str, Any]) -> str:
        """Return the section `Abwasser`."""
        return ('<h2>Abwasser</h2><p>Leitungen %s m, %d Durchbrüche, %d Formteile. Lage und Höhen geschätzt.</p>%s%s%s%s'
                % (decimal(totals.get("waste_water_length", 0), 2), totals.get("penetration_count", 0),
                   totals.get("fitting_count", 0), WasteWaterTables._runs(block["runs"]),
                   WasteWaterTables._penetrations(block["penetrations"], block["embedded"]),
                   WasteWaterTables._stock(block["stock"]), WasteWaterTables._cuts(block["cuts"])))

    @staticmethod
    def _runs(runs: List[Dict[str, Any]]) -> str:
        rows = "".join('<tr><td>%s</td><td>%s</td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
            escape(r["name"] + (EST if r["estimated"] else "")), escape(r["component_name"] or r["component"]),
            "%s DN %s" % (LINE_NAMES.get(r["line"], r["line"]), r["dn"]), decimal(r["length"], 2),
            decimal(r["min_slope"] * 100, 1),
            decimal(min(r["slopes"]) * 100, 1) if r["slopes"] else "–") for r in runs)
        return ('<h3>Leitungen</h3><table><tr><th>Leitung</th><th>Rohr</th><th class=n>System</th><th class=n>Länge m</th>'
                '<th class=n>Mindestgefälle %%</th><th class=n>kleinstes Gefälle %%</th></tr>%s<tr class="sum"><td>Summe</td>'
                '<td></td><td></td><td class=n>%s</td><td></td><td></td></tr></table>'
                % (rows, decimal(sum(r["length"] for r in runs), 2)))

    @staticmethod
    def _penetrations(through: List[Dict[str, Any]], embedded: List[Dict[str, Any]]) -> str:
        rows = "".join('<tr><td>%s</td><td>%s</td><td class=n>%s</td><td class=n>%s</td><td>%s</td>'
                       '<td class=n>%s</td><td>%s</td></tr>' % (
                           escape(p["element_name"]), escape(p["run_name"]),
                           "%s DN %s" % (LINE_NAMES.get(p["line"], p["line"]), p["dn"]),
                           decimal(p["core_drill"] * 100, 0), DIRECTION_NAMES.get(p["direction"], p["direction"]),
                           " / ".join(decimal(v, 2) for v in p["position"]),
                           escape(", ".join(x for x in ("abdichten" if p["airtight"] else "", p.get("sealing") or "",
                                                       p.get("fire_stop_type") or "", "erledigt" if p.get("done") else "",
                                                       p.get("note") or "") if x))) for p in through)
        notes = "".join("<li>%s in %s, %s m</li>" % (escape(p["run_name"]), escape(p["element_name"]),
                                                    decimal(p["length"], 2)) for p in embedded)
        return ('<h3>Durchbrüche (Kernbohrung = Außendurchmesser + 2 cm)</h3><table><tr><th>Bauteil</th><th>Leitung</th>'
                '<th class=n>Rohr</th><th class=n>Bohrung Ø cm</th><th>Richtung</th><th class=n>x / y / z m</th>'
                '<th>Hinweis</th></tr>%s</table>%s'
                % (rows, "<p>Im Bauteil verlegt (kein Durchbruch):</p><ul>%s</ul>" % notes if notes else ""))

    @staticmethod
    def _stock(stock: List[Dict[str, Any]]) -> str:
        if not stock:
            return ""
        rows = "".join('<tr><td>%s</td><td>%s</td><td class=n>%s</td><td class=n>%d</td><td>%s</td></tr>' % (
            escape(s["name"] + (EST if s["estimated"] else "")),
            "Rohr" if s["kind"] == "pipe" else FITTING_NAMES.get(s.get("fitting_type"), "Formteil"),
            decimal(s["length"], 2) if s.get("length") else "", s["count"],
            escape(s.get("note") or "")) for s in stock)
        return ('<h3>Stückliste (Formteile und Stangen)</h3><table><tr><th>Artikel</th><th>Art</th>'
                '<th class=n>Stange m</th><th class=n>Anzahl</th><th>Hinweis</th></tr>%s</table>' % rows)

    @staticmethod
    def _cuts(cuts: List[Dict[str, Any]]) -> str:
        if not cuts:
            return ""
        rows = "".join('<tr><td>%s</td><td>%s</td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
            escape(c["run_name"]), escape(c["name"]), decimal(c["net_length"], 3),
            " + ".join(decimal(p, 3) for p in c["pieces"]), decimal(c["deduction"], 3)) for c in cuts)
        return ('<h3>Zuschnitt je Abschnitt</h3><table><tr><th>Leitung</th><th>Rohr</th><th class=n>Rohrlänge m</th>'
                '<th class=n>Stücke m</th><th class=n>Abzug Formteile m</th></tr>%s</table>' % rows)
