# Wände nicht bis zur Decke

## Context
- Core unterstützt schon `wall.height` (optional, nur `shape.kind: rect`): `code/weingaerten_core/compute/storey_builder.py:140` setzt es, Fehler „Wandhöhe ungültig“ bei <= 0 oder > Geschosshöhe. Schichten, 3D, Wandansicht (`wand.js` nutzt `w.height`) und Mengen gehen schon davon aus.
- `plan.js:15` liest die Höhe als `wh`, `plan.js:201` speichert sie, aber **es gibt kein Eingabefeld** dafür.
- Keller: `house/storeys/basement.json` Wände `iw-oeltank-nord` / `iw-oeltank-ost` ohne `height` (also volle 2,00 m).
- Code ist ein Cache aus md-Spec-Abschnitten: Spec mit ändern, danach `scripts/rehash_cache.py`, Server per `start.cmd` neu starten.

## Was zu beachten ist
- **Höhe fehlt**: echte Höhe der Schutzwände ist unbekannt. Annahme 1,50 m mit Vermerk „geschätzt“, bitte korrigieren.
- **Öffnungen** dürfen nicht über die Wandoberkante gehen (OpeningParser bekommt `wall.height`, meldet Fehler) – bei Schutzwänden unkritisch.
- **Decke**: Decke liegt nicht auf, Deckenfläche/-Raum unverändert; Wand trägt nichts.
- **Wandoberseite** (Krone) ist sichtbar – Mengen: Wandkrone als Fläche zählt der Core aktuell nicht; nur Hinweis, nicht Teil dieser Änderung.
- **Raum-Wandflächen** (Putz/Anstrich) werden mit der reduzierten Höhe gerechnet – gewünscht.
- **Dachwände** (`shape: roof`) ignorieren `height`; das Feld nur bei `rect` anbieten.
- **Teilen/Versprung** in `plan.js:151` kopiert `wh` nicht -> mitkopieren.

## Implementierungsschritte
1. `plan.js` Wand-Panel: Feld „Wandhöhe (cm), leer = bis Decke“, nur bei `shape.kind==='rect'`; Validierung 1..Geschosshöhe; leer -> `wh=undefined`. Bei Split/Versprung `wh` übernehmen.
2. Grundriss-Darstellung: Teilhohe Wände gestrichelt/heller zeichnen + Tooltip „Höhe x cm“ (optional, klein).
3. `basement.json`: beide Schutzwände `"height": 1.5` (geschätzt; Notiz in `name`/Hinweis).
4. md-Spec-Abschnitt Grundriss/Wand ergänzen, `scripts/rehash_cache.py`, Server neu starten.
5. Test: `scripts/smoke_basement.py` um Höhenprüfung der Schutzwände erweitern (z1 - z0 == 1.5); Fall height > Geschosshöhe -> Fehler.

## Verification
- `python scripts/smoke_basement.py`, `scripts/check_web.py`, node-Syntaxcheck von plan.js.
- Browser: /grundriss?storey=basement Höhe ändern, speichern, /haus3d (Wand niedriger), /waende (Ansicht 1,50 m), /mengen (Volumen kleiner).

## Critical Files
- code/weingaerten_web/static/plan.js - Eingabefeld, Split übernimmt Höhe
- code/weingaerten_core/compute/storey_builder.py - bestehende Prüfung (nur lesen)
- house/storeys/basement.json - Werte setzen
- scripts/smoke_basement.py - Test
