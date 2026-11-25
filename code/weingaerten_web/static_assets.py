"""Reads the static page assets (page frame, CSS, browser scripts, SVG) once at start."""
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

# the only files that are ever read from the static folder
ASSET_NAMES = ("page.html", "style.css", "roundel.svg", "hatch_defs.svg", "tip.js", "common.js", "front.js",
               "haus3d.js", "detail3d.js", "plan.js", "plan_zoom.js", "plan_tooltips.js", "katalog.js", "katalog_layout.js", "katalog_ifc.js", "katalog_docs.js", "katalog_tga_tree.js", "katalog_tga_draw.js", "katalog_tga.js", "wand.js", "waende_layout.js",
               "lining.js", "techdoku.js", "waste3d.js", "water3d.js", "electric3d.js", "room3d.js", "raum.js",
               "install_tree.js", "install.js", "parts3d.js", "install3d.js", "wallheat3d.js")


class StaticAssets:
    """Holds the texts of the static assets; they are embedded inline into the pages."""

    def __init__(self, static_dir: str) -> None:
        """Read all assets.

        Args:
            static_dir: the `static` folder of the package.
        """
        self._texts: Dict[str, str] = {}
        for name in ASSET_NAMES:
            # newline="" keeps the line endings, so the pages are byte-identical to the asset files
            with open(os.path.join(static_dir, name), encoding="utf-8", newline="") as handle:
                self._texts[name] = handle.read()
        logger.info("%d static assets loaded from %s", len(self._texts), static_dir)

    def text(self, name: str) -> str:
        """Return the text of one asset (a name of ASSET_NAMES)."""
        return self._texts[name]
