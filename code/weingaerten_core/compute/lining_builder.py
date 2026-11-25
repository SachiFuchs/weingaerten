"""Interior linings (Innendämmung) on rectangles of wall faces: checks, layers, pieces and 3D parts."""
import logging
from typing import Any, Dict, List, Optional, Tuple

from ..constants import TOLERANCE
from ..geometry.polygon import Polygon
from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from ..validation.class_validator import ClassValidator
from .lining_geometry import LiningGeometry, Piece
from .wall_data import WallData

logger = logging.getLogger(__name__)

LINING_CATEGORY = "interior_lining"


class LiningBuilder:
    """Builds `linings` of a storey from `wall.linings[]`; a lining with an error is reported (kind "lining")
    and left out."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the loaded model (assemblies, materials).
            issues: receives the lining errors.
        """
        self._model = model
        self._issues = issues

    def build(self, storey_ref: str, z0: float, walls: List[WallData]) -> List[Dict[str, Any]]:
        """Return the linings of all walls in file order.

        Args:
            storey_ref: storey reference.
            z0: storey elevation.
            walls: the computed walls (footprint, openings and top line known).
        """
        self._z0 = z0
        ids = [l.get("id") for w in walls for l in (w.source.get("linings") or []) if isinstance(l, dict)]
        for duplicate in sorted({i for i in ids if ids.count(i) > 1}, key=str):
            self._issues.error("%s.%s" % (storey_ref, duplicate), "doppelte Dämmbereich-id")
        result = []
        for wall in walls:
            accepted: List[Dict[str, Any]] = []
            for source in wall.source.get("linings") or []:
                where = "%s.%s.%s" % (storey_ref, wall.id, source.get("id") if isinstance(source, dict) else "?")
                spec = self._checked(where, wall, source, accepted)
                if spec is not None:
                    accepted.append(spec)
                    result.append(self._lining(wall, spec))
        return result

    def _checked(self, where: str, wall: WallData, source: Any,
                 accepted: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not isinstance(source, dict):
            self._issues.lining_error(where, "Dämmbereich ungültig")
            return None
        assembly = self._model["elements"].get(source.get("assembly")) if isinstance(source.get("assembly"), str) else None
        if not isinstance(assembly, dict):
            self._issues.lining_error(where, "unbekannt: %s" % source.get("assembly"))
            return None
        if assembly.get("category") != LINING_CATEGORY:
            self._issues.lining_error(where, "Aufbau ist keine Innendämmung (category interior_lining)")
            return None
        layers = [l for l in assembly.get("layers") or [] if isinstance(l, dict)]
        if not layers or not all(ClassValidator.is_material(self._model, l.get("material")) for l in layers):
            self._issues.lining_error(where, "Schichten der Innendämmung ungültig")
            return None
        face = source.get("face")
        if face not in (("inside",) if wall.is_exterior else ("left", "right")):
            self._issues.lining_error(where, "Seite ungültig (Außenwand: inside, Innenwand: left|right)")
            return None
        spec = self._extent(where, wall, source, face)
        if spec is None:
            return None
        other = next((a for a in accepted if a["face"] == face and a["u0"] < spec["u1"] - TOLERANCE
                      and a["u1"] > spec["u0"] + TOLERANCE and a["z0"] < spec["z1"] - TOLERANCE
                      and a["z1"] > spec["z0"] + TOLERANCE), None)
        if other is not None:
            self._issues.lining_error(where, "Dämmbereich überlappt %s" % other["id"])
            return None
        spec.update(id=source.get("id"), assembly=source["assembly"], layers=layers, note=source.get("note"),
                    name=assembly.get("name"))
        return spec

    def _extent(self, where: str, wall: WallData, source: Dict[str, Any], face: str) -> Optional[Dict[str, Any]]:
        u0, u1 = source.get("u0"), source.get("u1")
        z0 = source.get("z0", 0.0)
        top = max(z for _, z in wall.profile(*wall.u_ranges[0.0]))
        z1 = source.get("z1", top)
        if not all(JsonValues.is_number(v) for v in (u0, u1, z0, z1)) or u1 <= u0 + TOLERANCE \
                or z1 <= z0 + TOLERANCE or z0 < 0:
            self._issues.lining_error(where, "Maße ungültig")
            return None
        low, high = wall.u_ranges[0.0 if face == "left" else wall.thickness]
        if u0 < min(low, high) - TOLERANCE or u1 > max(low, high) + TOLERANCE or z1 > top + TOLERANCE:
            self._issues.lining_error(where, "Dämmbereich außerhalb der Wand")
            return None
        return {"face": face, "u0": float(u0), "u1": float(u1), "z0": float(z0), "z1": float(z1)}

    def _lining(self, wall: WallData, spec: Dict[str, Any]) -> Dict[str, Any]:
        geometry = LiningGeometry(wall)
        pieces, gross = geometry.pieces(spec["u0"], spec["u1"], spec["z0"], spec["z1"])
        area = sum(LiningGeometry.area(p) for p in pieces)
        thickness = sum(float(l.get("thickness") or 0.0) for l in spec["layers"])
        layers, parts, depth = [], [], 0.0
        for index, layer in enumerate(spec["layers"]):
            layer_thickness = float(layer.get("thickness") or 0.0)
            band = self._band(wall, spec["face"], depth, layer_thickness)
            layers.append({"index": index, "material": layer["material"], "thickness": layer_thickness,
                           "area": area, "volume": area * layer_thickness})
            for n, piece in enumerate(pieces):
                parts.append(self._part(wall, spec, index, n, layer["material"], band, piece))
            depth += layer_thickness
        cut = [o.id for o in wall.openings if o.u0 < spec["u1"] and o.u1 > spec["u0"]
               and o.z_top > spec["z0"] and o.z_bottom < spec["z1"]]
        return {"id": spec["id"], "wall": wall.id, "wall_name": wall.source.get("name"), "face": spec["face"],
                "assembly": spec["assembly"], "name": spec["name"], "note": spec["note"],
                "u0": spec["u0"], "u1": spec["u1"], "z0": spec["z0"], "z1": spec["z1"], "thickness": thickness,
                "gross_area": gross, "opening_area": gross - area, "area": area, "volume": area * thickness,
                "openings": cut, "layers": layers, "parts": parts}

    @staticmethod
    def _band(wall: WallData, face: str, depth: float, thickness: float) -> Tuple[float, float]:
        # wall-depth range t of a layer: in front of the inside/right face (t > thickness) or the left face (t < 0)
        if face == "left":
            return -depth - thickness, -depth
        return wall.thickness + depth, wall.thickness + depth + thickness

    def _part(self, wall: WallData, spec: Dict[str, Any], layer: int, index: int, material: str,
              band: Tuple[float, float], piece: Piece) -> Dict[str, Any]:
        a, b, bottom, top_a, top_b = piece
        t0, t1 = band
        corners = [wall.point_3d(u, t, 0.0, 0.0)[:2] for u, t in ((a, t0), (b, t0), (b, t1), (a, t1))]
        footprint = Polygon.counter_clockwise([tuple(p) for p in corners])
        part = {"id": "%s-%d-%d" % (spec["id"], layer + 1, index + 1), "lining": spec["id"], "wall": wall.id,
                "layer": layer, "material": material, "footprint": [list(p) for p in footprint],
                "z0": self._z0 + bottom, "z1": self._z0 + max(top_a, top_b), "top_plane": None,
                "color": ((self._model["elements"].get(material) or {}).get("appearance") or {}).get("color")}
        if abs(top_b - top_a) > 1e-6:
            # sloped top below a roof line: plane through both top points along the wall
            d, start = wall.direction, wall.start
            s = (top_b - top_a) / (b - a)
            base = start[0] * d[0] + start[1] * d[1]
            part["top_plane"] = [s * d[0], s * d[1], self._z0 + top_a - s * a - s * base]
        return part
