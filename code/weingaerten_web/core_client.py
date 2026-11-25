"""Imports the house core package and forwards JSON commands to it."""
import importlib
import json
import logging
import os
import sys
from typing import Any, Dict

logger = logging.getLogger(__name__)


class CoreClient:
    """The connection to `weingaerten_core`; missing or broken core → `available` is False."""

    def __init__(self, core_dir: str) -> None:
        """Import the core once.

        Args:
            core_dir: the folder that contains the `weingaerten_core` package.
        """
        self._core = None
        if not os.path.isfile(os.path.join(core_dir, "weingaerten_core", "__init__.py")):
            logger.warning("core package missing in %s", core_dir)
            return
        try:
            if core_dir not in sys.path:
                sys.path.insert(0, core_dir)
            self._core = importlib.import_module("weingaerten_core")
            logger.info("core loaded from %s", core_dir)
        except Exception:
            logger.exception("core load failed")
            self._core = None

    @property
    def available(self) -> bool:
        """True if the core could be imported."""
        return self._core is not None

    def ask(self, command: str, **arguments: Any) -> Dict[str, Any]:
        """Send one command to the core.

        Args:
            command: the core command (e.g. `HOUSE`).
            arguments: the further request fields.

        Returns:
            The decoded JSON answer.
        """
        arguments["command"] = command
        return json.loads(self._core.handle(json.dumps(arguments)))
