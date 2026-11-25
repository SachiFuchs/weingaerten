# Plan: Tech.Doku – Links, Quellcode-Popup (Pygments), Paket-Diagramme

## Context
- [code/weingaerten_web/doc/code_pages.py](code/weingaerten_web/doc/code_pages.py) erzeugt das HTML jeder Modulseite schon in der Schleife, in der die Knoten entstehen. Die Knoten-IDs der anderen Module sind dann noch unbekannt, deshalb ist "Verwendet" heute reiner Text.
- [code_inspector.py](code/weingaerten_web/doc/code_inspector.py) liest mit `ast`. Die Zeilenbereiche (`lineno`, `end_lineno`) der Klassen und Methoden sind damit verfügbar.
- **Pygments** (BSD-2, reines Python, keine Abhängigkeiten) ist lokal in Version 2.20.0 installiert (`%APPDATA%\Python\Python311\site-packages\pygments`).
- Die Spec erlaubt bisher nur die Standardbibliothek, mit three.js als einziger Ausnahme. Pygments braucht deshalb eine neue Ausnahme.
- `HtmlFormatter` schließt die Spans am Zeilenende. Die Ausgabe lässt sich daher zeilenweise zerlegen und über die `ast`-Bereiche in `<details>`-Blöcke legen.
- **Popup:** HTML-`<dialog>` mit `showModal()`; nur `Schließen` (`<form method="dialog">`) und Esc beenden es.

## Implementation steps
1. **Spec [weingaerten-web.md](weingaerten-web.md):**
   - **Exception list:** neue Zeile `4 | Vendored library Pygments 2.20.0 (BSD-2) | syntax highlighting of the source popup in /techdoku | Library specification | weingaerten_web\vendor\pygments\`.
   - **Hard rules:** Pygments ist neben three.js zugelassener Fremdcode. Es wird aus der lokalen Installation kopiert, wenn die Version passt, sonst einmal als Wheel von `files.pythonhosted.org` geladen. Die Prüfung erfolgt gegen die SHA-256 des Wheels. Es wird nie bearbeitet und zur Laufzeit nur aus `vendor\` geladen.
   - **Library specification:** Zeile Pygments mit Wheel-URL und SHA-256. Den Hash ermittle ich beim Umsetzen aus dem Wheel `pygments-2.20.0-py3-none-any.whl`.
   - **Step 1:** Pygments wie die Bibliothek prüfen und bereitstellen.
   - **Server specification:** `__main__` setzt `code\weingaerten_web\vendor` auf `sys.path`. Fehlt Pygments, zeigt das Popup den Code ungefärbt (escaped, mit Zeilennummern) und den Hinweis `Pygments fehlt – weingaerten-web ausführen`.
   - **`/techdoku`:**
     - Links in `Verwendet` sowie die neue Zeile `Wird verwendet von`.
     - Der Dateiname öffnet das Quellcode-Popup.
     - Unterpaket-Knoten mit Klassendiagramm und aufklappbarer Inhaltsliste.
     - Neue Module `doc/python_source_html.py` (`PythonSourceHtml`) und `doc/group_diagram_svg.py` (`GroupDiagramSvg`).
2. **Pygments bereitstellen:**
   - Kopie nach `code\weingaerten_web\vendor\pygments\` samt Lizenzdatei `vendor\pygments-LICENSE`.
   - Der SHA-256 des Wheels kommt in die Library specification.
   - `check_clean_code.py` muss `vendor\` auslassen, sonst prüft es fremden Code gegen unsere Regeln.
3. **Zwei Durchläufe in `CodePages._classes`:**
   - Durchlauf 1 legt alle Knoten an und füllt `module -> node_id`.
   - Danach entsteht der Rückwärts-Index `used_by`.
   - Durchlauf 2 erzeugt das HTML der Modulseiten mit Links.
   - Ziele ohne eigenen Knoten bleiben reiner Text.
4. **`PythonSourceHtml`:**
   - `pygments.highlight(code, PythonLexer(), HtmlFormatter(nowrap=True))` färbt den Code; das Ergebnis wird an Zeilenenden zerlegt.
   - Die Zeilen kommen mit Zeilennummern in die Ausgabe; die `ast`-Bereiche von Klassen und Funktionen (auch verschachtelt) werden `<details open>`-Blöcke, die Kopfzeile ist die `summary`.
   - Knöpfe `Alle aufklappen` / `Alle zuklappen`.
   - Das Stylesheet kommt aus `HtmlFormatter().get_style_defs('.tdsrc')`, einmal erzeugt und inline eingebettet.
   - Fallback ohne Pygments: `html.escape` je Zeile.
   - Das Pygments-HTML wird nicht weiter verändert. Pygments escaped selbst; die Eingabe ist ohnehin nur eigener Code.
5. **`ModulePage`:**
   - `Datei` wird ein Link mit `data-src`.
   - Dazu kommt `<dialog class="tdsrc">` mit dem Dateinamen, `Schließen` und dem Code (scrollbar, max. 90 vw × 85 vh).
   - Eine Zeile `Wird verwendet von` kommt dazu.
6. **`GroupDiagramSvg`** für Unterpaket-Knoten (z. B. `compute`):
   - Klassenkästen im Raster (4 Spalten), Pfeile für Importe innerhalb des Unterpakets.
   - Rechts gestrichelt die benutzten Module anderer Unterpakete.
   - Die Kästen verlinken auf die Modulseiten; beim Überfahren werden ihre Pfeile hervorgehoben.
7. **Inhaltsliste je Unterpaket:**
   - Je Modul ein `<details>`; die Zusammenfassung zeigt Klasse, Zeilen und Beschreibung.
   - Aufgeklappt: Methoden mit Kurzbeschreibung und Link.
   - Knöpfe `Alle aufklappen` / `Alle zuklappen`.
8. **`techdoku.js` und CSS:**
   - JS: Dialog öffnen, Aufklapp-Knöpfe, Pfeile hervorheben. Alles über DOM-APIs, ohne `innerHTML`.
   - CSS: Zeilennummern, Dialog und `::backdrop`, Hervorhebung.
9. **`check_web.py`:**
   - Die Seite von `LiningGeometry` verlinkt auf die von `WallData`.
   - Die Seite von `WallData` zeigt `Wird verwendet von` mit Link auf `LiningGeometry`.
   - Die Modulseite enthält `<dialog`, Pygments-Klassen (z. B. `class="k"`) und `<details`.
   - Der Knoten `code-core-klassen-compute` enthält `<svg` und `<details`.
10. **Abschluss:** `check_clean_code.py` und `rehash_cache.py` laufen lassen, Server neu starten, `check_web.py` ausführen, im Browser prüfen. Die Tech.Doku-Seite "Sicherheit / AAA" bekommt bei "SCA / CVE" den Eintrag Pygments 2.20.0 als zweite feste, per Hash geprüfte Abhängigkeit.

## Sicherheit
- Pygments ist fest auf eine Version gepinnt und per SHA-256 geprüft; das Laden erfolgt nur aus `vendor\`.
- Gezeigt werden nur Dateien, die der Inspector selbst gefunden hat, nie Pfade aus der Anfrage.
- Der Code wird nur gelesen und gefärbt, nie ausgeführt.

## Verification
- `python scripts/check_web.py` bestanden, abgesehen vom bekannten veralteten Check `w-south`.
- `python scripts/check_clean_code.py` ohne Befund, `vendor\` ausgenommen.
- Im Browser: `LiningGeometry` → Link `compute.wall_data` → `WallData` zeigt `Wird verwendet von` mit Links.
- Im Browser: Der Klick auf die Datei öffnet das Popup mit Pygments-Farben; Klassen und Methoden lassen sich ein- und ausklappen; es schließt nur über `Schließen` oder Esc.
- Im Browser: `compute` zeigt das Diagramm und die aufklappbare Liste.

## Critical Files
- weingaerten-web.md: Exception #4, Library specification, /techdoku
- code/weingaerten_web/doc/code_pages.py: zwei Durchläufe, Rückwärts-Index, Unterpaket-Inhalt
- code/weingaerten_web/doc/python_source_html.py: neu, Pygments mit aufklappbaren Blöcken
- code/weingaerten_web/doc/group_diagram_svg.py: neu, Diagramm je Unterpaket
- code/weingaerten_web/static/techdoku.js: Dialog, Aufklappen, Hervorheben
