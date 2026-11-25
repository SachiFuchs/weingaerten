"""Reads the TGA catalog (tga-classes, tga-components) and the TGA house files (house/tga, penetrations)."""
import logging
import os
from typing import Any, Dict

from .issue_log import IssueLog

logger = logging.getLogger(__name__)

# folder below catalog/ or house/tga/ -> ref type of its files
CATALOG_FOLDERS = {"tga-classes": "tga-class", "tga-components": "tga-component", "tga-trees": "tga-tree"}
HOUSE_FOLDERS = {"terminals": "tga-terminal", "runs": "tga-run", "parts": "tga-part"}
TARGETS = {"tga-terminal": "terminals", "tga-run": "runs", "tga-part": "parts"}


class TgaLoader:
    """Fills model["tga"] = {elements, terminals, runs, parts, penetrations}; the main catalog stays untouched."""

    def __init__(self, home: str, read_json: Any) -> None:
        """Args:
            home: the WEINGAERTEN_HOME folder.
            read_json: function reading one JSON file (ModelLoader.read_json).
        """
        self._home = home
        self._read_json = read_json

    def load(self, model: Dict[str, Any], issues: IssueLog) -> None:
        """Read all TGA files into the model; broken files become model errors."""
        tga = {"elements": {}, "terminals": {}, "runs": {}, "parts": {}, "penetrations": []}
        for folder, ref_type in CATALOG_FOLDERS.items():
            self._load_folder(tga["elements"], issues, os.path.join("catalog", folder), ref_type)
        for folder, ref_type in HOUSE_FOLDERS.items():
            self._load_folder(tga[TARGETS[ref_type]], issues, os.path.join("house", "tga", folder), ref_type)
        tga["penetrations"] = self._penetrations(issues)
        model["tga"] = tga
        logger.debug("tga: %d elements, %d runs, %d terminals, %d parts", len(tga["elements"]), len(tga["runs"]),
                     len(tga["terminals"]), len(tga["parts"]))

    def _load_folder(self, target: Dict[str, Any], issues: IssueLog, relative_dir: str, ref_type: str) -> None:
        folder = os.path.join(self._home, relative_dir)
        if not os.path.isdir(folder):
            return
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".json"):
                continue
            relative = (relative_dir + "/" + name).replace("\\", "/")
            try:
                element = self._read_json(os.path.join(folder, name))
            except Exception:
                issues.error(relative, "kein gültiges JSON")
                continue
            if not isinstance(element, dict) or element.get("id") != name[:-5]:
                issues.error(relative, "id passt nicht zum Dateinamen '%s'" % name[:-5])
                continue
            target["%s:%s" % (ref_type, name[:-5])] = element

    def _penetrations(self, issues: IssueLog) -> list:
        path = os.path.join(self._home, "house", "penetrations.json")
        if not os.path.isfile(path):
            return []
        try:
            data = self._read_json(path)
        except Exception:
            issues.error("house/penetrations.json", "kein gültiges JSON")
            return []
        items = data.get("items") if isinstance(data, dict) else None
        if not isinstance(items, list):
            issues.error("house/penetrations.json", "items fehlt")
            return []
        return [item for item in items if isinstance(item, dict)]
