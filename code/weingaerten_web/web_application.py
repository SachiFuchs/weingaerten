"""Wires settings, assets, core, pages and API of the web server."""
import logging

from .core_client import CoreClient
from .rendering.page_context import PageContext
from .rendering.page_layout import PageLayout
from .rendering.page_registry import PageRegistry
from .server.api_router import ApiRouter
from .server_settings import ServerSettings
from .static_assets import StaticAssets

logger = logging.getLogger(__name__)

__all__ = ["WebApplication", "ServerSettings"]


class WebApplication:
    """The objects shared by all requests."""

    def __init__(self, settings: ServerSettings) -> None:
        """Load the assets and the core and build pages and API.

        Args:
            settings: port, paths and start time.
        """
        self.settings = settings
        self.assets = StaticAssets(settings.static_dir)
        self.core = CoreClient(settings.core_dir)
        self.layout = PageLayout(self.assets)
        self.pages = PageRegistry(PageContext(settings, self.core, self.assets, self.layout))
        self.api = ApiRouter(self.core)
