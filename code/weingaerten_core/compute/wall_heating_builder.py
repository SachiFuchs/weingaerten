"""Wall heating of a storey: heating panels (e.g. naturbo Klima) in fields on the room faces of the walls, their pipe
meanders, the feed lines to the distributor and the checks against rooms, roof, openings and catalog."""
import logging
from typing import Any, Dict, List, Optional

from ..constants import TOLERANCE
from ..geometry.vector2d import Point, Vector2D
from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from .assembly_info import AssemblyInfo
from .roof_profile import RoofProfile
from .wall_heating_field import WallHeatingField

logger = logging.getLogger(__name__)

AREA_TOLERANCE = 0.05


class WallHeatingBuilder:
    """Builds the `wall_heating` answer of a storey."""

    def __init__(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            model: the loaded model (assemblies in `elements`, panel components in `tga.elements`).
            issues: receives wall heating errors and warnings.
        """
        self._model = model
        self._tga = (model.get("tga") or {}).get("elements") or {}
        self._issues = issues
        self._fields = WallHeatingField(self._tga, issues)

    def build(self, storey_ref: str, storey: Dict[str, Any], z0: float, rooms: List[Dict[str, Any]],
              walls: List[Dict[str, Any]], roof: Optional[RoofProfile]) -> Optional[Dict[str, Any]]:
        """Return the computed wall heating or None.

        Args:
            storey_ref: storey reference.
            storey: the storey JSON.
            z0: storey elevation (output points are absolute).
            rooms: the computed rooms (rects).
            walls: the serialized walls (openings with rough u / z and plan points).
            roof: roof of the storey (panels must stay below it) or None.
        """
        spec = storey.get("wall_heating")
        if not isinstance(spec, dict):
            return None
        where = storey_ref + ".wall_heating"
        layer = self._panel_layer(where, spec)
        distributor = self._distributor(where, spec, z0, walls)
        if layer is None or distributor is None:
            return None
        circuits = {c.get("id"): c for c in spec.get("circuits") or [] if isinstance(c, dict)}
        if distributor["outlets"] is not None and len(circuits) > distributor["outlets"]:
            self._issues.error(where, "Verteiler hat nur %d Abgänge für %d Heizkreise"
                               % (distributor["outlets"], len(circuits)))
        context = {"spec": spec, "z0": z0, "rooms": rooms, "walls": walls, "roof": roof, "layer": layer,
                   "distributor": distributor}
        fields = []
        for source in spec.get("fields") or []:
            if not isinstance(source, dict):
                continue
            field_where = "%s.%s" % (where, source.get("id"))
            if source.get("circuit") not in circuits:
                self._issues.error(field_where, "Heizkreis unbekannt: %s" % source.get("circuit"))
                continue
            built = self._fields.build(field_where, source, context)
            if built is not None:
                fields.append(built)
        self._check_fittings(where, spec)
        built_circuits = [self._circuit("%s.%s" % (where, cid), circuit, fields) for cid, circuit in circuits.items()]
        counts: Dict[str, int] = {}
        for f in fields:
            for p in f["panels"]:
                counts[p["type"]] = counts.get(p["type"], 0) + 1
        duct = spec.get("duct") if isinstance(spec.get("duct"), dict) else None
        return {"name": spec.get("name"), "assembly": spec.get("assembly"), "pipe": spec.get("pipe"),
                "pipe_diameter": layer["pipe_diameter"], "feed_diameter": float(spec.get("feed_diameter") or 0.016),
                "coupling": spec.get("coupling"), "adapter": spec.get("adapter"),
                "supply_temperature": spec.get("supply_temperature"), "return_temperature": spec.get("return_temperature"),
                "estimated": bool(spec.get("estimated")), "note": spec.get("note"), "layers": layer["layers"],
                "distributor": distributor,
                "duct": {"name": duct.get("name"), "rect": [float(v) for v in duct["rect"]], "z0": z0}
                if duct and self._is_rect(duct.get("rect")) else None,
                "circuits": built_circuits, "fields": fields, "counts": dict(sorted(counts.items())),
                "panel_count": sum(counts.values()), "area": sum(c["area"] for c in built_circuits),
                "pipe_length": sum(c["pipe_length"] for c in built_circuits),
                "feed_length": sum(c["feed_length"] for c in built_circuits),
                "couplings": sum(c["couplings"] for c in built_circuits),
                "adapters": sum(c["adapters"] for c in built_circuits)}

    # --- setup ---------------------------------------------------------------------------------------------------

    # --- circuits and catalog ------------------------------------------------------------------------------------
    def _circuit(self, where: str, circuit: Dict[str, Any], fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        own = [f for f in fields if f["circuit"] == circuit.get("id")]
        area = sum(f["area"] for f in own)
        design = circuit.get("design_area")
        if not own:
            self._issues.warning(where, "Heizkreis ohne Plattenfeld")
        elif JsonValues.is_number(design) and abs(area - design) > AREA_TOLERANCE:
            self._issues.warning(where, "Heizfläche %.2f m² weicht von der Auslegung %.2f m² ab" % (area, design))
        output = circuit.get("design_output")
        return {"id": circuit.get("id"), "name": circuit.get("name"), "room": circuit.get("room"),
                "color": circuit.get("color"), "fields": [f["id"] for f in own],
                "panel_count": sum(len(f["panels"]) for f in own), "area": area,
                "design_area": design if JsonValues.is_number(design) else None,
                "design_output": output if JsonValues.is_number(output) else None,
                "pipe_length": sum(f["pipe_length"] for f in own), "feed_length": sum(f["feed_length"] for f in own),
                "couplings": sum(f["couplings"] for f in own), "adapters": sum(f["adapters"] for f in own)}

    def _check_fittings(self, where: str, spec: Dict[str, Any]) -> None:
        # panels end in 11.6 mm spigots: couplings take them, adapters change to the feed diameter
        panel_dns = {e.get("dn") for ref in (spec.get("panel_components") or {}).values()
                     for e in ((self._tga.get(ref) or {}).get("connection") or {}).get("ends") or []}
        for key, wanted in (("coupling", panel_dns), ("adapter", panel_dns)):
            ref = spec.get(key)
            if ref is None:
                continue
            fitting = self._tga.get(ref)
            if fitting is None:
                self._issues.error(where, "%s: unbekannt: %s" % (key, ref))
                continue
            dns = {e.get("dn") for e in (fitting.get("connection") or {}).get("ends") or []}
            if not dns & wanted:
                self._issues.error(where, "%s passt nicht zu den Plattenanschlüssen (DN %s)"
                                   % (ref, "/".join(str(d) for d in sorted(d for d in wanted if d))))
            if key == "adapter" and JsonValues.is_number(spec.get("feed_diameter")):
                feed_mm = round(float(spec["feed_diameter"]) * 1000, 1)
                if feed_mm not in dns:
                    self._issues.error(where, "Übergang %s passt nicht zur Anbindeleitung %g mm" % (ref, feed_mm))


    @staticmethod
    def _is_rect(value: Any) -> bool:
        return isinstance(value, list) and len(value) == 4 and all(JsonValues.is_number(v) for v in value)
    def _panel_layer(self, where: str, spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        info = AssemblyInfo.of(self._model, spec.get("assembly"))
        if info is None:
            self._issues.error(where, "unbekannt: %s" % spec.get("assembly"))
            return None
        if info["el"].get("category") != "interior_lining":
            self._issues.error(where, "%s ist keine Innenbekleidung (interior_lining)" % spec.get("assembly"))
            return None
        heated = [i for i, layer in enumerate(info["el"]["layers"]) if isinstance(layer, dict) and layer.get("heated")]
        if not heated:
            self._issues.error(where, "Aufbau ohne Plattenebene (heated): %s" % spec.get("assembly"))
            return None
        diameter = spec.get("pipe_diameter", 0.0116)
        if not JsonValues.is_number(diameter) or diameter <= 0:
            self._issues.error(where, "Maße ungültig")
            return None
        panel = info["layers"][heated[0]]
        # the pipe lies in the grooves on the room side of the panel
        return {"offset": panel["offset"], "thickness": panel["thickness"], "total": info["thickness"],
                "pipe_depth": panel["offset"] + panel["thickness"] - float(diameter) / 2 - 0.004,
                "pipe_diameter": float(diameter),
                "layers": [{"index": layer["index"], "material": layer["material"], "thickness": layer["thickness"],
                            "heated": layer["index"] == heated[0]} for layer in info["layers"]]}

    def _distributor(self, where: str, spec: Dict[str, Any], z0: float,
                     walls: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        source = spec.get("distributor") if isinstance(spec.get("distributor"), dict) else {}
        if not WallHeatingField.is_point(source.get("position")):
            self._issues.error(where, "Verteiler ungültig")
            return None
        wall = next((w for w in walls if w["id"] == source.get("wall")), None)
        axis: Point = (1.0, 0.0)
        if wall is not None:
            delta = Vector2D.sub(tuple(wall["end"]), tuple(wall["start"]))
            axis = Vector2D.scale(delta, 1.0 / max(Vector2D.length(delta), TOLERANCE))
        elif source.get("wall") is not None:
            self._issues.error(where, "Verteiler: Wand unbekannt: %s" % source.get("wall"))
        component = source.get("component")
        if component is not None and component not in self._tga:
            self._issues.error(where, "Verteiler: unbekannt: %s" % component)
        outlets = source.get("outlets")
        return {"name": source.get("name"), "component": component, "wall": source.get("wall"),
                "position": [float(v) for v in source["position"]], "axis": list(axis),
                "z": z0 + float(source.get("z") or 0.0), "width": float(source.get("width") or 0.4),
                "height": float(source.get("height") or 0.5), "depth": 0.1,
                "outlets": outlets if isinstance(outlets, int) and not isinstance(outlets, bool) else None,
                "note": source.get("note")}

