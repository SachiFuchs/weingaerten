# Plan: Code-Ablage flach machen und EG-Korrekturen einarbeiten

## Teil A – Doppelten Pfad entfernen

Heute stecken die Pakete eine Ebene zu tief:

| Heute | Neu |
|---|---|
| `code\weingaerten-core\weingaerten_core\` | `code\weingaerten_core\` |
| `code\weingaerten-web\weingaerten_web\` (+ `static\`) | `code\weingaerten_web\` (+ `static\`) |
| `code\weingaerten-web\lib\` (three.js) | `code\weingaerten_web\lib\` |
| `code\weingaerten-core\.hash\weingaerten_core.sha256` | `code\.hash\weingaerten_core.sha256` |
| `code\weingaerten-web\.hash\weingaerten_web.sha256` | `code\.hash\weingaerten_web.sha256` |

Die Paketnamen bleiben, damit `import weingaerten_core` unverändert funktioniert. `code\` ist dann der einzige `sys.path`-Eintrag für beide Pakete.

Schritte:
1. Server stoppen. Ordner verschieben, die leeren Ordner `weingaerten-core` und `weingaerten-web` löschen, `__pycache__` entfernen.
2. Web-Code:
   - `ServerSettings.from_arguments`: `code_dir` = Ordner über dem Paket. `core_dir` = `code_dir`, `lib_dir` = `<paket>\lib`.
   - `CoreClient` prüft `code\weingaerten_core\__init__.py`.
   - `__main__.py` ersetzt den Paketordner in `sys.path` durch `code\`.
   - Docstrings anpassen.
3. Specs ([weingaerten-core.md](weingaerten-core.md), [weingaerten-web.md](weingaerten-web.md)):
   - Code folder = `<folder of this prompt>\code\`.
   - Cache-Prüfbefehl, Generierungsschritte, Startbefehl, pid-Suche, Exception list und `lib\`-Pfad anpassen.
   - Der Startbefehl wird `python code\weingaerten_web`.
4. [start.cmd](start.cmd): `SERVER=%~dp0code\weingaerten_web`.
5. Skripte in `scripts/`: Pfade auf `code\` (rehash, clean-code check, smoke, baseline, check_ceilings, core_validate, time_core, profile_kat).
6. [weingaerten-doku.md](weingaerten-doku.md): Pfade in Einleitung und Architekturtabelle.
7. Hashes neu schreiben, Server mit `start.cmd` starten.
8. Prüfen:
   - Cache-Prüfung beider Specs ergibt `cache=hit`.
   - Byte-Vergleich ohne Abweichung (außer `/doku`, falls die Doku geändert wurde).
   - `check_clean_code.py` ohne Befund.
   - `check_web.py` wie bisher (nur der bekannte `w-south`-Check schlägt fehl).

## Teil B – Korrekturen EG (rote Markierungen)

### Kontext
- `data/EG-korrigiert.docx` enthält den EG-Plan als Bild und 8 rote Markierungen (Sprechblasen und Rechtecke). Ich habe sie in Hauskoordinaten umgerechnet. Maßstab: die Terrassenfläche (x 0–3,84, y 9,94–13,13) und das Flachdach-Rechteck (x 1,01–7,12, y 0–2,08).
- Der Core kennt in Öffnungen nur `window` und `door`. Unterzug, Stütze und Außenflächen gibt es nicht. `storey.schema.json` hat `additionalProperties: false`, und `class.schema.json` erlaubt nur `window | door | box`.

### Korrekturen und Abbildung

| # | Rot im Plan | Abbildung (Werte aus der Skizze, im Browser nachjustierbar) |
|---|---|---|
| 1 | Tür zum Bad 80 × 190 | Öffnung `o-bad-tuer` in `iw-flur-bad`, Offset ≈ 0,28, neues Bauteil `door-bad` (Innentür Holz 0,80 × 1,90, Tiefe 0,06, Anschlag `left`), `inset` 0,03 (Wand 12 cm) |
| 2 | Durchgang 80 × 200 | `o-durchgang-kueche` in `iw-gang-kueche`, Offset ≈ 1,15, Bauteil `passage-80x200` |
| 3 | Durchgang 60 × 180 | `o-durchgang-kammer` in `iw-kueche-kammer`, Offset ≈ 0,75, Bauteil `passage-60x180` |
| 4 | Innenwand | `iw-treppe-ost` wird bis y **4,99** verlängert (iw1, 12 cm), damit keine zwei offenen Wandenden auf einer Linie entstehen |
| 5 | Balken 20 × 10 | Unterzug `b-wohnzimmer`: Fichte 0,10 × 0,20, x 4,155, y 6,62 → 9,76, Oberkante 2,75 |
| 6 | Betondecke 15 cm mit Folie, Flachdach | Decke `c-flachdach` (`flat-roof-fd1`: PE-Folie + Beton C25 15 cm, Klasse slab) über Flur und Bad. `c-eg` bekommt einen expliziten Umriss nur für den Rest. Unterkante Beton auf 2,75 |
| 7 | Überdachte Terrasse | Außenfläche `t-terrasse` (x 0–3,84, y 9,94–13,13) und Decke `c-terrasse` (`terrace-roof-tr1`, Holz auf 2,75, Balken geschätzt) |
| 8 | Holzbalken als Stütze | Stütze `p-terrasse`: Fichte 0,12 × 0,12 an der Südwest-Ecke (≈ [0,18; 12,92]), z 0 → 2,75 |

### Neue Modellelemente
- **Durchgang:** Klassengeometrie `passage` (Rezept `width`, `height`), für Öffnungen erlaubt. Die Rohbauöffnung wird wie bei der Tür berechnet, Tiefe und Rahmen sind 0, er hat keine Teile. Laibung (falls gesetzt) über die volle Wandtiefe. In der BOM als Öffnungsfläche und als Bauteil ohne Preis.
- **Tragwerk** `storey.structure[]`:
  - `beam {id, name, material, width, height, start, end, z_top}` oder `post {id, name, material, width, depth, position, z0?, z1?}`.
  - Der Core prüft Material und Maße > 0 und berechnet einen Quader mit Volumen.
  - Ausgabe in HOUSE, in der BOM (Volumen je Material, Tabelle `structure`) und in `counts.structure`.
- **Außenflächen** `storey.outdoor_areas[]` `{id, name, rect}`: Sie werden nicht als Raum geprüft. Ausgabe mit Fläche in HOUSE und BOM.
- **Web:**
  - `/grundriss`: Durchgang offen ohne Rahmen. Stütze im Schnitt gefüllt, Unterzug gestrichelt. Terrasse schraffiert mit Name und Fläche.
  - `/haus3d`: Unterzug und Stütze als Quader mit Tooltip.
  - `/waende`: Ansicht des Durchgangs in `front.js`.
  - `/katalog/klassen`: Geometrie „Durchgang“.
  - `/mengen`: Tabellen „Tragwerk“ und „Außenflächen“.
- Neue Module, auch in den Tabellen der **Code structure**: `compute/structure_builder.py` (`StructureBuilder`), `compute/outdoor_area_builder.py` (`OutdoorAreaBuilder`), `plan/structure_svg.py` (`StructureSvg`).

### Schritte
1. Core-Spec: `passage`, **Structure**, **Outdoor areas**, Antworten, Module.
2. Web-Spec: Darstellung je Seite, Module, erwartete Strings in Step 5 (z. B. `/mengen` enthält `Tragwerk`).
3. Schemas (`passage`, `structure`, `outdoor_areas`) und Katalog:
   - Klasse `passage`.
   - Bauteile `passage-80x200`, `passage-60x180`, `door-bad`.
   - Material `pe-foil`.
   - Aufbauten `flat-roof-fd1` und `terrace-roof-tr1` (ohne Klasse, daher Warnung).
4. Core-Code: `RECIPE_PARAMETERS`, `OpeningParser`, `OpeningPartsBuilder`, `OpeningOutputBuilder`, neue Builder, `StoreyBuilder`, `HouseSummary`, `BillOfMaterials`, `ElementCounter`.
5. Web-Code: `StructureSvg`, Terrasse in `PlanSvg`, `OpeningSvg` (Durchgang), `MengenPage`, `FORM_ENUMS`; statische Skripte `haus3d.js`, `front.js`, `wand.js`, `katalog.js`.
6. Daten in [house/storeys/ground.json](house/storeys/ground.json): 3 Öffnungen, Wandverlängerung, 3 Decken (Umrisse aus den berechneten Wandflächen), Tragwerk, Terrasse.
7. Doku, Hashes, Neustart.

### Verifikation
- `VALIDATE`: `ok: true`. Neue Warnungen nur, wo erwartet: Terrassendach ohne Klasse, offenes Ende von `iw-treppe-ost`.
- Neues Testskript `scripts/smoke_eg_corrections.py`:
  - Rohbaumaße der 3 Öffnungen 0,82 × 1,92 / 0,82 × 2,02 / 0,62 × 1,82; Durchgang mit 0 Teilen.
  - Unterzug ≈ 0,063 m³, z 2,55–2,75; Stütze ≈ 0,040 m³.
  - Terrasse 12,25 m².
  - `c-flachdach` ist Beton 15 cm.
  - Fehlerfälle auf einer temporären Kopie: unbekanntes Material, Breite 0.
- `check_clean_code.py` ohne Befund, `check_web.py` wie bisher.
- Manuell: `/grundriss`, `/haus3d`, `/mengen`.

## Kritische Dateien
- [weingaerten-core.md](weingaerten-core.md), [weingaerten-web.md](weingaerten-web.md) - Specs (Pfade, neue Elemente)
- [code/weingaerten_web/server_settings.py](code/weingaerten_web/server_settings.py) - Pfadableitung nach dem Umzug
- [house/storeys/ground.json](house/storeys/ground.json) - EG-Daten mit allen Korrekturen
- [code/weingaerten_core/compute/storey_builder.py](code/weingaerten_core/compute/storey_builder.py) - bindet die neuen Builder ein
- [catalog/schema/storey.schema.json](catalog/schema/storey.schema.json) - neue Storey-Felder

## Annahmen
- Positionen von Tür und Durchgängen aus der Skizze (etwa ±10 cm), Feinkorrektur auf `/waende`.
- Badtür mit Anschlag links; Flachdach ohne Bekleidung, Unterkante 2,75.
- Terrassendach: Holzschalung 24 mm auf Balken 12 × 18 alle 0,80 m (geschätzt).
