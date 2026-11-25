"""Clamps of an electrical box per conductor (L, N, PE ...): active cable entries, wire checks and the clamp list."""
import logging
from typing import Any, Dict, List, Optional

from ..json_values import JsonValues
from ..model.issue_log import IssueLog
from ..validation.conductor_roles import ConductorRoles

logger = logging.getLogger(__name__)


class BoxClamps:
    """Applies the part's `clamps[{role, clamp}]` to a box after the port matching (parts are changed in place).

    The smallest pole count is the number of cables the box takes: entries beyond it are `active: false`
    (connected entries are taken first). Every conductor of a connected cable needs a clamp of its role,
    the wires per clamp must not exceed its poles and the cable cross-section must lie in the clamp's range."""

    def __init__(self, elements: Dict[str, Any], issues: IssueLog) -> None:
        """Args:
            elements: the TGA catalog (tga-components by ref).
            issues: receives part errors (unknown clamp) and warnings (wire checks).
        """
        self._elements = elements
        self._issues = issues

    def apply(self, parts: List[Dict[str, Any]]) -> None:
        """Set `clamp_list` (resolved `clamps`), `capacity` and the `active` flag of every entry port of the boxes."""
        by_id = {p["id"]: p for p in parts}
        for part in parts:
            for port in part["ports"]:
                port.setdefault("active", True)
            limit = part.get("assembly_max_connections")
            if part["shape"] != "box" or part["trade"] != "electrical":
                # other assemblies: only `max_connections` ports may be used (connected ones first)
                if JsonValues.is_number(limit):
                    part["capacity"] = int(limit)
                    self._activate(part, all_ports=True)
                continue
            clamps = self._clamps(part)
            part["clamp_list"] = clamps
            part["capacity"] = min((c["poles"] for c in clamps), default=None) if clamps else None
            limit = part.get("assembly_max_connections")
            if JsonValues.is_number(limit):
                part["capacity"] = int(limit) if part["capacity"] is None else min(part["capacity"], int(limit))
            if part["capacity"] is not None:
                self._activate(part)
                self._check(part, clamps, self._cables(part, by_id))

    def _clamps(self, part: Dict[str, Any]) -> List[Dict[str, Any]]:
        # resolved clamp choice; an unknown or non-clamp component is an error, a doubled role a warning
        result, seen = [], set()
        for entry in part.get("clamps") or []:
            role, ref = entry.get("role"), entry.get("clamp")
            element = self._elements.get(ref) or {}
            poles = (element.get("connection") or {}).get("poles")
            if (element.get("params") or {}).get("part_type") != "clamp" or not JsonValues.is_number(poles):
                self._issues.part_error(part["id"], "Klemme %s: keine Klemme mit Polzahl (%s)" % (role, ref))
                continue
            if role in seen:
                self._issues.warning("tga-part:" + part["id"], "Leiter %s doppelt geklemmt" % role)
                continue
            seen.add(role)
            section = (element.get("connection") or {}).get("cross_section")
            result.append({"role": role, "clamp": ref, "name": element.get("name"), "poles": int(poles),
                           "cross_section": section if isinstance(section, list) else None, "wires": 0})
        return result

    @staticmethod
    def _activate(part: Dict[str, Any], all_ports: bool = False) -> None:
        # cable entries = ports with a `cores` list (all ports for non-box assemblies); connected ones first,
        # then in catalog order up to the capacity
        entries = [q for q in part["ports"] if all_ports or q.get("cores")]
        ordered = [q for q in entries if q["connected_to"]] + [q for q in entries if not q["connected_to"]]
        for i, port in enumerate(ordered):
            port["active"] = i < part["capacity"]
            if not port["active"] and port["status"] == "open":
                port["status"] = "inactive"

    def _cables(self, part: Dict[str, Any], by_id: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        # cable components at the connected entries: a cable part itself or the cable pulled into a conduit
        cables = []
        for port in part["ports"]:
            if not (port.get("cores") and port["connected_to"]):
                continue
            other = by_id.get(port["connected_to"].split(".")[0]) or {}
            ref = other.get("component") if other.get("shape") == "cable" else other.get("cable")
            if ref in self._elements:
                cables.append(self._elements[ref])
        return cables

    def _check(self, part: Dict[str, Any], clamps: List[Dict[str, Any]], cables: List[Dict[str, Any]]) -> None:
        where = "tga-part:" + part["id"]
        if len(cables) > part["capacity"]:
            self._issues.warning(where, "%d Leitungen, Klemmen haben nur %d Pole" % (len(cables), part["capacity"]))
        for cable in cables:
            section = (cable.get("params") or {}).get("cross_section_mm2")
            for conductor in ConductorRoles.of(cable):
                clamp = self._clamp_for(clamps, conductor["role"])
                if clamp is None:
                    self._issues.warning(where, "Leiter %s (%s) ohne Klemme" % (conductor["role"], cable.get("name")))
                    continue
                clamp["wires"] += 1
                limits = clamp["cross_section"]
                if JsonValues.is_number(section) and limits and not limits[0] <= float(section) <= limits[1]:
                    self._issues.warning(where, "Klemme %s: %s mm² außerhalb %s–%s mm²"
                                         % (clamp["role"], section, limits[0], limits[1]))
        for clamp in clamps:
            if clamp["wires"] > clamp["poles"]:
                self._issues.warning(where, "Klemme %s: %d Adern, aber nur %d Pole"
                                     % (clamp["role"], clamp["wires"], clamp["poles"]))

    @staticmethod
    def _clamp_for(clamps: List[Dict[str, Any]], role: Optional[str]) -> Optional[Dict[str, Any]]:
        exact = next((c for c in clamps if c["role"] == role), None)
        return exact or next((c for c in clamps if ConductorRoles.same_kind(c["role"], role or "")), None)
