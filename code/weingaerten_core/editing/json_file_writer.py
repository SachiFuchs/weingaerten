"""Atomic JSON file writing in the format of the data files."""
import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class JsonFileWriter:
    """Writes data files: UTF-8, indent 2, keys in the given order, final newline, atomic replace."""

    @staticmethod
    def write(path: str, value: Any) -> None:
        """Write the value to path via a temporary file, so readers never see a half-written file."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        temporary = path + ".tmp"
        with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
        os.replace(temporary, path)
        logger.debug("written %s", path)
