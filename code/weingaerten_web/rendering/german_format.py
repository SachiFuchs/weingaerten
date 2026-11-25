"""German number formats of the pages (decimal comma, cm, €)."""
import logging
import re
from typing import Optional

from .html_tools import HtmlTools

logger = logging.getLogger(__name__)


class GermanFormat:
    """Formats numbers the German way."""

    @staticmethod
    def decimal(value: float, digits: int = 3) -> str:
        """Return the value with the given decimals and a decimal comma (`28,611`)."""
        return ("%.*f" % (digits, value)).replace(".", ",")

    @staticmethod
    def centimetres(metres: float) -> str:
        """Return a length in cm without trailing zeros (`32,8 cm`)."""
        text = ("%.2f" % (metres * 100)).rstrip("0").rstrip(".")
        return text.replace(".", ",") + " cm"

    @staticmethod
    def money(value: Optional[float], currency: Optional[str]) -> str:
        """Return a price with thousands dots and 2 decimals (`1.234,50 €`); empty for None."""
        if value is None:
            return ""
        whole, fraction = ("%.2f" % value).replace(".", ",").split(",")
        whole = re.sub(r"\B(?=(\d{3})+(?!\d))", ".", whole)
        symbol = "€" if (currency or "EUR") == "EUR" else HtmlTools.escape(currency)
        return "%s,%s %s" % (whole, fraction, symbol)
