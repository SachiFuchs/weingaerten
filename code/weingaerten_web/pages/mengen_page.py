"""Page /mengen: validation result and the bill of materials."""
import logging
from typing import Any, Dict, List

from ..rendering.german_format import GermanFormat
from ..rendering.html_tools import HtmlTools
from ..rendering.page_context import PageContext
from .facade_table import FacadeTable
from .floor_heating_tables import FloorHeatingTables
from .wall_heating_tables import WallHeatingTables
from .lining_table import LiningTable
from .room_tables import RoomTables
from .waste_water_tables import WasteWaterTables
from .water_supply_tables import WaterSupplyTables
from .electrical_tables import ElectricalTables
from .installation_tables import InstallationTables

logger = logging.getLogger(__name__)

TITLE, URL = "Mengen", "/mengen"
COUNT_LABELS = [("Materialien", "materials"), ("Aufbauten", "assemblies"), ("Klassen", "classes"),
                ("Bauteile", "components"), ("Firmen", "companies"), ("Geschosse", "storeys"), ("Wände", "walls"),
                ("Öffnungen", "openings"), ("Räume", "rooms"), ("Beläge", "coverings"), ("Schächte", "shafts"),
                ("Einbauteile", "parts")]
STRUCTURE_KINDS = {"beam": "Unterzug", "post": "Stütze"}
NUMBER = "<td class=n>%s</td>"

escape = HtmlTools.escape
decimal = GermanFormat.decimal
money = GermanFormat.money


class MengenPage:
    """Renders the quantities page from VALIDATE and BOM."""

    def __init__(self, context: PageContext) -> None:
        """Args:
            context: shared page services.
        """
        self._context = context

    def render(self) -> str:
        """Return the page HTML."""
        context = self._context
        if not context.core.available:
            return context.core_missing_page(TITLE, URL, TITLE)
        validation = context.core.ask("VALIDATE")
        bom = context.core.ask("BOM")
        body = ["<h1>Mengen</h1>"] + self._validation(validation)
        valid, error_count = validation.get("ok", True), len(validation.get("errors", []))
        if "error" in bom:
            body.append("<p>%s</p>" % escape(bom["error"]))
            return context.layout.render(TITLE, URL, "".join(body), valid, error_count)
        body += [self._materials(bom), self._walls(bom), self._components(bom), RoomTables.rooms(bom["rooms"])]
        if bom.get("coverings"):
            body.append(RoomTables.coverings(bom["coverings"]))
        if bom.get("shafts"):
            body.append(RoomTables.shafts(bom["shafts"]))
        if bom.get("ceilings", []):
            body.append(self._ceilings(bom["ceilings"]))
        if bom.get("structure", []):
            body.append(self._structure(bom["structure"]))
        if bom.get("outdoor_areas", []):
            body.append(self._outdoor_areas(bom["outdoor_areas"]))
        if bom.get("roof_structure", []):
            body.append(self._roof_structure(bom["roof_structure"]))
        for covering in bom.get("roof_covering", []):
            body.append(self._roof_covering(covering))
        for facade in bom.get("facade", []):
            body.append(FacadeTable.render(facade))
        if bom.get("linings", []):
            body.append(LiningTable.render(bom["linings"]))
        if bom.get("stairs", []):
            body.append(self._stairs(bom["stairs"]))
        if bom.get("light_wells", []):
            body.append(self._light_wells(bom["light_wells"]))
        if bom.get("floors", []):
            body.append(FloorHeatingTables.floors(bom["floors"]))
        if bom.get("heating", []):
            body.append(FloorHeatingTables.heating(bom["heating"]))
        if bom.get("wall_heating", []):
            body.append(WallHeatingTables.render(bom["wall_heating"]))
        if bom.get("waste_water"):
            body.append(WasteWaterTables.render(bom["waste_water"], bom["totals"]))
        if bom.get("water_supply"):
            body.append(WaterSupplyTables.render(bom["water_supply"], bom["totals"]))
        if bom.get("electrical"):
            body.append(ElectricalTables.render(bom["electrical"], bom["totals"]))
        if bom.get("installation"):
            body.append(InstallationTables.render(bom["installation"], bom["totals"]))
        body.append(self._totals(bom["totals"]))
        return context.layout.render(TITLE, URL, "".join(body), valid, error_count)

    @staticmethod
    def _issue_rows(issues: List[Dict[str, Any]]) -> str:
        return "".join("<tr><td><code>%s</code></td><td>%s</td></tr>" % (escape(x["where"]), escape(x["message"]))
                       for x in issues)

    def _validation(self, validation: Dict[str, Any]) -> List[str]:
        counts = validation.get("counts", {})
        summary = ", ".join("%s %d" % (label, counts.get(key, 0)) for label, key in COUNT_LABELS)
        if validation.get("ok"):
            parts = ['<p class="ok"><b>Modell gültig</b> – %s</p>' % escape(summary)]
        else:
            parts = ['<div class="bad"><b>Modell ungültig</b> – %s<table><tr><th>Ort</th><th>Meldung</th></tr>%s</table></div>'
                     % (escape(summary), self._issue_rows(validation.get("errors", [])))]
        if validation.get("warnings"):
            parts.append('<h3>Warnungen</h3><table class="warn"><tr><th>Ort</th><th>Meldung</th></tr>%s</table>'
                         % self._issue_rows(validation["warnings"]))
        return parts

    @staticmethod
    def _materials(bom: Dict[str, Any]) -> str:
        rows = "".join('<tr><td>%s</td><td>%s</td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
            escape(m.get("name") or m["material"]), escape(m.get("category") or ""), decimal(m["volume"]),
            decimal(m["area_outside"]), decimal(m["area_inside"]), decimal(m["area_reveal"])) for m in bom["materials"])
        sums = [sum(m[k] for m in bom["materials"]) for k in ("volume", "area_outside", "area_inside", "area_reveal")]
        return ('<h2>Materialien</h2><table><tr><th>Material</th><th>Kategorie</th><th class=n>Volumen m³</th><th class=n>Fläche außen m²</th>'
                '<th class=n>Fläche innen m²</th><th class=n>Laibung m²</th></tr>%s<tr class="sum"><td>Summe</td><td></td>%s</tr></table>'
                % (rows, "".join(NUMBER % decimal(x) for x in sums)))

    @staticmethod
    def _walls(bom: Dict[str, Any]) -> str:
        rows = "".join('<tr><td>%s</td><td><code>%s</code></td><td class=n>%s</td><td class=n>%s</td><td class=n>%d</td><td class=n>%s</td></tr>' % (
            escape(w["wall"]), escape(w["assembly"]), decimal(w["length_outside"]), decimal(w["length_inside"]),
            w.get("openings", 0), decimal(w["volume"])) for w in bom["walls"])
        return ('<h2>Wände</h2><table><tr><th>Wand</th><th>Aufbau</th><th class=n>Länge außen m</th><th class=n>Länge innen m</th>'
                '<th class=n>Öffnungen</th><th class=n>Volumen m³</th></tr>%s</table>' % rows)

    @staticmethod
    def _components(bom: Dict[str, Any]) -> str:
        rows = "".join('<tr><td>%s</td><td><code>%s</code></td><td>%s</td><td class=n>%d</td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
            escape(x.get("name") or x["component"]), escape(x.get("class") or ""), escape(x.get("manufacturer") or ""),
            x["count"], decimal(x["glass_area"]), money(x.get("unit_price"), x.get("currency")),
            money(x.get("total_price"), x.get("currency"))) for x in bom.get("components", []))
        return ('<h2>Bauteile</h2><table><tr><th>Bauteil</th><th>Klasse</th><th>Hersteller</th><th class=n>Anzahl</th><th class=n>Glasfläche m²</th>'
                '<th class=n>Stückpreis</th><th class=n>Summe</th></tr>%s<tr class="sum"><td>Summe</td><td></td><td></td><td></td><td></td><td></td>'
                '<td class=n>%s</td></tr></table>' % (rows, money(bom["totals"].get("component_price", 0), "EUR")))

    @staticmethod
    def _ceilings(ceilings: List[Dict[str, Any]]) -> str:
        rows = []
        for c in ceilings:
            joists = c["joists"]
            count = ("%d%s" % (joists["count"], " (geschätzt)" if joists["estimated"] else "")) if joists else ""
            rows.append('<tr><td>%s</td><td><code>%s</code></td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
                escape(c.get("name") or c["ceiling"]), escape(c["assembly"]), decimal(c["area"]), decimal(c["volume"]),
                count, decimal(joists["length"]) if joists else "", decimal(joists["volume"]) if joists else ""))
        return ('<h2>Decken</h2><table><tr><th>Decke</th><th>Aufbau</th><th class=n>Fläche m²</th><th class=n>Volumen m³</th>'
                '<th class=n>Balken</th><th class=n>Balkenlänge m</th><th class=n>Balkenvolumen m³</th></tr>%s</table>' % "".join(rows))

    @staticmethod
    def _structure(structure: List[Dict[str, Any]]) -> str:
        rows = "".join('<tr><td>%s</td><td>%s</td><td><code>%s</code></td><td class=n>%s</td><td class=n>%s</td></tr>' % (
            escape(s.get("name") or s["structure"]), escape(STRUCTURE_KINDS.get(s["kind"], s["kind"])), escape(s["material"]),
            decimal(s["length"]), decimal(s["volume"])) for s in structure)
        return ('<h2>Tragwerk</h2><table><tr><th>Element</th><th>Art</th><th>Material</th><th class=n>Länge m</th>'
                '<th class=n>Volumen m³</th></tr>%s</table>' % rows)

    @staticmethod
    def _roof_structure(rows_in: List[Dict[str, Any]]) -> str:
        rows = "".join('<tr><td>%s</td><td><code>%s</code></td><td class=n>%s × %s</td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
            escape(r["name"]), escape(r["material"]), decimal(r["width"] * 100, 0), decimal(r["height"] * 100, 0),
            "%d%s" % (r["count"], " (geschätzt)" if r["estimated"] else ""), decimal(r["length"]), decimal(r["volume"]))
            for r in rows_in)
        total = sum(r["volume"] for r in rows_in)
        return ('<h2>Dachstuhl</h2><table><tr><th>Bauteil</th><th>Material</th><th class=n>b × h cm</th><th class=n>Anzahl</th>'
                '<th class=n>Länge m</th><th class=n>Volumen m³</th></tr>%s<tr class="sum"><td>Summe</td><td></td><td></td><td></td>'
                '<td></td><td class=n>%s</td></tr></table>' % (rows, decimal(total)))

    @staticmethod
    def _roof_covering(c: Dict[str, Any]) -> str:
        # layers, then every quantity next to the invoice value (difference = model - invoice)
        layers = "".join('<tr><td>%d</td><td><code>%s</code></td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
            layer["index"] + 1, escape(layer["material"]), decimal(layer["thickness"] * 100, 2), decimal(layer["area"]),
            decimal(layer["volume"])) for layer in c["layers"])
        compare = [("Dachfläche brutto", "area", c["area"], "m²", (c.get("invoice") or {}).get("area"))]
        compare += [(i["name"] or i["component"], i["measure"], i["quantity"], i["unit"] or "", i["invoice_quantity"])
                    for i in c["items"]]
        measure_de = {"area": "Fläche", "ridge": "First", "verge": "Ortgang", "eaves": "Traufe", "invoice": "lt. Rechnung"}
        rows = "".join('<tr><td>%s</td><td>%s</td><td class=n>%s %s</td><td class=n>%s</td><td class=n>%s</td></tr>' % (
            escape(name), measure_de.get(measure, measure), decimal(value), escape(unit),
            decimal(invoice) if invoice is not None else "",
            decimal(value - invoice) if invoice is not None and value is not None else "")
            for name, measure, value, unit, invoice in compare)
        openings = ", ".join("%s (%s m²)" % (escape(o["name"] or o["id"]), decimal(o["area"])) for o in c["openings"])
        return ('<h2>Dach</h2><p>Aufbau <code>%s</code>, Dicke %s cm, Überstand Traufe %s m / Ortgang %s m%s; '
                'Fläche netto %s m², Volumen %s m³. Öffnungen: %s</p>'
                '<table><tr><th>Schicht</th><th>Material</th><th class=n>Dicke cm</th><th class=n>Fläche m²</th>'
                '<th class=n>Volumen m³</th></tr>%s</table>'
                '<h3>Dachmengen und Rechnung</h3><table><tr><th>Position</th><th>Messung</th><th class=n>Modell</th>'
                '<th class=n>Rechnung</th><th class=n>Differenz</th></tr>%s</table>' % (
                    escape(c["assembly"]), decimal(c["thickness"] * 100, 2), decimal(c["eaves_overhang"]),
                    decimal(c["verge_overhang"]), " (geschätzt)" if c["estimated"] else "", decimal(c["area_net"]),
                    decimal(c["volume"]), openings or "keine", layers, rows))

    @staticmethod
    def _stair_parts(counts: Dict[str, int]) -> str:
        # solid stairs only have block steps (Blockstufen)
        if "step" in counts:
            return "%d Blockstufen" % counts["step"]
        return "%d / %d / %d" % (counts["tread"], counts["riser"], counts["stringer"])

    @classmethod
    def _stairs(cls, stairs: List[Dict[str, Any]]) -> str:
        rows = "".join('<tr><td>%s</td><td><code>%s</code></td><td class=n>%s</td><td class=n>%s</td><td class=n>%s</td>'
                       '<td class=n>%s</td><td class=n>%s</td></tr>' % (
                           escape(s.get("name") or s["stair"]), escape(s["material"]),
                           "%d%s" % (s["risers"], " (geschätzt)" if s["estimated"] else ""),
                           decimal(s["rise"] * 100, 1), decimal(s["going"] * 100, 1), cls._stair_parts(s["counts"]),
                           decimal(s["volume"])) for s in stairs)
        return ('<h2>Treppe</h2><table><tr><th>Treppe</th><th>Material</th><th class=n>Steigungen</th>'
                '<th class=n>Steigung cm</th><th class=n>Auftritt cm</th><th class=n>Tritt- / Setzstufen / Wangen</th>'
                '<th class=n>Volumen m³</th></tr>%s</table>' % rows)

    @staticmethod
    def _light_wells(wells: List[Dict[str, Any]]) -> str:
        rows = "".join('<tr><td>%s</td><td><code>%s</code></td><td class=n>%s × %s × %s</td><td class=n>%s</td>'
                       '<td><code>%s</code></td><td class=n>%s</td></tr>' % (
                           escape((w.get("name") or w["light_well"]) + (" (geschätzt)" if w["estimated"] else "")),
                           escape(w["opening"]), decimal(w["width"] * 100, 0), decimal(w["projection"] * 100, 0),
                           decimal(w["depth"] * 100, 0), decimal(w["volume"]), escape(w["grating_material"]),
                           decimal(w["grating_area"])) for w in wells)
        return ('<h2>Lichtschächte</h2><table><tr><th>Lichtschacht</th><th>Fenster</th><th class=n>B × A × T cm</th>'
                '<th class=n>Beton m³</th><th>Gitterrost</th><th class=n>Gitter m²</th></tr>%s</table>' % rows)

    @staticmethod
    def _outdoor_areas(areas: List[Dict[str, Any]]) -> str:
        rows = "".join('<tr><td>%s</td><td class=n>%s</td></tr>' % (escape(a.get("name") or a["outdoor_area"]),
                                                                   decimal(a["area"])) for a in areas)
        return '<h2>Außenflächen</h2><table><tr><th>Fläche</th><th class=n>m²</th></tr>%s</table>' % rows

    @staticmethod
    def _totals(totals: Dict[str, Any]) -> str:
        return ('<h2>Summen</h2><table><tr><td>Wandvolumen</td><td class=n>%s m³</td></tr><tr><td>Bodenplatte</td><td class=n>%s m³</td></tr>'
                '<tr><td>Deckenbekleidung</td><td class=n>%s m³</td></tr><tr><td>Deckenbalken</td><td class=n>%s m³</td></tr>'
                '<tr><td>Tragwerk</td><td class=n>%s m³</td></tr><tr><td>Dachstuhl</td><td class=n>%s m³</td></tr>'
                '<tr><td>Dachfläche netto</td><td class=n>%s m²</td></tr><tr><td>Dachdeckung</td><td class=n>%s m³</td></tr>'
                '<tr><td>Treppe</td><td class=n>%s m³</td></tr><tr><td>Lichtschächte (Beton)</td><td class=n>%s m³</td></tr>'
                '<tr><td>Fassade</td><td class=n>%s m² / %d Bretter</td></tr><tr><td>Innendämmung</td><td class=n>%s m² / %s m³</td></tr>'
                '<tr><td>Fußboden</td><td class=n>%s m² / %s m³</td></tr><tr><td>Heizungsrohr</td><td class=n>%s m</td></tr><tr><td>Wandheizung</td><td class=n>%s m² / %d Platten / %s</td></tr>'
                '<tr><td>Öffnungsfläche (Rohbau)</td><td class=n>%s m²</td></tr><tr><td>Bauteile gesamt</td><td class=n>%d</td></tr>'
                '<tr><td>Bauteile Preis</td><td class=n>%s</td></tr></table>' % (
                    decimal(totals["wall_volume"]), decimal(totals["foundation_volume"]),
                    decimal(totals.get("ceiling_volume", 0)), decimal(totals.get("joist_volume", 0)),
                    decimal(totals.get("structure_volume", 0)), decimal(totals.get("roof_structure_volume", 0)),
                    decimal(totals.get("roof_area", 0)), decimal(totals.get("roof_covering_volume", 0)),
                    decimal(totals.get("stair_volume", 0)), decimal(totals.get("light_well_volume", 0)),
                    decimal(totals.get("facade_area", 0)), totals.get("facade_boards", 0),
                    decimal(totals.get("lining_area", 0)), decimal(totals.get("lining_volume", 0)),
                    decimal(totals.get("floor_area", 0)), decimal(totals.get("floor_volume", 0)),
                    decimal(totals.get("pipe_length", 0), 1),
                    decimal(totals.get("wall_heating_area", 0), 2), totals.get("wall_heating_panels", 0),
                    money(totals.get("wall_heating_price", 0), "EUR"),
                    decimal(totals.get("opening_area", 0)), totals.get("component_count", 0),
                    money(totals.get("component_price", 0), "EUR")))
