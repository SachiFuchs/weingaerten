"""Caches the computed model and reloads it when a data file changes."""
import logging
import os
import threading
from typing import Any, Dict, Optional

from ..compute.model_computer import ModelComputer
from .model_loader import ModelLoader

logger = logging.getLogger(__name__)


class ModelCache:
    """Holds the computed model of WEINGAERTEN_HOME and the lock around loading and writing."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self._signature = None
        self._model = None

    @staticmethod
    def home() -> Optional[str]:
        """Return WEINGAERTEN_HOME or None if it is not set."""
        return os.environ.get("WEINGAERTEN_HOME")

    @staticmethod
    def load_and_compute(home: str) -> Dict[str, Any]:
        """Load all files of home and compute the house (used for the cache and for edit previews)."""
        model = ModelLoader(home).load()
        ModelComputer(model).compute()
        return model

    def model(self) -> Optional[Dict[str, Any]]:
        """Return the current model, reloading it if any data file changed.

        Returns:
            The computed model, or None if WEINGAERTEN_HOME is not set.
        """
        home = self.home()
        if not home:
            return None
        with self.lock:
            signature = ModelLoader.file_signature(home)
            if self._signature != signature or self._model is None:
                logger.debug("data changed, recomputing model")
                self._model = self.load_and_compute(home)
                self._signature = signature
            return self._model

    def invalidate(self) -> None:
        """Force a reload on the next access; call while holding `lock` after a write."""
        self._signature = None
