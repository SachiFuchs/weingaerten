"""Security and format checks of a POST request before it reaches the API."""
import json
import logging
from typing import Any, Dict, Optional, Tuple

from ..constants import MAX_BODY_BYTES

logger = logging.getLogger(__name__)

Rejection = Tuple[int, Dict[str, Any]]


class PostRequestReader:
    """Checks Host, Origin, Content-Type and size and parses the JSON body."""

    def __init__(self, port: int) -> None:
        """Args:
            port: the server port (part of the allowed Host values).
        """
        self._hosts = ("localhost:%d" % port, "127.0.0.1:%d" % port)

    def read(self, headers: Any, body_stream: Any) -> Tuple[Optional[Dict[str, Any]], Optional[Rejection]]:
        """Read the request body.

        Args:
            headers: the request headers.
            body_stream: the request body stream.

        Returns:
            (request dict, None) or (None, (status, error body)).
        """
        # only pages of this server may post (blocks DNS rebinding and cross-site requests)
        host = headers.get("Host", "")
        origin = headers.get("Origin")
        if host not in self._hosts or (origin is not None and origin != "http://" + host):
            return None, (403, {"error": "forbidden"})
        if headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            return None, (415, {"error": "unsupported media type"})
        length = headers.get("Content-Length", "")
        if not length.isdigit() or int(length) > MAX_BODY_BYTES:
            return None, (400, {"error": "invalid request"})
        raw = body_stream.read(int(length))
        try:
            request = json.loads(raw.decode("utf-8") or "{}")
            if not isinstance(request, dict):
                raise ValueError
        except Exception:
            return None, (400, {"error": "invalid JSON"})
        return request, None
