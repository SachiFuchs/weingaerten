# Plan: Kellergeschoss

## Lage (aus Skizze, Maßstab ~57 px/m, geeicht an 7,12 m)
- Außenmaß Keller x 0–7,12, y 2,08–5,38 (unter EG Treppe / Wohnzimmer-Nord / Küche). Wände Beton 30 cm → Innen x 0,30–6,82, y 2,38–5,08 (≈ 6,52 × 2,70 m).
- Höhen: Bodenplatte bs1 25 cm (Oberkante 0) → Kellerdecke-Unterseite −0,25; Raumhöhe 2,0 → `elevation` −2,25; Betonboden 20 cm von −2,45 bis −2,25.
- Treppe NW (Entscheidung: Skizze): massive Betontreppe unter der EG-Treppe, oben an der Westtür `o-1` (Treppenraum, y ≈ 2,55–3,45), läuft nach Osten hinunter; Lauf-Rect ca. x 0,30–2,14, y 2,38–3,26 (in den Daten aufwärts Richtung West, `to_storey: storey:ground`, 12 Steigungen ≈ 18,8 cm, Warnung „steile Treppe“ erwartet).
- Öltank-Schutzwände: L-förmige Beton-Innenwände 12 cm um den Westraum (x 0,30–2,72, y 3,54–5,08, wie skizziert); den Tank selbst modelliere ich nicht.
- Kaminfundament: `structure` post Beton ca. 0,40 × 0,50 an der Südwand bei x ≈ 4,3 (geschätzt), z −2,25 bis −0,25.
- Fenster: Ost- und Westwand jeweils mittig (y ≈ 3,73), 50 × 50, Brüstung 1,40 → Unterkante −0,85, Oberkante −0,35.
- Lichtschacht je Fenster: lichte Breite 0,80, Ausladung 0,50, Tiefe 0,80 unter Gelände. **Annahme:** Gelände −0,15 (geschätzt) → Sohle −0,95 (10 cm unter der Fensterunterkante). Schachtwände Beton 0,08, Gitterrost Stahl 0,03.

## Core (Spec `weingaerten-core.md`, danach Code neu erzeugen und rehashen)
1. **Erdgeschoss-Erkennung:** Erdgeschoss ist das Geschoss mit `elevation` = `foundation.top` (bisher das erste in der Liste). Ein Geschoss darunter wird ohne Fundament-Prüfung berechnet. `house.storeys` dann `[ground, upper, basement]` oder sortiert; die Web-Seiten sortieren schon nach Elevation (KG-Kürzel ist bereits vorgesehen).
2. **Treppe `construction: "solid"`:** massive Stufen, je ein Block von Lauf-Unterseite bis Trittoberkante. Keine Setzstufen und keine Wangen, Keilstufen sinngemäß. Default bleibt `stringer` (bisheriges Verhalten, byte-gleich).
3. **Bodenplatten-Aussparung:** `house.foundation.cutouts: [[x,y,w,h]]` für das Treppenloch. Die Fläche und das Volumen der Platte werden um die Aussparung reduziert, in 3D wird sie als Loch gezeigt. Die Aussparung liegt über dem Treppenlauf, die Lage an der Tür prüfe ich gegen die EG-Daten.
4. **Lichtschächte:** `storey.light_wells[]` `{id, name, wall, opening, width, projection, depth, terrain, wall_thickness, material, grating {material, thickness}, estimated, note}`.
   - Platzierung vor der Öffnung auf der Außenseite der Wand.
   - Fehler: Wand/Öffnung unbekannt, Maße ungültig, Sohle über Fensterunterkante (`Lichtschacht zu flach`).
   - Teile: 3 Schachtwände, Sohle, Gitter (Prismen) → `storey.light_wells` mit Volumen.
   - BOM: Zeilen pro Schacht + `totals.light_well_volume`.
5. Neues Builder-Modul `light_well_builder.py` (clean-code-Grenzen), Schema `storey` um `light_wells` und `construction` erweitern.

## Katalog
- Aufbauklassen prüfen/erweitern: Außenwand Beton 30 (`exterior-wall-kw1`, concrete-c25 0,30), Innenwand Beton 12 (`interior-wall-kw2`), Bodenaufbau `floor-kg-beton` (concrete-c25 0,20, Klasse floor-build-up bzw. slab, falls die Dickenbereiche das zulassen; sonst Bereich anpassen).
- Material `steel-grating` (Gitterrost verzinkt).
- Komponente `window-kg-kipp` 0,50 × 0,50, class:window, 1 Flügel `opening_1: tilt`, `glazing_type: double`, Beschreibung „Kippfenster alte Bauart, 2-fach“, `estimated`.

## Daten `house/storeys/basement.json`
- Name „Kellergeschoss“, elevation −2,25, height 2,0.
- 4 Außenwände (outside_face, Beton 30), 2 Innenwände Öltank, Raum „Keller“ (Rects), Raum „Öltank“ und Treppe.
- `floors` mit z −0,20, Fenster in w-kg-ost/w-kg-west, `light_wells`, `stairs`, `structure` Kaminfundament.
- `house.json`: Storey-Liste + `foundation.cutouts`.

## Web (`weingaerten-web.md`)
- `/haus3d`: Checkbox `geschoss3d-basement` (KG) automatisch. Lichtschächte und Gitter als Prismen (Beton grau, Gitter Metall, Tooltip). Betontreppe ohne Setzstufenfarbe. Bodenplatte mit Loch.
- `/grundriss?storey=basement` und `/waende`: Lichtschacht im Grundriss als Umriss mit Gitterschraffur.
- `/mengen`: Tabelle „Lichtschächte“, Treppe massiv.

## Tests
- Neu: `scripts/smoke_basement.py` (temporäres WEINGAERTEN_HOME) prüft:
  - Erdgeschoss-Erkennung unabhängig von der Reihenfolge;
  - Höhen (Wände −2,25..−0,25, Boden −2,45..−2,25);
  - Fensterlage, Lichtschacht-Geometrie und den Fehler „zu flach“;
  - massive Treppe (12 Blöcke, keine Wangen) und die verkleinerte Plattenfläche.
- Regression: smoke_stairs, smoke_dg, smoke_floor_heating, smoke_roof_covering, check_haus3d_js, check_kat_js, check_ceilings; Server über start.cmd neu starten und Seiten prüfen.

## Offene Annahmen (geschätzt markiert)
Geländehöhe −0,15, Kaminfundament-Maße, genaue Lage der Öltankwände und der Treppe aus der Skizze (±10 cm).
