# Plan: Klassen für Aufbauten

## Context
- Aufbauten (`catalog/assemblies/*.json`) haben heute nur ein Enum `category` (`exterior_wall`, `interior_wall`, `base_slab`, `slab`, `roof`, `plinth`). Daraus leitet der Core `layer_order` ab ([weingaerten-core.md](weingaerten-core.md) Zeile 107) und prüft die Referenzen (Wand braucht `exterior_wall`/`interior_wall`, Fundament braucht `base_slab`, Zeile 150).
- Bauteil-Klassen (`catalog/classes`, `class:`) sind Parameter- und Rezeptträger für Komponenten. Würde man das auf Aufbauten übertragen, gäbe es eine Namenskollision und eine falsche Semantik, deshalb kommt ein **eigener Typ `assembly-class`** (Ordner `catalog/assembly-classes`, Ref `assembly-class:`), analog zu `tga-class`.
- Der Code wird aus den md-Specs erzeugt (Cache in `%LOCALAPPDATA%\non-code-cache`). Änderungen erfolgen also in den Specs, danach wird neu erzeugt und getestet.

## Datenmodell
```json
// catalog/assembly-classes/exterior-wall.json
{
  "id": "exterior-wall",
  "name": "Außenwand",
  "description": "Tragende/nichttragende Außenwand",
  "category": "exterior_wall",
  "din276": "330",
  "thickness": { "min": 0.15, "max": 0.80 },
  "layers": { "min": 1, "max": 12 },
  "allowed_material_categories": null
}
```
- Die Klasse ist Träger von `category`: Daraus ergeben sich `layer_order` und die erlaubte Verwendung (Wand oder Fundament).
- Der Aufbau bekommt `"class": "assembly-class:<id>"`. `category` bleibt im Aufbau stehen, wird aber gegen die Klasse geprüft und muss gleich sein (Fehler `Kategorie passt nicht zur Klasse`). Dadurch bleibt alter Lesecode kompatibel.
- `din276` des Aufbaus: Fehlt der Wert, wird der Default aus der Klasse genommen (nur Datenmodell, wie bisher).
- Prüfregeln: Die Gesamtdicke muss im Bereich `thickness` liegen und die Schichtanzahl im Bereich `layers`, sonst gibt es einen Fehler. `allowed_material_categories` ist optional (null = beliebig).
- Startklassen: `exterior-wall`, `interior-wall`, `base-slab`, `slab`, `roof`, `plinth`.
- Die vorhandenen 5 Aufbauten bekommen ihre `class`: ew1 -> exterior-wall, iw1/iw2 -> interior-wall, bs1 -> base-slab, r1 -> roof.

## Implementation steps
1. **Core-Spec** [weingaerten-core.md](weingaerten-core.md):
   - Typ `assembly-class` aufnehmen: Ordner-Mapping, Ref-Regex, `CATALOG` (category = Kategorie), `RESOLVE` (Aufbau löst seine Klasse auf), `USAGE`, `SAVE`/`DELETE` (Löschen gesperrt, solange die Klasse verwendet wird), `counts.assembly_classes`.
   - VALIDATE: Aufbau ohne `class` erzeugt eine Warnung `keine Klasse` (Übergang, damit fremde Daten nicht brechen). Ist eine Klasse gesetzt, gelten die Prüfregeln oben. Bei `SAVE` einer Klasse wird geprüft, ob alle zugehörigen Aufbauten die neuen Grenzen einhalten, sonst Fehler mit Liste (analog zur Bauteil-Klasse).
   - Testerwartungen in der Spec anpassen (Counts, neue Negativfälle: Dicke außerhalb des Bereichs, Kategorie passt nicht, Löschen einer verwendeten Klasse).
2. **Daten:** 6 Dateien in `catalog/assembly-classes/` anlegen und `class` in den 5 Aufbauten ergänzen.
3. **Web-Spec** [weingaerten-web.md](weingaerten-web.md):
   - Neue Seite `/katalog/aufbauklassen` (Überschrift `Katalog – Aufbauklassen`, Button `+ Aufbauklasse`). Die Karte zeigt Name, Kategorie (deutsch), Dickenbereich und die Liste `Aufbauten dieser Klasse`. Das Formular enthält Name, Kategorie, DIN 276, Dicke min/max (cm), Schichten min/max.
   - Aufbau-Formular: Das Select `Klasse` ersetzt das Kategorie-Select. Kategorie und Schichtreihenfolge werden aus der Klasse angezeigt (read-only), und der Dickenbereich erscheint als Hinweis neben der Live-Summe.
   - API-Ref-Regex und `type`-Enum um `assembly-class` erweitern; Navigation ergänzen.
4. **Doku** [weingaerten-doku.md](weingaerten-doku.md): Kette `Wand -> Aufbau -> Aufbauklasse` und den Ordner beschreiben.
5. **Neu erzeugen** und `scripts/rehash_cache.py` ausführen; Server stoppen und nach Abschluss per `start.cmd` neu starten.
6. **Tests erweitern:** `scripts/smoke_core.py` (neue Fälle auf Temp-Kopie) und `scripts/check_web.py` (Seite lädt, `/api/catalog {type: assembly-class}` liefert die 6 Klassen).
7. **Memory/Conventions** aktualisieren.

## Verification
- `scripts/core_validate.py` muss `ok: true` liefern, mit 6 Aufbauklassen und keiner Warnung `keine Klasse`.
- `scripts/smoke_core.py` und `scripts/smoke_baseline.py`: Die neuen Fälle bestehen. Der bekannte Altfehler beim Wall-Split (w-s2) bleibt bestehen und ist keine Regression.
- `scripts/check_web.py` gegen den laufenden Server, außerdem manuell im Browser: Aufbau bearbeiten, Klasse wechseln, Dicke außerhalb des Bereichs ergibt einen Fehler, und die Datei bleibt unverändert.

## Critical Files
- [weingaerten-core.md](weingaerten-core.md) - Typ, Validierung, Commands
- [weingaerten-web.md](weingaerten-web.md) - neue Katalogseite, Aufbau-Formular, API
- `catalog/assemblies/*.json` und das neue `catalog/assembly-classes/` - Daten
- [scripts/smoke_core.py](scripts/smoke_core.py) - Tests
