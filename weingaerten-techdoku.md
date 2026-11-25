# Technische Dokumentation – Haus Weingärten

## Einführung

**Motivation:** Haus Weingärten ist ein Experiment. Ein echtes Haus (Wände mit allen Schichten, Öffnungen, Decken, Dach, Mengen) wird als Datenmodell beschrieben. Den Code schreibt kein Mensch: Er wird von einem KI-Agenten aus Markdown-Spezifikationen („non-code programs“) erzeugt. Die Spezifikation ist das Programm, der Code nur ein Cache davon.

Ziele:

- Das Haus als prüfbares Modell: Katalog (Materialien, Aufbauten, Bauteile, Klassen, Firmen) und Geschosse (Wände, Räume, Öffnungen) in JSON.
- Daraus Geometrie, 3D-Ansicht, Grundriss, Wandansichten und Mengen berechnen.
- Zeigen, dass ein Programm vollständig aus einer verständlichen Beschreibung entstehen und reproduzierbar neu erzeugt werden kann.

Begriffe:

| Begriff | Bedeutung |
|---|---|
| Spezifikation / Prompt | Markdown-Datei, die ein Programm beschreibt (`weingaerten-core.md`, `weingaerten-web.md`) |
| Exception list | Liste der Teile, für die überhaupt Code erzeugt werden darf |
| Cache / Hash | SHA-256 des Spezifikationsabschnitts; stimmt er nicht, wird der Code neu erzeugt |
| Core | Paket `weingaerten_core`: lädt, prüft und rechnet das Modell |
| Web | Paket `weingaerten_web`: lokaler Web-Server, nur Anzeige und Formulare |
| Ref | Verweis auf ein Katalog-Element, z. B. `material:hollow-brick` |

## Fachliches Modell

{{code:userdoc}}

## Struktur der Anwendung

| Ordner / Datei | Inhalt |
|---|---|
| `weingaerten-core.md`, `weingaerten-web.md` | die Spezifikationen (Programme) |
| `weingaerten-doku.md`, `weingaerten-handbuch.md`, `weingaerten-techdoku.md` | fachliches Modell, Benutzerhandbuch, technische Dokumentation |
| `catalog\` | Katalog als JSON: `materials`, `assemblies`, `components`, `classes`, `companies`, `tga-classes`, `tga-components`, `photos`, `schema` (JSON-Schemas), `reference`, `imported_*` |
| `house\storeys\` | ein JSON pro Geschoss: Wände, Räume, Öffnungen, Decken, Dach … |
| `code\weingaerten_core\` | generierter Core |
| `code\weingaerten_web\` | generierter Web-Server mit `static\` (Seitenrahmen, CSS, Browser-Skripte) und `lib\` (three.js) |
| `code\.hash\` | Hash je Paket (Cache-Schlüssel) |
| `scripts\` | Prüf-, Smoke-, Import- und Refactoring-Skripte |
| `skills\` | Regeln für den Agenten (Clean Code) |
| `start.cmd` | startet den Server mit `WEINGAERTEN_HOME` |

Datenfluss: `catalog\` + `house\` → Core (laden, prüfen, rechnen) → JSON-Antwort → Web (HTML, SVG, 3D) → Browser. Änderungen aus dem Browser gehen als POST an den Web-Server, der sie als Befehl an den Core gibt; nur der Core schreibt Dateien.

## Dokumentationsdateien (*.md)

Alle Markdown-Dateien des Projekts und ihre Rolle:

| Datei | Art | Zweck |
|---|---|---|
| `weingaerten-core.md` | Spezifikation (Programm) | Beschreibt den Core: Datenmodell, Prüfregeln, Geometrie, Befehle. Abschnitt `## Core specification` ist die Quelle des Pakets `weingaerten_core`. |
| `weingaerten-web.md` | Spezifikation (Programm) | Beschreibt Server, Seiten, Layout, API und Sicherheit. `## Server specification` erzeugt `weingaerten_web`, `## Library specification` beschreibt three.js (Version, URL, SHA-256). |
| `weingaerten-doku.md` | Dokumentation | fachliches Modell (Referenzkette, Klassen, Öffnungen, Regeln, KG 300/400, IFC), angezeigt im Knoten **Fachliches Modell** dieser Seite. |
| `weingaerten-handbuch.md` | Dokumentation | Benutzerhandbuch (Bedienungsanleitung), eigener Menüpunkt `/handbuch` mit Baum; `/doku` leitet dorthin um. |
| `weingaerten-techdoku.md` | Dokumentation | diese technische Dokumentation, angezeigt unter `/techdoku`; der Teil „Code“ wird beim Aufruf aus dem Quellcode erzeugt. |
| `skills\clean-code.instructions.md` | Agenten-Regel | Clean-Code-Regeln für jeden generierten Python-Code (gilt für `**/*.py`). |
| `people\dilbert.md` | Daten-Prompt | Personendaten aus dem Schwesterprojekt „Dilbert“ (Vorlage des Hausmodells); in Weingärten nicht ausgeführt. |
| `.snowflake\cortex\plans\*.plan.md` | Umsetzungspläne | je Änderungswunsch ein Plan (Kontext, Schritte, Prüfung); Historie der Entwicklung. |
| `README.md` | Hinweis | Kurzbeschreibung des Repositorys. |

### Dateien im Einzelnen

Je Markdown-Datei (Projektordner, `skills\`, `people\`) ein Unterknoten mit Titel, Beschreibung und allen Abschnitten (`#` … `####`, mit Zeilenbereich). Ein Klick auf den Dateinamen öffnet den Quelltext mit Farben, jeder Abschnitt ist aufklappbar. Erzeugt bei jedem Aufruf aus den Dateien.

{{code:mdfiles}}

### Wie eine Spezifikation Code erzeugt

1. Der Agent liest die Spezifikation (z. B. `weingaerten-web.md`) und berechnet den SHA-256 des Abschnitts `## Server specification` (Zeilenenden `\n`).
2. Stimmt der Hash mit `code\.hash\weingaerten_web.sha256` überein, wird der vorhandene Code benutzt (`cache=hit`).
3. Sonst erzeugt der Agent das ganze Paket neu, prüft es mit `python -m compileall` und den Größenregeln und schreibt erst dann den Hash.
4. Code darf nur für Einträge der **Exception list** entstehen; alles andere erledigt der Agent mit Werkzeugen.

Folge: Jede gewünschte Code-Änderung muss zuerst in die Spezifikation. Nach einer Handänderung am Code gleicht `scripts\rehash_cache.py` die Hashes ab.

### Aufbau einer Spezifikation

| Abschnitt | Inhalt |
|---|---|
| Kopf (YAML) | Name, Beschreibung, Aufruf |
| `## Documentation` | Zweck, Adresse, Inhalt, Grenzen, Abhängigkeiten |
| `## Exception list` | erlaubter Code und seine Quelle |
| `## Code folder`, `## Hard rules` | Ablageort, Cache-Regeln, Verbote |
| `## Step 1 … 6` | Ablauf: Abhängigkeiten, Cache prüfen, erzeugen, starten, prüfen, melden |
| `## … specification` | die fachliche Beschreibung, aus der der Code entsteht (endet mit **Code structure**) |

## Architektur

Zwei Pakete, klar getrennt: Der Core kennt kein HTML, der Web-Server kein Hausmodell.

| Schicht | Paket | Aufgabe |
|---|---|---|
| Daten | `catalog\`, `house\` | JSON-Dateien, geprüft mit JSON-Schemas |
| Fachlogik | `weingaerten_core` | laden, prüfen, Referenzen auflösen, Geometrie und Mengen rechnen, Änderungen schreiben |
| Darstellung | `weingaerten_web` | HTTP-Server, Seiten, SVG, Einbettung der Browser-Skripte |
| Browser | `static\*.js`, three.js | 3D-Ansicht, Editoren, Tooltips |

Ablauf eines Seitenaufrufs:

1. `RequestHandler.do_GET` prüft Umleitungen, Bibliothek, Fotos und fragt `PageRegistry`.
2. Die Seitenklasse fragt über `CoreClient.ask` den Core (`HOUSE`, `CATALOG`, `BOM` …).
3. `CommandHandler` holt das Modell aus dem `ModelCache`; bei geänderten Dateien lädt `ModelLoader` neu und `ModelComputer` rechnet jedes Geschoss.
4. Die Seite baut HTML/SVG, `PageLayout` setzt den Rahmen mit Menü darum.

Ablauf einer Änderung: Browser → `POST /api/...` → `PostRequestReader` (Sicherheit) → `ApiArguments` (Argumente) → `ApiRouter` → Core-Befehl. Der Core rechnet die Änderung an einer Kopie und schreibt nur, wenn keine neuen Fehler entstehen (`JsonFileWriter`, atomar über eine temporäre Datei).

## Konzept Core und Web

Der Core ist eine Bibliothek mit genau einem Einstieg: `handle(command_json) -> answer_json`. Der Web-Server importiert ihn einmal beim Start und ruft ihn pro Anfrage auf. Dadurch sind beide Teile einzeln testbar, und der Core könnte auch von einem anderen Frontend benutzt werden.

### Core

Der Core (`weingaerten_core`) kennt kein HTTP und kein HTML. Er liest die JSON-Dateien unter `WEINGAERTEN_HOME` (`catalog\`, `house\`), rechnet daraus das ganze Haus und beantwortet Befehle. Er hat genau eine öffentliche Funktion:

```
weingaerten_core.handle(command_json: str) -> str      # JSON rein, JSON raus
```

#### Bausteine

```
                 handle(command_json)
                         |
                  +--------------+
                  |CommandHandler|  JSON parsen, Befehl prüfen, verteilen
                  +--------------+
                   |            |
         Lesebefehl|            |Schreibbefehl
                   v            v
            +---------+    +-----------+     +--------------------+
            | queries |    |  editing  |---->| StoreyChangeCheck  |
            +---------+    +-----------+     | (Kopie rechnen,    |
                   |            |            |  Fehler vergleichen)|
                   v            v            +--------------------+
              +------------------------+               |
              |  ModelCache (+ Lock)   |<--invalidate--+-- JsonFileWriter
              +------------------------+                   (atomar schreiben)
                         | geänderte Dateien?
                         v
          ModelLoader ---> ModelComputer ---> berechnetes Modell
          (Dateien lesen)  (validation, compute, geometry)
```

| Unterpaket | Aufgabe | wichtige Klassen |
|---|---|---|
| `command_handler.py` | Einstieg, Verteilung, Fehler → `{"error": …}` | `CommandHandler` |
| `model` | Dateien lesen, Cache nach Änderungszeit, Fehlerliste | `ModelLoader`, `ModelCache`, `IssueLog` |
| `validation` | JSON-Schemas (eigener Validator) und fachliche Regeln | `SchemaValidator`, `ElementValidator`, `ConnectionValidator` |
| `compute` | das berechnete Haus | `ModelComputer`, `StoreyBuilder` und je Bauteilart ein `…Builder` |
| `geometry` | 2D-Vektoren, Polygone, Polylinien, Prismen | `Vector2D`, `Polygon`, `OrthoPolygon`, `Polyline`, `SegmentPrism` |
| `queries` | Lesebefehle | `HouseSummary`, `CatalogLister`, `ReferenceResolver`, `BillOfMaterials`, `UsageFinder`, `TgaCatalog` |
| `editing` | Schreibbefehle mit Prüfung an einer Kopie | `ElementEditor`, `OpeningEditor`, `LiningEditor`, `WallsEditor`, `RoomEditor`, `PartEditor`, `StoreyChangeCheck`, `JsonFileWriter` |

#### Befehle

| Art | Befehl | Klasse | Antwort |
|---|---|---|---|
| Lesen | `HOUSE` | `HouseSummary` | `{id, name, unit, valid, errors, bbox, foundation, storeys, materials, assemblies, components}` |
| Lesen | `CATALOG` (`type?`, `full?`) | `CatalogLister` | Elemente eines Typs |
| Lesen | `ELEMENT` / `RESOLVE` (`ref`) | `CatalogLister` / `ReferenceResolver` | ein Element roh bzw. mit aufgelösten Referenzen |
| Lesen | `USAGE` (`ref` oder `all`) | `UsageFinder` | wer ein Element verwendet |
| Lesen | `BOM` | `BillOfMaterials` | Stückliste / Mengen |
| Lesen | `TGA_CATALOG` | `TgaCatalog` | TGA-Klassen, -Bauteile, Verbindungsregeln |
| Lesen | `VALIDATE` | `CommandHandler` | `{ok, errors, warnings, counts}` (geht auch ohne `WEINGAERTEN_HOME`) |
| Schreiben | `SAVE`, `DELETE` | `ElementEditor` | Katalogelement in `catalog\…` |
| Schreiben | `OPENING_SAVE`, `OPENING_DELETE` | `OpeningEditor` | Öffnung einer Wand |
| Schreiben | `LINING_SAVE`, `LINING_DELETE` | `LiningEditor` | Innendämmung einer Wand |
| Schreiben | `WALLS_SAVE` | `WallsEditor` | Wände/Räume/Höhe eines Geschosses |
| Schreiben | `ROOM_SAVE`, `ROOM_DELETE` | `RoomEditor` | Raum mit Belägen |
| Schreiben | `SHAFT_SAVE`, `SHAFT_DELETE` | `RoomEditor` | Schacht in `house\house.json` |
| Schreiben | `PART_SAVE`, `PART_DELETE` | `PartEditor` | Einbauteile (Elektro, Abwasser, Zuwasser) |

#### Ablauf Lesen (Beispiel `HOUSE`)

1. `handle('{"command": "HOUSE"}')` → `CommandHandler` parst das JSON; kein Objekt → `{"error": "invalid JSON"}`, unbekannter Befehl → `{"error": "unknown command"}`.
2. `ModelCache.model()` bildet unter dem Lock die Signatur aller JSON-Dateien (Pfad + Änderungszeit, `ModelLoader.file_signature`).
3. Signatur unverändert → das berechnete Modell aus dem Speicher wird benutzt (der Normalfall, schnell).
4. Signatur geändert → `ModelLoader.load()` liest alle Dateien neu (Dateifehler werden Modellfehler, keine Exception), `ModelComputer.compute()` rechnet:
   - jedes Element gegen Schema und Regeln prüfen, Dokumente, `house.json` und Geschossdateien prüfen, TGA-Verbindungen prüfen;
   - Fundament und Schächte vorbereiten;
   - je Geschoss `StoreyBuilder.build`: Wände → Ecken/Schichtstücke → Öffnungen → Umriss → Räume → Böden, Beläge, Heizung → Decken, Tragwerk, Treppen, Lichtschächte, Dach, Fassade, Innendämmung;
   - hausweit Abwasser, Zuwasser, Elektro, Einbauteile; doppelte Raumnummern.
   Alle Meldungen landen über `IssueLog` in `errors`/`warnings` mit `where` (z. B. `storey:ground.w3`).
5. `HouseSummary(model).build()` stellt die Antwort zusammen; `JsonValues.rounded` rundet Zahlen, `json.dumps` liefert den Text.

Ein ungültiges Modell wird trotzdem ausgeliefert (`valid: false`, Fehlerliste); der Web-Teil zeigt dann das rote Banner.

#### Ablauf Schreiben (Beispiel `OPENING_SAVE`)

```
Anfrage                         OpeningEditor              StoreyChangeCheck            Datei
  |  {storey, wall, opening}         |                            |                       |
  |--------------------------------->| Modell aus Cache           |                       |
  |                                  | Geschoss tief kopieren     |                       |
  |                                  | Öffnung einsetzen/ersetzen |                       |
  |                                  |--- new_errors(kopie) ----->| Dateien neu laden,    |
  |                                  |                            | Kopie einsetzen,      |
  |                                  |                            | ModelComputer rechnen |
  |                                  |<-- neue Fehler ------------| Fehler vorher/nachher |
  |                                  |                            |                       |
  |   neue Fehler? -> {error, errors}|                            |                       |
  |<---------------------------------|                            |                       |
  |   sonst                          |--- write(kopie) ---------->|-- Lock, atomar ------>| storeys\ground.json
  |                                  |                            |   Cache invalidieren  |
  |<-- {storey, wall, opening, warnings}                          |                       |
```

Beispiel-Anfrage (Maße in Metern, so wie gespeichert):

```
{"command": "OPENING_SAVE", "storey": "ground", "wall": "w3", "create": true,
 "opening": {"id": "f-kueche", "...": "Lage, Breite, Höhe, Brüstung, Bauteil-Ref"}}
```

Mögliche Antworten:

```
{"storey": "ground", "wall": "w3", "opening": {...}, "warnings": [...]}      # gespeichert
{"error": "existiert bereits: f-kueche"}                                      # Id schon im Geschoss
{"error": "unbekannt: Wand w9"}                                               # Wand fehlt
{"error": "<erste neue Meldung>", "errors": ["storey:ground.w3: ...", ...]}   # abgelehnt, nichts geschrieben
```

Regeln aller Schreibbefehle:

- **Nur neue Fehler zählen.** Verglichen wird die Menge `(where, message)` vorher und nachher. Ein schon ungültiges Modell bleibt also bearbeitbar, solange die Änderung nichts verschlechtert. Warnungen lehnen nie ab.
- **Ganze Objekte.** Der Aufrufer schickt das vollständige Objekt (Öffnung, Raum, Element); der Core ersetzt es als Ganzes.
- **Ids** werden mit `ID_RE` geprüft, bevor sie in Dateinamen oder Listen gelangen.
- **Schreiben** geschieht unter `ModelCache.lock` über `JsonFileWriter` (temporäre Datei, dann umbenennen) und setzt die Cache-Signatur zurück; der nächste Befehl rechnet neu.
- Die Prüfung an der Kopie läuft außerhalb des Locks; zwei gleichzeitige Änderungen am selben Geschoss werden nicht abgeglichen – die zuletzt geschriebene gilt.

#### Fehlerbehandlung

| Fall | Antwort |
|---|---|
| kein gültiges JSON / kein Objekt | `{"error": "invalid JSON"}` |
| unbekannter Befehl | `{"error": "unknown command"}` |
| `WEINGAERTEN_HOME` nicht gesetzt | `{"error": "WEINGAERTEN_HOME nicht gesetzt"}` |
| fachlicher Fehler (Ref unbekannt, Id ungültig, neue Modellfehler) | `{"error": …, "errors?": […]}` |
| unerwartete Exception | `{"error": "interner Fehler: <Typ>"}`, Stacktrace nur im Log |

#### Nutzung ohne Web

```
set WEINGAERTEN_HOME=C:\Development\weingaerten
python -c "import weingaerten_core as c; print(c.handle('{\"command\": \"VALIDATE\"}'))"
```

So arbeiten auch die Smoke-Tests (`scripts\smoke_*.py`) und der Refactoring-Vergleich (`refactor_baseline.py`).

### Web

- `WebApplication` verdrahtet `ServerSettings`, `CoreClient`, `StaticAssets`, `PageLayout`, `PageContext`, `PageRegistry`.
- `server`: HTTP auf `127.0.0.1` und `[::1]`, GET-Seiten, POST-API mit Sicherheitsprüfungen.
- `rendering`: Seitenrahmen, Escaping, deutsche Zahlen, Geschosswahl.
- `pages`: eine Klasse pro Seite.
- `plan`: das Grundriss-SVG.
- `doc`: Markdown-Teilmenge, Baum und Code-Doku dieser Seite.
- `static`: Browser-Code, beim Start gelesen und inline eingebettet; keine externen Ressourcen außer three.js aus `/lib/`.

#### Aufbau einer Seite

Jede Seite ist **eine vollständige HTML-Antwort** des Servers (kein Single-Page-Framework, kein Template-System, kein Build-Schritt). Sie entsteht in vier Teilen:

| Teil | Woher | Inhalt |
|---|---|---|
| Rahmen | `static\page.html` über `PageLayout.render` | `<head>` mit Titel, Favicon, `style.css` inline; Kopfzeile mit Logo und Menü-Schalter; Menü aus `MENU`; rotes Banner „Modell ungültig“, wenn der Core Fehler meldet |
| Gerüst | Seitenklasse in `pages\` (z. B. `WaendePage.render`) | statisches HTML mit leeren Containern und festen Ids (`#katlist`, `#wallsvg`, `#oppanel` …) |
| Daten | Core-Antwort, z. B. `core.ask("HOUSE")` | als `<script type="application/json" id="…">` eingebettet (`HtmlTools.embed_json`, `<` → `\u003c`); Ids: `house`, `plandata`, `wanddata`, `raumdata`, `katdata` |
| Verhalten | `static\*.js` über `StaticAssets` | als `<script>…</script>` inline angehängt; 3D-Teile als `<script type="module">` mit Import-Map auf `/lib/three.module.js` |

Zwei Arten von Seiten:

- **Serverseitig fertig** – `/grundriss`, `/mengen`, `/handbuch`, `/techdoku`, `/about`: HTML und SVG (`plan\PlanSvg`) entstehen komplett in Python; JavaScript ergänzt nur Zoom, Tooltips und den Bearbeiten-Modus.
- **Im Browser gezeichnet** – `/haus3d`, `/waende`, `/raeume`, `/katalog/…`: der Server liefert Gerüst + Daten, das Skript liest beim Start `JSON.parse(document.getElementById('…').textContent)` und baut Listen, Formulare, SVG-Ansichten und die three.js-Szene selbst (Helfer `h()`/`sv()` aus `common.js`, Werte nur über `textContent`/`.value`).

#### HTML-Seiten

Alle GET-Seiten aus `PageRegistry`; jede bekommt den Rahmen aus `page.html`. Skripte werden in der genannten Reihenfolge inline eingebettet (`tip.js` = Tooltips, `common.js` = Helfer, in fast allen Seiten).

| URL | Klasse | Art | Core-Befehle | Daten-Block | Skripte | Schreibt über |
|---|---|---|---|---|---|---|
| `/haus3d` | `Haus3dPage` | Browser (three.js) | `HOUSE` | `house` | `tip`, `detail3d`, `waste3d`, `water3d`, `electric3d`, `parts3d`, `room3d`, Modul `haus3d` | – (nur Anzeige) |
| `/grundriss?storey=&cut=` | `GrundrissPage` | Server-SVG + Editor | `HOUSE`, `CATALOG`, `RESOLVE` | `plandata` | `common`, `plan_zoom`, `plan`, `tip`, `plan_tooltips` | `/api/walls/save` |
| `/waende?storey=` | `WaendePage` | Browser | `HOUSE`, `CATALOG` (Elemente) | `wanddata` | `tip`, `common`, `front`, `katalog_layout`, `waende_layout`, `wand`, `lining`, `install`, `parts3d`, Modul `install3d` | `/api/opening/*`, `/api/lining/*`, `/api/part/save` |
| `/raeume?storey=` | `RaeumePage` | Browser | `HOUSE`, `CATALOG` (Elemente) | `raumdata` | `tip`, `common`, `katalog_layout`, `raum` | `/api/room/*`, `/api/shaft/*` |
| `/katalog/<slug>` (`materialien`, `aufbauten`, `klassen`, `bauteile`, `firmen`, `dokumente`) | `KatalogPage` | Browser | `CATALOG`, `HOUSE`, `USAGE` | `katdata` | `tip`, `common`, `front`, `katalog_layout`, `katalog_docs`, `katalog_ifc`, `katalog` | `/api/element/*` (Dokumente nur lesen) |
| `/katalog/tga` | `TgaKatalogPage` | Browser | `HOUSE`, `TGA_CATALOG` | `katdata` | `tip`, `common`, `katalog_layout`, `katalog_tga` | `/api/element/*` |
| `/mengen` | `MengenPage` | Server | `VALIDATE`, `BOM` | – | – | – |
| `/handbuch?node=` | `DocTreePage` | Server (Markdown) | – (liest `weingaerten-handbuch.md`) | – | `techdoku` | – |
| `/techdoku?node=` | `DocTreePage` | Server (Markdown + Code-Doku) | – (liest `weingaerten-techdoku.md` und Quellcode) | – | `techdoku` | – |
| `/about` | `AboutPage` | Server | – | – | – | – |
| sonst | `PageRegistry.render_not_found` | Server | – | – | – | 404 |

Seitenzustand außerhalb der Daten steht in der URL (`?storey=`, `?cut=`, `?node=`, `#<wand-id>`/`#edit`) und in `localStorage` (Menü ein/aus, Spaltenbreiten, gewähltes Katalogelement). Dadurch überlebt die Auswahl ein Neuladen.

#### Kommunikation Browser ↔ Server

Klassisches **AJAX mit `fetch` und JSON** – kein WebSocket, kein Server-Sent-Events, kein Polling. Der Server sendet nie von sich aus.

| Richtung | Mechanismus |
|---|---|
| Lesen beim Seitenaufruf | `GET /<seite>` → HTML mit eingebetteten Daten (ein Round-Trip, kein Nachladen) |
| Ändern | `post(url, body)` aus `common.js`: `fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)})`, Ergebnis `{ok, j}` |
| Nachladen ohne Seitenwechsel | `wand.js` und `raum.js` holen nach dem Speichern `POST /api/house` (`body: {}`) und zeichnen neu |
| Neuaufbau | übrige Editoren (`plan.js`, `katalog.js`, `katalog_tga.js`) setzen `location.hash` bzw. `localStorage` und rufen `location.reload()` – die Seite kommt frisch vom Server |
| Navigation | normale Links bzw. `location.href` (z. B. Geschosswahl, Klick auf ein Bauteil in 3D) |

Ablauf einer Änderung im Detail:

1. Benutzer ändert im Formular; das Skript prüft Eingaben vor Ort (`msg()` markiert Felder) und rechnet cm → m.
2. `post('/api/…', {…})` sendet das vollständige Objekt (z. B. Öffnung, Raum, Wandliste), nicht einzelne Felder.
3. Server: `PostRequestReader` (Host/Origin, `application/json`, ≤ 64 KB) → `ApiArguments` (Typen, Allowlist) → `ApiRouter` → Core-Befehl.
4. Core prüft an einer Kopie; nur ohne neue Fehler wird die JSON-Datei geschrieben.
5. Antwort `200` mit Ergebnis oder `400` mit `{error, errors?}`; der Browser zeigt Fehler am Formular bzw. als Liste, bei Erfolg Toast (`toast()`) und Neuaufbau wie oben.

Da jede Antwort aus dem aktuellen Datei-Stand kommt (`ModelCache` nach Änderungszeit), sehen auch andere offene Tabs nach einem Neuladen sofort die Änderung; ein gleichzeitiges Bearbeiten in zwei Tabs wird nicht abgeglichen (letzter Schreiber gewinnt).

## Datenmodell und Katalog

| Typ | Ordner | Beispiel-Ref |
|---|---|---|
| Material | `catalog\materials` | `material:hollow-brick` |
| Aufbau (Schichtfolge) | `catalog\assemblies` | `assembly:exterior-wall-ew1` |
| Klasse (Rezept + Parameter) | `catalog\classes` | `class:window-2` |
| Bauteil (Instanz einer Klasse) | `catalog\components` | `component:...` |
| Firma (Hersteller/Lieferant) | `catalog\companies` | `company:...` |
| Dokument (Rechnung/Angebot, nur Import) | `catalog\documents` | `document:2023-07-17-schuck-1783-schlussrechnung-dach` |
| Geschoss | `house\storeys` | `storey:ground` |

- JSON-Schlüssel immer Englisch, Texte für die Anzeige Deutsch.
- Längen in Metern gespeichert, im Browser in cm eingegeben.
- Ids: Kleinbuchstaben, Ziffern, `-` (`^[a-z0-9]+(-[a-z0-9]+)*$`).
- Jedes Element wird gegen sein Schema in `catalog\schema\` geprüft; Wände dürfen nur bekannte Felder haben (`additionalProperties: false`).

Die folgenden Unterseiten beschreiben die JSON-Struktur je Ordner `catalog\<ordner>\<id>.json`. Quelle ist jeweils das Schema `catalog\schema\<typ>.schema.json`; bei Abweichung gilt das Schema. **Pflichtfelder fett.**

### Gemeinsame Regeln

- Eine Datei = ein Element; Dateiname = `id` + `.json`; die Ref ist `<typ>:<id>` (z. B. `material:copper-sheet`).
- Alle Katalogschemas haben `additionalProperties: false` – unbekannte Felder sind ein Fehler.
- Verweise sind Refs als Text mit festem Präfix (`material:`, `company:`, `class:`, `tga-class:`, `document:`); der Core prüft, dass das Ziel existiert.
- Längen in Metern, Preise als Zahl mit `currency` (Standard `EUR`), Datum `JJJJ-MM-TT`.
- `photos`: Dateinamen (`.jpg|.jpeg|.png|.webp`) in `catalog\photos\<id>\`.
- `ifc` (bei Aufbau, Klasse, Bauteil, TGA-Klasse): `{entity, predefined_type?, object_type?}` für den IFC4-Export; vom Core nicht ausgewertet.
- `product` (bei Material, Bauteil, TGA-Komponente) hat überall dieselbe Form:

| Feld | Typ | Bedeutung |
|---|---|---|
| `manufacturer` | `company:` | Hersteller |
| `model`, `article_no`, `ean`, `url` | Text | Artikelangaben (`ean` nur Ziffern) |
| `details` | Objekt | Shop-Tabellen `product_data`, `dimensions_weight` = Liste `{label, value}` im Originaltext |
| `offers[]` | Liste | **`supplier`** (`company:`), **`price`** (≥ 0, je Verkaufseinheit), `currency`, `price_basis` (`net`/`gross`), `date`, `source` (Belegtext), `document` (`document:`) |

### materials – Material

`catalog\materials\*.json`, Schema `material.schema.json`, Ref `material:<id>`. Grundstoff einer Schicht oder gekaufter Artikel.

| Feld | Typ | Bedeutung |
|---|---|---|
| **`id`**, **`name`** | Text | Id und Anzeigename |
| **`category`** | Text | freie Kategorie (z. B. `Mauerwerk`, `Heizung`) |
| **`appearance`** | Objekt | **`color`** `#RRGGBB`, `roughness` 0–1, `hatch` (`none`, `plaster`, `masonry`, `concrete`, `insulation`, `wood`) |
| `description` | Text | |
| `conductivity` | Zahl/null | λ in W/(m·K) |
| `density` | Zahl/null | ρ in kg/m³ |
| `vapour_resistance` | Zahl/null | μ |
| `fire_class` | `A1`…`B3`/null | Baustoffklasse DIN 4102-1 |
| `values_source` | Text | Herkunft der Kennwerte |
| `imported_from[]` | Text | Dateien in `catalog\imported_material` (ohne `.json`) |
| `product` | Objekt | siehe *Gemeinsame Regeln* |
| `photos[]` | Text | |

```
{ "id": "weishaupt-wsb-8-a-rme-ai", "name": "Weishaupt Splitblock WSB 8-A-RME-AI",
  "category": "Heizung", "conductivity": null,
  "product": { "manufacturer": "company:weishaupt", "model": "WSB 8-A-RME-AI",
               "offers": [ { "supplier": "company:boehringer-heizungsbau", "price": 9701.47,
                             "price_basis": "net", "date": "2025-04-14",
                             "document": "document:2025-04-14-boehringer-25-0023-angebot-waermepumpe" } ] },
  "appearance": { "color": "#B87333", "roughness": 0.4, "hatch": "none" } }
```

### assemblies – Aufbau

`catalog\assemblies\*.json`, Schema `assembly.schema.json`, Ref `assembly:<id>`. Schichtfolge einer Wand, Decke, Bodenplatte, eines Dachs oder Belags.

| Feld | Typ | Bedeutung |
|---|---|---|
| **`id`**, **`name`** | Text | |
| **`category`** | Enum | `exterior_wall`, `interior_wall`, `base_slab`, `slab`, `roof`, `plinth`, `interior_lining`, `covering` |
| **`layer_order`** | Enum | Leserichtung der Schichten: `outside_in` (Außenwand), `left_right` (Innenwand), `top_down` (Platten, Dach), `wall_out` (Innendämmung, Beläge: Untergrund → Raum) |
| **`layers[]`** | Liste | **`material`** (`material:`), **`thickness`** (m, > 0), `direction` (`south_north`/`west_east`, Lattung), `heated` (Rohrebene Fußbodenheizung bzw. Plattenebene der Wandheizung), `cladding` (nur äußerste Schicht Außenwand: Stülpschalung `{board_length, board_width, overlap, bottom?, paint?, estimated?}`) |
| `din276` | `3xx` | Kostengruppe |
| `fire_rating` | Text | z. B. `REI90` |
| `impact_sound_lnw_db`, `airborne_sound_rw_db` | Zahl | Schallschutz (Override) |
| `waterproofing`, `white_tank` | Text, bool | nur `base_slab` |
| `visualization` | Objekt | `view`, `section`: `outer_layers`, `all_layers`, `solid` |
| `ifc`, `description`, `photos[]` | | |

```
{ "id": "covering-fliese-boden", "name": "Bodenbelag Fliese 33 × 33 im Dünnbett",
  "ifc": { "entity": "IfcCovering", "predefined_type": "FLOORING" },
  "category": "covering", "din276": "352", "layer_order": "wall_out",
  "layers": [ { "material": "material:mapei-flexmoertel-c2te-s1-5-kg", "thickness": 0.004 },
              { "material": "material:bodenfliese-leeds-blue-33x33", "thickness": 0.009 } ],
  "visualization": { "view": "all_layers", "section": "all_layers" } }
```

### classes – Bauteil-Klasse

`catalog\classes\*.json`, Schema `class.schema.json`, Ref `class:<id>`. Rezept für Bauteile: Zeichenform, Parameter und Materialrollen.

| Feld | Typ | Bedeutung |
|---|---|---|
| **`id`**, **`name`** | Text | |
| **`geometry`** | Enum | `window` (braucht `width`, `height`, `depth`, `frame_width`, `sashes`), `door` (wie window ohne `sashes`), `box`, `passage` (nur `width`, `height`) |
| **`opening_capable`** | bool | Vorgabe: Bauteile in Wandöffnungen einsetzbar |
| **`parameters[]`** | Liste | **`key`** (`a-z0-9_`), **`name`**, **`type`** (`length` in m, `number`, `choice`, `bool`), `default`, `min`, `max`, `options` (Pflicht bei `choice`), `required` |
| **`material_roles[]`** | Liste | **`key`**, **`name`**, `default` (`material:`) |
| `din276` | `3xx` | ohne Angabe aus der Wand abgeleitet |
| `ifc`, `description`, `photos[]` | | |

```
{ "id": "roof-part", "name": "Dachbauteil", "geometry": "box", "opening_capable": false, "din276": "360",
  "parameters": [ { "key": "width", "name": "Länge/Breite", "type": "length", "default": 1.0, "min": 0.01, "max": 200, "required": true },
                  { "key": "unit", "name": "Einheit", "type": "choice", "default": "pcs", "options": ["pcs", "m", "m2"] } ],
  "material_roles": [ { "key": "main", "name": "Material", "default": "material:copper-sheet" } ] }
```

### components – Bauteil

`catalog\components\*.json`, Schema `component.schema.json`, Ref `component:<id>`. Konkretes Bauteil einer Klasse (Fenster, Tür, Dachteil …), wird in Öffnungen und Bauteillisten verwendet.

| Feld | Typ | Bedeutung |
|---|---|---|
| **`id`**, **`name`** | Text | |
| **`class`** | `class:` | Klasse, deren Parameter gelten |
| **`opening_capable`** | bool | für Öffnungen geeignet |
| **`params`** | Objekt | `key` der Klassenparameter → Wert (Längen in m); geprüft gegen Typ, `min`/`max`, `options`, `required` der Klasse |
| **`materials`** | Objekt | `key` der Materialrolle → `material:` |
| `ifc` | Objekt | überschreibt die Klasse (z. B. Balkontür → `IfcDoor`) |
| `product`, `imported_from[]`, `description`, `photos[]` | | |

```
{ "id": "roof-eaves-flashing", "name": "Einlaufblech Kupfer, Zuschnitt bis 0,40 m",
  "class": "class:roof-part", "opening_capable": false,
  "params": { "width": 24.0, "height": 0.0007, "depth": 0.4, "quantity": 24, "unit": "m" },
  "materials": { "main": "material:copper-sheet" },
  "product": { "offers": [ { "supplier": "company:schuck-dach", "price": 38.9, "price_basis": "net",
                             "date": "2023-07-17", "document": "document:2023-07-17-schuck-1783-schlussrechnung-dach" } ] } }
```

### companies – Firma

`catalog\companies\*.json`, Schema `company.schema.json`, Ref `company:<id>`.

| Feld | Typ | Bedeutung |
|---|---|---|
| **`id`**, **`name`** | Text | |
| **`roles[]`** | Enum | mindestens eins: `manufacturer` (Hersteller), `supplier` (Lieferant) |
| `description`, `address`, `web`, `photos[]` | Text | |

```
{ "id": "pci-augsburg", "name": "PCI Augsburg GmbH", "roles": ["manufacturer"], "description": "PCI Augsburg GmbH" }
```

### documents – Beleg

`catalog\documents\*.json`, Schema `document.schema.json`, Ref `document:<id>`. Rechnung, Angebot, Auftragsbestätigung, Gutschrift oder Plan; im Browser nur lesbar, entsteht durch Import.

| Feld | Typ | Bedeutung |
|---|---|---|
| **`id`**, **`name`** | Text | Id = `<datum>-<firma>-<nummer>-<art>-<thema>` |
| **`doc_type`** | Enum | `invoice`, `quote`, `order_confirmation`, `credit_note`, `plan` |
| **`supplier`** | `company:` | Aussteller |
| **`date`** | Datum | |
| **`currency`** | Text | |
| **`items[]`** | Liste | **`description`**, `position`, `quantity`, `unit`, `unit_raw`, `unit_price`, `total_price`, `ref` (`material:`/`component:`/`tga-component:` der Position) |
| `number`, `customer_number`, `project`, `category`, `object`, `description` | Text | |
| `prices_are_net`, `items_gross` | bool | Preisbasis der Positionen |
| `subtotal_net`, `discount_net`, `shipping_net`, `deductions_net`, `total_net`, `vat_rate`, `vat_amount`, `total_gross` | Zahl/null | Summen |
| `related[]` | `document:` | zugehörige Belege (Angebot ↔ Rechnung) |
| `pdf`, `imported_from`, `source_sha256`, `original_filename`, `photos[]` | Text | Herkunft der Quelldatei |

### tga-classes – TGA-Klasse

`catalog\tga-classes\*.json`, Schema `tga-class.schema.json`, Ref `tga-class:<id>`. Klassen der Haustechnik (KG 400).

| Feld | Typ | Bedeutung |
|---|---|---|
| **`id`**, **`name`** | Text | |
| **`kind`** | Enum | `pipe`, `cable`, `duct` (Leitungsträger), `terminal` (Endstelle), `fitting` (Formteil), `part` (Zubehör ohne Geometrie) |
| **`parameters[]`** | Liste | wie bei *classes*, zusätzlich Typ `text` |
| `material_roles[]` | Liste | wie bei *classes* |
| `connection_rules[]` | Liste | **`medium`** (`power`, `water_supply`, `waste_water`, `heating`), `line` (`ht`, `kg`, `ppr`, `alu_composite`, `power`), `types[]`, `method` (`clamp`, `weld`, `push`, `press`, `screw`), `partners[]`, `locations[]`, `directed`, `note` – ausgewertet vom `ConnectionValidator` |
| `ifc`, `description` | | |

### tga-components – TGA-Komponente

`catalog\tga-components\*.json`, Schema `tga-component.schema.json`, Ref `tga-component:<id>`. Konkretes Produkt einer TGA-Klasse (Rohr, Formteil, Kabel, Dose …).

| Feld | Typ | Bedeutung |
|---|---|---|
| **`id`**, **`name`** | Text | |
| **`class`** | `tga-class:` | |
| **`din276`** | `4xx` | Kostengruppe; Gewerk über `catalog\reference\din276.json` |
| **`system_type`** | Text | Anlagensystem, z. B. `Stromkreis`, `Trinkwasser` |
| **`params`** | Objekt | Werte zu den Klassenparametern |
| `connection` | Objekt | `line`; `ends[]` `{id, dn, gender (spigot/socket/any), line?, flow?}`; Elektro: `conductors[]`, `poles`, `cross_section`, `may_be_end`, `partial_use`, `mounting` (`surface`/`flush`/`hollow_wall`), `box_function` (`junction`/`device`), `accepts[]` |
| `install` | Objekt | Einbau als Einzelteil: **`trade`** (`electrical`, `waste_water`, `water_supply`), **`shape`** (`pipe`, `fitting`, `box`, `valve`, `cap`, `insert`, `cable`), **`ports[]`** `{id, pos[3], dir[3], line, dn, gender, flow?, cores?, at_length?}`, `group`, `palette`, `outer_diameter`, `size[3]`, `stretch {max_length, default_length?}`; erzeugt von `scripts\build_ports.py` |
| `stock` | Objekt | **`lengths[]`** Stangenlängen m, `cuttable` |
| `materials` | Objekt | Rolle → `material:` |
| `catalog_material`, `material_offer` | `material:`, Zahl | gleiches Produkt als Material; nur dieses Angebot gilt |
| `estimated`, `note`, `product`, `imported_from[]`, `photos[]` | | |

```
{ "id": "kaiser-9063-02-hohlwand-geraetedose-o-range-49-mm", "name": "Kaiser Hohlwand-Gerätedose 9063-02 O-range 49 mm",
  "class": "tga-class:install-part", "din276": "440", "system_type": "Stromkreis",
  "params": { "part_type": "box" },
  "product": { "manufacturer": "company:kaiser", "article_no": "8999484",
               "offers": [ { "supplier": "company:obi", "price": 0.99, "price_basis": "gross", "date": "2026-11-21" } ] },
  "connection": { "line": "power", "mounting": "hollow_wall", "box_function": "device" } }
```

### reference – Referenzlisten

`catalog\reference\din276.json`, Schema `din276.schema.json`: **`id`** = `din276`, **`name`**, `description`, **`groups[]`** `{code (100–899), name, parent?, trade?}`. Liefert Namen der Kostengruppen und das Gewerk der KG 4xx.

### Import-Ordner (nicht Teil des Modells)

| Ordner | Inhalt |
|---|---|
| `imported_material\` | Baumarkt-Rohdaten je Artikel (Schema `product.schema.json`: `article_number`, `ean`, `name`, `unit_price`, `supplier`, Bilder, `details` …); Materialien verweisen über `imported_from[]` |
| `imported_purchases\` | Kassenbons |
| `imported_documents\` | Eingang der Belege vor der Übernahme nach `documents\` |
| `photos\` | Fotos je Element-Id |
| `schema\` | die JSON-Schemas selbst |

Der Core lädt nur die Element-Ordner (`CATALOG_FOLDERS`, `TGA_FOLDERS` in `constants.py`), nicht diese Ordner. Die drei `imported_*`-Ordner sind nicht versioniert (siehe **Versionsverwaltung**).

## Ausnahmeliste

Grundsatz der Non-Code-Anwendung: Die Spezifikation *ist* das Programm. Code darf nur für die Punkte der **Exception list** einer Spezifikation entstehen; jede Zeile nennt, *warum* hier Code nötig ist und aus welchem Abschnitt er erzeugt wird. Alles andere erledigt der Agent mit Werkzeugen. Die Tabelle wird bei jedem Aufruf direkt aus `weingaerten-core.md` und `weingaerten-web.md` gelesen.

{{code:exceptions}}

Regeln für Ausnahmen:

- Eine neue Ausnahme braucht eine Zeile in der Exception list **und** einen eigenen Spezifikationsabschnitt; ohne Zeile kein Code.
- **Fremdcode** (three.js, Pygments) wird nicht erzeugt, sondern einmal bezogen, auf eine Version festgelegt und per SHA-256 geprüft (Abschnitt *Library specification*). Er wird nie geändert und zur Laufzeit nur aus dem Projekt geladen.
- Ausnahmen werden vom Benutzer freigegeben („approved by the user“ in den *Hard rules*).

## Sicherheit

Der Server ist ein lokales Werkzeug; trotzdem gilt „Verteidigung in der Tiefe“:

| Maßnahme | Umsetzung |
|---|---|
| nur lokal erreichbar | Bindung nur an `127.0.0.1` und `[::1]` (`DualStackServer`, `IPv6HttpServer`) |
| Schutz vor fremden Webseiten (CSRF, DNS-Rebinding) | POST nur mit `Host` `localhost:<port>`/`127.0.0.1:<port>` und passendem `Origin`, sonst 403 (`PostRequestReader`) |
| Eingabeformat | nur `application/json` (415), Body höchstens 64 KB (400), ungültiges JSON 400 |
| Argumente | Allowlist-Regex für Refs und Ids (`REF_RE`, `EDIT_RE`, `ID_RE`), Typprüfung je Route (`ApiArguments`) |
| Pfade | Dateinamen entstehen nur aus geprüften Ids; Fotos zusätzlich `realpath` + `commonpath` gegen `catalog\photos` (`PhotoSender`); Bibliotheksdateien nur aus fester Liste |
| XSS | alle Werte serverseitig mit `HtmlTools.escape`, eingebettetes JSON mit `<` → `\u003c`; Browser-Code setzt Daten nur mit `textContent`/`.value`, nie `innerHTML` |
| Markdown | Text wird vor dem Inline-Markup escaped, kein rohes HTML |
| Fehler | Ausnahmen → 500 `internal error`, Details nur in der Konsole |
| Log-Injection | Pfade werden vor dem Loggen von CR/LF befreit (`_loggable`) |
| Fremdcode | three.js r160 (Browser) und Pygments 2.20.0 (Quellcode-Färbung in Tech.Doku), beide per SHA-256 geprüft; three.js zur Laufzeit nur vom eigenen Server, Pygments nur aus `vendor\` |
| Code-Doku | `/techdoku` liest Python nur mit `ast` (kein Import, keine Ausführung), Node-Ids nur als Lookup im Baum |

### AAA Security-Checks (aaa-security-fixer)

Der Agent **aaa-security-fixer** (AST Agentic Approach, Plugin `aaa-security-remediation`) behebt Befunde aus **GHAS / CodeQL** (SAST) und **Wiz Code** (SCA, IaC). Er braucht ein GitHub-Repository mit Code-Scanning. Das Projekt liegt in **https://bmw.ghe.com/Sachindra-Suri/weingaerten** (siehe **Versionsverwaltung**); dort ist Code Scanning (CodeQL-Workflow) noch einzurichten. Die folgenden Prüfkategorien des Skills `aaa-ghas-remediation` sind gegen den Code abgeglichen:

| CodeQL-Kategorie | Regel (Python/JS) | Stand im Projekt |
|---|---|---|
| Path traversal | `py/path-injection` | Ids per Allowlist-Regex; Fotos mit `realpath` + `commonpath`; keine freien Pfade aus Anfragen |
| XSS | `py/reflective-xss`, `js/xss` | zentrales `HtmlTools.escape`; JS nur `textContent`; kein `innerHTML` mit Daten |
| Log injection | `py/log-injection` | Request-Pfade über `_loggable` (CR/LF entfernt); POST-Pfade nur nach Abgleich mit `API_COMMANDS` geloggt |
| SQL / LDAP injection | `py/sql-injection` | nicht relevant – keine Datenbank, kein LDAP |
| SSRF | `py/ssrf` | Server macht keine ausgehenden Anfragen; nur Import-Skripte in `scripts\` laden feste Shop-URLs (nicht Teil des Servers) |
| Weak crypto | `py/weak-sensitive-data-hashing` | nur SHA-256 (Cache-Hashes, three.js-Prüfung), keine Passwörter |
| Sensitive log / data | `py/clear-text-logging-sensitive-data` | keine Geheimnisse im System; 500-Antworten ohne Details |
| Zip Slip | `py/zipslip` | nicht relevant – keine Archive |
| Tainted arithmetic | – | Zahlen aus Anfragen werden vom Core in Bereichen geprüft (z. B. Port 1–65535, Maße gegen Wand) |
| SCA / CVE (Wiz) | Abhängigkeiten | nur Python-Standardbibliothek, three.js r160 und Pygments 2.20.0 (beide fest, per SHA-256 geprüft, im Projekt abgelegt) |
| IaC (Wiz) | Dockerfile, Terraform, Actions | nicht vorhanden |

Grundsätze des Skills, die auch hier gelten: zentrale Hilfsfunktionen statt verstreuter Einzelfixes, Allowlists statt Denylists, kontextgerechtes Encoding, alle Aufrufer einer Schwachstelle prüfen, nach jeder Änderung Regressionsprüfung.

Ausführen, sobald im Repository `Sachindra-Suri/weingaerten` ein CodeQL-Workflow läuft (GitHub › Settings › Code security › Code scanning, Sprachen Python und JavaScript): im Chat den Agenten `aaa-security-fixer` mit `/security-fix target=ghas` (CodeQL) bzw. `/security-fix target=wiz` (Wiz) starten. Lokal geht es auch mit der CodeQL-CLI (`codeql_scan.py --language python`), wenn `codeql` installiert ist.

## Schnittstellen

Alle API-Aufrufe sind `POST` mit JSON-Body an `http://localhost:8008`. Antwort `application/json`; Fehler 400 mit `{error, errors?}`.

| Route | Core-Befehl | Argumente |
|---|---|---|
| `/api/house` | `HOUSE` | – |
| `/api/catalog` | `CATALOG` | `type?` (`material`, `assembly`, `class`, `component`, `company`) |
| `/api/resolve` | `RESOLVE` | `ref` |
| `/api/validate` | `VALIDATE` | – |
| `/api/bom` | `BOM` | – |
| `/api/usage` | `USAGE` | `ref` |
| `/api/element/save` | `SAVE` | `ref`, `element` (Objekt), `create` (bool) |
| `/api/element/delete` | `DELETE` | `ref` |
| `/api/opening/save` | `OPENING_SAVE` | `storey`, `wall`, `opening`, `create` |
| `/api/opening/delete` | `OPENING_DELETE` | `storey`, `wall`, `id` |
| `/api/lining/save` | `LINING_SAVE` | `storey`, `wall`, `lining`, `create` |
| `/api/lining/delete` | `LINING_DELETE` | `storey`, `wall`, `id` |
| `/api/walls/save` | `WALLS_SAVE` | `storey`, `upsert?`, `delete?`, `rooms?`, `height?` |
| `/api/room/save` | `ROOM_SAVE` | `storey`, `room` (vollständiges Raum-JSON mit Belägen), `create` |
| `/api/room/delete` | `ROOM_DELETE` | `storey`, `id` |
| `/api/shaft/save` | `SHAFT_SAVE` | `shaft`, `create` (schreibt `house\house.json`, nur `shafts`) |
| `/api/shaft/delete` | `SHAFT_DELETE` | `id` |

GET-Seiten: `/haus3d`, `/grundriss?storey=&cut=`, `/waende?storey=`, `/raeume?storey=`, `/katalog/<seite>`, `/mengen`, `/handbuch?node=`, `/techdoku?node=`, `/about` (`/doku` leitet auf das Benutzerhandbuch um); dazu `/lib/<datei>`, `/favicon.svg`, `/catalog-photo/<id>/<datei>`.

Core-Schnittstelle (Python): `weingaerten_core.handle('{"command": "RESOLVE", "ref": "assembly:exterior-wall-ew1"}')` gibt einen JSON-Text zurück.

### KI-Module und Modelle

**Im Code gibt es keine KI.** Geprüft wurden alle Python-Module beider Pakete, die Browser-Skripte und `scripts\`: kein Import von KI-Bibliotheken (z. B. OpenAI, Anthropic, Snowflake Cortex, transformers, torch), keine Modelldateien, keine Aufrufe von KI-Diensten. Der Server macht überhaupt keine ausgehenden Anfragen; der Browser spricht nur mit `/api/...` des eigenen Servers. Nur die Import-Skripte in `scripts\` (z. B. `fetch_obi_details.py`, `import_hornbach.py`) laden von Hand gestartet Produktseiten von Baumärkten – ohne KI. Die vollständige Liste der importierten Module steht unter **Code › Importierte Module**.

KI kommt nur **bei der Entstehung** vor, nicht zur Laufzeit:

| Wo | Rolle der KI | Schnittstelle |
|---|---|---|
| Code-Erzeugung | ein KI-Agent (Cortex Code) liest die Spezifikation und erzeugt daraus den Code der Ausnahmeliste | Chat / Werkzeuge des Agenten; Ergebnis nur im Ordner `code\` |
| Pläne und Änderungen | der Agent schreibt Pläne (`.snowflake\cortex\plans\`) und ändert Spezifikationen nach Freigabe | Chat |
| Sicherheitsprüfung | Agent `aaa-security-fixer` (siehe **Sicherheit**) | GitHub Code Scanning in `bmw.ghe.com/Sachindra-Suri/weingaerten` (Workflow noch einzurichten) |

Folgen: Die laufende Anwendung ist deterministisch und offline lauffähig; Daten des Hauses verlassen den Rechner nicht. Eine spätere KI-Funktion (z. B. Fragen an das Modell) wäre eine neue Ausnahme mit eigener Spezifikation und eigener API-Route.

## Entwicklungsrichtlinien

- **Spec first:** Änderungen zuerst in der Spezifikation, dann Code erzeugen, dann Hash schreiben.
- **Clean Code** (`skills\clean-code.instructions.md`): eine Klasse pro Modul, Modulname = Klassenname in snake_case; Module ≤ 256 Zeilen, Funktionen ≤ 80 Zeilen; Docstrings und Type Hints; Logger pro Modul; keine Bool-Flag-Argumente; kein toter Code; keine Duplikate (ein Escape-Helfer, ein Zahlenformat).
- **Nur Standardbibliothek** in Python; einziger Fremdcode ist three.js.
- **Daten:** JSON-Schlüssel Englisch; neue Wandfelder auch im Schema ergänzen.
- **Browser:** keine externen Ressourcen, Daten nur über `textContent`/`.value`.
- **Ablage:** Hilfsskripte nach `scripts\`, nie in den Projektordner.
- **Pläne:** größere Änderungen erst als Plan in `.snowflake\cortex\plans\`, dann nach Freigabe umsetzen.

## Build und Start

- Start: `start.cmd` (setzt `WEINGAERTEN_HOME`), anderer Port `start.cmd -port ####`. Vorher laufende `python …weingaerten_web`-Prozesse beenden.
- Nach einer Codeänderung: `python scripts\rehash_cache.py` (Hash + compileall), danach die Tests (siehe **Test**).

## Test

Die Tests sind eigenständige Python-Skripte in `scripts\`; es gibt kein Testframework (nur Standardbibliothek). Ein gemeinsamer Runner führt sie aus und legt das Ergebnis ab, das unter **Ergebnisse** angezeigt wird.

### Testkonzept

| Ebene | Skripte | Was gesichert wird | Voraussetzung |
|---|---|---|---|
| Struktur | `check_clean_code.py` | Clean-Code-Grenzen (Modul ≤ 256, Funktion ≤ 80 Zeilen) | – |
| Daten | übrige `check_*.py` ohne Server | Katalog, Verbindungen, Decken, Produktdaten, JS/Python-Parität | `WEINGAERTEN_HOME` |
| Web | `check_web.py`, `check_kat_js.py`, `check_haus3d_js.py`, `check_documents.py` | alle Seiten, Weiterleitungen, API-Antworten | laufender Server auf Port 8008 |
| Fachlich | `smoke_*.py` | Rechenergebnisse des Core je Thema (Geschosse, TGA, Dach, Wandheizung …) | `WEINGAERTEN_HOME` |
| Regression | `refactor_baseline.py` + `refactor_compare.py` | Core-Antworten und HTML byte-genau vor/nach einem Refactoring | alter und neuer Code; nicht im Runner |

Grundsätze: jede neue Funktion bekommt ein `smoke_<thema>.py`; ein Test prüft gegen die echten Hausdaten und schreibt nichts (Bearbeitungen nur auf temporären Kopien); ein veralteter Test wird angepasst oder gelöscht, nicht ignoriert.

### Technische Umsetzung

- Runner `scripts\run_tests.py`: findet `check_*.py` und `smoke_*.py`, ordnet sie den Ebenen zu und startet jedes Skript als eigenen Prozess (feste Argumentliste, keine Shell, Timeout 300 s, `WEINGAERTEN_HOME` gesetzt).
- Vertrag eines Testskripts: Exit-Code 0 = bestanden, sonst fehlgeschlagen; die letzte Ausgabezeile ist die Meldung.
- Web-Tests werden als *übersprungen* gemeldet, wenn kein Server auf Port 8008 antwortet.
- Ausgenommen: `smoke_baseline.py` (Hilfsskript der Regression) und `check_connections.py` (Bericht ohne Bestanden-Kriterium).
- Ergebnis: `scripts\test_results.json` (nicht versioniert) mit Zeitpunkt und je Test Name, Ebene, Status (`ok`, `fehler`, `übersprungen`), Dauer und Meldung. Die Seite liest die Datei bei jedem Aufruf.
- Historie: jeder Lauf zusätzlich als `scripts\test_history\<JJJJMMTT-hhmmss>.json` (nicht versioniert); der Runner löscht dabei Läufe, die älter als 31 Tage sind.
- Testfälle: die Seiten unter **Testfälle** entstehen aus dem Quelltext – Beschreibung = Docstring des Skripts, Prüfungen = alle Aufrufe `check(…)`/`chk(…)` mit ihrem Text.

### Durchführung

- Alle Tests: `python scripts\run_tests.py` (für die Web-Ebene vorher `start.cmd`).
- Eine Ebene: `python scripts\run_tests.py --level smoke` (`struktur`, `daten`, `web`, `fachlich` oder `check`/`smoke`).
- Ein Test: `python scripts\run_tests.py --only smoke_dg`.
- Wann: nach jeder Codeerzeugung und vor jedem Commit; Exit-Code des Runners ≠ 0, sobald ein Test fehlschlägt.

### Testfälle

Jede Ebene und jedes Testskript ist eine eigene Unterseite: was der Test prüft (Docstring), Voraussetzung, Aufruf, letzter Status und die Liste der einzelnen Prüfungen.

{{code:testcases}}

### Ergebnisse

Letzter Lauf des Runners (aus `scripts\test_results.json`).

{{code:tests}}

### Historie

Alle Läufe der letzten 31 Tage und der Verlauf je Test.

{{code:testhistory}}

## Versionsverwaltung (Git)

| | |
|---|---|
| Repository | **https://bmw.ghe.com/Sachindra-Suri/weingaerten** |
| Server | BMW GitHub Enterprise (`bmw.ghe.com`) |
| Besitzer | `Sachindra-Suri` |
| Klonen | `git clone https://bmw.ghe.com/Sachindra-Suri/weingaerten.git` |

Was versioniert wird (laut `.gitignore`):

| Versioniert | Nicht versioniert |
|---|---|
| alle `*.md` (Spezifikationen, Dokumentation, Pläne), `catalog\` (ohne Importe), `house\`, `people\` | `data\` (private Quelldokumente), `catalog\imported_material\` (Baumarkt-Rohdaten, Bilder), `catalog\imported_purchases\` (Kassenbons), `catalog\imported_documents\` (Belege-Eingang), `people\state\`, `.token\`, Laufzeitdateien (`*.pid`, `*.tmp`, `server*.log`) |
| `code\weingaerten_core\**\*.py`, `code\weingaerten_web\**\*.py` (inkl. `vendor\pygments`) | `__pycache__\`, `*.pyc` |
| `code\weingaerten_web\lib\*.js` (three.js), `code\weingaerten_web\static\*` (Seitenrahmen, CSS, Browser-Skripte, SVG) | übrige `*.js`, `*.css`, `*.html` |
| `scripts\*.py` | sonstige Dateien in `scripts\` (Caches, Ausgaben) |
| `start.cmd` | übrige `*.cmd`, `*.ps1`, `*.bat` |

Ein frischer Klon ist damit sofort lauffähig (`start.cmd`). Die Baumarkt-Importe fehlen dort; die daraus übernommenen Materialien in `catalog\materials\` sind versioniert, ein neuer Import braucht die Rohdaten lokal.

Arbeitsweise:

- Änderungen zuerst in der Spezifikation, dann Code erzeugen, prüfen (`check_clean_code.py`, `check_web.py`), Hash schreiben – erst dann committen, damit Spezifikation, Code und Hash zusammenpassen.
- Kein Geheimnis ins Repository: `.token\` und `data\` sind ausgeschlossen.
- Fremdcode (three.js, Pygments) bleibt unverändert; ein Update heißt neue Version und neuer SHA-256 in der *Library specification*.

## Code

Dieser Teil wird bei jedem Aufruf direkt aus dem Quellcode gelesen (Python mit `ast`, JavaScript mit regulären Ausdrücken) und ist daher immer aktuell. Beschreibungen stammen aus den Docstrings bzw. dem ersten Kommentar einer Datei.

### Scripte

Hilfs-, Prüf- und Importskripte in `scripts\`; sie gehören nicht zum Server.

{{code:scripts}}

### Core

Klassendiagramm des Pakets `weingaerten_core`: ein Kasten pro Unterpaket mit seinen Klassen, Bögen = Importe zwischen Unterpaketen (Zahl = Anzahl Importe).

{{code:diagram core}}

#### Klassen

{{code:classes core}}

### Web

Klassendiagramm des Pakets `weingaerten_web`.

{{code:diagram web}}

#### Klassen

{{code:classes web}}

#### Web Parts

Browser-Skripte in `weingaerten_web\static\`; sie werden beim Start gelesen und inline in die Seiten eingebettet.

{{code:js web}}

### Importierte Module

Alle Module, die der Code der beiden Pakete importiert (absolute Importe, auch innerhalb von Funktionen und `try`-Blöcken), mit ihrer Art, der verwendeten Version (Standardbibliothek = laufende Python-Version, Fremdbibliothek = deren `__version__`, eigene Pakete `–`) und den verwendenden Modulen. Erzeugt bei jedem Aufruf aus dem Quellcode; `unbekannt – prüfen` würde eine nicht freigegebene Abhängigkeit anzeigen.

{{code:imports}}

## Glossar

| Begriff | Bedeutung |
|---|---|
| Aufbau | Schichtfolge einer Wand, Decke oder eines Bodens |
| Laibung | Innenfläche einer Öffnung in der Wanddicke |
| Brüstung | Höhe der Rohbauöffnung über dem Fußboden |
| Rohbauöffnung | Öffnung im Mauerwerk vor dem Einbau des Bauteils |
| BOM | Bill of Materials – Stückliste / Mengen |
| TGA | technische Gebäudeausrüstung (Heizung, Elektro, Wasser) |
| IFC | offenes Austauschformat für Gebäudemodelle |
