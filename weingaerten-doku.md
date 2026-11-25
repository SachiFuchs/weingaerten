# Fachliches Modell – Haus Weingärten

Diese Seite wird vom Web-Server aus der Datei `weingaerten-doku.md` erzeugt und erscheint in **Tech.Doku › Fachliches Modell**; Änderungen sind beim nächsten Aufruf sichtbar, ohne Neustart. Die Bedienung der Anwendung beschreibt das **Benutzerhandbuch**.


## Referenzkette

Wand (Instanz im Geschoss) → Bauteilaufbau (Typ im Katalog) → Schichten → Material.

Wand → Öffnungen → Bauteil (z. B. Fenster) → Klasse (z. B. „Fenster“, legt die Parameter fest); Bauteil → Materialien je Rolle (Rahmen, Verglasung, Türblatt); Öffnung → Laibungsmaterial.

Referenzen werden als `<typ>:<id>` geschrieben, z. B. `assembly:exterior-wall-ew1`, `component:window-w1` oder `class:window`.

## Erstes Beispiel

Vier Außenwände, Außenmaß 11 m × 7 m, Wandhöhe 2,75 m, auf einer Bodenplatte (Oberkante 0).

| Nr | Schicht (außen → innen) | Dicke |
|---|---|---|
| 1 | Fassadenfarbe weiß | 0,5 cm |
| 2 | Außenputz | 1 cm |
| 3 | Hohlraumziegel | 30 cm |
| 4 | Innenputz | 1 cm |
| 5 | Innenfarbe weiß | 0,3 cm |

Gesamtdicke 32,8 cm. Der Wärmeleitwert der Materialien folgt später.

Öffnungen im Beispiel: zwei Fenster 2-flüglig 1,20 × 1,35 in der Südwand (Brüstung 90 cm), die Haustür 1,01 × 2,13 in der Nordwand, das „Fenster Klein“ 0,50 × 0,50 in der Ostwand (Brüstung 150 cm).

## Klassen und Bauteile

- Eine **Klasse** (Fenster, Tür, …) beschreibt, welche Parameter ihre Bauteile haben (Name, Typ Länge/Zahl/Auswahl/Ja-Nein, Default, Min, Max, Pflicht) und welche Materialrollen. Das **Rezept** der Klasse bestimmt die Zeichnung; Fenster und Tür brauchen Breite, Höhe, Tiefe, Rahmenbreite, das Fenster zusätzlich die Anzahl Flügel (0 = fest verglast, 1, 2). Ein **Durchgang** (Rezept `passage`) ist eine Wandöffnung ohne Zarge und Türblatt und braucht nur Breite und Höhe.
- Ein **Bauteil** gehört zu einer Klasse, hat Werte für deren Parameter, ein Material je Rolle und die Markierung **für Öffnungen geeignet**.
- Eine Klasse kann nur so geändert werden, dass alle ihre Bauteile gültig bleiben.

## Produkte, Hersteller und Lieferanten

- Ein Bauteil kann als Ganzes ein **Produkt** sein (z. B. ein Fenster IDEAL 4000 oder ein VELUX-Dachfenster): mit **Hersteller**, Modell, Artikelnummer und einer Liste von **Angeboten** (Lieferant, Stückpreis, Währung, netto/brutto, Datum, Beleg).
- Auch ein **Material** kann ein gekaufter Artikel sein (z. B. aus OBI-Einkäufen), zusätzlich mit EAN und Shop-Link. Importierte Baumarkt-Artikel landen zuerst in `catalog\imported_material\`; `scripts\import_materials.py` übernimmt die Baustoffe daraus als Materialien (Angebote aus den Kassenbons in `catalog\imported_purchases\`). Der Import-Ordner bleibt erhalten, `imported_from` im Material merkt sich die Quelle. Die Tabellen „Produktdaten“ und „Maße & Gewicht“ der Produktseite liest `scripts\fetch_obi_details.py --write` (OBI, Seiten-Cache in `scripts\obi_pages\`) bzw. `scripts\import_hornbach.py` (Hornbach, aus den Artikelmerkmalen) in die Import-Dateien; `import_materials.py --write` übernimmt sie als `product.details` (`product_data`, `dimensions_weight`) – auch in bereits importierte Materialien. Die Katalog-Detailansicht zeigt sie als eigene Abschnitte.
- Hersteller und Lieferanten sind **Firmen** (`catalog\companies\`) mit den Rollen Hersteller und/oder Lieferant. Eine Firma, die in einem Produkt verwendet wird, kann nicht gelöscht und ihre verwendete Rolle nicht entfernt werden.
- In den Mengen erscheinen je Bauteil der Hersteller, der günstigste Stückpreis und die Summe.
- **Dokumente** (`catalog\documents\`, Ref `document:<id>`) sind die Rechnungen, Angebote, Auftragsbestätigungen und Gutschriften zum Haus. Sie kommen nur über `scripts\import_documents.py [--write]` aus dem Eingang `catalog\imported_documents\` (nur Objekt `weingaerten-8`; der Eingang bleibt erhalten) und sind im Browser nur lesbar. Der Lieferant ist eine Firma mit Rolle Lieferant; Einheiten werden vereinheitlicht (Original in `unit_raw`); `items_gross` markiert Belege mit Brutto-Positionen, `deductions_net` Abzüge ohne eigenes Feld (Abschläge, Rabatte); `related` verbindet Angebot und Rechnung. Positionen können per `ref` auf ein Material oder Bauteil zeigen; daraus entsteht dort ein Angebot mit `document`. Summen, die nicht aufgehen, sind Warnungen („Belegsumme weicht ab“). Auch das Angebot eines Bodens (`floors[].offer.document`) kann ein Dokument sein.
- **Materialien** sind echte Baustoffe: Glas ist ein Material (`glass`); 2- oder 3-fach-Verglasung ist eine Eigenschaft des Fensters (Parameter Verglasungsart, Ug-Wert), kein Material.

## Öffnungen

- Eine Öffnung ist ein Unterelement einer Wand: Bauteil, Abstand vom Wandanfang (`offset`), Brüstung (`sill`), Fuge (`joint`, Standard 1 cm), Einbautiefe von außen (`inset`, Standard 10 cm) und Laibungsmaterial.
- **Das Bauteil bestimmt die Größe:** Rohbauöffnung = Bauteilmaß + 2 × Fuge.
- Geprüft wird: Öffnung innerhalb der Innen- und Außenfläche der Wand, unter der Wandoberkante, keine Überlappung, Bauteil nicht tiefer als die Wand.
- Der Core zerlegt jede Schicht in **Stücke** um die Öffnungen – Volumen und Flächen werden dadurch automatisch um die Öffnungen vermindert; Laibungen werden als eigene Flächen gezählt.
- Ein **Durchgang** hat keine Teile; Tiefe, Rahmen und Einbautiefe sind 0, die Laibung läuft über die ganze Wanddicke.

## Räume, Beläge und Schächte

- **Raum** (`storey.rooms[]`, IFC `IfcSpace`): ein Vieleck im **Lichtmaß** (`polygon`, fertige Innenoberflächen) mit nur rechten Winkeln – wie die Wände im 90°-Raster. Ein L-förmiger Raum wie das Wohnzimmer ist **ein** Raum mit 8 Ecken. Dazu `number` (im Haus eindeutig, z. B. `0.06`), `name`, `usage` (Nutzung nach DIN 277: NUF 1–7, TF 8 Technik, VF 9 Verkehr) und optional die lichte Höhe `height`. Ohne Höhe gilt Geschosshöhe minus Bodenaufbau. Der Core rechnet Fläche, Umfang, Volumen und die Wandflächen je Raum; intern zerlegt er das Vieleck in Rechtecke (für Böden, Heizung, Durchbrüche). Mehrere Räume dürfen gleich heißen (z. B. die Abseiten im DG); Boden und Heizung meinen dann alle Räume dieses Namens.
- **Belag** (`room.coverings[]`, IFC `IfcCovering`): ein eigener **Aufbau** der Kategorie `covering` (Schichten vom Untergrund zum Raum, z. B. Kleber + Fliese). Am **Boden** gilt er für den ganzen Raum (`area: "room"`) oder für eine rechtwinklige Teilfläche; Teilflächen ersetzen dort den Raumbelag und dürfen sich nicht überlappen. An der **Wand** (Fliesenspiegel, Sockelleiste) gilt er für alle oder einzelne Wandflächen des Raums (Bereich `u` entlang der Wand) und einen Höhenbereich `z`; Türen und Fenster werden ausgespart. Der Oberbelag liegt **auf** dem Bodenaufbau; der Bodenaufbau (Estrich, Heizung, Dämmung, Bestand) bleibt unverändert.
- **Schacht** (`house.shafts[]`, IFC `IfcOpeningElement`): eine rechtwinklige Öffnung durch mehrere Geschosse, von `from_storey` (dessen Boden geöffnet wird) bis `to_storey` (dessen Decke geöffnet wird, dessen Boden bleibt zu). Er schneidet Böden, Decken und Beläge dazwischen; Heizkreise und Deckenbalken im Schacht werden gemeldet. Leitungen im Schacht (`penetrations`) müssen ihn wirklich durchlaufen. Beispiel: Versorgungsschacht Küche vom DG bis in den Keller um Fallleitung und Trinkwasser-Steigleitungen (Lage geschätzt).
- **Möblierung** (`room.furniture[]`) ist im Schema vorbereitet und wird noch nicht ausgewertet.

## Tragwerk und Außenflächen

- **Tragwerk** (`storey.structure[]`): Unterzüge (`beam`: Material, Breite, Höhe, Achse `start` → `end`, Oberkante `z_top`, Standard Geschosshöhe) und Stützen (`post`: Material, Breite in x, Tiefe in y, Mittelpunkt `position`, `z0`…`z1`). Der Core rechnet Grundfläche, Höhe, Länge und Volumen; das Volumen zählt beim Material mit.
- **Außenflächen** (`storey.outdoor_areas[]`, z. B. die überdachte Terrasse): Rechteck `[x, y, w, h]` außerhalb der Außenwände. Ein Dach darüber ist eine Decke mit eigenem `outline`.
- **Decken mit eigenem Umriss:** das Erdgeschoss hat drei Decken – Flachdach (Betondecke 15 cm, Folie) über Flur und Bad, Holzbalkendecke mit Bekleidung über dem Rest, Holzdach über der Terrasse.

## Regeln

- **Außenwände** sind von außen nach innen geschichtet (`outside_in`); die Wand gibt mit `outside` an, auf welcher Seite der Linie außen ist, und mit `reference`, wo die Linie im Querschnitt liegt (hier: Außenoberfläche).
- **Innenwände** (kommen später) sind in Laufrichtung von links nach rechts geschichtet (`left_right`).
- **Wände und Räume sind getrennt:** eine Außenwand kann an mehrere Räume grenzen; welche Wandfläche zu welchem Raum gehört, berechnet der Core.
- **Ecken** werden auf Gehrung gerechnet – jede Schicht stößt an die gleiche Schicht der Nachbarwand, auch an einspringenden Ecken (Versprung).
- **Wände** sind freie Einzelwände im 90°-Raster; berühren sich Endpunkte, entsteht eine Ecke. Die Außenwände ergeben zusammen den **Umriss** – das Haus muss kein Quader sein.
- **Bodenplatte** folgt dem Umriss (`follow: outline`, optional mit Überstand); ist der Umriss offen, wird sie nicht berechnet (Warnung).
- **Öffnungen behalten ihre absolute Lage**, wenn eine Wand verschoben oder verlängert wird; ragt eine Öffnung danach über die Wand, wird das als Öffnungskonflikt gemeldet und auf der Seite Wände korrigiert.
- **Räume** werden im Lichtmaß (fertige Innenoberflächen) als rechtwinkliges Vieleck angegeben.
- **Darstellung:** in der Ansicht sieht man die äußerste Schicht jeder Seite, im Schnitt alle Schichten mit Farbe und Schraffur des Materials.

## Ausblick

Einbauteile (Steckdosen, Schalter) werden eine weitere Bauteil-Klasse. Innenwände, Giebelwände und ein Sockel sind vorbereitet, werden aber noch nicht berechnet.

## Systematik KG 300 / KG 400 (Datenmodell)

Die Begriffe folgen DIN 276: **Baukonstruktion (KG 300)** und **Technische Gebäudeausrüstung (KG 400)**, verbunden über gemeinsame Basisklassen und **Durchdringungen**. Stand: Datenmodell; ausgewertet wird bisher das Abwasser (siehe unten).

| Begriff | Ablage | Bemerkung |
|---|---|---|
| Baustoff | `catalog\materials\` | λ (`conductivity`), ρ (`density`), μ (`vapour_resistance`), Baustoffklasse (`fire_class`), Herkunft (`values_source`) |
| Kostengruppe | `catalog\reference\din276.json` | Codes 300–360, 400–440; Gewerk (`trade`) hängt an der KG |
| Schicht | `assembly.layers[]` | Reihenfolge = Listenreihenfolge + `layer_order` |
| Bauteil (Wand, Gründung) | Aufbau mit `din276` + Wand bzw. Bodenplatte | U-Wert wird berechnet (später); Overrides: `fire_rating`, `airborne_sound_rw_db`, `impact_sound_lnw_db`; Gründung: `waterproofing`, `white_tank`; Wand: `load_bearing` |
| Decke, Dach | `storey.ceilings[]`, `house.roof` | **Vorschlag**, noch ohne Daten |
| Öffnungsabschluss (Fenster, Tür) | `catalog\classes\`, `wall.openings[]` | neue optionale Parameter: Verglasung, g-, Uw-Wert, Einbruchschutz, Rauch-/Brandschutz; KG aus der Wand (330 → 334, 340 → 344) |
| TGA-Klasse | `catalog\tga-classes\` | `kind`: Rohrleitung, Elektrische Leitung, Lüftungskanal (Leitungsträger) oder Endstelle |
| TGA-Komponente | `catalog\tga-components\` | Produkt mit `din276` (41x–44x) und `system_type`; zurzeit nur Muster |
| Leitung | `house\tga\runs\` (Schema `tga-run`) | Verlauf `points[]`, Länge berechnet |
| Endstelle | `house\tga\terminals\` (Schema `tga-terminal`) | Punkt im Raum/an der Wand |
| Durchdringung | berechnet; `house\penetrations.json` nur für Bestätigungen | Leitung × Bauteil (`through`) oder Endstelle × Wand (`recess`); Brandschott aus `fire_rating`, Luftdichtheit aus Außenbauteil |

Abweichungen vom Ausgangsdiagramm: Baustoff ist kein Gebäudeelement (keine KG); bauphysikalische Werte des Bauteils werden berechnet statt gespeichert; Öffnungen bleiben Teil der Wand; Gewerk und Leitungslänge werden abgeleitet.

### Abwasser

Erstes ausgewertetes TGA-System (KG 411, Stand Nov 2026, Lage und Höhen geschätzt nach Skizze):

- **Rohre:** `tga-component` der Klasse `pipe` mit `medium: waste_water` und `system_line` `ht` oder `kg`; `stock.lengths` = lieferbare Stangen (kürzbar). Sortiment: KG DN 110 (2 / 1 / 0,5 m), HT DN 50 (1 / 0,5 / 0,25 m). HT DN 90 ist als Platzhalter (`estimated`) angelegt.
- **Formteile:** Klasse `pipe-fitting` – Bogen, Abzweig, Übergang (KG DN 110 auf HT DN 90 / DN 50), Stopfen; `z_length` = Baulänge, die vom Rohr abgeht. Platzhalter: KG-Abzweig 110/110 45°, HT-Bögen DN 90, Stopfen.
- **Leitung** (`house\tga\runs\`): Achse `points[]` mit absolutem z in Fließrichtung; `into` = mündet in eine andere Leitung (`continue` = geht über, `branch` = Abzweig auf deren Achse). Mindestgefälle HT 2 %, KG 1 % (`min_slope`).
- **Berechnet:** Gefälle je Abschnitt, Durchbrüche durch Wände, Decken, Böden und Bodenplatte (Kernbohrung = Außendurchmesser + 2 cm, Außenbauteile abdichten), Formteile an jedem Knick und jeder Einmündung, Zuschnitt der Stangen und Stückliste.
- **Verlauf:** Bad EG (WC DN 90; Dusche und Waschbecken DN 50 über Abzweige in eine HT-Sammelleitung DN 90) durch die Außenwand Ost nach außen; Küche: Spüle DN 50 als Abzweig in die Fallleitung DN 90 (verschlossener Stutzen im DG), durch EG-Decke, EG-Boden, Bodenplatte in den Keller und durch die Kellerwand Ost; alles über KG DN 110 in die Grundleitung Ost zur Kläranlage.

### Zuwasser

Trinkwasser (KG 412), Version 2 vom Nov 2026. Lage geschätzt, die genauen Leitungsbahnen kommen später:

- **Rohre:** PPR DN 20 (`ppr-rohr-dn-20-x-2-m`, Stange 2 m, Außendurchmesser 2 cm, `system_line: ppr`). Dasselbe Rohr dient für Kalt- und Warmwasser; das Medium steht an der Leitung (`tga-run.medium` = `cold_water` | `hot_water`).
- **Formteile:** PP-R-Schweißwinkel 90° (`ppr-bend-20-90`), PPR-Winkel 45° (`ppr-winkel-45deg-dn-20`), T-Stück DN 20/20 (`ppr-tee-20`, Platzhalter, nicht im Sortiment), Endkappe (`ppr-cap-20`). Die Baulängen sind geschätzt. An jedem Anschluss sitzt eine Schweiß-Wandscheibe mit Innengewinde ½″ (`ppr-wall-plate-20`, Endstellen-Art `wall_plate`).
- **Regeln:** Die Leitungen laufen 5 cm vor der Wand, warm oben (z 0,25 m), kalt darunter (z 0,20 m). Die Höhen gelten ab Rohfußboden. Ein Abzweig endet auf der Achse seiner Zuleitung (`into`, `branch`) und wird dort zum T-Stück.
- **Kreuzungen:** Wo sich zwei Leitungen kreuzen, legt der Core automatisch eine Schleife mit 4 × 45° an. Die Leitung mit mehr Platz bis zum nächsten Knick oder Abzweig weicht aus, und zwar von der Wand weg, um Außendurchmesser + 1 cm.
- **Verlauf:** Die Steigleitungen kalt und warm laufen im Versorgungsschacht neben dem Abwasser-Fallrohr vom Keller (offen, Endkappe) bis ins DG. Dort enden sie verschlossen für das spätere Bad. Die EG-Hauptleitungen zweigen ab und laufen an der Ostwand durch die Wand Bad/Küche ins Bad. Davon gehen die Anschlüsse ab: Spüle (warm + kalt, z 0,50), Dusche (warm + kalt, z 1,10), Waschbecken an der Wand zur Küche (warm + kalt, z 0,50) und WC-Spülkasten (nur kalt, z 0,50). Daten erzeugt `scripts\build_water_supply_data.py`, Test `scripts\smoke_water_supply.py`. In der 3D-Ansicht sind die Leitungen grün (kalt dunkel, warm hell).

## IFC-Zuordnung

Klassen, Aufbauten, TGA-Klassen und Bauteile können das optionale Feld `ifc` tragen: `{ "entity": "IfcWindow", "predefined_type": "WINDOW" }`. Gemeint ist die IFC4-Instanzklasse; der Typ (`IfcWindowType`, `IfcWallType` + `IfcMaterialLayerSet` beim Aufbau) ergibt sich daraus. Bei `predefined_type` `USERDEFINED` steht die Bezeichnung in `object_type`. Ein Bauteil überschreibt die Zuordnung seiner Klasse (Balkontür in Klasse Fenster → `IfcDoor`, Dachfenster → `IfcWindow` `SKYLIGHT`, Dachrinne → `IfcPipeSegment` `GUTTER`). Der Core wertet das Feld nicht aus; es ist die Grundlage für einen späteren IFC-Export. Bearbeitbar auf den Katalogseiten Aufbauten, Bauteile und Klassen; TGA-Klassen nur in der Datei. Erstbelegung: `scripts\set_ifc_mapping.py`.

| Element | IFC |
|---|---|
| Außenwand, Innenwand 28 cm | `IfcWall` `STANDARD` |
| Innenwand 10 cm, Kellerinnenwand | `IfcWall` `PARTITIONING` |
| Bodenplatte / Kellerboden | `IfcSlab` `BASESLAB` / `FLOOR` |
| Flachdach, Terrassendach, Steildach | `IfcSlab` `ROOF` |
| Deckenbekleidung / Fußbodenaufbau | `IfcCovering` `CEILING` / `FLOORING` |
| Raum | `IfcSpace` `INTERNAL` (Grundfläche = `polygon`, Nutzung DIN 277, Nummer) |
| Bodenbelag / Wandbelag / Sockelleiste | `IfcCovering` `FLOORING` / `CLADDING` / `SKIRTINGBOARD` (Aufbauten der Kategorie `covering`) |
| Schacht | `IfcOpeningElement` `OPENING` (durch mehrere `IfcSlab`) |
| Fenster / Tür / Durchgang | `IfcWindow` `WINDOW` / `IfcDoor` `DOOR` / `IfcOpeningElement` `OPENING` |
| Dachbauteil (allgemein) | `IfcBuildingElementProxy` `ELEMENT`, Bauteile mit eigener Zuordnung (Covering, Member, Beam, DiscreteAccessory) |
| Rohr / Leitung / Kanal / Endstelle | `IfcPipeSegment` / `IfcCableSegment` / `IfcDuctSegment` / `IfcFlowTerminal` |
