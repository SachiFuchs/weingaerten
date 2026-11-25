"""Reads the German display labels for English keys/enum values (`catalog/reference/labels-de.json`), read-only."""
import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

RELATIVE_PATH = os.path.join("catalog", "reference", "labels-de.json")


class CatalogLabels:
    """Loads the label tables; a missing or broken file gives empty tables (pages then show the raw values)."""

    @staticmethod
    def load(home: str) -> Dict[str, Any]:
        """Return {"values": {table: {key: label}}, "aliases": {param: table}} from WEINGAERTEN_HOME.

        Args:
            home: WEINGAERTEN_HOME (empty when unset).
        """
        empty: Dict[str, Any] = {"values": {}, "aliases": {}}
        if not home:
            return empty
        path = os.path.join(home, RELATIVE_PATH)
        if not os.path.isfile(path):
            return empty
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError) as error:
            logger.warning("labels-de.json unlesbar: %s", error)
            return empty
        values = data.get("values") if isinstance(data.get("values"), dict) else {}
        aliases = data.get("aliases") if isinstance(data.get("aliases"), dict) else {}
        return {"values": values, "aliases": aliases}
