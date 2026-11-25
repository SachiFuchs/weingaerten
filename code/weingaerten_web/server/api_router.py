"""Forwards a checked API request to the core command and maps the answer to an HTTP status."""
import logging
from typing import Any, Dict, Tuple

from ..constants import API_COMMANDS, CORE_MISSING
from ..core_client import CoreClient
from .api_arguments import ApiArguments

logger = logging.getLogger(__name__)


class ApiRouter:
    """POST /api/* → core command."""

    def __init__(self, core: CoreClient) -> None:
        """Args:
            core: the core client.
        """
        self._core = core

    def answer(self, path: str, request: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """Return (status, JSON body) of an API call.

        Core errors become 400 with `{error, errors?}`; a successful answer is returned unchanged.
        """
        if path not in API_COMMANDS:
            return 404, {"error": "not found"}
        if not self._core.available:
            return 500, {"error": CORE_MISSING}
        arguments = ApiArguments.for_route(path, request)
        if arguments is None:
            return 400, {"error": "invalid request"}
        logger.debug("POST %s -> %s", path, API_COMMANDS[path])
        answer = self._core.ask(API_COMMANDS[path], **arguments)
        if isinstance(answer, dict) and "error" in answer:
            body = {"error": answer["error"]}
            if isinstance(answer.get("errors"), list):
                body["errors"] = answer["errors"]
            return 400, body
        return 200, answer
