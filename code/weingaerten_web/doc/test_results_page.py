"""The `{{code:tests}}` part of /techdoku: the last run of scripts\\run_tests.py from scripts\\test_results.json."""
import json
import logging
import os
from typing import Any, Dict, List

from ..rendering.html_tools import HtmlTools

logger = logging.getLogger(__name__)

RESULT_FILE = os.path.join("scripts", "test_results.json")
LEVELS = (("struktur", "Struktur"), ("daten", "Daten"), ("web", "Web"), ("fachlich", "Fachlich"), ("szenario", "Szenario (Testhaus)"))
# same rules as scripts\run_tests.py
EXCLUDED = ("smoke_baseline.py", "check_connections.py")
STRUCTURE = ("check_clean_code.py",)
WEB = ("check_web.py", "check_kat_js.py", "check_haus3d_js.py", "check_documents.py")
COLOURS = {"ok": "#1B7F3B", "fehler": "#C62828", "übersprungen": "#888888"}
NO_RUN = '<p class="note">Noch kein Testlauf – python scripts\\run_tests.py ausführen</p>'


class TestResultsPage:
    """Renders the result file as a summary line and one table per test level."""

    def __init__(self, home: str) -> None:
        """Args:
            home: WEINGAERTEN_HOME (contains `scripts`).
        """
        self._path = os.path.join(home, RESULT_FILE)

    @staticmethod
    def is_test(name: str) -> bool:
        """Return True for a script file name the runner executes."""
        return name.endswith(".py") and name.startswith(("check_", "smoke_", "scen_")) and name not in EXCLUDED

    @staticmethod
    def level_of(name: str) -> str:
        """Return the test level of a script file name."""
        if name.startswith("scen_"):
            return "szenario"
        if name in STRUCTURE:
            return "struktur"
        if name in WEB:
            return "web"
        return "daten" if name.startswith("check_") else "fachlich"

    def last(self) -> Dict[str, Dict[str, Any]]:
        """Return the entries of the last run by script name (empty without a run)."""
        record = self._load() or {}
        return {r["name"]: r for r in record.get("results", []) if isinstance(r, dict) and "name" in r}

    @staticmethod
    def status_html(status: str, text: str = "") -> str:
        """Return a coloured status cell content (text defaults to the status)."""
        return '<span style="color:%s;font-weight:bold">%s</span>' % (COLOURS.get(status, "inherit"), HtmlTools.escape(text or status))

    def render(self) -> str:
        """Return the HTML of the last run, or a note when there is none."""
        record = self._load()
        if record is None:
            return NO_RUN
        results: List[Dict[str, Any]] = [r for r in record.get("results", []) if isinstance(r, dict)]
        counts = {status: sum(1 for r in results if r.get("status") == status) for status in COLOURS}
        parts = ["<p>Lauf %s (Auswahl %s): %d Tests, %d bestanden, %d fehlgeschlagen, %d übersprungen.</p>"
                 % (HtmlTools.escape(str(record.get("time", ""))), HtmlTools.escape(str(record.get("selection", ""))),
                    len(results), counts["ok"], counts["fehler"], counts["übersprungen"])]
        for level, title in LEVELS:
            rows = [r for r in results if r.get("level") == level]
            if rows:
                parts.append("<h3>%s</h3>%s" % (title, self._table(rows)))
        return "".join(parts)

    def _load(self) -> Any:
        if not os.path.isfile(self._path):
            return None
        try:
            with open(self._path, encoding="utf-8") as handle:
                record = json.load(handle)
        except (OSError, ValueError) as error:
            logger.warning("test results unreadable: %s", error)
            return None
        return record if isinstance(record, dict) else None

    @staticmethod
    def _table(rows: List[Dict[str, Any]]) -> str:
        cells = []
        for row in rows:
            status = str(row.get("status", ""))
            cells.append('<tr><td><code>%s</code></td><td>%s</td><td>%s</td><td>%s</td></tr>'
                         % (HtmlTools.escape(str(row.get("name", ""))), TestResultsPage.status_html(status),
                            HtmlTools.escape(str(row.get("seconds", ""))), HtmlTools.escape(str(row.get("message", "")))))
        return ("<table><tr><th>Test</th><th>Status</th><th>Dauer (s)</th><th>Meldung</th></tr>%s</table>"
                % "".join(cells))
