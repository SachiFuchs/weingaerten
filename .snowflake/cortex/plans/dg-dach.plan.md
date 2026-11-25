# Plan: Dach (Deckung) über dem DG

## Context

- Rechnung bereits importiert: `assembly:roof-r1` (top_down: Rubin 13 V 0,02 / Traglattung 0,03 / Konterlattung 0,04 / PIR 0,14 / Dampfbremse 0,0005, Summe 0,2305), Bauteile `class:roof-part` (First 10 m, Ortgang 22 m, Rinne/Einlaufblech/Lüfterkamm/Traufbohlen 24 m, Rinnenhalter 35, Untersicht 117 m, Balkenwechsel 3, Kamin-Verwahrung/-Verkleidung/-Abdeckung), Fenster `roof-window-velux-ck04/-fk06` mit Eindeckrahmen, Firma `schuck-dach`.
- DG `upper.json`: `roof` (gable 30 Grad, Kniestock 1,25, Traufen x 0 / 7,12, First x 3,56) und `roof_structure` (Flächen west 2,08..9,94, west-kammer 9,94..13,13 bis x 2,72, east 2,08..9,94; Sparren 8x16). `house.roof` ist nur ein Schema-Vorschlag, nicht ausgewertet.
- Entscheidungen: Dachform wie Dachstuhl (kein Dach über dem Balkon), Überstände aus der Rechnung ableiten (geschätzt), Fenster und Kamin platzieren: FK06 Ost im Schlafzimmer, CK04 West im Durchgangszimmer, Kamin Ost nahe First im Durchgangszimmer 0,50 x 0,50.

## Data

`upper.json`, neuer Block `roof_covering` neben `roof_structure` (Flächen teilen die `slopes`-IDs):

```json
"roof_covering": {
  "assembly": "assembly:roof-r1", "estimated": true,
  "note": "Schuck Dach RE 17.07.2023, 130 m2; Ueberstaende aus Rechnung abgeleitet",
  "eaves_overhang": 0.80, "verge_overhang": 0.50,
  "base": "rafter_top",
  "openings": [
    { "id": "dfe-schlaf", "component": "component:roof-window-velux-fk06", "slope": "east", "flashing": "component:roof-flashing-velux-fk06", "y": 7.70, "sill": 0.90 },
    { "id": "dfe-durchgang", "component": "component:roof-window-velux-ck04", "slope": "west", "flashing": "component:roof-flashing-velux-ck04", "y": 3.77, "sill": 0.90 },
    { "id": "kamin", "kind": "chimney", "slope": "east", "rect_plan": [3.80, 3.52, 0.50, 0.50], "parts": ["component:chimney-flashing", "component:chimney-cladding", "component:chimney-cap"] }
  ],
  "items": [
    { "component": "component:roof-ridge", "measure": "ridge" },
    { "component": "component:roof-verge-tile", "measure": "verge" },
    { "component": "component:roof-gutter", "measure": "eaves" },
    { "component": "component:roof-eaves-flashing", "measure": "eaves" },
    { "component": "component:roof-eaves-vent-comb", "measure": "eaves" },
    { "component": "component:roof-eaves-boards", "measure": "eaves" },
    { "component": "component:roof-gutter-bracket", "measure": "eaves", "per_m": 1.5 },
    { "component": "component:roof-soffit-cladding", "measure": "invoice" },
    { "component": "component:roof-trimmer", "measure": "invoice" }
  ]
}
```

Werte zur Bestätigung: y der Fenster = Raummitte, `sill` = Unterkante über Fußboden DG (gemessen an der Dachunterseite); Kamin-x so, dass er knapp östlich am First sitzt. Überstände: Start mit Traufe 0,80 / Ortgang 0,50. Der Core rechnet die Ist-Mengen und `/mengen` zeigt sie neben den Rechnungswerten (Fläche 130, First 10, Ortgang 22, Traufe 24). Ich passe die zwei Überstände so an, dass die Summe der Abweichungen am kleinsten ist, und nenne die übrigen Differenzen offen. Die Rechnung passt mit der Dachform „wie Dachstuhl“ nicht exakt zusammen.

## Geometry (Core, neu `compute/roof_covering_builder.py`)

- Pro Dachfläche ein Polygon in der Grundrissebene: Traufe = eaves -/+ eaves_overhang, First x 3,56 (west-kammer: Endkante x 2,72), y-Bereich der Fläche +- verge_overhang an freien Rändern (Nord, Süd 9,94 Ost, Süd 13,13 West, Kammer-Ostkante 2,72). Keine Verlängerung an inneren Stößen (west/west-kammer bei 9,94).
- Ebene: Unterseite = Sparren-Oberkante (Dachlinie + Sparrenhöhe/cos), Schichten senkrecht zur Dachfläche darüber gestapelt (top_down, also Ziegel oben); jede Schicht = geneigtes Prisma mit bottom_plane/top_plane (wie die Dachstuhl-Teile).
- Öffnungen: Fenster als Rechteck in der Dachebene (Breite entlang y, Höhe entlang Gefälle), Lage aus y und sill; Kamin als senkrechte Projektion von rect_plan. Sie werden aus allen Schichten ausgeschnitten (Fläche abgezogen, wie bei Wandöffnungen). Fehler, wenn eine Öffnung außerhalb der Fläche liegt oder einen Sparren schneidet: Warnung `Balkenwechsel nötig` (informativ, passt zu roof-trimmer).
- Kanten-Messungen: ridge = Firstlänge (Fläche bis First), verge = geneigte Ortganglängen, eaves = Trauflängen; `per_m` für Stückzahl; `invoice` = params.quantity unverändert.
- Fehler (`<storey>.roof_covering`): kein roof -> `Dach ohne Dachform`; Aufbau nicht Kategorie roof; unbekannte Fläche / Bauteil; Überstand < 0.

## Output / BOM / Web

- Storey-Ausgabe `roof_covering {faces[{slope, polygon, layers[{material, thickness, bottom_plane, top_plane, area}]}], openings[...], edges {ridge, verge, eaves}}`.
- BOM: Tabelle `roof_covering` (Schicht-Material, Fläche brutto/netto, Volumen), Bauteile (Fenster, Eindeckrahmen, Kamin-Teile, items mit berechneter Menge und Preis aus offers), totals `roof_area`, `roof_volume`; Materialvolumen addiert; VALIDATE-Zähler `roof_covering`.
- `/haus3d`: Checkbox `Dach` aktivieren (`dach3d`, localStorage, an DG-Sichtbarkeit gekoppelt), Schichten als geneigte Prismen (Ziegelfarbe oben, transparent wählbar), Fenster als Glas, Kamin als Quader bis 1,0 m über First; Tooltip Schicht/Bauteil, `(geschätzt)`.
- `/mengen`: Tabelle `Dach` (Schichten, Kanten mit Spalte „Rechnung“ und Differenz, Bauteile mit Preis); Summe.
- Schema `storey.schema.json` `roof_covering`; Spezifikationen core und web (Code wird aus den md-Abschnitten erzeugt, danach rehash).

## Implementation steps

1. Core: Spezifikation + `roof_covering_builder.py` (Helfer ab 256 Zeilen auslagern), Einbindung in `storey_builder.py`, BOM, VALIDATE; Schema.
2. Daten: Block in `upper.json`, Überstände nach dem ersten Lauf anhand des Rechnungsvergleichs festlegen.
3. Web: `/haus3d` Dach + Öffnungen, `/mengen` Tabelle Dach.
4. Tests: neu `scripts/smoke_roof_covering.py` (Flächen je Seite, Schichtstapel 0,2305 senkrecht, Öffnungsabzug = Fensterfläche, Kanten-Längen, Item-Mengen, Fehlerfälle auf Temp-Kopie); dazu `smoke_roof_structure.py`, `smoke_dg.py`, `check_haus3d_js.py`, `check_clean_code.py`, `core_validate.py`; rehash, Server neu starten, Browser-Check (ohne die Seite des Users zu wechseln).
5. Memory aktualisieren.

## Verification

- `core_validate.py` ok, Zähler enthält roof_covering; EG/Dachstuhl unverändert.
- Rechnungsvergleich in `/mengen` plausibel (Abweichungen benannt).
- `/haus3d`: Dach sitzt auf den Sparren, Fenster/Kamin an der richtigen Stelle, Checkbox schaltet.

## Critical files

- `code/weingaerten_core/compute/roof_covering_builder.py` (neu), `storey_builder.py`, BOM-Builder
- `house/storeys/upper.json`, `catalog/schema/storey.schema.json`
- `code/weingaerten_web/static/haus3d.js`, `pages/mengen_page.py`
- `weingaerten-core.md`, `weingaerten-web.md`
