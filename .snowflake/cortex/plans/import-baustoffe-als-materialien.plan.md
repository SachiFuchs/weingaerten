# Plan: Import-Baustoffe als Materialien übernehmen

## Kontext
- `catalog/imported_material` (1078 Artikel von OBI und Hornbach, Bilder in `imported_material/images`, 265 Dateien) ist nur der Eingangsordner. Er bleibt erhalten.
- Entscheidungen: nur Baustoffe übernehmen; ein Material je Artikel; Importdateien behalten.
- Baustoffe nach `category_path`: Wohnen/Farben, Wohnen/Tapeten, Bauen/Baustoffe, Bauen/Bauholz, Bauen/Fliesen, Bauen/Entwässerung (zusammen rund 140). Artikel ohne Kategorie (429, meist Hornbach) bleiben vorerst draußen, ebenso Elektro, Sanitär, Werkzeug, Pflanzen und Eisenwaren.
- Vorhandenes Muster: `component.product {manufacturer company:, model, article_no, offers[{supplier, price, currency, price_basis, date, source}]}` mit `ProductValidator` (core), `productView()` in `static/katalog.js:60`, Firmen in `catalog/companies` und Fotos in `catalog/photos/<id>/` (Feld `photos[]`).
- Kaufdatum und Markt stehen in `catalog/imported_purchases/obi_purchases.json` (Kassenbons nach Artikelnummer).

## Schritte
1. **Schema**: `material.schema.json` übernimmt den `product`-Block aus dem component-Schema. Außerdem bekommt es `imported_from` (Liste der Import-Dateinamen) anstelle des bisherigen `products`. Bei den 4 schon verknüpften Materialien wird `products` umgezogen: Sie bekommen `imported_from` und die zugehörigen Angebote (offers) im `product`-Block, aber kein eigenes neues Material.
2. **Firmen**: `company:obi` und `company:hornbach` (Rolle supplier) anlegen, dazu je Hersteller der übernommenen Artikel eine Firma mit Rolle manufacturer (Slug aus `manufacturer`). Vorhandene Firmen werden wiederverwendet.
3. **Übernahme-Skript** `scripts/import_materials.py`, wiederholbar und mit `--dry-run`:
   - Auswahl nach Kategorie; Artikel, die schon in einem `imported_from` stehen, werden übersprungen.
   - id = Slug aus dem Dateinamen ohne Präfix; bei Kollision wird die EAN angehängt.
   - name, description; category auf die vorhandenen Katalog-Kategorien abgebildet (Farbe, Holz, Baustoffe, Fliesen, Entwässerung, Tapete).
   - appearance mit einem Standardwert je Kategorie (Farbe und Schraffur, Holz mit `wood`). Bei weißen Farben wird `#FFFFFF` gesetzt.
   - conductivity null; values_source "Baumarkt-Artikel, Kennwerte offen".
   - product: manufacturer, article_no, offers [OBI/Hornbach, unit_price, EUR, gross, Datum + Markt aus dem Kassenbon als source].
   - photos: Bilder nach `catalog/photos/<id>/` kopieren.
4. **Vorschau**: Die Dry-run-Liste (id, Name, Kategorie, Preis) wird dir zur Freigabe gezeigt. Erst danach werden die Dateien geschrieben.
5. **Core**: `ProductValidator` wird auch für Materialien aufgerufen (Prüfung in `element_editor.py`, analog zu `component_validator.py`). `imported_from` gilt als Freitext und wird nicht weiter geprüft.
6. **Web** (`static/katalog.js`):
   - Material-Detail zeigt `productView(e)` mit Hersteller, Angeboten und Beleg.
   - Die Liste zeigt bei Materialien den besten Preis an.
   - Das Bearbeitungsformular bekommt den Produktabschnitt wie bei Bauteilen.
   - Die Fotos funktionieren schon über `KatLayout.photos`.
   - Firmenseite: "Angebotene Produkte" zählt auch Materialien mit.
7. **Spezifikation und Cache**: Die Abschnitte in `weingaerten-core.md` und `weingaerten-web.md` werden ergänzt, danach `scripts/rehash_cache.py` ausführen und den Server neu starten.

## Verifikation
- `scripts/check_material_products.py` anpassen: Materialien und Importe gegen ihr Schema prüfen, jedes `imported_from` muss existieren, jeder supplier/manufacturer muss als Firma vorhanden sein.
- `scripts/core_validate.py`: ok, keine neuen Fehler.
- Bisherige Material-IDs und Verweise aus den Aufbauten unverändert (Vergleich mit grep).
- Web: `scripts/check_web.py` und `scripts/check_kat_js.py`; im Browser `/katalog/materialien` öffnen, ein OBI-Material zeigt Foto, Preis und Beleg; `/katalog/firmen` zeigt bei OBI die Materialien.
- Wiederholter Lauf des Skripts legt nichts doppelt an.

## Kritische Dateien
- catalog/schema/material.schema.json - product, imported_from
- scripts/import_materials.py - Übernahme (neu)
- code/weingaerten_core/editing/element_editor.py, validation/product_validator.py - Produktprüfung für Materialien
- code/weingaerten_web/static/katalog.js - Anzeige und Bearbeitung
- weingaerten-core.md, weingaerten-web.md - Spezifikation
