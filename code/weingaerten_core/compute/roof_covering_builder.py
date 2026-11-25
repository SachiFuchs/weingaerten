"""Roof covering of a storey (Dachdeckung): the layers of a roof assembly on the rafters of every roof face, with
eaves / verge overhangs, openings (roof windows, chimney), edge lengths and invoice items."""
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from ..geometry.polygon import Polygon
from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from .assembly_info import AssemblyInfo
from .roof_covering_edges import RoofCoveringEdges
from .roof_covering_openings import RoofCoveringOpenings
from .roof_profile import RoofProfile

logger = logging.getLogger(__name__)

SIDES = ("west", "east")
SIDE_NAMES = {"west": "West", "east": "Ost"}


class RoofCoveringBuilder:
    """Builds `roof_covering` of a storey; layers are sloped slabs between a bottom and a top plane."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the loaded model (assemblies, materials, components).
            issues: receives the roof covering errors and warnings.
        """
        self._model = model
        self._issues = issues

    def build(self, storey_ref: str, storey: Dict[str, Any], z0: float, roof: Optional[RoofProfile],
              structure: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Return the computed covering or None (no or invalid `roof_covering`).

        Args:
            storey_ref: storey reference.
            storey: the storey JSON (`roof_covering`, faces from `roof_structure.slopes`).
            z0: storey elevation.
            roof: the storey roof (required).
            structure: the computed roof structure (rafter height, rafters for the trimmer check) or None.
        """
        spec = storey.get("roof_covering")
        if not isinstance(spec, dict):
            return None
        where = "%s.roof_covering" % storey_ref
        info = self._checked(where, spec, roof, storey)
        if info is None:
            return None
        self._roof, self._z0 = roof, z0
        self._cos = math.cos(math.radians(roof.pitch))
        rafter_height = float(((storey.get("roof_structure") or {}).get("rafters") or {}).get("height") or 0.0)
        eaves_o, verge_o = float(spec.get("eaves_overhang") or 0.0), float(spec.get("verge_overhang") or 0.0)
        faces = self._faces(storey["roof_structure"]["slopes"], eaves_o, verge_o)
        members = (structure or {}).get("members") or []
        rafters = [m for m in members if m["kind"] == "rafter"]
        ridge_top = z0 + roof.ridge_height + (rafter_height + info["thickness"]) / self._cos
        openings = RoofCoveringOpenings(self._model, self._issues).build(
            where, spec.get("openings"), {f["id"]: f for f in faces}, roof, rafters, ridge_top)
        for face in faces:
            self._finish(face, info, rafter_height, [o for o in openings if o["slope"] == face["id"]])
        for opening in openings:
            if opening["kind"] == "chimney":
                opening["z0"] = z0
        edges = RoofCoveringEdges.measure(faces, roof.ridge, self._cos)
        items = RoofCoveringEdges(self._model, self._issues).items(where, spec.get("items"), edges)
        invoice = spec.get("invoice") if isinstance(spec.get("invoice"), dict) else {}
        return {"assembly": spec["assembly"], "estimated": bool(spec.get("estimated")), "note": spec.get("note"),
                "eaves_overhang": eaves_o, "verge_overhang": verge_o, "thickness": info["thickness"],
                "faces": faces, "openings": openings, "edges": edges, "items": items,
                "invoice": {"area": invoice.get("area") if JsonValues.is_number(invoice.get("area")) else None},
                "area": sum(f["area"] for f in faces), "area_net": sum(f["area_net"] for f in faces),
                "volume": sum(layer["volume"] for f in faces for layer in f["layers"])}

    def _checked(self, where: str, spec: Dict[str, Any], roof: Optional[RoofProfile],
                 storey: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # returns the assembly info or None after reporting the first problem
        if roof is None:
            self._issues.error(where, "Dachdeckung ohne Dach")
            return None
        assembly = self._model["elements"].get(spec.get("assembly"))
        if assembly is None:
            self._issues.error(where, "unbekannt: %s" % spec.get("assembly"))
            return None
        if assembly.get("category") != "roof":
            self._issues.error(where, "%s ist kein Dachaufbau (roof)" % spec.get("assembly"))
            return None
        for key in ("eaves_overhang", "verge_overhang"):
            value = spec.get(key, 0.0)
            if not JsonValues.is_number(value) or value < 0:
                self._issues.error(where, "Überstand ungültig")
                return None
        slopes = (storey.get("roof_structure") or {}).get("slopes")
        if not isinstance(slopes, list) or not slopes or not all(
                isinstance(s, dict) and s.get("side") in SIDES and isinstance(s.get("range"), list)
                and len(s["range"]) == 2 and all(JsonValues.is_number(v) for v in s["range"]) for s in slopes):
            self._issues.error(where, "Dachflächen fehlen (roof_structure.slopes)")
            return None
        return AssemblyInfo.of(self._model, spec["assembly"])

    def _faces(self, slopes: List[Dict[str, Any]], eaves_o: float, verge_o: float) -> List[Dict[str, Any]]:
        # free ends of a face (no adjoining face of the same side) get the verge overhang
        roof, faces = self._roof, []
        for slope in slopes:
            side, (a, b) = slope["side"], (float(slope["range"][0]), float(slope["range"][1]))
            joins = lambda y: any(s is not slope and s["side"] == side and y in (float(s["range"][0]),
                                                                                 float(s["range"][1])) for s in slopes)
            along = (a if joins(a) else a - verge_o, b if joins(b) else b + verge_o)
            end = float(slope.get("end", roof.ridge))
            across = (roof.eaves[0] - eaves_o, end) if side == "west" else (end, roof.eaves[1] + eaves_o)
            faces.append({"id": slope.get("id") or side, "side": side, "name": "Dachfläche %s" % SIDE_NAMES[side],
                          "across": list(across), "along": list(along), "end": end})
        return faces

    def _point(self, across: float, along: float) -> Tuple[float, float]:
        return (across, along) if self._roof.axis == 0 else (along, across)

    def _plane(self, side: str, offset: float) -> List[float]:
        # absolute plane z = a*x + b*y + c, `offset` (vertical) above the roof underside line of that side
        roof = self._roof
        rise, eave = (roof.slope, roof.eaves[0]) if side == "west" else (-roof.slope, roof.eaves[1])
        a = [rise, 0.0] if roof.axis == 0 else [0.0, rise]
        return [a[0], a[1], self._z0 + roof.knee + offset - rise * eave]

    def _finish(self, face: Dict[str, Any], info: Dict[str, Any], rafter_height: float,
                openings: List[Dict[str, Any]]) -> None:
        (a0, a1), (b0, b1) = face["across"], face["along"]
        corners = [self._point(a0, b0), self._point(a1, b0), self._point(a1, b1), self._point(a0, b1)]
        face["polygon"] = [list(p) for p in Polygon.counter_clockwise(corners)]
        face["area_plan"] = (a1 - a0) * (b1 - b0)
        face["area"] = face["area_plan"] / self._cos
        face["area_net"] = face["area"] - sum(o["area"] for o in openings)
        face["openings"] = [o["id"] for o in openings]
        base = rafter_height / self._cos
        face["base_plane"] = self._plane(face["side"], base)
        total, layers = info["thickness"], []
        for layer in info["layers"]:
            # top_down: offset counts from the top face
            bottom = base + (total - layer["offset"] - layer["thickness"]) / self._cos
            material = self._model["elements"].get(layer["material"], {})
            layers.append({"index": layer["index"], "material": layer["material"], "thickness": layer["thickness"],
                           "bottom_plane": self._plane(face["side"], bottom),
                           "top_plane": self._plane(face["side"], bottom + layer["thickness"] / self._cos),
                           "area": face["area_net"], "volume": face["area_net"] * layer["thickness"],
                           "color": (material.get("appearance") or {}).get("color")})
        face["layers"] = layers
