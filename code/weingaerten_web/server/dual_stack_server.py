"""Listens on 127.0.0.1 and, if available, on [::1] (Windows resolves localhost to ::1 first)."""
import logging
import threading
from http.server import ThreadingHTTPServer
from typing import Any, Type

from .ipv6_http_server import IPv6HttpServer

logger = logging.getLogger(__name__)


class DualStackServer:
    """Two ThreadingHTTPServer instances sharing one handler class and application."""

    def __init__(self, port: int, handler_class: Type, application: Any) -> None:
        """Args:
            port: TCP port.
            handler_class: the request handler class.
            application: made available to the handlers as `server.application`.
        """
        self._port = port
        self._ipv4 = ThreadingHTTPServer(("127.0.0.1", port), handler_class)
        self._ipv4.application = application
        self._handler_class = handler_class
        self._application = application

    def _start_ipv6(self) -> None:
        try:
            server = IPv6HttpServer(("::1", self._port), self._handler_class)
            server.application = self._application
            threading.Thread(target=server.serve_forever, daemon=True).start()
        except Exception:
            logger.info("IPv6 loopback not available, serving on 127.0.0.1 only")

    def serve_forever(self) -> None:
        """Start the IPv6 listener in a daemon thread and serve IPv4 in the calling thread."""
        self._start_ipv6()
        print("Serving on http://localhost:%d" % self._port, flush=True)
        logger.info("serving on port %d", self._port)
        self._ipv4.serve_forever()
