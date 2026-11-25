"""Small value helpers shared by all modules: number test and float rounding of JSON answers."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class JsonValues:
    """Stateless helpers for JSON-like values (dicts, lists, numbers)."""

    @staticmethod
    def is_number(value: Any) -> bool:
        """Return True for int or float values; booleans are not numbers here."""
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @staticmethod
    def rounded(value: Any, digits: int = 4) -> Any:
        """Round every float in a nested JSON value.

        Args:
            value: dict, list, tuple or scalar.
            digits: number of decimals.

        Returns:
            A copy with rounded floats; tuples become lists, other values are returned unchanged.
        """
        if isinstance(value, bool) or value is None:
            return value
        if isinstance(value, float):
            # "+ 0.0" turns -0.0 into 0.0 so answers never show a negative zero
            return round(value, digits) + 0.0
        if isinstance(value, (list, tuple)):
            return [JsonValues.rounded(item, digits) for item in value]
        if isinstance(value, dict):
            return {key: JsonValues.rounded(item, digits) for key, item in value.items()}
        return value
