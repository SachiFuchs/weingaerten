"""One-off patch: adds the `{{code:tests}}` generator (TestResultsPage) to weingaerten-web.md (CRLF kept)."""
import os

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "weingaerten-web.md")
ANCHOR = b"- **Browser scripts** (`{{code:js web}}`"
BULLET = (b"- **Test results** (`{{code:tests}}`, class `TestResultsPage`): reads `scripts\\test_results.json` written by "
          b"`scripts\\run_tests.py` (`{time, selection, results: [{name, level, status, seconds, message}]}`) on every call. "
          b"Shows a line `Lauf <time> (Auswahl <selection>): <n> Tests, <ok> bestanden, <fehler> fehlgeschlagen, <n> \xc3\xbcbersprungen` "
          b"and one table per level in the order `struktur`, `daten`, `web`, `fachlich` (heading = level title Struktur/Daten/Web/Fachlich) "
          b"with columns `Test | Status | Dauer (s) | Meldung`; status `ok` green `#1B7F3B`, `fehler` red `#C62828`, "
          b"`\xc3\xbcbersprungen` grey. File missing or not valid JSON \xe2\x86\x92 note `Noch kein Testlauf \xe2\x80\x93 python scripts\\run_tests.py ausf\xc3\xbchren`. "
          b"All values escaped; only this fixed path is read.\r\n")
MODULE_OLD = b"`script_page.py` (`ScriptPage`) |"
MODULE_NEW = b"`script_page.py` (`ScriptPage`), `test_results_page.py` (`TestResultsPage`) |"


def main() -> None:
    """Apply the patch once."""
    with open(PATH, "rb") as handle:
        data = handle.read()
    if b"{{code:tests}}" in data:
        print("already patched")
        return
    assert data.count(ANCHOR) == 1 and data.count(MODULE_OLD) == 1
    data = data.replace(ANCHOR, BULLET + ANCHOR).replace(MODULE_OLD, MODULE_NEW)
    with open(PATH, "wb") as handle:
        handle.write(data)
    print("patched")


if __name__ == "__main__":
    main()
