# Plan: Clean-Code-Regeln ergänzen

## Kontext
- [skills/clean-code.instructions.md](skills/clean-code.instructions.md) gilt für `**/*.py`. Die Regeln sind auf Englisch und in nummerierten Abschnitten organisiert (1 Principles, 1a Details, 2 Size Limits, 3 Readability, 4 Editing, 5 Logging, 6 Jira).
- Konflikt: Punkt 1a.6 "Self-Documenting Code" sagt "rarely needs comments", die neue Regel sagt "Kommentare einfügen". Diese Stelle muss angepasst werden, sonst widersprechen sich die Regeln.
- Nebenbefund: Zeile 76 ("mail logic"), wohl ein Tippfehler für "main logic", und Zeile 80, ein abgebrochener Satz ("split the class with different"). Beides korrigiere ich mit, weil die neuen Regeln direkt daneben stehen.

## Änderungen
1. Neuer Abschnitt **"## 2a. Classes and File Structure"** nach "2. Size Limits":
   - Prefer classes whenever possible: group related state and behaviour in a class instead of loose module-level functions. Module-level functions only for small stateless helpers or entry points (`main`).
   - One class per file: each class lives in its own module, named after the class in snake_case (`WallBuilder` -> `wall_builder.py`).
   - Use sub-folders (packages with `__init__.py`) to structure related classes when it adds clarity, e.g. `core/geometry/`, `core/bom/`. Re-export the public classes in `__init__.py`.
2. Neuer Abschnitt **"## 3a. Comments"** nach "3. Readability":
   - Add comments: every class and public method gets a docstring. Non-trivial blocks (algorithms, geometry, business rules, workarounds) get a short comment explaining *why*.
   - Keep comments up to date when the code changes; remove comments that no longer match.
3. Punkt 1a.6 anpassen: "Self-Documenting Code" bleibt das Ziel (gute Namen), aber der Satz "rarely needs comments" wird ersetzt durch "Names carry the *what*; comments (see 3a) carry the *why*."
4. Zeile 76 "mail logic" -> "main logic"; Zeile 80 vervollständigen: "If a class file exceeds the size limit, split the class by responsibility into collaborating classes (one file each)."

## Verifikation
- Die Datei lesen und prüfen, dass Front-Matter (`applyTo`), die Nummerierung und der Stil (englisch, Bullet-Listen) erhalten bleiben und keine widersprüchlichen Aussagen zu Kommentaren übrig sind.

## Kritische Dateien
- [skills/clean-code.instructions.md](skills/clean-code.instructions.md)
