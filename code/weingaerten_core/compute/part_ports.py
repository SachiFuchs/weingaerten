"""Port matching of the installed parts: connected (green), deliberately open (blue), transfer (blue arrow), open (red)."""
import logging
import math
from typing import Any, Dict, List, Optional

from ..model.issue_log import IssueLog
from .part_frame import PartFrame

logger = logging.getLogger(__name__)

SNAP_DISTANCE = 0.002          # ports closer than 2 mm sit on each other
OPPOSITE = -math.cos(math.radians(1.0))   # directions must be opposite within 1 degree
TRANSFER_TOLERANCE = 0.002
CLASH_DISTANCE = 0.03          # an unjoined port closer than 3 cm to another one sits on it


class PartPorts:
    """Sets `status`, `connected_to` and `transfer` of every port and checks the stored connections."""

    def __init__(self, issues: IssueLog) -> None:
        """Args:
            issues: receives the connection warnings.
        """
        self._issues = issues

    @staticmethod
    def compatible(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        """True when two ports may be joined: same line and DN, spigot into socket (`any` fits everything).
        Cables: a cable end (line `power`, dn = cores) fits only a cable entry whose `cores` lists its core count
        (never another cable end); a conduit carrying a cable (`cores` on its ends) fits an entry only when the
        core counts overlap."""
        if "power" in (a["line"], b["line"]):
            if a["line"] == b["line"]:
                return False
            cable, entry = (a, b) if a["line"] == "power" else (b, a)
            return int(cable["dn"]) in (entry.get("cores") or []) and PartPorts.cable_fits(cable, entry)
        if a["line"] != b["line"] or abs(float(a["dn"]) - float(b["dn"])) > 1e-6:
            return False
        if a.get("cores") and b.get("cores") and not set(a["cores"]) & set(b["cores"]):
            return False
        if not (PartPorts.cable_fits(a, b) and PartPorts.cable_fits(b, a)):
            return False
        genders = {a["gender"], b["gender"]}
        return "any" in genders or genders == {"spigot", "socket"}

    @staticmethod
    def cable_fits(cable: Dict[str, Any], entry: Dict[str, Any]) -> bool:
        """True unless the entry restricts the cable type (`cable_types`) or cross-section (`cross_section`) and the
        cable end (or a conduit carrying a cable: `cable_type`, `section`) does not match; unknown values fit."""
        types, section = entry.get("cable_types"), entry.get("cross_section")
        if types and cable.get("cable_type") is not None and cable["cable_type"] not in types:
            return False
        if types and cable.get("line") == "power" and cable.get("cable_type") is None:
            return False
        return not (section and cable.get("section") is not None and abs(float(cable["section"]) - float(section)) > 1e-6)

    @staticmethod
    def against_flow(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        """True when both ports carry a waste-water flow and they do not meet as out -> in."""
        flows = {a.get("flow"), b.get("flow")}
        if None in flows or "none" in flows:
            return False
        return flows != {"in", "out"}

    @staticmethod
    def angle_of(port: Dict[str, Any]) -> str:
        """Angle rule of a port: own `angle`, else `any` for cable ends and cable entries (cores), else `right`."""
        if port.get("angle") in ("right", "any"):
            return port["angle"]
        return "any" if port.get("line") == "power" or port.get("cores") else "right"

    @staticmethod
    def seated(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
        """True when two ports lie on each other and face each other (any angle if one port allows it)."""
        if math.dist(a["position"], b["position"]) > SNAP_DISTANCE:
            return False
        if "any" in (PartPorts.angle_of(a), PartPorts.angle_of(b)):
            return True
        dot = sum(a["direction"][i] * b["direction"][i] for i in range(3))
        return dot <= OPPOSITE

    def match(self, parts: List[Dict[str, Any]], storeys: Dict[str, Dict[str, Any]]) -> None:
        """Connect seated compatible ports, then mark the rest; parts are changed in place."""
        index = {(p["id"], q["id"]): (p, q) for p in parts for q in p["ports"]}
        flat = [(p, q) for p in parts for q in p["ports"]]
        for i, (part_a, a) in enumerate(flat):
            for part_b, b in flat[i + 1:]:
                if part_a is part_b or a["connected_to"] or b["connected_to"] or not self.seated(a, b):
                    continue
                if self.compatible(a, b):
                    a["connected_to"], b["connected_to"] = "%s.%s" % (part_b["id"], b["id"]), "%s.%s" % (part_a["id"], a["id"])
                    if self.against_flow(a, b):
                        self._issues.warning("tga-part:" + part_a["id"], "Anschluss %s gegen die Fließrichtung an %s.%s"
                                             % (a["id"], part_b["id"], b["id"]))
                else:
                    self._issues.warning("tga-part:" + part_a["id"], "Anschluss %s passt nicht zu %s.%s (%s DN %s / %s DN %s)"
                                         % (a["id"], part_b["id"], b["id"], a["line"], a["dn"], b["line"], b["dn"]))
        self._clashes(flat)
        for part in parts:
            self._check_stored(part, index)
            for port in part["ports"]:
                port["transfer"] = self._transfer(part, port, storeys.get(part["storey"]))
                if port["connected_to"]:
                    port["status"] = "connected"
                elif port["id"] in part["open_ok"]:
                    port["status"] = "open_ok"
                elif port["transfer"]:
                    port["status"] = "transfer"

    def _clashes(self, flat: List[tuple]) -> None:
        # a free port lying on another port without being joined to it (wrong angle, port already taken, misfit):
        # a joint takes exactly one part per port and only in line; only the nearest port counts, joined ports are fine
        reported = set()
        for part_a, a in flat:
            if a["connected_to"]:
                continue
            # ports joined to this part itself (the other end of a short elbow) do not count
            near = min(((math.dist(a["position"], b["position"]), part_b, b) for part_b, b in flat
                        if part_b is not part_a and (b["connected_to"] or "").split(".")[0] != part_a["id"]),
                       key=lambda item: item[0], default=None)
            if near is None or near[0] > CLASH_DISTANCE:
                continue
            gap, part_b, b = near
            if (not b["connected_to"] and self.seated(a, b)) or (part_b["id"], b["id"], part_a["id"], a["id"]) in reported:
                continue  # seated free misfit (reported in match) or the same pair seen from the other port
            reported.add((part_a["id"], a["id"], part_b["id"], b["id"]))
            self._issues.warning("tga-part:" + part_a["id"], "Anschluss %s liegt an %s.%s ohne Verbindung (%.0f mm)"
                                 % (a["id"], part_b["id"], b["id"], gap * 1000))

    def _check_stored(self, part: Dict[str, Any], index: Dict[tuple, tuple]) -> None:
        # stored connections are the intent of the editor; the geometry decides whether they hold
        for own, target in part["connections"].items():
            port = next((q for q in part["ports"] if q["id"] == own), None)
            other_id, _, other_port = target.partition(".")
            other = index.get((other_id, other_port))
            if port is None or other is None:
                self._issues.warning("tga-part:" + part["id"], "Verbindung %s -> %s: Anschluss unbekannt" % (own, target))
            elif port["connected_to"] != target:
                gap = math.dist(port["position"], other[1]["position"])
                self._issues.warning("tga-part:" + part["id"], "Verbindung %s -> %s sitzt nicht (%.0f mm)"
                                     % (own, target, gap * 1000))

    @staticmethod
    def _transfer(part: Dict[str, Any], port: Dict[str, Any], storey: Optional[Dict[str, Any]]) -> Optional[str]:
        # an open port on the other face of its wall, on the storey floor or at the storey ceiling continues elsewhere
        if storey is None:
            return None
        z = port["position"][2] - float(storey["elevation"])
        if z <= TRANSFER_TOLERANCE:
            return "below"
        if z >= float(storey["height"]) - TRANSFER_TOLERANCE:
            return "above"
        host = part["host"]
        if not host:
            return None
        wall = next((w for w in storey["walls"] if w["id"] == host["wall"]), None)
        if wall is None:
            return None
        t_face, sign = PartFrame.face_depth(wall, host["face"])
        start, n = wall["start"], wall["normal_in"]
        t = (port["position"][0] - start[0]) * n[0] + (port["position"][1] - start[1]) * n[1]
        depth = (t - t_face) * sign
        return "beside" if depth <= -float(wall["thickness"]) + TRANSFER_TOLERANCE else None
