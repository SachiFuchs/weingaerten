"""Answer of the BOM command: quantities per material, wall, component, room, ceiling, structure element and
outdoor area."""
import logging
from typing import Any, Dict, List

from ..json_values import JsonValues
from .covering_tally import CoveringTally
from .floor_heating_tally import FloorHeatingTally
from .lining_tally import LiningTally
from .material_tally import MaterialTally
from .waste_water_tally import WasteWaterTally
from .water_supply_tally import WaterSupplyTally
from .electrical_tally import ElectricalTally
from .part_tally import PartTally
from .wall_heating_tally import ZERO_TOTALS as WALL_HEATING_TOTALS, WallHeatingTally

logger = logging.getLogger(__name__)

ROOF_KIND_NAMES = {"rafter": "Sparren", "purlin": "Mittelpfetten", "foot_purlin": "Fußpfetten", "collar": "Kehlbalken", "ridge_purlin": "Firstpfetten"}


class BillOfMaterials:
    """Sums the computed house into the BOM (3 decimals)."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the computed model.
        """
        self._model = model
        self._materials = MaterialTally(model)
        self._components: Dict[str, Dict[str, Any]] = {}
        self._totals = {"wall_volume": 0.0, "foundation_volume": 0.0, "ceiling_volume": 0.0, "joist_volume": 0.0,
                        "opening_area": 0.0, "component_count": 0, "component_price": 0.0, "structure_volume": 0.0,
                        "roof_structure_volume": 0.0, "roof_area": 0.0, "roof_covering_volume": 0.0, "stair_volume": 0.0,
                        "floor_area": 0.0, "floor_volume": 0.0, "pipe_length": 0.0, "light_well_volume": 0.0,
                        "facade_area": 0.0, "facade_volume": 0.0, "facade_boards": 0,
                        "lining_area": 0.0, "lining_volume": 0.0, "waste_water_length": 0.0, "penetration_count": 0,
                        "fitting_count": 0, "water_supply_length": 0.0, "water_fitting_count": 0,
                        "covering_floor_area": 0.0, "covering_wall_area": 0.0, "covering_wall_length": 0.0,
                        "covering_volume": 0.0, "shaft_cut_area": 0.0, "room_area": 0.0, "room_volume": 0.0,
                        "electrical_conduit_length": 0.0, "electrical_cable_length": 0.0, "electrical_price": 0.0,
                        **PartTally.ZERO_TOTALS, **WALL_HEATING_TOTALS}
        self._floor_heating = FloorHeatingTally(self._materials, self._totals)
        self._wall_heating = WallHeatingTally(model, self._materials, self._totals)
        self._linings = LiningTally(self._materials, self._totals)
        self._coverings = CoveringTally(self._materials, self._totals)

    def build(self) -> Dict[str, Any]:
        """Return `{materials, walls, components, rooms, ceilings, structure, outdoor_areas, totals}` (3 decimals)."""
        walls, rooms, ceilings, structure, outdoor_areas, roof_structure, roof_covering = [], [], [], [], [], [], []
        stairs, floors, heating, wall_heating, light_wells = [], [], [], [], []  # type: ignore[var-annotated]
        facades, linings, coverings = [], [], []  # type: List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]
        for storey in self._model["storeys_out"]:
            floors += self._floor_heating.floors(storey)
            heating += self._floor_heating.heating(storey)
            wall_heating += self._wall_heating.rows(storey)
            ceilings += [self._ceiling(storey, ceiling) for ceiling in storey["ceilings"]]
            walls += [self._wall(wall) for wall in storey["walls"]]
            rooms += [self._coverings.room(storey, r) for r in storey["rooms"]]
            structure += [self._structure(storey, element) for element in storey["structure"]]
            outdoor_areas += [{"outdoor_area": a["id"], "storey": storey["id"], "name": a["name"], "area": a["area"]}
                              for a in storey["outdoor_areas"]]
            roof_structure += self._roof_structure(storey)
            roof_covering += self._roof_covering(storey)
            stairs += [self._stair(storey, stair) for stair in storey["stairs"]]
            light_wells += [self._light_well(storey, well) for well in storey.get("light_wells") or []]
            facades += self._facade(storey)
            linings += self._linings.rows(storey)
            coverings += self._coverings.rows(storey)
        self._add_foundation()
        materials = self._materials.sorted_entries()
        self._add_prices()
        totals = self._totals
        totals["component_count"] = sum(c["count"] for c in self._components.values())
        return JsonValues.rounded({
            "materials": materials, "walls": walls,
            "components": [self._components[ref] for ref in sorted(self._components)], "rooms": rooms,
            "ceilings": ceilings, "structure": structure, "outdoor_areas": outdoor_areas, "roof_structure": roof_structure,
            "roof_covering": roof_covering, "stairs": stairs, "floors": floors, "heating": heating,
            "wall_heating": wall_heating, "light_wells": light_wells, "facade": facades, "linings": linings,
            "waste_water": WasteWaterTally(totals).block(self._model.get("waste_water")),
            "water_supply": WaterSupplyTally(totals).block(self._model.get("water_supply")),
            "electrical": ElectricalTally(totals).block(self._model.get("electrical")),
            "installation": PartTally(totals, self._model).block(self._model.get("installation")),
            "coverings": coverings, "shafts": self._coverings.shafts(self._model.get("shafts") or []),
            "totals": dict(totals)}, 3)

    def _facade(self, storey: Dict[str, Any]) -> List[Dict[str, Any]]:
        # one row per storey; boards and paint are wall layers (volume and outside area come with the walls),
        # the row only adds the cutting plan and the board face to paint (overlap included)
        spec = storey.get("facade")
        if not spec:
            return []
        self._totals["facade_area"] += spec["area"]
        self._totals["facade_volume"] += spec["volume"]
        self._totals["facade_boards"] += spec["boards"]
        return [{"storey": storey["id"], "material": spec["material"], "paint": spec["paint"], "board": spec["board"],
                 "overlap": spec["overlap"], "cover": spec["cover"], "walls": spec["walls"],
                 "pieces": spec["pieces"], "length": spec["length"], "area": spec["area"],
                 "board_area": spec["board_area"], "volume": spec["volume"], "boards": spec["boards"],
                 "stock_length": spec["stock_length"], "waste_length": spec["waste_length"],
                 "waste_share": spec["waste_share"], "paint_area": spec["paint_area"],
                 "estimated": spec["estimated"]}]

    def _light_well(self, storey: Dict[str, Any], well: Dict[str, Any]) -> Dict[str, Any]:
        # concrete parts count as light well volume; the grating counts with its plan area
        for part in well["parts"]:
            self._materials.add(part["material"], "volume", part["volume"])
        self._materials.add(well["grating_material"], "area_outside", well["grating_area"])
        self._totals["light_well_volume"] += well["volume"]
        return {"storey": storey["id"], "light_well": well["id"], "name": well["name"], "wall": well["wall"],
                "opening": well["opening"], "material": well["material"], "width": well["width"],
                "projection": well["projection"], "depth": well["depth"], "volume": well["volume"],
                "grating_material": well["grating_material"], "grating_area": well["grating_area"],
                "estimated": well["estimated"]}

    def _stair(self, storey: Dict[str, Any], stair: Dict[str, Any]) -> Dict[str, Any]:
        self._materials.add(stair["material"], "volume", stair["volume"])
        self._totals["stair_volume"] += stair["volume"]
        return {"storey": storey["id"], "stair": stair["id"], "name": stair["name"], "material": stair["material"],
                "risers": stair["risers"], "rise": stair["rise"], "going": stair["going"], "counts": stair["counts"],
                "volume": stair["volume"], "estimated": stair["estimated"]}

    def _roof_covering(self, storey: Dict[str, Any]) -> List[Dict[str, Any]]:
        # one row per storey: layers summed per material, edges, invoice items; openings count as components
        spec = storey.get("roof_covering")
        if not spec:
            return []
        layers: Dict[str, Dict[str, Any]] = {}
        for face in spec["faces"]:
            for layer in face["layers"]:
                self._materials.add(layer["material"], "volume", layer["volume"])
                row = layers.setdefault("%d" % layer["index"], {"index": layer["index"], "material": layer["material"],
                                                              "thickness": layer["thickness"], "area": 0.0, "volume": 0.0})
                row["area"], row["volume"] = row["area"] + layer["area"], row["volume"] + layer["volume"]
            self._materials.add(face["layers"][0]["material"], "area_outside", face["area_net"])
        self._totals["roof_area"] += spec["area_net"]
        self._totals["roof_covering_volume"] += spec["volume"]
        for opening in spec["openings"]:
            self._totals["opening_area"] += opening["area"]
            for ref in [opening["component"], opening["flashing"]] + opening["parts"]:
                if ref:
                    self._add_component(ref, opening["glass_area"] if ref == opening["component"] else 0.0)
        return [{"storey": storey["id"], "assembly": spec["assembly"], "area": spec["area"],
                 "area_net": spec["area_net"], "volume": spec["volume"], "thickness": spec["thickness"],
                 "eaves_overhang": spec["eaves_overhang"], "verge_overhang": spec["verge_overhang"],
                 "estimated": spec["estimated"], "layers": [layers[k] for k in sorted(layers, key=int)],
                 "edges": spec["edges"], "invoice": spec["invoice"], "items": spec["items"],
                 "openings": [{"id": o["id"], "kind": o["kind"], "name": o["name"], "slope": o["slope"],
                               "area": o["area"]} for o in spec["openings"]]}]

    def _add_component(self, ref: str, glass_area: float) -> None:
        element = self._model["elements"].get(ref) or {}
        component = self._components.setdefault(ref, {"component": ref, "name": element.get("name"),
                                                      "class": element.get("class"), "count": 0, "glass_area": 0.0})
        component["count"] += 1
        component["glass_area"] += glass_area

    def _roof_structure(self, storey: Dict[str, Any]) -> List[Dict[str, Any]]:
        # one row per member kind (Sparren, Mittelpfetten, Fußpfetten, Kehlbalken)
        spec = storey.get("roof_structure")
        if not spec:
            return []
        rows: Dict[str, Dict[str, Any]] = {}
        for member in spec["members"]:
            self._materials.add(member["material"], "volume", member["volume"])
            self._totals["roof_structure_volume"] += member["volume"]
            row = rows.setdefault(member["kind"], {
                "storey": storey["id"], "kind": member["kind"], "name": ROOF_KIND_NAMES[member["kind"]],
                "material": member["material"], "width": member["width"], "height": member["height"],
                "count": 0, "length": 0.0, "volume": 0.0, "estimated": spec["estimated"]})
            row["count"], row["length"], row["volume"] = row["count"] + 1, row["length"] + member["length"], \
                row["volume"] + member["volume"]
        return list(rows.values())

    def _structure(self, storey: Dict[str, Any], element: Dict[str, Any]) -> Dict[str, Any]:
        self._materials.add(element["material"], "volume", element["volume"])
        self._totals["structure_volume"] += element["volume"]
        return {"structure": element["id"], "storey": storey["id"], "name": element["name"], "kind": element["kind"],
                "material": element["material"], "length": element["length"], "volume": element["volume"]}

    def _ceiling(self, storey: Dict[str, Any], ceiling: Dict[str, Any]) -> Dict[str, Any]:
        volume = 0.0
        for layer in ceiling["layers"]:
            self._materials.add(layer["material"], "volume", layer["volume"])
            volume += layer["volume"]
        # the underside of the lowest layer is the visible ceiling surface
        self._materials.add(ceiling["layers"][-1]["material"], "area_inside", ceiling["area"])
        self._totals["ceiling_volume"] += volume
        joists = ceiling["joists"]
        joist_summary = None
        if joists:
            self._materials.add(joists["material"], "volume", joists["volume"])
            self._totals["joist_volume"] += joists["volume"]
            joist_summary = {"material": joists["material"], "count": joists["count"], "length": joists["length"],
                             "volume": joists["volume"], "estimated": joists["estimated"]}
        return {"ceiling": ceiling["id"], "storey": storey["id"], "name": ceiling["name"],
                "assembly": ceiling["assembly"], "area": ceiling["area"], "volume": volume, "joists": joist_summary}

    def _wall(self, wall: Dict[str, Any]) -> Dict[str, Any]:
        volume = 0.0
        for layer in wall["layers"]:
            self._materials.add(layer["material"], "volume", layer["volume"])
            volume += layer["volume"]
        self._totals["wall_volume"] += volume
        faces = wall["faces"]
        if "outside" in faces:
            self._materials.add(faces["outside"]["material"], "area_outside", faces["outside"]["area"])
            self._materials.add(faces["inside"]["material"], "area_inside", faces["inside"]["area"])
            length_outside, length_inside = faces["outside"]["length"], faces["inside"]["length"]
        else:
            for side in ("left", "right"):
                self._materials.add(faces[side]["material"], "area_inside", faces[side]["area"])
            length_outside, length_inside = faces["left"]["length"], faces["right"]["length"]
        for opening in wall["openings"]:
            self._add_opening(opening)
        return {"wall": wall["id"], "assembly": wall["assembly"], "length_outside": length_outside,
                "length_inside": length_inside, "volume": volume, "openings": len(wall["openings"])}

    def _add_opening(self, opening: Dict[str, Any]) -> None:
        self._totals["opening_area"] += opening["rough"]["area"]
        component = self._components.setdefault(opening["component"], {
            "component": opening["component"], "name": opening["name"], "class": opening["class"],
            "count": 0, "glass_area": 0.0})
        component["count"] += 1
        for part in opening["parts"]:
            if part["material"]:
                self._materials.add(part["material"], "volume", part["volume"])
            if part["kind"] == "glass":
                component["glass_area"] += part["size"][0] * part["size"][2]
        for reveal in opening["reveals"]:
            self._materials.add(reveal["material"], "area_reveal", reveal["area"])

    def _add_foundation(self) -> None:
        for layer in (self._model["foundation"] or {}).get("layers") or []:
            self._materials.add(layer["material"], "volume", layer["volume"])
            self._totals["foundation_volume"] += layer["volume"]

    def _add_prices(self) -> None:
        # the price of a component is its cheapest offer; only EUR prices are summed
        elements = self._model["elements"]
        for component in self._components.values():
            product = (elements.get(component["component"]) or {}).get("product")
            product = product if isinstance(product, dict) else {}
            manufacturer_ref = product.get("manufacturer")
            manufacturer = elements.get(manufacturer_ref) if isinstance(manufacturer_ref, str) else None
            component["manufacturer"] = manufacturer.get("name") if isinstance(manufacturer, dict) else None
            offers = [o for o in product.get("offers") or [] if isinstance(o, dict) and JsonValues.is_number(o.get("price"))]
            best = min(offers, key=lambda o: o["price"]) if offers else None
            component["unit_price"] = best["price"] if best else None
            component["currency"] = (best.get("currency") or "EUR") if best else None
            component["total_price"] = best["price"] * component["count"] if best else None
            if best and component["currency"] == "EUR":
                self._totals["component_price"] += component["total_price"]
