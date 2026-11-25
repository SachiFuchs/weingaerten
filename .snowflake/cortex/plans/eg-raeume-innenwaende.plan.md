# Plan: EG-Räume und Innenwände

## Kontext
- `house/storeys/ground.json`: 6 Außenwände (`exterior-wall-ew1`, 30 cm, reference outside_face), lichtes Innenmaß ca. x 0,30–10,70 / y 0,30–7,12. Der Rücksprung NO (x 8,98–11, y 0–0,88) verschiebt dort die Innenkante nach y 1,18. `rooms: []`, keine Innenwände.
- Räume sind lichte Rechtecke. Ob es schon ein Innenwand-Assembly gibt, prüfe ich vor dem Anlegen. Wenn nicht, lege ich `assembly:interior-wall-iw1` an (ca. 0,12 m).
- Nach deinen Vorgaben: WZ Süd/West/Ost, Küche Ost, Bad Nord+Ost, Eingang West, Kammer zwischen Küche und WZ. Den Winterraum lasse ich weg.

## Annahmen (die Maße im Dokument passen nicht konsistent ins Haus)
- Flur 4,86 × 3,88 ergibt 18,9 m², das Dokument nennt aber 8,0 m². Ich nehme 4,86 × 1,65 an.
- Das WZ wird ein Rechteck im Südwesten mit der Restfläche (ca. 38,5 m² statt 39,7). Bei Bedarf kann ich es L-förmig in zwei Rechtecke teilen.
- Die Kammer liegt quer an der Ostwand (2,22 Ost-West, 0,78 Nord-Süd), so dass ihr Ostfenster 0,51 × 0,51 passt.

## Anordnung (lichte Rechtecke, m)
| Raum | x | y | Maß |
|---|---|---|---|
| Flur (Haustür West) | 0,30–5,16 | 0,30–1,95 | 4,86 × 1,65 |
| Bad (Nord+Ost) | 9,00–10,70 | 1,18–3,58 | 1,70 × 2,40 |
| Küche (Ost) | 8,05–10,70 | 3,70–6,15 | 2,65 × 2,45 |
| Kammer (Ost, zwischen Küche und WZ) | 8,48–10,70 | 6,27–7,05 | 2,22 × 0,78 |
| Wohnzimmer (Süd/West) | 0,30–7,93 | 2,07–7,12 | ca. 7,63 × 5,05 |

Die Innenwände (0,12 m) liegen zwischen den Raumkanten und sind achsparallel, ihre Endpunkte treffen sich. Die Raumhöhe von 2,35 m kommt als Raumattribut dazu, falls das Schema es erlaubt.

## Schritte
1. Schema/Core prüfen: Felder von Räumen und Innenwänden, vorhandenes Innenwand-Assembly
2. Falls nötig, Innenwand-Assembly im Katalog anlegen
3. Innenwände in ground.json eintragen
4. 5 Räume eintragen (room-flur, room-wohnzimmer, room-kueche, room-kammer, room-bad)
5. Validieren und im Browser kontrollieren

## Verifikation
- `scripts/core_validate.py` ohne Fehler
- `scripts/check_web.py`, Sichtprüfung /grundriss und /haus3d
- Raumflächen gegen die Tabelle im Dokument vergleichen

## Kritische Dateien
- [house/storeys/ground.json](house/storeys/ground.json)
- catalog/assemblies/ (Innenwand)
- scripts/core_validate.py
