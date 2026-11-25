"""The `{{code:testhistory}}` part of /techdoku: the runs of the last 31 days from scripts\\test_history\\*.json."""
import json
import logging
import os
import re
from typing import Any, Dict, List

from ..rendering.html_tools import HtmlTools
from .test_results_page import TestResultsPage

logger = logging.getLogger(__name__)

HISTORY_DIR = os.path.join("scripts", "test_history")
FILE_RE = re.compile(r"^\d{8}-\d{6}\.json$")
MATRIX_RUNS = 15
SYMBOLS = {"ok": "✓", "fehler": "✗", "übersprungen": "–"}
NO_HISTORY = '<p class="note">Noch keine Historie – python scripts\\run_tests.py ausführen</p>'


class TestHistoryPage:
    """Renders a table of all kept runs and a matrix test × the latest runs."""

    def __init__(self, home: str) -> None:
        """Args:
            home: WEINGAERTEN_HOME (contains `scripts`).
        """
        self._folder = os.path.join(home, HISTORY_DIR)

    def render(self) -> str:
        """Return the HTML of the history, or a note when there is none."""
        runs = self._runs()
        if not runs:
            return NO_HISTORY
        rows = []
        for run in runs:
            results = run["results"]
            counts = [sum(1 for r in results if r.get("status") == s) for s in ("ok", "fehler", "übersprungen")]
            rows.append("<tr><td>%s</td><td>%s</td><td>%d</td><td>%d</td><td>%d</td><td>%d</td></tr>"
                        % (HtmlTools.escape(str(run.get("time", ""))), HtmlTools.escape(str(run.get("selection", ""))),
                           len(results), counts[0], counts[1], counts[2]))
        return ("<p>%d Läufe (aufbewahrt 31 Tage, neueste zuerst).</p><table><tr><th>Zeitpunkt</th><th>Auswahl</th><th>Tests</th>"
                "<th>bestanden</th><th>fehlgeschlagen</th><th>übersprungen</th></tr>%s</table>%s"
                % (len(runs), "".join(rows), self._matrix(runs[:MATRIX_RUNS])))

    def _runs(self) -> List[Dict[str, Any]]:
        if not os.path.isdir(self._folder):
            return []
        runs = []
        for name in sorted(os.listdir(self._folder), reverse=True):
            if not FILE_RE.match(name):
                continue
            try:
                with open(os.path.join(self._folder, name), encoding="utf-8") as handle:
                    run = json.load(handle)
            except (OSError, ValueError) as error:
                logger.warning("history file %s unreadable: %s", name, error)
                continue
            if isinstance(run, dict) and isinstance(run.get("results"), list):
                run["results"] = [r for r in run["results"] if isinstance(r, dict)]
                runs.append(run)
        return runs

    @staticmethod
    def _matrix(runs: List[Dict[str, Any]]) -> str:
        names = sorted({str(r.get("name", "")) for run in runs for r in run["results"]},
                       key=lambda n: (TestResultsPage.level_of(n), n))
        by_run = [{str(r.get("name", "")): str(r.get("status", "")) for r in run["results"]} for run in runs]
        head = "".join("<th>%s</th>" % HtmlTools.escape(str(run.get("time", ""))[5:16].replace("T", " ")) for run in runs)
        rows = []
        for name in names:
            cells = "".join("<td title=\"%s\">%s</td>" % (HtmlTools.escape(statuses.get(name, "")),
                                                          TestResultsPage.status_html(statuses.get(name, ""),
                                                                                      SYMBOLS.get(statuses.get(name, ""), " ")))
                            for statuses in by_run)
            rows.append("<tr><td><code>%s</code></td>%s</tr>" % (HtmlTools.escape(name), cells))
        return ("<h3>Verlauf je Test (letzte %d Läufe)</h3><table><tr><th>Test</th>%s</tr>%s</table>"
                % (len(runs), head, "".join(rows)))
