"""Floor build-ups of a storey: assembly layers over the rooms named in `floors[].rooms`, offer comparison."""
import logging
from typing import Any, Dict, List, Optional

from ..constants import TOLERANCE
from ..geometry.ortho_polygon import OrthoPolygon
from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from .assembly_info import AssemblyInfo

logger = logging.getLogger(__name__)


class FloorBuilder:
    """Builds the `floors` answer of a storey."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog, shaft_rects: List[List[float]]) -> None:
        """Args:
            model: the loaded model (assemblies, materials, companies).
            issues: receives floor errors and warnings.
            shaft_rects: rects of the shafts that open the floors of this storey (`ShaftBuilder`).
        """
        self._model = model
        self._issues = issues
        self._shaft_rects = shaft_rects

    def build(self, storey_ref: str, storey: Dict[str, Any], z0: float,
              rooms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return the computed floors.

        Args:
            storey_ref: storey reference.
            storey: the storey JSON.
            z0: storey elevation.
            rooms: the computed rooms; all rooms with the same name form one room.
        """
        result = []
        for floor in storey.get("floors") or []:
            if isinstance(floor, dict):
                built = self._floor("%s.%s" % (storey_ref, floor.get("id")), floor, z0, rooms)
                if built is not None:
                    result.append(built)
        return result

    @staticmethod
    def room_rects(rooms: List[Dict[str, Any]], name: str) -> List[List[float]]:
        """Return the rects (polygon decomposition) of every room with this name."""
        return [rect for room in rooms if room.get("name") == name for rect in room["rects"]]

    def _floor(self, where: str, floor: Dict[str, Any], z0: float,
               rooms: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        assembly_ref = floor.get("assembly")
        assembly = self._model["elements"].get(assembly_ref)
        if assembly is None:
            self._issues.error(where, "unbekannt: %s" % assembly_ref)
            return None
        if assembly.get("category") != "slab":
            self._issues.error(where, "%s ist kein Bodenaufbau (slab)" % assembly_ref)
            return None
        info = AssemblyInfo.of(self._model, assembly_ref)
        if info is None:
            return None
        floor_rooms = []
        for name in floor.get("rooms") or []:
            rects = self.room_rects(rooms, name)
            if not rects:
                self._issues.error(where, "Raum unbekannt: %s" % name)
                continue
            gross = sum(r[2] * r[3] for r in rects)
            shaft_area = OrthoPolygon.overlap_area(rects, self._shaft_rects)
            floor_rooms.append({"name": name, "rects": rects, "area": gross - shaft_area, "shaft_area": shaft_area,
                                "edge_length": self._union_perimeter(rects)})
        area = sum(r["area"] for r in floor_rooms)
        bottom = z0 + float(floor["z"] if JsonValues.is_number(floor.get("z")) else 0.0)
        top = bottom + info["thickness"]
        edge_length = sum(r["edge_length"] for r in floor_rooms)
        return {"id": floor.get("id"), "name": floor.get("name"), "assembly": assembly_ref,
                "estimated": bool(floor.get("estimated")), "note": floor.get("note"),
                "z_bottom": bottom, "z_top": top, "thickness": info["thickness"], "area": area,
                "edge_length": edge_length, "rooms": floor_rooms,
                "layers": self._layers(assembly, info, top, area),
                "offer": self._offer(where, floor.get("offer"), area, edge_length)}

    def _layers(self, assembly: Dict[str, Any], info: Dict[str, Any], top: float, area: float) -> List[Dict[str, Any]]:
        layers = []
        for layer in info["layers"]:
            material = self._model["elements"].get(layer["material"], {})
            source = assembly["layers"][layer["index"]]
            layers.append({"index": layer["index"], "material": layer["material"],
                           "z0": top - layer["offset"] - layer["thickness"], "z1": top - layer["offset"],
                           "thickness": layer["thickness"], "area": area, "volume": area * layer["thickness"],
                           "heated": bool(source.get("heated")),
                           "color": (material.get("appearance") or {}).get("color")})
        return layers

    @staticmethod
    def _union_perimeter(rects: List[List[float]]) -> float:
        # rooms never overlap, so the outline of the union = all perimeters minus twice every shared edge
        total = sum(2 * (r[2] + r[3]) for r in rects)
        for i, a in enumerate(rects):
            for b in rects[i + 1:]:
                total -= 2 * FloorBuilder._shared_edge(a, b)
        return total

    @staticmethod
    def _shared_edge(a: List[float], b: List[float]) -> float:
        ax0, ay0, ax1, ay1 = a[0], a[1], a[0] + a[2], a[1] + a[3]
        bx0, by0, bx1, by1 = b[0], b[1], b[0] + b[2], b[1] + b[3]
        if abs(ax1 - bx0) <= TOLERANCE or abs(bx1 - ax0) <= TOLERANCE:
            return max(0.0, min(ay1, by1) - max(ay0, by0))
        if abs(ay1 - by0) <= TOLERANCE or abs(by1 - ay0) <= TOLERANCE:
            return max(0.0, min(ax1, bx1) - max(ax0, bx0))
        return 0.0

    def _offer(self, where: str, offer: Any, area: float, edge_length: float) -> Optional[Dict[str, Any]]:
        if not isinstance(offer, dict):
            return None
        company = self._model["elements"].get(offer.get("company"))
        if company is None:
            self._issues.error(where + ".offer", "unbekannt: %s" % offer.get("company"))
        document = offer.get("document")
        document_element = self._model["elements"].get(document) if isinstance(document, str) else None
        if isinstance(document, str) and document.startswith("document:") and document_element is None:
            self._issues.error(where + ".offer", "unbekannt: %s" % document)
        model_quantity = {"area": area, "edge": edge_length}
        items = []
        for item in offer.get("items") or []:
            if not isinstance(item, dict) or not JsonValues.is_number(item.get("unit_price")):
                continue
            quantity = float(item.get("quantity") or 0.0)
            measured = model_quantity.get(item.get("measure"), quantity)
            items.append({"pos": item.get("pos"), "name": item.get("name"), "material": item.get("material"),
                          "measure": item.get("measure"), "unit": item.get("unit"), "quantity": quantity,
                          "model_quantity": measured, "unit_price": float(item["unit_price"]),
                          "offer_total": quantity * item["unit_price"], "model_total": measured * item["unit_price"]})
        return {"company": offer.get("company"), "company_name": (company or {}).get("name"),
                "document": document, "document_name": (document_element or {}).get("name"),
                "date": offer.get("date"), "items": items,
                "offer_total": sum(i["offer_total"] for i in items),
                "model_total": sum(i["model_total"] for i in items)}
