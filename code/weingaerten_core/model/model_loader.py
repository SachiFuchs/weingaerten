"""Reads the catalog, the schemas and the house files of WEINGAERTEN_HOME into a model dict."""
import json
import logging
import os
from typing import Any, Dict, Tuple

from ..constants import CATALOG_FOLDERS, REF_RE
from .issue_log import IssueLog
from .tga_loader import TgaLoader

logger = logging.getLogger(__name__)

SCHEMA_SUFFIX = ".schema.json"


class ModelLoader:
    """Loads all data files of one home folder; file problems become model errors."""

    def __init__(self, home: str) -> None:
        """Args:
            home: the WEINGAERTEN_HOME folder.
        """
        self._home = home

    @staticmethod
    def file_signature(home: str) -> Tuple[Tuple[str, int], ...]:
        """Return (path, mtime) of every JSON file below catalog and house.

        A changed signature (edited, added or removed file) means the cached model is stale.
        The import inbox folders (`catalog/imported_*`) are not part of the model and are skipped.
        """
        signature = []
        for sub in ("catalog", "house"):
            for root, dirs, files in os.walk(os.path.join(home, sub)):
                dirs[:] = sorted(d for d in dirs if not d.startswith("imported_"))
                for name in sorted(files):
                    if name.endswith(".json"):
                        path = os.path.join(root, name)
                        try:
                            signature.append((path, os.stat(path).st_mtime_ns))
                        except OSError:
                            pass
        return tuple(signature)

    @staticmethod
    def read_json(path: str) -> Any:
        """Read one UTF-8 JSON file."""
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def load(self) -> Dict[str, Any]:
        """Read every data file.

        Returns:
            The raw model: elements and their files, schemas, house, storeys and the load errors.
        """
        model = {"home": self._home, "elements": {}, "files": {}, "schemas": {}, "house": None,
                 "storeys": {}, "storey_files": {}, "errors": [], "warnings": []}
        issues = IssueLog(model)
        catalog = os.path.join(self._home, "catalog")
        self._load_schemas(model, issues, os.path.join(catalog, "schema"))
        for folder, element_type in CATALOG_FOLDERS.items():
            self._load_catalog_folder(model, issues, catalog, folder, element_type)
        self._load_house(model, issues)
        if isinstance(model["house"], dict):
            self._load_storeys(model, issues)
        TgaLoader(self._home, self.read_json).load(model, issues)
        logger.debug("loaded %d elements, %d storeys from %s", len(model["elements"]), len(model["storeys"]), self._home)
        return model

    def _load_schemas(self, model: Dict[str, Any], issues: IssueLog, schema_dir: str) -> None:
        if not os.path.isdir(schema_dir):
            return
        for name in sorted(os.listdir(schema_dir)):
            if name.endswith(SCHEMA_SUFFIX):
                try:
                    model["schemas"][name[:-len(SCHEMA_SUFFIX)]] = self.read_json(os.path.join(schema_dir, name))
                except Exception:
                    issues.error("catalog/schema/" + name, "kein gültiges JSON")

    def _load_catalog_folder(self, model: Dict[str, Any], issues: IssueLog, catalog: str, folder: str,
                             element_type: str) -> None:
        folder_path = os.path.join(catalog, folder)
        if not os.path.isdir(folder_path):
            return
        for name in sorted(os.listdir(folder_path)):
            if not name.endswith(".json"):
                continue
            relative = "catalog/%s/%s" % (folder, name)
            try:
                element = self.read_json(os.path.join(folder_path, name))
            except Exception:
                issues.error(relative, "kein gültiges JSON")
                continue
            if not isinstance(element, dict):
                issues.error(relative, "Element muss ein Objekt sein")
                continue
            stem = name[:-5]
            if element.get("id") != stem:
                issues.error(relative, "id '%s' passt nicht zum Dateinamen '%s'" % (element.get("id"), stem))
                continue
            ref = "%s:%s" % (element_type, stem)
            model["elements"][ref] = element
            model["files"][ref] = relative

    def _load_house(self, model: Dict[str, Any], issues: IssueLog) -> None:
        house_path = os.path.join(self._home, "house", "house.json")
        if not os.path.isfile(house_path):
            issues.error("house/house.json", "Datei fehlt")
            return
        try:
            model["house"] = self.read_json(house_path)
        except Exception:
            issues.error("house/house.json", "kein gültiges JSON")

    def _load_storeys(self, model: Dict[str, Any], issues: IssueLog) -> None:
        for storey_ref in model["house"].get("storeys", []) or []:
            match = REF_RE.match(storey_ref) if isinstance(storey_ref, str) else None
            if not match or match.group(1) != "storey":
                issues.error("house.storeys", "ungültige Referenz %r" % (storey_ref,))
                continue
            storey_id = match.group(2)
            relative = "house/storeys/%s.json" % storey_id
            path = os.path.join(self._home, "house", "storeys", storey_id + ".json")
            if not os.path.isfile(path):
                issues.error("house.storeys", "unbekannt: " + storey_ref)
                continue
            try:
                storey = self.read_json(path)
            except Exception:
                issues.error(relative, "kein gültiges JSON")
                continue
            if not isinstance(storey, dict) or storey.get("id") != storey_id:
                issues.error(relative, "id passt nicht zum Dateinamen '%s'" % storey_id)
                continue
            model["storeys"][storey_ref] = storey
            model["storey_files"][storey_ref] = relative
