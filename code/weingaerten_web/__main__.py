"""Launcher: `python <project>\\code\\weingaerten_web [port]`.

Running the package folder puts the folder itself on sys.path; it is replaced by its parent (the
code folder with both packages) so the package is imported as `weingaerten_web` and its modules
never shadow standard modules.
"""
import logging
import os
import sys

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
if sys.path and os.path.abspath(sys.path[0]) == PACKAGE_DIR:
    sys.path.pop(0)
sys.path.insert(0, os.path.dirname(PACKAGE_DIR))
# Exception #4: the vendored Pygments, before site-packages so the hash-checked copy wins; vendor holds only
# `pygments`, so it cannot shadow a standard module
sys.path.insert(1, os.path.join(PACKAGE_DIR, "vendor"))

from weingaerten_web.server.dual_stack_server import DualStackServer  # noqa: E402
from weingaerten_web.server.request_handler import RequestHandler  # noqa: E402
from weingaerten_web.web_application import ServerSettings, WebApplication  # noqa: E402

logger = logging.getLogger("weingaerten_web")


def main() -> None:
    """Configure console logging and serve until the process is stopped."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = ServerSettings.from_arguments(sys.argv[1:])
    application = WebApplication(settings)
    DualStackServer(settings.port, RequestHandler, application).serve_forever()


if __name__ == "__main__":
    main()
