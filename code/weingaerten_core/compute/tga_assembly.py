"""TGA assemblies (tga-component.assembly): main object with parts; install, placement and connection come from the main object."""
import logging
from typing import Any, Dict, List, Optional

from ..json_values import JsonValues

logger = logging.getLogger(__name__)

# taken from the main object when the assembly has no own value
INHERITED = ("install", "placement", "connection", "cut")


class TgaAssembly:
    """Resolves TGA assemblies against the TGA catalog (no nesting: an assembly is never a main object or a part)."""

    def __init__(self, elements: Dict[str, Any]) -> None:
        """Args:
            elements: model["tga"]["elements"].
        """
        self._elements = elements

    @staticmethod
    def is_assembly(element: Any) -> bool:
        """True for a tga-component with an assembly block."""
        return isinstance(element, dict) and isinstance(element.get("assembly"), dict)

    def main_of(self, element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """The main object (None if unknown or itself an assembly)."""
        main = self._elements.get((element.get("assembly") or {}).get("main"))
        return main if isinstance(main, dict) and not self.is_assembly(main) else None

    def effective(self, element: Any) -> Any:
        """The element as installed: an assembly takes install, placement, connection and cut of its main object
        and the main params below its own; any other element is returned unchanged."""
        if not self.is_assembly(element):
            return element
        main = self.main_of(element)
        if main is None:
            return element
        out = dict(element)
        for key in INHERITED:
            if key not in element and key in main:
                out[key] = main[key]
        out["params"] = dict(main.get("params") or {}, **(element.get("params") or {}))
        return out

    def items(self, element: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parts as [{ref, name, count, role, poles}] (count defaults to 1)."""
        rows = []
        for item in (element.get("assembly") or {}).get("parts") or []:
            if not isinstance(item, dict):
                continue
            part = self._elements.get(item.get("ref")) or {}
            poles = (part.get("connection") or {}).get("poles")
            rows.append({"ref": item.get("ref"), "name": part.get("name"), "count": int(item.get("count") or 1),
                         "role": item.get("role"), "poles": int(poles) if JsonValues.is_number(poles) else None})
        return rows

    def clamps(self, element: Any) -> List[Dict[str, Any]]:
        """Clamp choice of an installed box [{role, clamp}] = the parts with a role."""
        if not self.is_assembly(element):
            return []
        return [{"role": i["role"], "clamp": i["ref"]} for i in self.items(element) if i["role"]]

    def extras(self, element: Any) -> List[Dict[str, Any]]:
        """Parts without a role (counted in the BOM next to the main object) [{ref, count}]."""
        if not self.is_assembly(element):
            return []
        return [{"ref": i["ref"], "count": i["count"]} for i in self.items(element) if not i["role"]]

    def capacity(self, element: Dict[str, Any]) -> Optional[int]:
        """Max. connections = smallest pole count of the clamps (one cable occupies one pole per conductor),
        limited by the assembly's own `max_connections` (allowed connection points)."""
        poles = [i["poles"] for i in self.items(element) if i["role"] and i["poles"]]
        limit = (element.get("assembly") or {}).get("max_connections")
        if JsonValues.is_number(limit):
            poles.append(int(limit))
        return min(poles) if poles else None

    def main_ports(self, element: Dict[str, Any]) -> int:
        """Number of connection points of the main object (install.ports)."""
        main = self.main_of(element) or {}
        return len((main.get("install") or {}).get("ports") or [])

    def summary(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """TGA_CATALOG row of an assembly: {main, main_name, items, capacity, max_connections, main_ports}."""
        main_ref = (element.get("assembly") or {}).get("main")
        return {"main": main_ref, "main_name": (self._elements.get(main_ref) or {}).get("name"),
                "items": self.items(element), "capacity": self.capacity(element),
                "max_connections": (element.get("assembly") or {}).get("max_connections"),
                "main_ports": self.main_ports(element)}

    def errors(self, element: Dict[str, Any]) -> List[str]:
        """German messages: unknown or nested main object / parts, role only on clamps, roles unique, count 1 with role."""
        if not self.is_assembly(element):
            return []
        errors = []
        main_ref = element["assembly"].get("main")
        main = self._elements.get(main_ref)
        if main is None:
            errors.append("assembly.main: unbekannt: %s" % main_ref)
        elif self.is_assembly(main):
            errors.append("assembly.main: Baugruppe kann kein Hauptobjekt sein: %s" % main_ref)
        elif not (main.get("install") or main.get("class") == "tga-class:cable"):
            errors.append("assembly.main: Hauptobjekt ohne Einbaudaten: %s" % main_ref)
        limit = element["assembly"].get("max_connections")
        if JsonValues.is_number(limit) and main is not None and not self.is_assembly(main):
            count = len((main.get("install") or {}).get("ports") or [])
            if count and limit > count:
                errors.append("assembly.max_connections: %d erlaubt, Hauptobjekt hat nur %d Anschlusspunkte" % (limit, count))
        roles = set()
        for n, item in enumerate(element["assembly"].get("parts") or []):
            ref, role = (item or {}).get("ref"), (item or {}).get("role")
            part = self._elements.get(ref)
            where = "assembly.parts[%d]" % n
            if part is None:
                errors.append("%s: unbekannt: %s" % (where, ref))
                continue
            if self.is_assembly(part):
                errors.append("%s: Baugruppe in Baugruppe nicht erlaubt: %s" % (where, ref))
            if role is not None:
                if (part.get("params") or {}).get("part_type") != "clamp":
                    errors.append("%s: Leiter %s nur bei Klemmen" % (where, role))
                if role in roles:
                    errors.append("%s: Leiter %s doppelt" % (where, role))
                if int(item.get("count") or 1) != 1:
                    errors.append("%s: Klemme mit Leiter hat Anzahl 1" % where)
                roles.add(role)
        return errors
