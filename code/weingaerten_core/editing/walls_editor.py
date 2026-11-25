"""WALLS_SAVE: changes walls, rooms and the height of a storey."""
import copy
import logging
from typing import Any, Dict, List, Optional

from ..constants import ID_RE
from ..json_values import JsonValues
from ..model.model_cache import ModelCache
from .opening_transfer import OpeningTransfer
from .storey_change_check import StoreyChangeCheck

logger = logging.getLogger(__name__)


class WallsEditor:
    """Applies wall and room upserts / deletes; opening errors are allowed and returned as conflicts."""

    def __init__(self, cache: ModelCache) -> None:
        """Args:
            cache: the model cache.
        """
        self._cache = cache
        self._check = StoreyChangeCheck(cache)

    def save(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Apply the change.

        Args:
            request: `{storey, upsert?, delete?, rooms?: {upsert?, delete?}, height?}`.

        Returns:
            `{storey, walls, rooms, height, opening_conflicts, lining_conflicts, covering_conflicts, warnings}` or
            `{error, errors?}`.
        """
        model = self._cache.model()
        storey_id = request.get("storey")
        storey_ref = "storey:%s" % storey_id
        if not isinstance(storey_id, str) or storey_ref not in model["storeys"]:
            return {"error": "unbekannt: %s" % storey_ref}
        storey = copy.deepcopy(model["storeys"][storey_ref])
        error = self._apply_walls(model, storey, request) or self._apply_rooms(storey, request.get("rooms") or {}) \
            or self._apply_height(storey, request)
        if error:
            return error
        new_errors, all_errors = self._check.new_errors(model, storey_ref, storey)
        hard_errors = [e for e in new_errors if e.get("kind") not in ("opening", "lining", "covering")]
        if hard_errors:
            return StoreyChangeCheck.rejection(hard_errors)
        mine = [e for e in all_errors if e["where"].startswith(storey_ref + ".")]
        conflicts = [{"opening": e.get("opening"), "wall": e.get("wall"), "message": e["message"]}
                     for e in mine if e.get("kind") == "opening"]
        lining_conflicts = [{"lining": e.get("lining"), "wall": e.get("wall"), "message": e["message"]}
                            for e in mine if e.get("kind") == "lining"]
        covering_conflicts = [{"covering": e.get("covering"), "room": e.get("room"), "message": e["message"]}
                              for e in mine if e.get("kind") == "covering"]
        self._check.write(storey_id, storey)
        return {"storey": storey_id, "walls": storey["walls"], "rooms": storey["rooms"], "height": storey.get("height"),
                "opening_conflicts": conflicts, "lining_conflicts": lining_conflicts,
                "covering_conflicts": covering_conflicts, "warnings": self._cache.model()["warnings"]}

    def _apply_walls(self, model: Dict[str, Any], storey: Dict[str, Any],
                     request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        walls = storey.setdefault("walls", [])
        storey.setdefault("rooms", [])
        originals = {w.get("id"): copy.deepcopy(w) for w in walls if isinstance(w, dict)}
        upserts = request.get("upsert") or []
        takes = self._taken_openings(upserts)
        for wall in walls:
            if isinstance(wall, dict) and wall.get("openings"):
                wall["openings"] = [o for o in wall["openings"] if o.get("id") not in takes]
        for upsert in upserts:
            if not isinstance(upsert, dict) or not isinstance(upsert.get("id"), str) or not ID_RE.match(upsert["id"]):
                return {"error": "ungültige Wand-id"}
            new_wall = {k: copy.deepcopy(v) for k, v in upsert.items() if k not in ("openings", "linings", "take_openings")}
            taken = []
            for opening_id, target in takes.items():
                if target != upsert["id"]:
                    continue
                source = next((w for w in originals.values()
                               if any(o.get("id") == opening_id for o in w.get("openings") or [])), None)
                if source is None:
                    return {"error": "unbekannte Öffnung: %s" % opening_id}
                opening = next(o for o in source["openings"] if o.get("id") == opening_id)
                taken.append(OpeningTransfer.moved_opening(opening, source, new_wall, model))
            index = next((i for i, w in enumerate(walls) if isinstance(w, dict) and w.get("id") == upsert["id"]), None)
            if index is None:
                new_wall["openings"] = taken
                walls.append(new_wall)
                continue
            # openings and linings of an existing wall come from the file, never from the request
            new_wall["openings"] = OpeningTransfer.shifted_openings(walls[index], new_wall) + taken
            if walls[index].get("linings"):
                new_wall["linings"] = OpeningTransfer.shifted_linings(walls[index], new_wall)
            walls[index] = new_wall
        deleted = set(request.get("delete") or [])
        storey["walls"] = [w for w in walls if not (isinstance(w, dict) and w.get("id") in deleted)]
        return None

    @staticmethod
    def _taken_openings(upserts: List[Any]) -> Dict[Any, Any]:
        # opening id -> id of the wall that takes it over (split walls, bays)
        takes = {}
        for upsert in upserts:
            if isinstance(upsert, dict) and isinstance(upsert.get("take_openings"), list):
                for opening_id in upsert["take_openings"]:
                    takes[opening_id] = upsert.get("id")
        return takes

    @staticmethod
    def _apply_rooms(storey: Dict[str, Any], rooms_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        rooms = storey["rooms"]
        for upsert in rooms_request.get("upsert") or []:
            if not isinstance(upsert, dict) or not isinstance(upsert.get("id"), str) or not ID_RE.match(upsert["id"]):
                return {"error": "ungültige Raum-id"}
            index = next((i for i, r in enumerate(rooms) if isinstance(r, dict) and r.get("id") == upsert["id"]), None)
            if index is None:
                rooms.append({k: copy.deepcopy(v) for k, v in upsert.items() if k != "coverings"})
            else:
                # the plan editor sends the shape; the other room fields and the coverings come from the file
                room = copy.deepcopy(rooms[index])
                room.update({k: copy.deepcopy(v) for k, v in upsert.items() if k != "coverings"})
                rooms[index] = room
        deleted = set(rooms_request.get("delete") or [])
        storey["rooms"] = [r for r in rooms if not (isinstance(r, dict) and r.get("id") in deleted)]
        return None

    @staticmethod
    def _apply_height(storey: Dict[str, Any], request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if "height" in request and request["height"] is not None:
            if not JsonValues.is_number(request["height"]) or request["height"] <= 0:
                return {"error": "Höhe muss > 0 sein"}
            storey["height"] = request["height"]
        return None
