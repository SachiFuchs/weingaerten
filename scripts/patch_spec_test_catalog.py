"""One-off patch: adds the `{{code:testcases}}` and `{{code:testhistory}}` generators to weingaerten-web.md (CRLF kept)."""
import os

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "weingaerten-web.md")
ANCHOR = b"- **Browser scripts** (`{{code:js web}}`"
BULLETS = (
    b"- **Test cases** (`{{code:testcases}}`, class `TestCatalogPage`): the scripts of `scripts\\` that the runner executes "
    b"(`check_*`/`smoke_*` minus the exclusions, level rules shared via `TestResultsPage.level_of`) \xe2\x86\x92 table `Ebene | Tests | Voraussetzung`, "
    b"one child node per level (table `Test | Pr\xc3\xbcfungen | Letzter Lauf | Beschreibung`) and below it one lazy node per script "
    b"(title = name without `.py`): full docstring, table Datei/Ebene/Voraussetzung/Aufruf/Letzter Lauf and a table `Nr. | Zeile | Was gepr\xc3\xbcft wird` "
    b"of every call `check|chk|ok|expect|test(...)` found with `ast` (text = first string argument; `\"..\" % x` \xe2\x86\x92 the format string; "
    b"f-string unparsed; max 160 characters). The code is never executed.\r\n"
    b"- **Test history** (`{{code:testhistory}}`, class `TestHistoryPage`): every `scripts\\test_history\\<YYYYMMDD-HHMMSS>.json` "
    b"(same format as the result file; `run_tests.py` deletes runs older than 31 days) newest first \xe2\x86\x92 table "
    b"`Zeitpunkt | Auswahl | Tests | bestanden | fehlgeschlagen | \xc3\xbcbersprungen` and a matrix `Test \xc3\x97 last 15 runs` with \xe2\x9c\x93/\xe2\x9c\x97/\xe2\x80\x93 "
    b"in the status colours. No folder or no run \xe2\x86\x92 note `Noch keine Historie \xe2\x80\x93 python scripts\\run_tests.py ausf\xc3\xbchren`.\r\n")
MODULE_OLD = b"`test_results_page.py` (`TestResultsPage`) |"
MODULE_NEW = b"`test_results_page.py` (`TestResultsPage`), `test_catalog_page.py` (`TestCatalogPage`), `test_history_page.py` (`TestHistoryPage`) |"


def main() -> None:
    """Apply the patch once."""
    with open(PATH, "rb") as handle:
        data = handle.read()
    if b"{{code:testcases}}" in data:
        print("already patched")
        return
    assert data.count(ANCHOR) == 1 and data.count(MODULE_OLD) == 1
    data = data.replace(ANCHOR, BULLETS + ANCHOR).replace(MODULE_OLD, MODULE_NEW)
    with open(PATH, "wb") as handle:
        handle.write(data)
    print("patched")


if __name__ == "__main__":
    main()
