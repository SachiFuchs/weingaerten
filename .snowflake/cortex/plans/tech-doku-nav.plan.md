# Plan: Technische Dokumentation (Tech.Doku)

## Context
- Menü: `MENU` in [code/weingaerten_web/constants.py](code/weingaerten_web/constants.py). Routing: `PageRegistry._pages` in [code/weingaerten_web/rendering/page_registry.py](code/weingaerten_web/rendering/page_registry.py). Die einfachste Vorlage ist [code/weingaerten_web/pages/doku_page.py](code/weingaerten_web/pages/doku_page.py).
- Der Code wird aus der Spezifikation erzeugt. Deshalb muss jede Änderung zuerst in [weingaerten-web.md](weingaerten-web.md) unter "Server specification" stehen (Routen, Code structure, Step 5 checks, Doku-Tabelle). Danach wird der Code neu generiert und der Hash neu geschrieben.
- Einen Tree-View gibt es noch nicht. Wiederverwendbar ist das Zwei-Spalten-Layout mit Split-Bar aus [katalog_layout.js](code/weingaerten_web/static/katalog_layout.js).
- Den Markdown-Renderer gibt es schon (`doc/markdown_renderer.py`): Überschriften #–###, Listen, Tabellen und Code.
- Der Abschnitt "Architektur / Code-Struktur" steht heute in [weingaerten-doku.md](weingaerten-doku.md) (Z. 159-200). Er zieht in die Tech.Doku um, in der Benutzer-Doku bleibt ein Verweis.

## Struktur
| nav "Tech.Doku" | tree-view (links, einklappbar) | doku-page (rechts) |

Die URL ist `/techdoku?node=<id>`. Ohne JavaScript wird die Seite vom Server gerendert. Ein Klick im Baum lädt die Seite neu, oder es wird nur der rechte Bereich ausgetauscht, wenn das per fetch einfach geht.

## Baum (mit den ergänzten Teilen, markiert mit *)
- Einführung (Motivation, Ziele, Begriffe*)
- Struktur der Anwendung (Ordner, Datenfluss catalog -> core -> web)
- *Dokumentationsdateien (*.md)*: Erklärung jeder .md-Datei
  - weingaerten-core.md: Spezifikation des Core-Pakets, aus der der Code generiert wird
  - weingaerten-web.md: Spezifikation von Server und Library
  - weingaerten-doku.md: Benutzerdokumentation (/doku)
  - weingaerten-techdoku.md: diese technische Dokumentation (neu)
  - skills/clean-code.instructions.md: Coding-Regeln
  - people/dilbert.md: Persona und Agent-Regeln
  - .snowflake/cortex/plans/*.plan.md: Umsetzungspläne
  - README.md
  - Spec-Mechanismus: Abschnitt hashen, Code als Cache, Exception list, rehash
- Architektur (Mermaid-artige Diagramme als Text/SVG, Ablauf eines Requests)
- Konzept Core und Web
  - Core (command_handler, Befehle, Modell, Berechnung, Validierung)
  - Web (Server, Seiten, Rendering, static JS)
- *Datenmodell / Katalog* (JSON-Schemas, Typen, IDs)
- Sicherheit (nur localhost, Host/Origin-Prüfung, Größenlimit, Eingabe-Regex, Whitelists, Fehlerbehandlung)
- Schnittstellen (Tabelle der API_COMMANDS: Route, Core-Befehl, Argumente, Antwort und Fehler; Core-Command-JSON)
- Entwicklungsrichtlinien (Clean-Code-Limits, eine Klasse pro Modul, Logger, englische JSON-Keys, Spec-first-Workflow)
- *Build, Start und Test* (start.cmd, WEINGAERTEN_HOME, check_*/smoke_*, Baseline-Vergleich)
- Code
  - Scripte (Tabelle: Datei, Zweck; automatisch aus dem Docstring bzw. der ersten Kommentarzeile)
  - Core (Klassendiagramm)
    - Klassen: eine Seite pro Klasse mit Datei, Zeilen, Beschreibung (warum und wofür), öffentlichen Methoden und Attributen
  - Web (Klassendiagramm)
    - Klassen (wie bei Core)
    - Web Parts (*.js): Datei, Zeilen, Zweck, exportierte Funktionen
- *Glossar*

## Generierung des Code-Teils
Die Seiten unter "Code" entstehen beim Aufruf automatisch, damit sie nicht veralten. Dafür gibt es eine neue Klasse `doc/code_inspector.py`:
- Python-Module werden mit `ast` gelesen, ohne Import: Klasse, Docstring als Beschreibung, öffentliche Methoden mit Signatur, Attribute aus `self.x =` in `__init__` sowie Modulkonstanten, Zeilenzahl.
- JS-Dateien werden per Regex gelesen: Kopfkommentar, `function`- und `export`-Namen, Zeilen.
- Das Klassendiagramm wird als SVG erzeugt. Es zeigt die Klassen als Kästen, gruppiert nach Unterpaket, mit Pfeilen für Abhängigkeiten aus den `import`s. Die SVG-Hilfen aus plan/ dienen als Vorbild. Es gibt keine externe Bibliothek.
- Fehlende Docstrings werden als "(keine Beschreibung)" markiert und als TODO-Liste ausgegeben. Optional werden sie in der Spec nachgetragen.

Die Prosa-Teile stehen in `weingaerten-techdoku.md`. Jede `##`-Überschrift ist ein Knoten, `###` ein Unterknoten. Für die Code-Knoten gibt es Platzhalter wie `<!-- code:core -->`.

## Implementation steps
1. Spec [weingaerten-web.md](weingaerten-web.md) erweitern: Route `/techdoku`, MENU-Eintrag "Tech.Doku" nach "Doku", die neuen Klassen `pages/techdoku_page.py`, `doc/doc_tree.py` (md -> Baum), `doc/code_inspector.py`, `doc/class_diagram_svg.py`, `static/techdoku.js` (Auf- und Zuklappen, Zustand in localStorage, Split-Bar), CSS, Step 5 checks.
2. `weingaerten-techdoku.md` mit allen Prosa-Kapiteln schreiben, einschließlich der Erklärung der .md-Dateien. Den Architektur-Teil aus weingaerten-doku.md hierher verschieben und dort einen Verweis lassen.
3. Den Web-Code aus der Spec neu generieren: constants, page_registry, die neuen Module, JS und CSS.
4. `check_clean_code.py` und `compileall` ausführen, danach `rehash_cache.py`.
5. Den Check in `scripts/check_web.py` ergänzen: /techdoku liefert 200, der Baum enthält alle Knoten, die Klassen-Seite von `PageLayout` zeigt Methoden, das SVG ist vorhanden.
6. Den Server stoppen, mit start.cmd neu starten und im Browser prüfen.

## Verification
- `python scripts/check_web.py`, `python scripts/check_clean_code.py`
- Im Browser: alle Baumknoten öffnen; die Klassen-Seiten zeigen Zeilen und Methoden; das Diagramm wird angezeigt; das Menü markiert "Tech.Doku" als aktiv.

## Critical Files
- weingaerten-web.md: Spec, die den Code bestimmt
- weingaerten-techdoku.md: neuer Inhalt
- code/weingaerten_web/constants.py: MENU
- code/weingaerten_web/rendering/page_registry.py: Route
- code/weingaerten_web/doc/code_inspector.py: neu, automatische Code-Doku
