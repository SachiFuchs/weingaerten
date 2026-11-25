"""The layer list below the /grundriss plan ("Schichtaufbau" of the first wall)."""
import logging
from typing import Any, Dict

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

escape = HtmlTools.escape


class CornerDetail:
    """Renders the layer table of the first wall (the enlarged corner drawing was removed)."""

    def __init__(self, house: Dict[str, Any], storey: Dict[str, Any]) -> None:
        """Args:
            house: the HOUSE answer.
            storey: its first storey.
        """
        self._house = house
        self._storey = storey

    def render(self) -> str:
        """Return the heading and the layer table of the first wall (empty without walls)."""
        table = self._layer_table()
        return '<h2>Schichtaufbau</h2>' + table if table else ""

    def _layer_table(self) -> str:
        walls = self._storey["walls"]
        if not walls:
            return ""
        materials = self._house.get("materials", {})
        rows = "".join('<tr><td>%d</td><td><span class="sw" style="background:%s"></span> %s</td><td class=n>%s</td></tr>' % (
            i + 1, escape((materials.get(layer["material"], {}).get("appearance") or {}).get("color", "#ccc")),
            escape(materials.get(layer["material"], {}).get("name", layer["material"])),
            escape(GermanFormat.centimetres(layer["thickness"]))) for i, layer in enumerate(walls[0]["layers"]))
        return "<table><tr><th>Nr</th><th>Material (außen → innen)</th><th class=n>Dicke</th></tr>" + rows + "</table>"
