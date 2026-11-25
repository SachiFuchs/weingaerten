---
name: "fassade im wandaufbau"
created: "2026-11-20T19:03:36.172Z"
status: pending
---

# Plan: Fassade als Schicht im Wandaufbau

## Context

- Das Material `facade-board-spruce` und die Farbe `facade-paint-taubenblau` gibt es schon in catalog/materials. Die Fassade hängt aber bisher als eigener Block `storey.facade` in upper.json und ist nicht Teil des Wandaufbaus.
- Alle DG-Außenwände nutzen derzeit `exterior-wall-ew1` mit 32,8 cm, Schichten von außen nach innen: Farbe weiß 0,5, Außenputz 1, Hohlziegel 30, Innenputz 1, Farbe 0,3 cm. Bezugslinie ist die Außenfläche (`reference outside_face`).
- Die Checkbox `fassade3d` wird ausgeliefert (geprüft per GET /haus3d). Dass sie im Browser fehlte, lag sehr wahrscheinlich an einem Tab vom alten Server. Nach dieser Änderung entfällt sie ohnehin.

## Steps

1. **Neuer Aufbau** `catalog/assemblies/exterior-wall-ew1-holz.json`, Name "Außenwand DG Hohlziegel 30 cm, Holzfassade Stülpschalung". Klasse wie ew1, `layer_order` outside\_in. Schichten:

   - Fassadenbrett 2,5 cm mit optionalem Schichtfeld `cladding {kind: lap_siding, board_length 5.0, board_width 0.20, overlap 0.03, paint: material:facade-paint-taubenblau}`
   - Hohlziegel 30, Innenputz 1, Farbe 0,3 cm
   - Summe 33,8 cm, also 1 cm mehr als ew1.
   - Das Schema `assembly.schema.json` bekommt das Feld `cladding` an der Schicht.

2. **Wände umstellen** (upper.json): w-dg-north, w-dg-east, w-dg-south-kammer und w-dg-west bekommen den neuen Aufbau. Die Wand soll nach außen wachsen, deshalb wird die Bezugslinie die Innenfläche (`reference inside_face`) und start/end liegen auf der bisherigen Innenkante, also 32,8 cm nach innen versetzt. Damit bleiben Räume und Innenmaße unverändert, die Fassade steht 1 cm über. Die Balkonwände behalten ew1. Die Öffnungen behalten ihre absolute Lage, die Offsets werden geprüft.

3. **Den Block `facade` in upper.json entfernen.** Der FacadeBuilder liest die Parameter künftig aus der äußeren Schicht des Wandaufbaus, sobald dort `cladding` gesetzt ist: wall.layers\[0] plus Aufbau. Die Berechnung (Reihen, Stöße, Dachschnitt, Öffnungen, Zuschnitt) bleibt gleich und läuft pro Geschoss automatisch. Das Ergebnis `storey.facade` behält seine Form, damit Mengenliste und /mengen unverändert weiterlaufen. Bretter und Farbe werden nur einmal gezählt: Das Schichtvolumen der Wand gilt als die Bretter, der Fassadenblock in der Mengenliste liefert nur Stückzahl, Zuschnitt und Farbfläche.

4. **3D**: Die Checkbox `fassade3d` und ihr localStorage-Eintrag entfallen. Die Fassadenbretter werden gezeichnet, wenn ihr Geschoss sichtbar ist. Die Wandschicht mit `cladding` wird nicht als glatte Fläche gezeichnet, sondern durch die Brettreihen ersetzt. "Wände transparent" gilt auch für die Bretter.

5. **Specs** (Core: Aufbau, Schicht `cladding`, FacadeBuilder-Quelle; Web: Checkbox entfernt) nachziehen, rehash\_cache.py ausführen, den Server neu starten.

## Verification

- smoke\_facade.py anpassen: Die Parameter kommen jetzt aus dem Aufbau, die Wandstärke ist 0,338, die Raumflächen im DG sind unverändert, keine Doppelzählung (das Brettvolumen der Wandschicht entspricht ungefähr dem Volumen in der Fassadenzeile), die Balkonwände haben keine Fassade.
- Danach laufen smoke\_roof\_covering, smoke\_roof\_structure, smoke\_dg, check\_haus3d\_js und check\_web.
- Sichtprüfung in /haus3d: keine Checkbox Fassade mehr, die Fassade verschwindet mit DG aus, die Ecken sind geschlossen.

## Hinweis

- Unter den Brettern ist weiterhin der Hohlziegel aus ew1 angenommen. Ob die DG-Wand tatsächlich gemauert oder eine Holzkonstruktion ist, ist nicht geprüft. Bei Holzständerwerk müsste der Aufbau angepasst werden.

## Critical Files

- catalog/assemblies/exterior-wall-ew1-holz.json (neu)
- house/storeys/upper.json (Wände, Block facade entfällt)
- code/weingaerten\_core/compute/facade\_builder.py (Quelle: Wandschicht)
- code/weingaerten\_web/static/haus3d.js und pages/haus3d\_page.py (Checkbox weg, Schicht durch Bretter ersetzen)
- catalog/schema/assembly.schema.json
