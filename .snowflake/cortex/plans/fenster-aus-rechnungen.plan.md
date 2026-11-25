# Fenster aus "Rechnung, Angebote Fenster-Tueren gesamt.docx" in den Katalog

## 1. Context
Das Dokument enthält ein Marquardt-Angebot (nur Haustür + Nebeneingangstür) und Neuffer-Rechnungen/Bestellungen (30.07.2023, 16.11.2023, 06.10.2024, 03.11.2025). Alle Fenster: Kunststoff weiß.

"Materialliste" wird als **Katalog** verstanden: Fenster = Bauteile (`catalog/components/`, Klasse `class:window`), ihre Werkstoffe = Materialien (`catalog/materials/`). Die Fenster werden **nicht** in Wände eingesetzt (Lage im Grundriss unbekannt).

| Nr | id | Position | B x H (mm) | Flügel / Öffnung | Verglasung | Extras | Profil, Beleg |
|---|---|---|---|---|---|---|---|
| 1 | window-wz-gross | Wohnzimmer großes Fenster | 2970 x 1175 | 3 DK | 3-fach Ug 0,7 | Schall 32 dB, VSG 8 i/a, RC1, Sprossen | Aluplast IDEAL 8000, RE 3358369 (06.10.2024) |
| 2 | window-wz-terrasse | Wohnzimmer zu Terrasse | 1030 x 1175 | 1 DK | 3-fach Ug 0,7 | Schall 32 dB, VSG, RC1, Sprossen | IDEAL 8000, RE 3358369 |
| 3 | window-kammer | Kammer | 900 x 1060 | 2 fest | 2-fach Ug 1,1 | Sprossen | IDEAL 4000, Best. 3308385 (30.07.2023) |
| 4 | window-balkonkammer | Balkonkammer | 900 x 1060 | 2 (Dreh + DK) | 2-fach Ug 1,1 | Sprossen, Basissicherheit | Kömmerling Trocal 70 AD, Best. 3320751 (16.11.2023) |
| 5 | window-schlafzimmer | Schlafzimmer | 960 x 1360 | 1 DK | 3-fach Ug 0,7 | Schall 36 dB, ESG 4, RC1, Sprossen | IDEAL 8000, Best. 3320751 |
| 6 | window-eg-kueche | EG Küche | 900 x 1010 | 1 DK + Unterlicht fest (650/360) | 3-fach Ug 0,6 | VSG, RC1, Insektenschutz, Rahmenverbreiterung 30 mm | IDEAL 8000, RE 3417279 (03.11.2025) |
| 7 | window-eg-bad | EG Bad | 650 x 850 | 1 DK | 3-fach Ug 0,6 | VSG, RC1 | IDEAL 8000, RE 3417279 |
| 8 | window-eg-flur | EG Flur | 1000 x 650 | fest | 3-fach Ug 0,6 | VSG | IDEAL 8000, RE 3417279 |
| 9 | window-eg-kammer | EG Kammer | 510 x 510 | fest | 3-fach Ug 0,6 | VSG außen | IDEAL 8000, RE 3417279 |
| 10 | window-wz-klein | Wohnzimmer kleines Fenster | 510 x 1010 | 1 DK | 3-fach Ug 0,6 | VSG, RC1 | IDEAL 8000, RE 3417279 |

Nicht übernommen (Türen, kein Fenster): Balkontür und Tür Treppenzimmer (je 1050 x 2100, Best. 3320751), Alu-Haustür und Nebeneingangstür (Marquardt-Angebot).

### Einschränkungen des Modells
- **3-flügliges Fenster (Nr. 1):** Das Rezept `window` erlaubt laut Core nur `sashes` aus {0, 1, 2}. Vorschlag: als `sashes: 2` anlegen und "3-teilig" in Name/Beschreibung vermerken; echte 3 Flügel erfordern eine Änderung der Core-Spezifikation (eigene Aufgabe).
- **Unterlicht (Nr. 6):** nicht modellierbar; Fenster als 1 Flügel, Unterlicht in Beschreibung.
- **Uw-Wert:** in den Belegen nicht angegeben (nur Ug) -> `uw_value` bleibt leer, neuer Parameter `ug_value`.
- **Bautiefe** (Richtwerte Hersteller, nicht im Beleg): IDEAL 8000 85 mm, IDEAL 4000 70 mm, Trocal 70 AD 70 mm. Rahmenbreite: Klassen-Default 0,07 m.
- Preise: Gesamtpreis brutto je Position in `description` (kein Preisfeld im Schema).

## 2. Implementation steps
1. **Klasse Fenster erweitern** ([catalog/classes/window.json](catalog/classes/window.json)), optionale Parameter:
   - `ug_value` (number 0,3-6, "Ug-Wert W/(m²K)")
   - `sound_class` (choice none, SSK1-SSK4, "Schallschutzklasse")
   - `safety_glass` (choice none, ESG, VSG, "Sicherheitsglas")
   - `glazing_bars` (bool, "Sprossen")
   - `glazing_type` hat bereits single/double/triple.
2. **Material** `catalog/materials/glass-double.json` "2-fach-Verglasung" (Kategorie Glas, λ 1,0, ρ 2500, A1, Farbe wie glass-triple etwas dunkler). Rahmen: vorhandenes `pvc-white`.
3. **10 Bauteile** `catalog/components/<id>.json` gemäß Tabelle, z. B.:
```json
{
  "id": "window-eg-bad",
  "name": "Fenster EG Bad 0,65 × 0,85",
  "description": "Neuffer RE 3417279 vom 03.11.2025, Pos. 2; Aluplast IDEAL 8000, 1-teilig Dreh-Kipp links, VSG 8 mm innen/außen, RC 1 N, abschließbarer Griff; 311,42 €",
  "class": "class:window",
  "opening_capable": true,
  "params": { "width": 0.65, "height": 0.85, "depth": 0.085, "frame_width": 0.07, "sashes": 1,
              "glazing_type": "triple", "ug_value": 0.6, "safety_glass": "VSG", "burglary_class": "RC1" },
  "materials": { "frame": "material:pvc-white", "glazing": "material:glass-triple" }
}
```
   2-fach-Fenster (Nr. 3, 4) mit `glazing: material:glass-double`. Feste Fenster `sashes: 0`.
4. **Prüfen** mit `scripts/core_validate.py`: 0 Fehler, `components` = bisher 3 + 10.

## 3. Verification
- `python scripts/core_validate.py` -> ok, keine Fehler, counts.components 13, materials 10.
- Seite `/katalog/bauteile` zeigt die 10 Fenster mit Vorschau (manuell im Browser, Server Port 8008).

## 4. Critical Files
- [catalog/classes/window.json](catalog/classes/window.json) - neue Parameter
- [catalog/components/](catalog/components/) - 10 neue Fenster
- [catalog/materials/glass-double.json](catalog/materials/glass-double.json) - neue Verglasung
- [scripts/core_validate.py](scripts/core_validate.py) - Prüfung
