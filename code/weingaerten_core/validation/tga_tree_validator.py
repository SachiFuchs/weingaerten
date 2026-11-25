"""Rules of TGA trees (catalog/tga-trees) and abstract TGA objects (tga-component.abstract)."""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class TgaTreeValidator:
    """German error messages of a tga-tree or an abstract tga-component (schema is checked separately)."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the loaded model (tga.elements).
        """
        self._elements = (model.get("tga") or {}).get("elements") or {}

    def tree_errors(self, tree: Dict[str, Any]) -> List[str]:
        """Unknown refs, duplicate sibling ids, nodes that are neither folder nor object."""
        errors: List[str] = []
        self._nodes(tree.get("nodes"), "nodes", errors)
        return errors

    def _nodes(self, nodes: Any, path: str, errors: List[str]) -> None:
        if not isinstance(nodes, list):
            return
        seen = set()
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                continue
            where = "%s[%d]" % (path, i)
            if node.get("id") in seen:
                errors.append("%s: Knoten-id doppelt: %s" % (where, node.get("id")))
            seen.add(node.get("id"))
            ref, children = node.get("ref"), node.get("nodes")
            if ref is not None and children is not None:
                errors.append("%s: Knoten ist Ordner oder Objekt, nicht beides" % where)
            elif ref is None and children is None:
                errors.append("%s: Knoten braucht ref oder nodes" % where)
            elif ref is not None and ref not in self._elements:
                errors.append("%s: unbekannt: %s" % (where, ref))
            elif ref is None and not node.get("name"):
                errors.append("%s: Ordner ohne name" % where)
            flt = node.get("filter")
            if isinstance(flt, dict):
                if ref is not None:
                    errors.append("%s: filter nur an Ordnern" % where)
                elif flt.get("class") is not None and flt["class"] not in self._elements:
                    errors.append("%s: filter.class unbekannt: %s" % (where, flt["class"]))
            self._nodes(children, where + ".nodes", errors)

    def abstract_errors(self, element: Dict[str, Any]) -> List[str]:
        """Axes must be parameters of the class, not fixed in params; default must be a concretisation."""
        abstract = element.get("abstract")
        if not isinstance(abstract, dict):
            return []
        errors = []
        keys = {p.get("key") for p in (self._elements.get(element.get("class")) or {}).get("parameters") or []
                if isinstance(p, dict)}
        params = element.get("params") or {}
        for axis in abstract.get("axes") or []:
            param = (axis or {}).get("param")
            if param not in keys:
                errors.append("abstract.axes: %s ist kein Parameter der Klasse" % param)
            elif param in params:
                errors.append("abstract.axes: %s ist schon fest in params" % param)
        default = abstract.get("default")
        if default is not None and not self.concretises(element, self._elements.get(default)):
            errors.append("abstract.default: keine Konkretisierung: %s" % default)
        return errors

    @staticmethod
    def install_errors(element: Dict[str, Any]) -> List[str]:
        """Cut lengths (min <= default <= max) and ports of the drawing (unique ids, unit direction) and cable shapes (ports exist)."""
        errors = []
        cut = element.get("cut")
        if isinstance(cut, dict) and all(isinstance(cut.get(k), (int, float)) for k in ("max_length", "default_length")):
            if cut["default_length"] > cut["max_length"]:
                errors.append("cut: Vorgabelänge größer als max. Länge")
            if isinstance(cut.get("min_length"), (int, float)) and cut["min_length"] > cut["default_length"]:
                errors.append("cut: Mindestlänge größer als Vorgabelänge")
        ports = (element.get("install") or {}).get("ports") or []
        ids = [p.get("id") for p in ports if isinstance(p, dict)]
        for dup in sorted({i for i in ids if ids.count(i) > 1}):
            errors.append("install.ports: id doppelt: %s" % dup)
        for port in ports:
            d = port.get("dir") if isinstance(port, dict) else None
            if isinstance(d, list) and len(d) == 3 and all(isinstance(v, (int, float)) for v in d) \
                    and abs(sum(v * v for v in d) - 1.0) > 1e-3:
                errors.append("install.ports %s: Richtung ist kein Einheitsvektor" % port.get("id"))
        shapes = ((element.get("install") or {}).get("layout") or {}).get("shapes") or []
        for n, shape in enumerate(shapes, 1):
            if isinstance(shape, dict) and shape.get("kind") == "cable":
                for key in ("from", "to"):
                    if shape.get(key) not in ids:
                        errors.append("install.layout.shapes %d: Kabel %s unbekannter Anschlusspunkt %s" % (n, key, shape.get(key)))
                if shape.get("from") is not None and shape.get("from") == shape.get("to"):
                    errors.append("install.layout.shapes %d: Kabel beginnt und endet am selben Anschlusspunkt" % n)
        return errors

    @staticmethod
    def concretises(abstract: Dict[str, Any], element: Any) -> bool:
        """True if `element` is a concrete tga-component of the same class with all fixed params of `abstract`."""
        if not isinstance(element, dict) or element.get("abstract") or element.get("class") != abstract.get("class"):
            return False
        params = element.get("params") or {}
        return all(params.get(k) == v for k, v in (abstract.get("params") or {}).items())
