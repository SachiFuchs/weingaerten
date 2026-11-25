"""HTTP request handler: pages, assets, three.js files and the JSON API."""
import json
import logging
import os
from http.server import BaseHTTPRequestHandler
from typing import Any, Dict, Optional
from urllib.parse import parse_qs

from ..constants import LIBRARY_FILES, REDIRECTS
from .photo_sender import PhotoSender
from .post_request_reader import PostRequestReader

logger = logging.getLogger(__name__)

HTML = "text/html; charset=utf-8"


def _loggable(text: str) -> str:
    """Escape CR/LF so a request path cannot forge extra log lines."""
    return text.replace("\r", "\\r").replace("\n", "\\n")


class RequestHandler(BaseHTTPRequestHandler):
    """Handles one request; the WebApplication is taken from `self.server.application`."""

    server_version = "Weingaerten"

    def log_message(self, format: str, *args: Any) -> None:
        """Silence the default access log of BaseHTTPRequestHandler."""

    def _send(self, status: int, body: Any, content_type: str = HTML, headers: Optional[Dict[str, str]] = None) -> None:
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, status: int, value: Any) -> None:
        self._send(status, json.dumps(value, ensure_ascii=False), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        """Serve redirects, the favicon, the three.js files and the pages; everything else is 404."""
        application = self.server.application
        path, _, query_text = self.path.partition("?")
        try:
            if path in REDIRECTS:
                self.send_response(302)
                self.send_header("Location", REDIRECTS[path])
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if path in ("/favicon.svg", "/favicon.ico"):
                return self._send(200, application.assets.text("roundel.svg"), "image/svg+xml")
            if path.startswith("/lib/") and path[5:] in LIBRARY_FILES and self._send_library(path[5:]):
                return
            if PhotoSender.handles(path):
                photo = PhotoSender(application.settings.home()).read(path)
                if photo is not None:
                    return self._send(200, photo[0], photo[1], {"Cache-Control": "max-age=3600"})
                return self._send(404, application.pages.render_not_found())
            if application.pages.has(path):
                return self._send(200, application.pages.render(path, self._query(query_text)))
            self._send(404, application.pages.render_not_found())
        except Exception:
            logger.exception("GET %s failed", _loggable(path))
            self._send(500, "internal error", "text/plain; charset=utf-8")

    @staticmethod
    def _query(text: str) -> Dict[str, str]:
        # first value of every query parameter
        return {key: values[0] for key, values in parse_qs(text).items()}

    def _send_library(self, name: str) -> bool:
        # returns False if the file is unknown or missing, so the request ends as 404;
        # the file name is taken from LIBRARY_FILES, never from the request
        known = next((entry for entry in LIBRARY_FILES if entry == name), None)
        if known is None:
            return False
        path = os.path.join(self.server.application.settings.lib_dir, known)
        if not os.path.isfile(path):
            return False
        with open(path, "rb") as handle:
            self._send(200, handle.read(), "text/javascript; charset=utf-8", {"Cache-Control": "max-age=86400"})
        return True

    def do_POST(self) -> None:
        """Check the request (host, origin, type, size, JSON) and answer the API call."""
        application = self.server.application
        path = self.path.split("?", 1)[0]
        try:
            request, rejection = PostRequestReader(application.settings.port).read(self.headers, self.rfile)
            if rejection is not None:
                return self._send_json(*rejection)
            self._send_json(*application.api.answer(path, request))
        except Exception:
            logger.exception("POST %s failed", _loggable(path))
            self._send_json(500, {"error": "internal error"})
