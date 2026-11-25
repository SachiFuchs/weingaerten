"""Checks a request for a catalog photo (`/catalog-photo/<id>/<file>`) and reads the file."""
import logging
import os
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

PREFIX = "/catalog-photo/"
ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FILE_PATTERN = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*\.(jpg|jpeg|png|webp)$", re.IGNORECASE)
CONTENT_TYPES = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}


class PhotoSender:
    """Resolves photo requests read-only inside `catalog/photos/` of WEINGAERTEN_HOME."""

    def __init__(self, home: str) -> None:
        """Args:
            home: WEINGAERTEN_HOME (empty when unset: every request is unknown).
        """
        self._root = os.path.realpath(os.path.join(home, "catalog", "photos")) if home else ""

    @staticmethod
    def handles(path: str) -> bool:
        """True for paths below `/catalog-photo/`."""
        return path.startswith(PREFIX)

    def read(self, path: str) -> Optional[Tuple[bytes, str]]:
        """Return (content, content type) of the photo, None when the path is invalid or the file missing."""
        parts = path[len(PREFIX):].split("/")
        if not self._root or len(parts) != 2:
            return None
        element_id, name = parts
        if not ID_PATTERN.match(element_id) or not FILE_PATTERN.match(name) or ".." in name:
            return None
        target = os.path.realpath(os.path.join(self._root, element_id, name))
        # the resolved file must stay inside the photo folder (no links out of it)
        if os.path.commonpath([self._root, target]) != self._root or not os.path.isfile(target):
            return None
        with open(target, "rb") as handle:
            content = handle.read()
        return content, CONTENT_TYPES[name.rsplit(".", 1)[1].lower()]
