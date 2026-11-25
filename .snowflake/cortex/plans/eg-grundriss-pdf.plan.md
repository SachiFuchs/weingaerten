# Plan: EG nach PDF-Grundriss

## Kontext
- Das PDF [data/Grundriss-Weingaerten8-EG.pdf](data/Grundriss-Weingaerten8-EG.pdf) zeigt ein Haus, das in Nord-Süd-Richtung lang ist: 7,12 m breit (West-Ost) und 13,13 m tief (Nord-Süd). Das aktuelle Modell ist 11 × 7,42 m groß, also völlig anders. Deshalb werden alle Wände, Räume und Öffnungen in [house/storeys/ground.json](house/storeys/ground.json) ersetzt.
- Kontrolle: Das WZ aus 3 Rechtecken ergibt 29,8 m², das PDF nennt 29,7 m². Küche 7,8 (PDF 7,7), Bad 4,5 (4,57), Kammer 2,55 (2,47), Treppe 2,8 (2,73). Die Maße passen also.
- Koordinaten: x = West nach Ost, y = Nord nach Süd, Außenkanten. Die Außenwand `exterior-wall-ew1` ist 0,328 m dick (laut PDF 0,30); die Innenkanten liegen deshalb 2,8 cm weiter innen.
- Rechteck-Räume: Das L-förmige WZ und der L-förmige Flur werden in mehrere Rechtecke geteilt, die denselben Namen tragen.
- Zimmer 2 im Süden (laut Dokument der Winterraum, kein Zugang zum Haus) gehört zum Baukörper. Ich nehme es als Raum auf, denn ohne es wäre der Umriss falsch. Die überdachte Terrasse wird nicht modelliert.

## Außenumriss (outside_face, outside left, im Uhrzeigersinn)
(1,01|0) -> (7,12|0) -> (7,12|13,13) -> (3,84|13,13) -> (3,84|9,94) -> (0|9,94) -> (0|2,08) -> (1,01|2,08) -> (1,01|0)
Das sind 8 Wände: Nord, Ost (durchgehend), Süd Zimmer 2, West Zimmer 2, Süd WZ (Terrasse), West WZ, Nord Treppe (kurz), West Eingang.

## Innenwände
Neue Aufbauten: `interior-wall-iw1` (0,12, gibt es schon) und neu `interior-wall-iw2` 0,30 m (ehemalige Außenwand vor dem Anbau von 1960: Ziegel 0,28 + 2 × 1 cm Putz). Alle Wände mit reference center.

| Wand | Aufbau | von | bis |
|---|---|---|---|
| Alte Nordwand West (Flur/Treppe) | iw2 | (1,338, 2,23) | (3,24, 2,23) |
| Alte Nordwand Ost (Bad/Küche) | iw2 | (4,095, 2,23) | (6,792, 2,23) |
| Flur/Bad | iw1 | (4,155, 0,328) | (4,155, 2,08) |
| Gang/Küche/Kammer | iw1 | (4,155, 2,38) | (4,155, 6,62) |
| Treppe Ost | iw1 | (3,18, 2,38) | (3,18, 3,495) |
| Treppe Süd | iw1 | (0,328, 3,435) | (3,24, 3,435) |
| Küche/Kammer | iw1 | (4,215, 5,45) | (6,792, 5,45) |
| Kammer/WZ | iw1 | (4,215, 6,56) | (6,792, 6,56) |
| WZ/Zimmer 2 | iw2 | (3,84, 9,776) | (6,792, 9,776) |

## Räume (rect [x, y, w, h], lichte Maße)
- Flur: [1,338, 0,328, 2,757, 1,752] + Flur (Gang): [3,24, 2,08, 0,855, 2,91]
- Bad: [4,215, 0,328, 2,577, 1,752]
- Treppe: [0,328, 2,38, 2,792, 0,995]
- Küche: [4,215, 2,38, 2,577, 3,01]
- Kammer: [4,215, 5,51, 2,577, 0,99]
- Wohnzimmer: [0,328, 3,495, 2,912, 1,495] + [0,328, 4,99, 3,767, 4,622] + [4,095, 6,62, 2,697, 3,006]
- Zimmer 2 (Winterraum): [4,168, 9,926, 2,624, 2,876]
- Die bisherigen Räume Diele und Gang fallen weg.

## Öffnungen (bestehende Katalog-Bauteile, Lage aus dem PDF abgegriffen, ca. ±10 cm)
- West Eingang: Haustür `door-d1` (Flur)
- Nord: Flur-Fenster `window-eg-flur`
- Ost: Bad `window-eg-bad`, Küche `window-eg-kueche`, Kammer `window-eg-kammer`, WZ `window-wz-klein`
- West WZ: `window-wz-gross` (2,97 m, ca. y 6,1-9,1)
- Süd WZ (Terrasse): `window-wz-terrasse` und die Terrassentür
- Zimmer 2: Holztür West 1,00 × 2,00 und Fenster Süd 2,00 × 1,50
- Neue Bauteile nach den Maßen im Dokument (Klassen door/window): `door-terrasse` (Annahme 1,00 × 2,10, das Maß ist im Dokument nicht angegeben), `door-winterraum` (1,00 × 2,00) und `window-winterraum` (2,00 × 1,50, einfach verglast).
- Die Platzhalter `window-w1` und `window-small` werden nicht mehr verwendet; sie bleiben aber im Katalog.

## Schritte
1. Assembly `interior-wall-iw2` und die 3 neuen Bauteile anlegen
2. Außenwände in ground.json ersetzen (8 Wände)
3. Innenwände ersetzen (9 Wände)
4. Räume ersetzen
5. Öffnungen setzen (offset ab Wandanfang)
6. Beschreibung in house.json anpassen ("7,12 × 13,13 m"), validieren und im Grundriss prüfen

## Verifikation
- `scripts/core_validate.py`: keine Fehler und keine Öffnungskonflikte
- Raumflächen mit dem PDF vergleichen
- Server neu starten (start.cmd), `scripts/check_web.py`, Sichtprüfung /grundriss und /haus3d

## Kritische Dateien
- [house/storeys/ground.json](house/storeys/ground.json)
- [house/house.json](house/house.json)
- catalog/assemblies/interior-wall-iw2.json
- catalog/components/door-terrasse.json, door-winterraum.json, window-winterraum.json
