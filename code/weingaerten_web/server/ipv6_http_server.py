"""Threading HTTP server bound to an IPv6 address."""
import logging
import socket
from http.server import ThreadingHTTPServer

logger = logging.getLogger(__name__)


class IPv6HttpServer(ThreadingHTTPServer):
    """ThreadingHTTPServer for IPv6 addresses such as `::1`."""

    address_family = socket.AF_INET6
