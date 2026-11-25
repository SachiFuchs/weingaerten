---
name: "bauteil tga klassenstruktur"
created: "2026-11-13T22:11:02.130Z"
status: pending
---

# Datenmodell: Baukonstruktion (KG 300) / TGA (KG 400)

## 1. Context

Entscheidungen: (1) nur Datenmodell, (2) reales TGA-System später, (3) Decke/Dach nur als Vorschlag, (4) Abweichungen vom Diagramm akzeptiert:

- Baustoff erbt nicht von Gebaeudeelement; `din276` nur an Bauteilen, Öffnungen, TGA-Komponenten.
- Bauphysik am Bauteil wird berechnet, nicht gespeichert (nur optionale Overrides wie `fire_rating`).
- Öffnungen bleiben `wall.openings[]`.
- Gewerk aus KG ableiten; Leitungslänge aus `points[]` ableiten.
- Durchdringung = Leitung x Bauteil, `kind: through|recess`.

Bestehend: `catalog/schema/*.schema.json`, Daten je Element als JSON, Keys englisch, Werte deutsch, Refs `"<type>:<id>"`. Alle neuen Felder optional, damit Bestandsdaten und Smoke-Tests unverändert gültig bleiben.

## 2. Implementation steps

### Schritt 1 - Basis

- catalog/schema/material.schema.json: `density` (kg/m3), `vapour_resistance` (mu), `fire_class` (enum A1, A2, B1, B2, B3); `conductivity` bleibt.
- Bestehende Materialien mit Richtwerten ergänzen (Quelle "Richtwert" in `description` vermerken).
- Neu `catalog/din276.json` + `din276.schema.json`: Liste `{code, name, parent}` für 300/320/330/340/350/360 und 400/410/420/430/440; je 4xx-Code das abgeleitete `trade` (Gewerk).

### Schritt 2 - KG 300 Bauteile

- catalog/schema/assembly.schema.json: `din276` (Ref auf Code), optional `fire_rating` (REI-Klasse), `impact_sound_lnw_db` (Override). Bestehende Assemblies: EW1 -> 330, BS1 -> 320.

- catalog/schema/storey.schema.json: Bodenplatte optional `waterproofing`, `white_tank`; wall optional `load_bearing`.

- **Vorschlag Decke/Dach** (nur Schema, keine Daten, im Schema als `description` gekennzeichnet "Vorschlag"):

  - `ceilings[]`: `{id, assembly, z, outline: "storey"|polygon}`; Assembly-Kategorie `ceiling`, `layer_order: top_down`.
  - `roof` am Haus: `{assembly, form: gable|hip|mono|flat, pitch_deg, eaves_overhang, ridge_direction: x|y}`; Assembly-Kategorie `roof`, `layer_order: outside_in`.

### Schritt 3 - Öffnungsabschlüsse

- `classes/window.json`: optionale Parameter `glazing_type` (choice), `g_value`, `uw_value`, `burglary_class` (RC0-RC3).
- `classes/door.json`: `leaf_type`, `frame_type`, `smoke_protection` (bool), `fire_rating` (choice keine/T30/T60/T90), `burglary_class`.
- `class.schema.json`: Feld `din276` (Fenster/Türen 334/344).

### Schritt 4 - KG 400 Katalog

- Neue Schemas `tga-class.schema.json`, `tga-component.schema.json` (analog class/component: `parameters`, `params`, Feld `kind: pipe|cable|duct|terminal`, `din276`, `system_type`).
- Neue Ordner `catalog/tga-classes/` mit `pipe.json` (nominal\_size\_dn, pressure\_bar, insulation\_mm, medium), `cable.json` (cable\_type, cores, cross\_section\_mm2, conduit\_type), `duct.json` (profile, size\_mm, insulated), `terminal.json` (mounting, room-bezogen).
- `catalog/tga-components/`: je Klasse ein generisches Beispiel (z. B. `pipe-mlcp-16`, `cable-nym-3x15`), als Muster, kein reales System.

### Schritt 5 - Haus-TGA und Schnittstellen (nur Schema)

- `tga-run.schema.json`: `{id, component, system, points:[{x,y,z}], from?, to?}`.
- `tga-terminal.schema.json`: `{id, component, storey, room?, position:{x,y,z}}`.
- `penetration.schema.json`: Override-Einträge `{wall|slab, run, index, kind, fire_stop_type?, done?}`; abgeleitete Felder (`needs_fire_stop`, `airtight`) im Schema als "berechnet" dokumentiert.
- Ablage vorgesehen: `house/tga/runs/`, `house/tga/terminals/`, `house/penetrations.json` - Ordner nicht anlegen, nur in Doku beschreiben.

### Schritt 6 - Doku

- weingaerten-doku.md bzw. Konventionen: Klassendiagramm (mermaid) und Abbildungstabelle Diagramm -> Datei/Feld, inkl. der akzeptierten Abweichungen und des Decke/Dach-Vorschlags.
- Projekt-Memory `conventions.md` um neue Ordner/Schemas ergänzen.

## 3. Verification

- Alle JSON-Dateien gegen ihre Schemas validieren (kleines Skript in `scripts/`, gitignored-Konvention).
- `python scripts/smoke_core.py` und `scripts/smoke_baseline.py` laufen unverändert grün (neue Felder optional, Core liest sie noch nicht).
- Server-Seiten Katalog laden weiterhin ohne Fehler (`scripts/check_web.py`).

## 4. Critical Files

- catalog/schema/material.schema.json - Baustoff-Kennwerte
- catalog/schema/assembly.schema.json - DIN 276, Overrides, Decke/Dach-Kategorien
- catalog/schema/storey.schema.json - Decke/Dach-Vorschlag, Bodenplatte
- catalog/schema/class.schema.json - Vorlage für TGA-Schemas
- weingaerten-doku.md - Diagramm und Abbildung
