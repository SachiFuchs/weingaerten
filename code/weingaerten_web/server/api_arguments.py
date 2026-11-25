"""Argument checks per API route; the result is the keyword set of the core command."""
import logging
from typing import Any, Dict, Optional

from ..constants import CATALOG_TYPES, EDIT_RE, ID_RE, REF_RE

logger = logging.getLogger(__name__)


class ApiArguments:
    """Validates a POST body for one route; None means `400 invalid request`."""

    @staticmethod
    def _is_id(value: Any) -> bool:
        return bool(isinstance(value, str) and ID_RE.match(value))

    @staticmethod
    def for_route(path: str, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Return the core arguments for the request of a route, or None if it is invalid."""
        if path == "/api/catalog":
            return ApiArguments._catalog(request)
        if path == "/api/resolve":
            ref = request.get("ref")
            return {"ref": ref} if isinstance(ref, str) and REF_RE.match(ref) else None
        if path in ("/api/usage", "/api/element/save", "/api/element/delete"):
            return ApiArguments._element(path, request)
        if path in ("/api/opening/save", "/api/opening/delete", "/api/lining/save", "/api/lining/delete"):
            return ApiArguments._wall_item(path, request)
        if path == "/api/walls/save":
            return ApiArguments._walls(request)
        if path in ("/api/room/save", "/api/room/delete", "/api/shaft/save", "/api/shaft/delete"):
            return ApiArguments._room_item(path, request)
        if path in ("/api/part/save", "/api/part/delete"):
            return ApiArguments._parts(path, request)
        return {}

    @staticmethod
    def _parts(path: str, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # installed parts: save {upsert: [part], delete: [ids]}, delete {id}
        if path.endswith("/delete"):
            return {"id": request["id"]} if ApiArguments._is_id(request.get("id")) else None
        upsert, delete = request.get("upsert") or [], request.get("delete") or []
        if not isinstance(upsert, list) or not all(isinstance(p, dict) and ApiArguments._is_id(p.get("id"))
                                                   for p in upsert):
            return None
        if not isinstance(delete, list) or not all(ApiArguments._is_id(x) for x in delete):
            return None
        return {"upsert": upsert, "delete": delete}

    @staticmethod
    def _room_item(path: str, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # rooms of a storey: save {storey, room, create}, delete {storey, id}; shafts of the house: save {shaft, create},
        # delete {id}
        room = path.startswith("/api/room/")
        arguments: Dict[str, Any] = {}
        if room:
            if not ApiArguments._is_id(request.get("storey")):
                return None
            arguments["storey"] = request["storey"]
        if path.endswith("/save"):
            key = "room" if room else "shaft"
            item = request.get(key)
            if not isinstance(item, dict) or not ApiArguments._is_id(item.get("id")) \
                    or not isinstance(request.get("create"), bool):
                return None
            arguments.update({key: item, "create": request["create"]})
        elif ApiArguments._is_id(request.get("id")):
            arguments["id"] = request["id"]
        else:
            return None
        return arguments

    @staticmethod
    def _catalog(request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        element_type = request.get("type")
        if element_type is not None and element_type not in CATALOG_TYPES:
            return None
        return {"type": element_type} if element_type else {}

    @staticmethod
    def _element(path: str, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        ref = request.get("ref")
        if not isinstance(ref, str) or not EDIT_RE.match(ref):
            return None
        if path != "/api/element/save":
            return {"ref": ref}
        if not isinstance(request.get("element"), dict) or not isinstance(request.get("create"), bool):
            return None
        return {"ref": ref, "element": request["element"], "create": request["create"]}

    @staticmethod
    def _wall_item(path: str, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # openings and linings of one wall: save {storey, wall, <item>, create}, delete {storey, wall, id}
        storey_id, wall_id = request.get("storey"), request.get("wall")
        if not (ApiArguments._is_id(storey_id) and ApiArguments._is_id(wall_id)):
            return None
        arguments = {"storey": storey_id, "wall": wall_id}
        if path.endswith("/save"):
            key = "opening" if path.startswith("/api/opening/") else "lining"
            item = request.get(key)
            if not isinstance(item, dict) or not ApiArguments._is_id(item.get("id")) \
                    or not isinstance(request.get("create"), bool):
                return None
            arguments.update({key: item, "create": request["create"]})
        else:
            if not ApiArguments._is_id(request.get("id")):
                return None
            arguments["id"] = request["id"]
        return arguments

    @staticmethod
    def _walls(request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        def objects_with_ids(items: Any) -> bool:
            return isinstance(items, list) and all(isinstance(o, dict) and ApiArguments._is_id(o.get("id")) for o in items)

        def ids(items: Any) -> bool:
            return isinstance(items, list) and all(ApiArguments._is_id(x) for x in items)
        rooms = request.get("rooms") or {}
        height = request.get("height")
        if not ApiArguments._is_id(request.get("storey")) or not objects_with_ids(request.get("upsert") or []) \
                or not ids(request.get("delete") or []) or not isinstance(rooms, dict) \
                or not objects_with_ids(rooms.get("upsert") or []) or not ids(rooms.get("delete") or []) \
                or (height is not None and not isinstance(height, (int, float))):
            return None
        return {"storey": request.get("storey"), "upsert": request.get("upsert") or [],
                "delete": request.get("delete") or [], "rooms": rooms, "height": height}
