"""Shared services of the pages: core access, the page frame and the core-missing page."""
import logging
from typing import Any, Dict, Optional

from ..constants import CORE_MISSING
from ..core_client import CoreClient
from ..server_settings import ServerSettings
from ..static_assets import StaticAssets
from .html_tools import HtmlTools
from .page_layout import PageLayout

logger = logging.getLogger(__name__)


class PageContext:
    """Everything a page needs; every page request asks the core again, so data edits show on reload."""

    def __init__(self, settings: ServerSettings, core: CoreClient, assets: StaticAssets, layout: PageLayout) -> None:
        """Args:
            settings: port, paths, start time.
            core: the core client.
            assets: the static assets.
            layout: the page frame.
        """
        self.settings = settings
        self.core = core
        self.assets = assets
        self.layout = layout

    def house_or_none(self) -> Optional[Dict[str, Any]]:
        """Return the HOUSE answer, or None if the core is missing."""
        if not self.core.available:
            return None
        return self.core.ask("HOUSE")

    def all_elements(self) -> Dict[str, Dict[str, Any]]:
        """Return every catalog element (ELEMENT answer) by ref, from one CATALOG `full` call."""
        return {entry["ref"]: entry for entry in self.core.ask("CATALOG", full=True).get("elements", [])}

    def model_page(self, title: str, active: str, body: str, house: Dict[str, Any], head: str = "") -> str:
        """Render a page that shows the invalid-model banner when the house has errors."""
        return self.layout.render(title, active, body, house.get("valid", True), len(house.get("errors", [])), head)

    def core_missing_page(self, title: str, active: str, heading: str) -> str:
        """Render the hint page shown when the core is missing."""
        return self.layout.render(title, active, "<h1>%s</h1><p>%s</p>" % (heading, HtmlTools.escape(CORE_MISSING)))
