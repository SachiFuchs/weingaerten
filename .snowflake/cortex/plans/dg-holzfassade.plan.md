---
name: "dg holzfassade"
created: "2026-11-20T17:49:31.638Z"
status: pending
---

# Plan: DG-Holzfassade

## Context

- DG = storey:upper (house/storeys), Wände mit shape {kind: roof}. Die Oberkante folgt dem Dach, die Profile kommen aus RoofProfile bzw. WallData.top\_at.
- Vorbild für ein Hüllelement: `storey.roof_covering`, umgesetzt in roof\_covering\_builder. Es erzeugt eine eigene BOM-Tabelle, eine 3D-Checkbox und eine Tabelle in /mengen.
- Der Balkon t-balkon liegt im Südosten. Seine Außenwände und die Trennwand iw-dg-balkon-trenn werden ausgenommen.
- Code liegt im non-code-cache und wird aus den md-Spec-Abschnitten erzeugt. Nach Änderungen muss rehash\_cache.py laufen.

## Daten

- Material `spruce-cladding-taubenblau`: Fichte mit Anstrich taubenblau, color ca. #7D8FA6, estimated.
- Komponente/Produkt `board-stuelp-500x20x2.5`: Länge 5,00, Breite 0,20, Dicke 0,025.
- In der Datei für storey:upper kommt hinzu: `facade { board: component, overlap 0.03 (Deckbreite 0,17), start_z (Unterkante DG / Geschossdecke), walls: auto = exterior ohne balcony_exclude [Wand-IDs am Balkon], joint_stagger true, color }`.
- Eine Unterkonstruktion gibt es nicht.

## Core

- Neue Datei compute/facade\_builder.py. Für jede Fassadenwand wird die Außenfläche über das Profil abgewickelt (Giebeldreieck bzw. Kniestock). Daraus ergeben sich Reihen n = ceil(h / 0,17).
- Jede Reihe ist ein Brett, das um 2,5 cm von der Wand absteht. Die Schräge kippt die Bretter (Stülpneigung). Die Bretter sind oben an der Dachlinie gekappt, Fenster und Öffnungen werden ausgespart.
- Ist eine Reihe länger als 5 m, wird sie gestückelt. Der Stoßversatz wechselt pro Reihe um 2,5 m. Reststücke über 0,5 m werden wiederverwendet (einfache Verschnittrechnung).
- Ergebnis in der BOM: facade\[] pro Wand (Reihen, lfm, Fläche, Brettanzahl), totals.facade\_boards, facade\_area, facade\_volume, Verschnitt in %, dazu die Anstrichfläche (beidseitig plus Kanten optional, Standard ist die Sichtseite).

## Web

- /haus3d: neue Checkbox fassade3d im Fieldset Stockwerke, Speicherung in localStorage. Bretter werden als Prismen in Taubenblau mit sichtbaren Fugenkanten gezeichnet.
- /mengen: neue Tabelle Fassade.
- /waende: in der Wandansicht wird die Brettteilung optional als Linien angezeigt.

## Verification

- Neuer Test scripts/smoke\_facade.py prüft: Balkonwände sind ohne Fassade; Reihenzahl = ceil(Höhe/0,17); kein Brett ist länger als 5 m; die Fläche ist plausibel gegenüber der Wandfläche minus Öffnungen.
- scripts/check\_haus3d\_js.py und scripts/check\_web.py laufen weiterhin durch.
- Sichtprüfung in /haus3d im Vergleich mit den Fotos.

## Critical Files

- house/storeys/upper.json: facade-Block
- compute/facade\_builder.py (neu, im Cache) plus der dazugehörige md-Spec-Abschnitt
- BOM-/Mengen-Seiten (pages/\*), haus3d\_page.py, static/haus3d JS
- catalog/materials und catalog/components: neue Einträge
