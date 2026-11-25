"""Section `Zuwasser` of the page /mengen: runs, crossing loops, penetrations, parts list and cutting list."""
import logging
from typing import Any, Dict, List

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

escape = HtmlTools.escape
decimal = GermanFormat.decimal
PART_NAMES = {"bend": "Bogen", "plug": "Endkappe", "branch": "T-Stück", "adapter": "Übergang", "wall_plate": "Wandscheibe"}
EST = " (geschätzt)"


class WaterSupplyTables:
    """Renders the drinking water block of the BOM."""

    @staticmethod
    def render(block: Dict[str, Any], totals: Dict[str, Any]) -> str:
        """Return the section `Zuwasser`."""
        return ('<h2>Zuwasser</h2><p>Leitungen %s m, %d Formteile und Wandscheiben, %d Kreuzungsschleifen. '
                'Version 1, Leitungsbahnen vorläufig.</p>%s%s%s%s%s'
                % (decimal(totals.get("water_supply_length", 0), 2), totals.get("water_fitting_count", 0),
                   len(block["loops"]), WaterSupplyTables._runs(block["runs"]), WaterSupplyTables._loops(block["loops"]),
                   WaterSupplyTables._penetrations(block["penetrations"]), WaterSupplyTables._stock(block["stock"]),
                   WaterSupplyTables._cuts(block["cuts"])))

    @staticmethod
    def _runs(runs: List[Dict[str, Any]]) -> str:
        rows = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td class=n>%s</td></tr>' % (
            escape(r["name"] + (EST if r["estimated"] else "")), escape(r["medium_name"]),
            escape(r["component_name"] or r["component"]), decimal(r["length"], 2)) for r in runs)
        return ('<h3>Leitungen</h3><table><tr><th>Leitung</th><th>Medium</th><th>Rohr</th><th class=n>Länge m</th></tr>'
                '%s<tr class="sum"><td>Summe</td><td></td><td></td><td class=n>%s</td></tr></table>'
                % (rows, decimal(sum(r["length"] for r in runs), 2)))

    @staticmethod
    def _loops(loops: List[Dict[str, Any]]) -> str:
        if not loops:
            return ""
        rows = "".join('<tr><td>%s</td><td>%s</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
            escape(l["run_name"]), escape(l["other_name"]), " / ".join(decimal(v, 2) for v in l["position"]),
            decimal(l["offset"] * 100, 1)) for l in loops)
        return ('<h3>Kreuzungsschleifen (4 × 45°)</h3><table><tr><th>Leitung mit Schleife</th><th>kreuzt</th>'
                '<th class=n>x / y / z m</th><th class=n>Versatz cm</th></tr>%s</table>' % rows)

    @staticmethod
    def _penetrations(through: List[Dict[str, Any]]) -> str:
        if not through:
            return ""
        rows = "".join('<tr><td>%s</td><td>%s</td><td class=n>%s</td></tr>' % (
            escape(p["element_name"]), escape(p["run_name"]), decimal(p["core_drill"] * 100, 0)) for p in through)
        return ('<h3>Durchbrüche</h3><table><tr><th>Bauteil</th><th>Leitung</th><th class=n>Bohrung Ø cm</th></tr>'
                '%s</table>' % rows)

    @staticmethod
    def _stock(stock: List[Dict[str, Any]]) -> str:
        rows = "".join('<tr><td>%s</td><td>%s</td><td class=n>%s</td><td class=n>%d</td><td>%s</td></tr>' % (
            escape(s["name"] + (EST if s["estimated"] else "")),
            "Rohr" if s["kind"] == "pipe" else PART_NAMES.get(s.get("fitting_type"), "Formteil"),
            decimal(s["length"], 2) if s.get("length") else "", s["count"], escape(s.get("note") or "")) for s in stock)
        return ('<h3>Stückliste</h3><table><tr><th>Artikel</th><th>Art</th><th class=n>Stange m</th>'
                '<th class=n>Anzahl</th><th>Hinweis</th></tr>%s</table>' % rows)

    @staticmethod
    def _cuts(cuts: List[Dict[str, Any]]) -> str:
        rows = "".join('<tr><td>%s</td><td class=n>%d</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
            escape(c["run_name"]), c["segment"] + 1, decimal(c["net_length"], 3),
            " + ".join(decimal(p, 3) for p in c["pieces"])) for c in cuts)
        return ('<h3>Zuschnitt je Abschnitt</h3><table><tr><th>Leitung</th><th class=n>Abschnitt</th>'
                '<th class=n>Rohrlänge m</th><th class=n>Stücke m</th></tr>%s</table>' % rows)
