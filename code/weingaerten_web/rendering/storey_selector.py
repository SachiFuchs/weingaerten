"""Storey selection of the plan pages (`?storey=<id>`)."""
import html
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class StoreySelector:
    """Picks the storey of a page and renders the storey links."""

    @staticmethod
    def view(house: Dict[str, Any], storey_id: Optional[str]) -> Dict[str, Any]:
        """Return a shallow copy of the house with the chosen storey first (default the first storey).

        The plan drawings use the first storey, so they show the chosen one without further changes.
        """
        storeys = list(house.get("storeys") or [])
        chosen = next((s for s in storeys if s.get("id") == storey_id), None)
        if chosen is None:
            return house
        return dict(house, storeys=[chosen] + [s for s in storeys if s is not chosen])

    @staticmethod
    def links(house: Dict[str, Any], url: str) -> str:
        """Return the storey switch (empty with fewer than two storeys); the first storey is the shown one."""
        storeys = house.get("storeys") or []
        if len(storeys) < 2:
            return ""
        current = storeys[0].get("id")
        ordered = sorted(storeys, key=lambda s: s.get("elevation") or 0)
        parts = []
        for storey in ordered:
            name = html.escape(str(storey.get("name") or storey.get("id")))
            if storey.get("id") == current:
                parts.append('<b class="btn" style="background:#1C69D4;color:#fff">%s</b>' % name)
            else:
                parts.append('<a class="btn" href="%s?storey=%s">%s</a>' % (url, html.escape(str(storey.get("id"))), name))
        return '<p id="storeysel" style="display:flex;gap:.4rem;align-items:center">Geschoss: %s</p>' % "".join(parts)

    @staticmethod
    def select(house: Dict[str, Any]) -> str:
        """Return the storey `<select id="storeysel">` (ordered by elevation, the first storey selected)."""
        storeys = house.get("storeys") or []
        current = storeys[0].get("id") if storeys else None
        options = []
        for storey in sorted(storeys, key=lambda s: s.get("elevation") or 0):
            storey_id = html.escape(str(storey.get("id")))
            options.append('<option value="%s"%s>%s</option>' % (
                storey_id, " selected" if storey.get("id") == current else "",
                html.escape(str(storey.get("name") or storey.get("id")))))
        return '<select id="storeysel">%s</select>' % "".join(options)
