---
name: "material produktdaten masse"
created: "2026-11-20T14:59:22.414Z"
status: pending
---

## Kontext

- Im Repo gibt es keinen OBI-Scraper. Die OBI-Datensätze in `catalog/imported_material/*.json` haben nur `dimensions_and_weight` (Gewicht, Höhe, Breite, Tiefe), aber keine `attributes`.

- Hornbach-Datensätze (`scripts/import_hornbach.py`) haben `attributes` und `dimensions_and_weight`.

- `scripts/import_materials.py` (Z. 176-183) verwirft `attributes` und `dimensions_and_weight`, deshalb kommen sie nie in `catalog/materials/*.json` an.

- In `code/weingaerten_web/static/katalog.js` rendern `view()` (Z. 99-102) und `productView()` (Z. 62-66) nur feste Zeilen. Darum zeigen alle Materialien dieselben Attribute.

- Die OBI-Seite (`https://www.obi.de/p/<art>`) hat ein Akkordeon „Produktdaten & -maße“ mit den Untertabellen „Produktdaten“ und „Maße & Gewicht“. Die Überschrift ist im Textauszug sichtbar, die Tabelleninhalte aber nicht. Das genaue Markup muss deshalb am Roh-HTML geprüft werden.

- Der Code wird aus der md-Spezifikation generiert. Deshalb wird die Spezifikation mitgepflegt:

  - `weingaerten-core.md`: Materialmodell
  - `weingaerten-web.md`: Katalogdetail, Z. 171-172
  - `weingaerten-doku.md`: Z. 47 und 106

## Datenmodell (neu)

`product.details` im Materialdatensatz ist ein geordnetes Dict mit den Abschnitten aus dem Shop:

```json
"details": {
  "Produktdaten":   {"Material": "Polypropylen (PP)", "Farbe": "Grau", "Nennweite": "DN 50"},
  "Maße & Gewicht": {"Länge": "150 mm", "Gewicht": "70 g", "Höhe": "6,4 cm"}
}
```

- Die Werte sind Strings, genau wie der Shop sie anzeigt.
- Das Feld ist optional und fehlt bei manuell angelegten Materialien.

## Umsetzungsschritte

1. **Neues `scripts/fetch_obi_details.py`**

   - Für jeden `imported_material/*.json` mit `obi.de`-URL die Seite per urllib laden: mit User-Agent, 1 s Pause, Optionen `--only <ean>` und `--force`.
   - Geladene Seiten in `scripts/obi_pages/` zwischenspeichern (gitignored).
   - Die Tabellen „Produktdaten“ und „Maße & Gewicht“ mit `html.parser` auslesen (stdlib, keine neue Abhängigkeit).
   - Fallback, falls die Tabellen erst im Browser gerendert werden: JSON-LD `additionalProperty` bzw. eingebettetes State-JSON.
   - `details` in den Importdatensatz schreiben.
   - Ist „Maße & Gewicht“ leer, `dimensions_and_weight` mit deutschen Labels übernehmen (Gewicht, Höhe, Breite, Tiefe).
   - `details_status` auf `ok` oder `missing` setzen.
   - Standard ist ein Probelauf; erst `--write` schreibt.

2. **`scripts/import_hornbach.py` `enrich()`:** zusätzlich `details` schreiben.

   - Attribute mit `DIMENSION_KEYS` kommen nach „Maße & Gewicht“, der Rest nach „Produktdaten“.
   - Damit haben beide Shops dasselbe Format.

3. **`scripts/import_materials.py`**

   - `details` in `product()` übernehmen. Gibt es nur `dimensions_and_weight`, wird es auf „Maße & Gewicht“ abgebildet.
   - Update-Pfad für bestehende Materialien (Abgleich über EAN bzw. article\_no): Nur `product.details` wird ergänzt, manuell gepflegte Felder bleiben unverändert. So passen sich die bestehenden Materialien an.

4. **Spezifikation**

   - `weingaerten-core.md`: `product.details` beschreiben (optional, Abschnitt → Schlüssel → String) samt Validierung (nur Strings).
   - `weingaerten-web.md`: Katalogdetail ergänzen. Nach dem Produktblock folgt je Abschnitt ein `kv`-Block mit dem Abschnittsnamen als Überschrift, nur lesend, ausschließlich `textContent`.
   - `weingaerten-doku.md`: Importablauf um den Fetch-Schritt ergänzen.

5. **Core-Validierung:** Dort, wo das Produkt geprüft wird (laut `weingaerten-core.md` Z. 66/209), `details` als Dict von Dicts mit String-Werten zulassen.

6. **`katalog.js`**

   - Neue Funktion `detailsView(pr)`, aufgerufen aus `productView()`.
   - Sie iteriert über `pr.details` und zeigt je Abschnitt eine Überschrift plus `kv(Object.entries(sec))`. Es gibt keine fest codierten Schlüssel, also zeigt jedes Material seine eigenen Attribute.
   - Der Editor behält `details` beim Speichern (wie `ean`/`url`, Z. 89).

7. **Import ausführen:** `fetch_obi_details.py --write`, dann `import_hornbach.py`, dann `import_materials.py --write`. Danach den Diff von `catalog/materials` prüfen.

## Verifikation

- OBI-Seite 7436736 laden: „Produktdaten“ und „Maße & Gewicht“ sind befüllt. Zusätzlich 2-3 weitere Kategorien prüfen (Dämmung, Platte, Rohr).

- Unit-Tests:

  - Parser gegen eine gespeicherte HTML-Fixture (`tests/fixtures/obi_7436736.html`)
  - Hornbach-Mapping
  - `import_materials`-Merge lässt manuelle Felder unverändert

- Bestehende Testsuite und Baseline-Vergleichsskripte laufen lassen.

- Manuell im Katalogdetail: OBI- und Hornbach-Materialien zeigen unterschiedliche Abschnittsinhalte. Materialien ohne Details zeigen keine leeren Überschriften.

## Kritische Dateien

- scripts/import\_materials.py: Details übernehmen und in bestehende Materialien ergänzen
- scripts/import\_hornbach.py: Attribute auf die Abschnitte abbilden
- scripts/fetch\_obi\_details.py (neu): OBI-Produktseiten lesen
- code/weingaerten\_web/static/katalog.js: generische Anzeige der Abschnitte
- weingaerten-core.md, weingaerten-web.md: Spezifikation als Quelle des generierten Codes
