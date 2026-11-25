"""Cutting plan of a board facade: which pieces come out of how many stock boards."""
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# offcuts shorter than this are waste (too short to nail over two battens)
MIN_REUSE = 0.5


class FacadeCutting:
    """First-fit-decreasing cut of the facade pieces from stock boards of one length."""

    @staticmethod
    def plan(lengths: List[float], board_length: float) -> Dict[str, Any]:
        """Return `{boards, used_length, stock_length, waste_length, waste_share}`.

        Args:
            lengths: the piece lengths (each ≤ board_length).
            board_length: length of one stock board.
        """
        rests: List[float] = []
        for length in sorted(lengths, reverse=True):
            # take the tightest offcut that still fits, else a new board
            fitting = [i for i, rest in enumerate(rests) if rest + 1e-6 >= length]
            if fitting:
                best = min(fitting, key=lambda i: rests[i])
                rests[best] -= length
            else:
                rests.append(board_length - length)
            rests = [r if r >= MIN_REUSE else 0.0 for r in rests]
        used = sum(lengths)
        stock = len(rests) * board_length
        waste = stock - used
        return {"boards": len(rests), "used_length": used, "stock_length": stock, "waste_length": waste,
                "waste_share": waste / stock if stock > 0 else 0.0}
