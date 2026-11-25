"""Table "Fassade" of the page /mengen: board facade per wall, stock boards and paint."""
import logging
from typing import Any, Dict

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

escape = HtmlTools.escape
decimal = GermanFormat.decimal


class FacadeTable:
    """Renders one facade row of the BOM."""

    @staticmethod
    def render(f: Dict[str, Any]) -> str:
        """Return the HTML of the facade section of one storey."""
        board = f["board"]
        rows = "".join('<tr><td>%s</td><td class=n>%d</td><td class=n>%d</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
            escape(w.get("name") or w["wall"]), w["rows"], w["pieces"], decimal(w["length"]), decimal(w["area"]))
            for w in f["walls"])
        paint = ('<tr><td>Anstrich <code>%s</code> (Brettfläche Sichtseite)</td><td class=n>%s m²</td></tr>'
                 % (escape(f["paint"]), decimal(f["paint_area"]))) if f["paint"] else ""
        return ('<h2>Fassade</h2><p>Stülpschalung <code>%s</code>, Brett %s × %s × %s cm, Überlappung %s cm, '
                'Deckbreite %s cm%s; Geschoss %s.</p>'
                '<table><tr><th>Wand</th><th class=n>Reihen</th><th class=n>Stücke</th><th class=n>Länge m</th>'
                '<th class=n>Ansichtsfläche m²</th></tr>%s<tr class="sum"><td>Summe</td><td></td><td class=n>%d</td>'
                '<td class=n>%s</td><td class=n>%s</td></tr></table>'
                '<table><tr><td>Bretter à %s m (Zuschnitt mit Restverwertung)</td><td class=n>%d Stück</td></tr>'
                '<tr><td>Einkaufslänge / Verschnitt</td><td class=n>%s m / %s m (%s %%)</td></tr>'
                '<tr><td>Brettfläche inkl. Überlappung</td><td class=n>%s m²</td></tr>'
                '<tr><td>Holzvolumen</td><td class=n>%s m³</td></tr>%s</table>' % (
                    escape(f["material"]), decimal(board["length"] * 100, 0), decimal(board["width"] * 100, 0),
                    decimal(board["thickness"] * 100, 1), decimal(f["overlap"] * 100, 1), decimal(f["cover"] * 100, 1),
                    " (geschätzt)" if f["estimated"] else "", escape(f["storey"]), rows, f["pieces"],
                    decimal(f["length"]), decimal(f["area"]), decimal(board["length"], 1), f["boards"],
                    decimal(f["stock_length"]), decimal(f["waste_length"]), decimal(f["waste_share"] * 100, 0),
                    decimal(f["board_area"]), decimal(f["volume"]), paint))
