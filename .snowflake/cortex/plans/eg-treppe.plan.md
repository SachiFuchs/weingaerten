# Plan: Treppe EG -> DG

## Context

- Treppenraum EG `room-treppe` rect [0.328, 2.408, 2.792, 0.967] (x 0.328..3.12, y 2.408..3.375), zwischen Nordwand, `iw-treppe-sued` (y 3.435 Mitte) und `iw-treppe-ost` (x 3.18). DG elevation 2.95.
- Vorhandene Muster: `storey.structure[]` (StructureBuilder -> Prismen mit footprint/z0/z1, BOM-Zeilen, 3D-Prismen mit Tooltip), Material `material:spruce-wood`.
- Entscheidungen: Antritt Ost (x 3.12), Lauf nach Westen, oben Viertelwendel links (nach Süden), Austritt nach Süden bei y 3.375; 16 Steigungen = 11 gerade + 4 gewendelte Trittstufen + Austritt auf DG-Fußboden; Wangentreppe mit Setzstufen; nur die Treppe (kein Deckenloch, keine Handläufe).

## Geometrie (abgeleitet)

- Steigung h = 2.95 / 16 = 0.184 m.
- Wendelbereich = Quadrat am Westende x 0.328..1.295, y 2.408..3.375 (Laufbreite 0.967).
- Gerader Lauf x 3.12 -> 1.295: 11 Auftritte à 1.825 / 11 = 0.166 m (steil wie im Foto; wird als Hinweis ausgegeben, Schrittmaß 2h + a = 0.53).
- Wendelstufen: 4 Sektoren um die Innenecke (1.295, 3.375) von 0 bis 90 Grad (je 22.5 Grad), als Polygone geschnitten am Quadrat; die letzte endet an der Kante y 3.375 = Austritt (DG-Fußboden).
- Trittstufe: Polygon, Dicke 0.04, Oberkante i·h (i = 1..15); Setzstufe: 0.02 dick, Höhe h, an der Vorderkante jeder Stufe (gerade Linie, bei Wendelstufen entlang der radialen Kante); Wangen: zwei Bohlen 0.05 × 0.28 entlang Nord- und Südwand (gerader Lauf) bzw. West- und Nordseite im Wendel, schräg (bottom/top plane) – vereinfacht als je ein geneigtes Prisma pro Lauf-Abschnitt.

## Daten (`house/storeys/ground.json`)

```json
"stairs": [{
  "id": "treppe-eg-dg", "name": "Treppe EG–DG", "material": "material:spruce-wood", "estimated": true,
  "note": "Foto Nov 2026; Maße aus Raum und Geschosshöhe abgeleitet",
  "to_storey": "storey:upper", "risers": 16,
  "run": { "start": [3.12, 2.408], "direction": "west", "width": 0.967, "straight_steps": 11 },
  "turn": { "side": "left", "steps": 4 },
  "tread_thickness": 0.04, "riser_thickness": 0.02, "stringer": { "width": 0.05, "height": 0.28 }
}]
```

Höhe = to_storey.elevation − storey.elevation; Fehler `where <storey>.<id>`: unbekanntes Material / Zielgeschoss, Maße <= 0, Lauf passt nicht in die angegebene Länge (Auftritt < 0.10 -> Fehler, < 0.21 -> Warnung `steile Treppe (Auftritt … cm)`).

## Implementation steps

1. **Core**: neu `compute/stair_builder.py` (`StairBuilder`, ggf. Helfer `stair_winders.py`): parts `[{id, kind: tread|riser|stringer, name, material, footprint, z0, z1, bottom_plane?, top_plane?, volume}]`, Kennwerte `{rise, going, steps}`; `StoreyBuilder` -> `stairs`; HOUSE-Materialien; BOM `stairs: [{storey, stair, name, material, steps, rise, going, volume, estimated}]` + `totals.stair_volume`, Materialvolumen; VALIDATE count `stairs`. Schema `storey.stairs`; Core-Spezifikation.
2. **Daten**: Block in `ground.json`.
3. **Web**: `/haus3d` Teile als Prismen (wie Dachstuhl, mit Ebenen für Wangen), Holzfarbe, Setzstufen weiß angestrichen dargestellt (Farbe aus Teil `color` = #F4F4F0, Material bleibt Holz), sichtbar mit EG-Checkbox; Tooltip `Trittstufe i/15`, `Steigung 18,4 cm, Auftritt 16,6 cm`. `/mengen` Tabelle `Treppe`. Grundriss: Umriss der Trittstufen mit Lauflinie (Pfeil) im EG. Web-Spezifikation.
4. **Tests**: `scripts/smoke_stairs.py` (15 Trittstufen, Oberkante letzte = 2.76, Austritt 2.95, Wendelpolygone im Quadrat, Fläche-Summe, BOM, Fehlerfälle auf Temp-Kopie mit frischem Verzeichnis); dazu `smoke_roof_*`, `check_haus3d_js`, `check_clean_code`, `core_validate`; rehash, Neustart, Browserblick.
5. **Memory** aktualisieren.

## Verification

- VALIDATE ok, counts stairs 1, nur erwartete Warnung (steile Treppe).
- 3D: Treppe steigt im Treppenraum nach Westen, dreht oben nach Süden, letzte Stufe 18,4 cm unter DG-Boden.

## Hinweis

Der Austritt nach Süden bei x 0.33..1.30 liegt im DG unter der Dachschräge (Abseite / 2-m-Linie bei x 1.30). Das wird nur berichtet, nicht korrigiert.

## Critical files

- `code/weingaerten_core/compute/stair_builder.py` (neu), `storey_builder.py`, `queries/bill_of_materials.py`
- `house/storeys/ground.json`, `catalog/schema/storey.schema.json`
- `code/weingaerten_web/static/haus3d.js`, `static/plan.js`, `pages/mengen_page.py`
- `weingaerten-core.md`, `weingaerten-web.md`
