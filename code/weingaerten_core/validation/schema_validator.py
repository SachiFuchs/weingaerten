"""Checks a value against the subset of JSON Schema used by the catalog schemas."""
import logging
import re
from typing import Any, Dict, List, Tuple

from ..json_values import JsonValues

logger = logging.getLogger(__name__)

Finding = Tuple[str, str]


class SchemaValidator:
    """Validates JSON values against one schema (type, enum, pattern, ranges, required, properties, items, $defs)."""

    def __init__(self, schema: Dict[str, Any]) -> None:
        """Args:
            schema: the root schema; `#/$defs/...` references are resolved against it.
        """
        self._root = schema

    def check(self, value: Any, path: str) -> List[Finding]:
        """Validate a value.

        Args:
            value: the JSON value.
            path: location prefix used in the findings (e.g. the element ref).

        Returns:
            (path, message) per violation, in document order.
        """
        findings = []
        self._check(value, self._root, path, findings)
        return findings

    @staticmethod
    def _type_matches(value: Any, type_name: str) -> bool:
        return {"null": value is None, "object": isinstance(value, dict), "array": isinstance(value, list),
                "string": isinstance(value, str), "boolean": isinstance(value, bool),
                "number": JsonValues.is_number(value),
                "integer": isinstance(value, int) and not isinstance(value, bool)}.get(type_name, True)

    def _check(self, value: Any, schema: Dict[str, Any], path: str, findings: List[Finding]) -> None:
        if "$ref" in schema and schema["$ref"].startswith("#/$defs/"):
            definition = self._root.get("$defs", {}).get(schema["$ref"][8:], {})
            schema = dict(definition, **{k: x for k, x in schema.items() if k != "$ref"})
        expected = schema.get("type")
        if expected is not None:
            types = expected if isinstance(expected, list) else [expected]
            if not any(self._type_matches(value, t) for t in types):
                findings.append((path, "falscher Typ (erwartet %s)" % "/".join(types)))
                return
        if "enum" in schema and value not in schema["enum"]:
            findings.append((path, "ungültiger Wert %r (erlaubt: %s)" % (value, ", ".join(map(str, schema["enum"])))))
        if isinstance(value, str):
            self._check_string(value, schema, path, findings)
        if JsonValues.is_number(value):
            self._check_number(value, schema, path, findings)
        if isinstance(value, dict):
            self._check_object(value, schema, path, findings)
        if isinstance(value, list):
            self._check_array(value, schema, path, findings)

    @staticmethod
    def _check_string(value: str, schema: Dict[str, Any], path: str, findings: List[Finding]) -> None:
        if "pattern" in schema and not re.search(schema["pattern"], value):
            findings.append((path, "Format ungültig: %r" % value))
        if "minLength" in schema and len(value) < schema["minLength"]:
            findings.append((path, "leer"))

    @staticmethod
    def _check_number(value: float, schema: Dict[str, Any], path: str, findings: List[Finding]) -> None:
        if "minimum" in schema and value < schema["minimum"]:
            findings.append((path, "Wert < %s" % schema["minimum"]))
        if "maximum" in schema and value > schema["maximum"]:
            findings.append((path, "Wert > %s" % schema["maximum"]))
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            findings.append((path, "Wert muss > %s sein" % schema["exclusiveMinimum"]))

    def _check_object(self, value: Dict[str, Any], schema: Dict[str, Any], path: str, findings: List[Finding]) -> None:
        for key in schema.get("required", []):
            if key not in value:
                findings.append((path, "%s fehlt" % key))
        if "if" in schema:
            # minimal if/then/else: the condition only supports properties with const
            cond = schema["if"].get("properties", {})
            hit = all(key in value and value[key] == rule.get("const") for key, rule in cond.items())
            for key in (schema.get("then" if hit else "else") or {}).get("required", []):
                if key not in value:
                    findings.append((path, "%s fehlt" % key))
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                self._check(item, properties[key], path + "." + key, findings)
            elif schema.get("additionalProperties") is False:
                findings.append((path, "unbekannter Schlüssel '%s'" % key))

    def _check_array(self, value: List[Any], schema: Dict[str, Any], path: str, findings: List[Finding]) -> None:
        if "minItems" in schema and len(value) < schema["minItems"]:
            findings.append((path, "zu wenige Einträge"))
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            findings.append((path, "zu viele Einträge"))
        if "items" in schema:
            for i, item in enumerate(value):
                self._check(item, schema["items"], "%s[%d]" % (path, i), findings)
