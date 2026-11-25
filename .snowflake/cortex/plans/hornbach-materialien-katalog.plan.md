# Plan: Hornbach-Baustoffe in den Katalog übernehmen

## Kontext
- [scripts/import_materials.py](scripts/import_materials.py) übernimmt Baustoffe aus `catalog/imported_material` nach `catalog/materials`. Es ist für Hornbach schon vorbereitet:
  - `SUPPLIERS` enthält „HORNBACH Baumarkt AG“ und `RECEIPTS` die Datei `hornbach_purchases.json`.
  - `photos_of` findet die Bilder `hornbach-<Artikelnr>_<n>.jpg`.
  - Eine Firma `company:hornbach` gibt es noch nicht. Das Skript legt sie an.
- Grund, warum bisher nichts übernommen wurde: `category_of` und `CATEGORIES` kennen nur OBI-Pfade (`Start/Bauen/...`, `Start/Wohnen/...`). Hornbach-Pfade beginnen mit `Sortiment/...`.
- Relevante Hornbach-Kategorien (Anzahl Artikel):
  - Farbe: Farben (10)
  - Baustoffe: Rohbau (5), Fassadendämmung (3), Dämmung (1), Trockenbau (2), Sanierung (2), Bedachung (2), Spachtelmasse (2), Kleber & Kleister (2)
  - Entwässerung: Baustoffe/Entwässerung (9)
  - Holz: Bauholz (7), Leisten (2), Möbelbau & Holzplatten (4), OSB Platten & Verlegeplatten (1)
  - Fliesen: Fliesen (1)
  - Zusammen rund 50 Kandidaten.
- Nicht übernommen werden, wie bei OBI: Malerbedarf, Fliesenzubehör, Eisenwaren, Sanitär, Elektro, Werkzeug, Garten, Türen und Fenster. Ebenso die 59 Artikel ohne Produktseite.

## Schritte
1. **Kategorie-Zuordnung**: Eine Tabelle `HORNBACH_CATEGORIES` (Pfadpräfix ohne `Sortiment/` -> Schlüssel in `CATEGORIES`) mit den Pfaden oben. `category_of` prüft zuerst die OBI-Regel und danach diese Tabelle. Die OBI-Logik bleibt unverändert.
2. **Preisbasis**: Hornbach rechnet manche Positionen nach Gewicht ab (Einheit `Kilogramm`). In diesem Fall bekommt das Angebot `price_basis` "gross per kg", und `source` nennt die Einheit. Bei der Einheit `ST` bleibt alles wie bisher.
3. **Dry run**: `python scripts/import_materials.py` ausführen. Ich zeige dir die Liste (id, Kategorie, bester Preis, Name) und die neuen Firmen (hornbach und Hersteller) zur Freigabe.
4. **Ausschlüsse nachschärfen**: Was du in der Vorschau streichst, kommt in `NOT_MATERIAL` oder in die Ausschlussliste.
5. **Schreiben** nach deiner Freigabe: `python scripts/import_materials.py --write` legt die Materialien, die Firmen und die Fotos in `catalog/photos/<id>/` an.

## Verifikation
- Ein zweiter Dry run nach `--write` zeigt 0 neue Hornbach-Materialien, es entstehen also keine Duplikate.
- `scripts/check_material_products.py` und `scripts/core_validate.py` laufen ohne neue Fehler.
- Die bisherigen 102 Materialien bleiben unverändert (Vergleich der Dateien vorher und nachher).
- Im Browser `/katalog/materialien`: Ein Hornbach-Material zeigt Foto, Hersteller und Angebot mit Kassenbon. `/katalog/firmen` zeigt HORNBACH.

## Kritische Dateien
- [scripts/import_materials.py](scripts/import_materials.py) - Kategorie-Zuordnung, Preisbasis
- [catalog/imported_material](catalog/imported_material) - Hornbach-Quelldateien (werden nur gelesen)
- [catalog/imported_purchases/hornbach_purchases.json](catalog/imported_purchases/hornbach_purchases.json) - Kassenbons für die Angebote
- [catalog/companies](catalog/companies) - neue Firma hornbach und Hersteller
