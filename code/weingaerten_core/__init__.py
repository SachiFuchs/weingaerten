"""Weingärten house core – generated from weingaerten-core.md (Core specification). Do not edit.

The package loads the element catalog and the house from JSON files, resolves the references,
computes walls, layers, openings, foundation, rooms and ceilings, and answers JSON commands
through `handle(command_json) -> str`.
"""
import logging

from .command_handler import handle
from .compute.window_panes import WindowPanes

logger = logging.getLogger(__name__)

pane_openings = WindowPanes.opening_types

__all__ = ["handle", "pane_openings"]
