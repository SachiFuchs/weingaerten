"""Answer of the USAGE command: who references an element."""
import logging
from typing import Any, Dict, List, Set

from ..constants import REF_RE

logger = logging.getLogger(__name__)


class UsageFinder:
    """Finds every catalog element, the house and every wall that references a given ref."""

    def __init__(self, model: Dict[str, Any]) -> None:
        """Args:
            model: the loaded model.
        """
        self._model = model

    def users_of(self, ref: str) -> List[str]:
        """Return the sorted users: catalog refs, `house` or `storey:<id>.<wall id>`."""
        return self.all_users().get(ref, [])

    def all_users(self) -> Dict[str, List[str]]:
        """Return the sorted users of every catalog element in one pass (elements without users map to [])."""
        users: Dict[str, Set[str]] = {ref: set() for ref in self._model["elements"]}
        holders = [(user_ref, element) for user_ref, element in self._model["elements"].items()]
        # tga-components link their material (catalog_material); the material shows them and cannot be deleted
        holders += [(user_ref, element) for user_ref, element in
                    ((self._model.get("tga") or {}).get("elements") or {}).items() if user_ref.startswith("tga-component:")]
        if isinstance(self._model["house"], dict):
            holders.append(("house", self._model["house"]))
        for storey_ref, storey in self._model["storeys"].items():
            holders += [("%s.%s" % (storey_ref, wall.get("id")), wall) for wall in storey.get("walls") or []
                        if isinstance(wall, dict)]
        for user, value in holders:
            for ref in self.references_in(value):
                if ref != user:
                    users.setdefault(ref, set()).add(user)
        return {ref: sorted(found) for ref, found in users.items()}

    @staticmethod
    def references_in(value: Any) -> Set[str]:
        """Return every reference string anywhere in a JSON value."""
        found: Set[str] = set()
        UsageFinder._collect(value, found)
        return found

    @staticmethod
    def _collect(value: Any, found: Set[str]) -> None:
        if isinstance(value, str):
            if REF_RE.match(value):
                found.add(value)
        elif isinstance(value, list):
            for item in value:
                UsageFinder._collect(item, found)
        elif isinstance(value, dict):
            for item in value.values():
                UsageFinder._collect(item, found)
