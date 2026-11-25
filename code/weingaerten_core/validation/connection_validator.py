"""Connection rules of the TGA catalog: ends, flow direction, PP-R welding, conductors, clamps, boxes, terminals and runs."""
import logging
import re
from typing import Any, Dict, List, Optional

from .conductor_roles import ConductorRoles

logger = logging.getLogger(__name__)

END_COUNTS = {"bend": 2, "coupling": 2, "adapter": 2, "branch": 3, "plug": 1}
ELECTRICAL_TERMINALS = ("socket", "switch", "light", "distribution_board", "radiator", "heat_pump", "cooker_outlet")
DRAIN_LINES = ("ht", "kg")
RISE_TOLERANCE = 0.001
TELECOM = re.compile(r"J-?Y|2Y", re.I)


class ConnectionValidator:
    """Checks tga-classes / tga-components against the connection rules and the runs against their end points."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the loaded model (`model["tga"]["elements"]` holds the TGA catalog).
        """
        self._model = model
        self._tga = (model.get("tga") or {}).get("elements") or {}

    # --- catalog -------------------------------------------------------------------------------------------------
    @staticmethod
    def line_of(element: Dict[str, Any]) -> Optional[str]:
        """The pipe system or `power` of a component (connection block first)."""
        connection = element.get("connection") if isinstance(element.get("connection"), dict) else {}
        return connection.get("line") or (element.get("params") or {}).get("system_line")

    @staticmethod
    def type_of(element: Dict[str, Any]) -> Optional[str]:
        params = element.get("params") or {}
        return params.get("part_type") or params.get("terminal_type") or params.get("fitting_type")

    def rules_for(self, element: Dict[str, Any], tga_class: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """The rules of the component's class that apply to its line and type."""
        if tga_class is None:
            tga_class = self._tga.get(element.get("class")) or {}
        rules = tga_class.get("connection_rules") if isinstance(tga_class.get("connection_rules"), list) else []
        line, kind = self.line_of(element), self.type_of(element)
        return [r for r in rules if isinstance(r, dict) and (not r.get("line") or r["line"] == line)
                and (not r.get("types") or kind in r["types"])]

    def errors(self, ref: str, element: Dict[str, Any], tga_class: Optional[Dict[str, Any]] = None) -> List[str]:
        """German error messages of one tga-component (tga-classes are covered by their schema)."""
        if not ref.startswith("tga-component:"):
            return []
        connection = element.get("connection")
        if not isinstance(connection, dict):
            return []
        params = element.get("params") or {}
        class_kind = (tga_class or self._tga.get(element.get("class")) or {}).get("kind")
        rules = self.rules_for(element, tga_class)
        errors = self._end_errors(element, connection, params, class_kind, rules)
        errors += self._electrical_errors(element, connection, params, class_kind)
        return errors

    def _end_errors(self, element: Dict[str, Any], connection: Dict[str, Any], params: Dict[str, Any],
                    class_kind: Optional[str], rules: List[Dict[str, Any]]) -> List[str]:
        errors = []
        ends = [e for e in connection.get("ends") or [] if isinstance(e, dict)]
        ids = [e.get("id") for e in ends]
        if len(set(ids)) != len(ids):
            errors.append("connection.ends: doppelte Anschluss-id")
        line = connection.get("line")
        if line and params.get("system_line") and line != params["system_line"]:
            errors.append("connection.line: Leitungssystem passt nicht zu system_line")
        fitting_type = params.get("fitting_type")
        if ends and class_kind == "pipe" and len(ends) != 2:
            errors.append("connection.ends: Rohr braucht 2 Anschlüsse")
        if ends and class_kind == "fitting" and fitting_type in END_COUNTS and len(ends) != END_COUNTS[fitting_type]:
            errors.append("connection.ends: %s braucht %d Anschlüsse" % (fitting_type, END_COUNTS[fitting_type]))
        main = {params.get("dn"), params.get("nominal_size_dn"), params.get("dn_branch")} - {None}
        if line == "alu_composite" and isinstance(params.get("outer_diameter"), (int, float)):
            # Verbundrohre werden nach Außendurchmesser in mm benannt (11,6 / 16)
            main.add(round(params["outer_diameter"] * 1000, 1))
        directed = any(r.get("directed") for r in rules)
        welded = any(r.get("method") in ("weld", "press") for r in rules)
        for end in ends:
            dn, gender = end.get("dn"), end.get("gender")
            own_line = end.get("line") and end.get("line") != line
            if class_kind in ("pipe", "fitting"):
                expected = {params.get("dn_to")} if own_line else (
                    main | {params.get("dn_to")} if fitting_type == "adapter" else main)
                if expected - {None} and dn not in expected:
                    errors.append("Anschluss %s: DN %s passt nicht zu den Parametern" % (end.get("id"), dn))
            if directed:
                errors += self._flow_errors(end, fitting_type)
            if welded and not own_line and gender in ("spigot", "socket"):
                # Rohrenden einer Heizplatte (Verbundrohr) sind Spitzenden wie ein Rohr
                wanted = "spigot" if class_kind == "pipe" or (class_kind == "terminal" and line == "alu_composite") \
                    else "socket"
                if gender != wanted:
                    errors.append("Anschluss %s: %s: Rohr nur über Formteile verbinden"
                                  % (end.get("id"), "PP-R" if line == "ppr" else "Verbundrohr"))
        return errors

    @staticmethod
    def _flow_errors(end: Dict[str, Any], fitting_type: Optional[str]) -> List[str]:
        flow, gender = end.get("flow"), end.get("gender")
        if flow is None:
            return ["Anschluss %s: Fließrichtung fehlt" % end.get("id")]
        if fitting_type == "plug" or gender == "any":
            return []
        # Spitzende zeigt in Fließrichtung, Muffe nimmt das Wasser auf (Überschiebmuffe: beide Seiten Muffe)
        ok = (gender == "spigot" and flow == "out") or (gender == "socket" and flow == "in") or (
            gender == "socket" and flow == "out" and fitting_type == "coupling")
        return [] if ok else ["Anschluss %s: Fließrichtung passt nicht zu Muffe/Spitzende" % end.get("id")]

    @staticmethod
    def _electrical_errors(element: Dict[str, Any], connection: Dict[str, Any], params: Dict[str, Any],
                           class_kind: Optional[str]) -> List[str]:
        errors = []
        electrical = str(element.get("din276", "")).startswith("44")
        if class_kind == "cable" and isinstance(connection.get("conductors"), list) and connection["conductors"]:
            roles = [c.get("role") for c in connection["conductors"] if isinstance(c, dict)]
            if isinstance(params.get("cores"), (int, float)) and len(roles) != int(params["cores"]):
                errors.append("connection.conductors: Leiter passen nicht zur Aderzahl")
            if roles.count("PE") > 1:
                errors.append("connection.conductors: PE doppelt")
        part_type = params.get("part_type")
        if part_type == "clamp":
            poles = connection.get("poles")
            if not isinstance(poles, int) or isinstance(poles, bool) or not 2 <= poles <= 12:
                errors.append("connection.poles: Klemme ohne Polzahl")
            cross = connection.get("cross_section")
            if isinstance(cross, list) and len(cross) == 2 and all(isinstance(v, (int, float)) for v in cross) \
                    and cross[0] > cross[1]:
                errors.append("connection.cross_section: Querschnitt min > max")
        if part_type == "box" and electrical and not connection.get("mounting"):
            errors.append("connection.mounting: Dose ohne Montageart")
        if class_kind == "terminal" and electrical and params.get("terminal_type") in ELECTRICAL_TERMINALS \
                and not connection.get("accepts"):
            errors.append("connection.accepts: Endgerät ohne Leiterarten")
        return errors

    def missing(self, element: Dict[str, Any]) -> bool:
        """True when a component should carry a connection block but has none (VALIDATE warning)."""
        return not isinstance(element.get("connection"), dict) and self._expects(element)

    def _expects(self, element: Dict[str, Any]) -> bool:
        params = element.get("params") or {}
        kind = (self._tga.get(element.get("class")) or {}).get("kind")
        electrical = str(element.get("din276", "")).startswith("44")
        if kind in ("pipe", "fitting") and params.get("system_line") in ("ht", "kg", "ppr"):
            return True
        if kind == "cable" and electrical:
            return not TELECOM.search(str(params.get("cable_type", "")) + " " + str(element.get("name", "")))
        if params.get("part_type") == "clamp" or (params.get("part_type") == "box" and electrical):
            return True
        return kind == "terminal" and electrical and params.get("terminal_type") in ELECTRICAL_TERMINALS

    # --- runs ----------------------------------------------------------------------------------------------------
    def run_issues(self) -> List[Dict[str, str]]:
        """Warnings `{where, message}` of the electrical and waste-water runs."""
        tga = self._model.get("tga") or {}
        issues = []
        for ref, run in sorted((tga.get("runs") or {}).items()):
            component = self._tga.get(run.get("component")) or {}
            kind = (self._tga.get(component.get("class")) or {}).get("kind")
            if kind == "cable":
                messages = self._cable_run(run, component, tga.get("terminals") or {})
            elif self.line_of(component) in DRAIN_LINES:
                messages = self._drain_run(run)
            else:
                messages = []
            issues += [{"where": ref, "message": m} for m in messages]
        return issues

    def _cable_run(self, run: Dict[str, Any], cable: Dict[str, Any], terminals: Dict[str, Any]) -> List[str]:
        messages = []
        roles = [c["role"] for c in ConductorRoles.of(cable)]
        for side in ("from", "to"):
            target = run.get(side)
            if not target:
                if side == "from" and isinstance(run.get("open_end"), dict):
                    continue
                messages.append("Kabelende offen ohne open_end (%s)" % side)
                continue
            terminal = terminals.get(target) or {}
            device = self._tga.get(terminal.get("component")) or {}
            params = device.get("params") or {}
            connection = device.get("connection") if isinstance(device.get("connection"), dict) else {}
            if params.get("part_type") == "box":
                messages += self._joint_check(run, side, target, cable, roles)
                continue
            device_kind = (self._tga.get(device.get("class")) or {}).get("kind")
            if device_kind != "terminal" or params.get("terminal_type") not in ELECTRICAL_TERMINALS:
                messages.append("Kabelende nicht in Dose oder an Endgerät: %s" % target)
                continue
            accepts = connection.get("accepts") or []
            if accepts:
                rest = [r for r in roles if not any(ConductorRoles.same_kind(r, a) for a in accepts)]
                if rest:
                    messages.append("%s nimmt Leiter %s nicht auf (Ader mit Klemme als Endstück abschließen)"
                                    % (target, " ".join(rest)))
        return messages

    def _joint_check(self, run: Dict[str, Any], side: str, target: str, cable: Dict[str, Any],
                     roles: List[str]) -> List[str]:
        # every conductor of a power cable ending in a box sits in a clamp of its own role
        if (cable.get("connection") or {}).get("line") != "power":
            return []
        joints = [j for j in run.get("joints") or [] if isinstance(j, dict) and j.get("at") == side]
        messages = []
        cross = (cable.get("params") or {}).get("cross_section_mm2")
        for joint in joints:
            clamp = self._tga.get(joint.get("clamp")) or {}
            conn = clamp.get("connection") if isinstance(clamp.get("connection"), dict) else {}
            role, wires = joint.get("role"), joint.get("wires") or 1
            if (clamp.get("params") or {}).get("part_type") != "clamp":
                messages.append("%s ist keine Klemme" % joint.get("clamp"))
                continue
            if role not in roles:
                messages.append("Klemme %s: Leitung hat keinen Leiter %s" % (role, role))
            if isinstance(conn.get("poles"), int) and wires > conn["poles"]:
                messages.append("Klemme %s: %d Adern, aber nur %d Pole" % (role, wires, conn["poles"]))
            if wires == 1 and not conn.get("may_be_end"):
                messages.append("Klemme %s darf kein Endstück sein" % role)
            span = conn.get("cross_section")
            if isinstance(cross, (int, float)) and isinstance(span, list) and len(span) == 2 \
                    and not span[0] <= cross <= span[1]:
                messages.append("Klemme %s passt nicht für %s mm²" % (role, cross))
        clamped = [j.get("role") for j in joints]
        loose = [r for r in roles if r not in clamped]
        if loose:
            messages.append("Leiter %s in %s nicht geklemmt" % (" ".join(loose), target))
        doubled = sorted({r for r in clamped if clamped.count(r) > 1})
        if doubled:
            messages.append("Leiter %s doppelt geklemmt" % " ".join(doubled))
        return messages

    @staticmethod
    def _drain_run(run: Dict[str, Any]) -> List[str]:
        points = [p for p in run.get("points") or [] if isinstance(p, list) and len(p) == 3]
        return ["Gefälle gegen die Fließrichtung (Segment %d)" % i
                for i in range(len(points) - 1) if points[i + 1][2] - points[i][2] > RISE_TOLERANCE]
