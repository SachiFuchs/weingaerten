"""Port, code paths and start time of the web server."""
import datetime
import logging
import os
from typing import List

logger = logging.getLogger(__name__)

DEFAULT_PORT = 8008
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))


class ServerSettings:
    """Settings derived from the command line and the environment."""

    def __init__(self, port: int, code_dir: str) -> None:
        """Args:
            port: TCP port on localhost.
            code_dir: the `code` folder of the project (contains `weingaerten_core` and `weingaerten_web`).
        """
        self.port = port
        self.code_dir = code_dir
        self.started = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def from_arguments(cls, arguments: List[str]) -> "ServerSettings":
        """Build the settings; the optional first argument is the port (1–65535), else 8008."""
        port = DEFAULT_PORT
        if arguments:
            try:
                candidate = int(arguments[0])
                if 1 <= candidate <= 65535:
                    port = candidate
            except ValueError:
                logger.warning("invalid port %r, using %d", arguments[0], DEFAULT_PORT)
        # the package lives in <code>\weingaerten_web
        code_dir = os.path.dirname(PACKAGE_DIR)
        return cls(port, code_dir)

    @property
    def core_dir(self) -> str:
        """Folder that contains the core package (the code folder)."""
        return self.code_dir

    @property
    def lib_dir(self) -> str:
        """Folder of the vendored three.js files (`lib` in the web package)."""
        return os.path.join(PACKAGE_DIR, "lib")

    @property
    def static_dir(self) -> str:
        """The `static` folder of the web package."""
        return os.path.join(PACKAGE_DIR, "static")

    @staticmethod
    def home(default: str = "") -> str:
        """WEINGAERTEN_HOME of the running process (default if unset)."""
        return os.environ.get("WEINGAERTEN_HOME", default)
