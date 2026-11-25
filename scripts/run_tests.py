"""Runs all check_*/smoke_*/scen_* test scripts and writes scripts\\test_results.json (shown in /techdoku > Test > Ergebnisse).

scen_* = scenario tests on the Testhaus (tests/fixtures/testhaus) in their own sandbox; they define "fertig".
--home original (default) runs check_/smoke_ against the real house, --home testhaus runs only the scenarios.
"""
import argparse
import datetime
import json
import logging
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.dirname(SCRIPTS)
RESULT_FILE = os.path.join(SCRIPTS, "test_results.json")
HISTORY_DIR = os.path.join(SCRIPTS, "test_history")
HISTORY_DAYS = 31
SERVER = "http://localhost:8008/about"
TIMEOUT = 300
EXCLUDED = {"smoke_baseline.py", "check_connections.py"}
STRUCTURE = {"check_clean_code.py"}
WEB = {"check_web.py", "check_kat_js.py", "check_haus3d_js.py", "check_documents.py"}
LEVELS = ("struktur", "daten", "web", "fachlich", "szenario")
PREFIXES = ("check_", "smoke_", "scen_")


class TestRunner:
    """Finds, runs and records the test scripts."""

    def __init__(self, level: str, only: str, home: str = "original") -> None:
        """Args:
            level: `struktur`, `daten`, `web`, `fachlich`, `szenario`, `check`, `smoke`, `scen` or empty for all.
            only: script name (with or without `.py`) or empty.
            home: `original` (all scripts) or `testhaus` (only the sandbox scenarios).
        """
        self._level = level
        self._only = only[:-3] if only.endswith(".py") else only
        self._home = home

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

    def selected(self) -> List[str]:
        """Return the script names to run, sorted by level and name."""
        names = [n for n in os.listdir(SCRIPTS)
                 if n.endswith(".py") and n.startswith(PREFIXES) and n not in EXCLUDED]
        if self._home == "testhaus":
            names = [n for n in names if n.startswith("scen_")]
        if self._only:
            names = [n for n in names if n[:-3] == self._only]
        if self._level in LEVELS:
            names = [n for n in names if self.level_of(n) == self._level]
        elif self._level in ("check", "smoke", "scen"):
            names = [n for n in names if n.startswith(self._level + "_")]
        return sorted(names, key=lambda n: (LEVELS.index(self.level_of(n)), n))

    @staticmethod
    def server_up() -> bool:
        """Return True when the web server answers on port 8008."""
        try:
            with urllib.request.urlopen(SERVER, timeout=5) as response:
                return response.status == 200
        except (urllib.error.URLError, OSError):
            return False

    @staticmethod
    def run_one(name: str) -> Dict[str, Any]:
        """Run one script in its own process and return its result entry."""
        env = dict(os.environ, WEINGAERTEN_HOME=HOME, PYTHONIOENCODING="utf-8")
        start = time.time()
        try:
            done = subprocess.run([sys.executable, os.path.join(SCRIPTS, name)], cwd=HOME, env=env,
                                  capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TIMEOUT)
            lines = [line for line in (done.stdout + "\n" + done.stderr).splitlines() if line.strip()]
            status = "ok" if done.returncode == 0 else "fehler"
            message = lines[-1].strip() if lines else ""
        except subprocess.TimeoutExpired:
            status, message = "fehler", "Timeout nach %d s" % TIMEOUT
        return {"name": name, "level": TestRunner.level_of(name), "status": status,
                "seconds": round(time.time() - start, 1), "message": message[:300]}

    def run(self) -> int:
        """Run the selection, write the result file and return the process exit code."""
        names = self.selected()
        web_up = any(self.level_of(n) == "web" for n in names) and self.server_up()
        results = []
        for name in names:
            if self.level_of(name) == "web" and not web_up:
                result = {"name": name, "level": "web", "status": "übersprungen", "seconds": 0.0,
                          "message": "kein Server auf Port 8008"}
            else:
                result = self.run_one(name)
            results.append(result)
            print("%-13s %-30s %6.1f s  %s" % (result["status"], name, result["seconds"], result["message"][:80]))
        record = {"time": datetime.datetime.now().isoformat(timespec="seconds"),
                  "selection": self._only or self._level or "alle", "results": results}
        with open(RESULT_FILE, "w", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False, indent=1)
        self.keep_history(record)
        failed = sum(1 for r in results if r["status"] == "fehler")
        print("%d Tests, %d fehlgeschlagen -> %s" % (len(results), failed, RESULT_FILE))
        return 1 if failed else 0

    @staticmethod
    def keep_history(record: Dict[str, Any]) -> None:
        """Store the run as test_history\\<YYYYMMDD-HHMMSS>.json and delete runs older than HISTORY_DAYS."""
        os.makedirs(HISTORY_DIR, exist_ok=True)
        stamp = datetime.datetime.fromisoformat(record["time"])
        with open(os.path.join(HISTORY_DIR, stamp.strftime("%Y%m%d-%H%M%S") + ".json"), "w", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False)
        limit = stamp - datetime.timedelta(days=HISTORY_DAYS)
        for name in os.listdir(HISTORY_DIR):
            try:
                old = datetime.datetime.strptime(name, "%Y%m%d-%H%M%S.json")
            except ValueError:
                continue
            if old < limit:
                os.remove(os.path.join(HISTORY_DIR, name))


def main() -> int:
    """Parse the arguments and run the tests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--level", default="", choices=("",) + LEVELS + ("check", "smoke", "scen"))
    parser.add_argument("--only", default="")
    parser.add_argument("--home", default="original", choices=("original", "testhaus"))
    args = parser.parse_args()
    return TestRunner(args.level, args.only, args.home).run()


if __name__ == "__main__":
    sys.exit(main())
