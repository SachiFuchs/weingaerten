"""Tables of /mengen for rooms (DIN 277), coverings (Beläge) and shafts (Schächte)."""
import logging
from typing import Any, Dict, List

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

escape = HtmlTools.escape
decimal = GermanFormat.decimal
SURFACE_DE = {"floor": "Boden", "wall": "Wand"}
SCOPE_DE = {"room": "ganzer Raum", "zone": "Teilfläche", "wall": "Wandfläche"}
KIND_DE = {"floor": "Boden", "ceiling": "Decke"}


class RoomTables:
    """Renders the room, covering and shaft tables of the BOM."""

    @staticmethod
    def rooms(rows_in: List[Dict[str, Any]]) -> str:
        """Rooms with number, usage, area, height and volume, then the areas summed per DIN 277 usage."""
        rows = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class=n>%s</td><td class=n>%s</td>'
                       '<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
                           escape(r["storey"]), escape(r.get("number") or ""), escape(r.get("name") or r["room"]),
                           escape(r.get("usage") or ""), decimal(r["floor_area"]), decimal(r["perimeter"]),
                           decimal(r["height"]), decimal(r["volume"]), decimal(r["wall_area"])) for r in rows_in)
        usages: Dict[str, List[float]] = {}
        for r in rows_in:
            entry = usages.setdefault(r.get("usage") or "", [0.0, 0.0, r.get("usage_name") or "ohne Nutzung"])
            entry[0] += r["floor_area"]
            entry[1] += r["volume"]
        din = "".join('<tr><td>%s</td><td>%s</td><td class=n>%s</td><td class=n>%s</td></tr>'
                      % (escape(key), escape(name), decimal(area), decimal(volume))
                      for key, (area, volume, name) in sorted(usages.items()))
        total_area, total_volume = sum(r["floor_area"] for r in rows_in), sum(r["volume"] for r in rows_in)
        return ('<h2>Räume</h2><table><tr><th>Geschoss</th><th>Nr.</th><th>Raum</th><th>Nutzung</th>'
                '<th class=n>Fläche m²</th><th class=n>Umfang m</th><th class=n>Höhe m</th><th class=n>Volumen m³</th>'
                '<th class=n>Wandfläche m²</th></tr>%s<tr class="sum"><td>Summe</td><td></td><td></td><td></td>'
                '<td class=n>%s</td><td></td><td></td><td class=n>%s</td><td></td></tr></table>'
                '<h3>Flächen nach DIN 277</h3><table><tr><th>Gruppe</th><th>Nutzung</th><th class=n>Fläche m²</th>'
                '<th class=n>Volumen m³</th></tr>%s</table>'
                % (rows, decimal(total_area), decimal(total_volume), din))

    @staticmethod
    def coverings(rows_in: List[Dict[str, Any]]) -> str:
        """Coverings per room with area (and length for wall coverings)."""
        rows = "".join('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class=n>%s</td>'
                       '<td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
                           escape(("%s %s" % (r.get("room_number") or "", r.get("room_name") or r["room"])).strip()),
                           escape(r["covering"] + (" (geschätzt)" if r["estimated"] else "")),
                           SURFACE_DE.get(r["surface"], r["surface"]), SCOPE_DE.get(r["scope"], r["scope"]),
                           escape(r.get("assembly_name") or r["assembly"]), decimal(r["thickness"] * 100, 1),
                           decimal(r["area"]), decimal(r["length"]) if r["length"] is not None else "",
                           decimal(r["volume"], 4)) for r in rows_in)
        return ('<h2>Beläge</h2><table><tr><th>Raum</th><th>Belag</th><th>Fläche</th><th>Bereich</th><th>Aufbau</th>'
                '<th class=n>Dicke cm</th><th class=n>Fläche m²</th><th class=n>Länge m</th><th class=n>Volumen m³</th>'
                '</tr>%s</table>' % rows)

    @staticmethod
    def shafts(rows_in: List[Dict[str, Any]]) -> str:
        """Shafts with the cut floor and ceiling areas."""
        rows = "".join('<tr><td>%s</td><td>%s – %s</td><td class=n>%s</td><td>%s</td><td class=n>%s</td><td>%s</td></tr>' % (
            escape((s.get("name") or s["shaft"]) + (" (geschätzt)" if s["estimated"] else "")),
            escape(s["from_storey"].replace("storey:", "")), escape(s["to_storey"].replace("storey:", "")),
            decimal(s["area"]), escape(", ".join("%s %s %s m²" % (c["storey"], KIND_DE.get(c["kind"], c["kind"]),
                                                                     decimal(c["area"])) for c in s["cuts"])),
            decimal(s["cut_area"]), escape(", ".join(p.replace("tga-run:", "") for p in s["penetrations"])))
            for s in rows_in)
        return ('<h2>Schächte</h2><table><tr><th>Schacht</th><th>von – bis</th><th class=n>Querschnitt m²</th>'
                '<th>geöffnet</th><th class=n>Summe m²</th><th>Leitungen</th></tr>%s</table>' % rows)
