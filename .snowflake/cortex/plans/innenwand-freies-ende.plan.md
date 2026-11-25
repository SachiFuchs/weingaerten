# Plan: Interior walls with a free end ("Innenwand ohne Anschluss")

## Context
- Floor plan editor: [code/weingaerten_web/static/plan.js](code/weingaerten_web/static/plan.js). `openEnds()` (line 50) counts the walls that share an end point. The drawing (line 76) shows green for a connected end and orange `#F57C00` for an open one. The panel (line 171) shows "n offene Wandenden (orange)". `save()` (line 178) builds the wall payload.
- Spec (code is generated from it, see project memory): [weingaerten-web.md](weingaerten-web.md) line 156/166 (colours, live checks) and [weingaerten-core.md](weingaerten-core.md) line 122/203 (warning `offenes Wandende`, wall schema).
- In the screenshot, `iw-treppe-sued` stops against another wall without sharing its end point. That is why it shows orange.

## Assumptions
- The setting is stored per end: optional wall field `free_ends: ["start"|"end", ...]`. It is only allowed on walls with category `interior_wall`.
- The "Abfrage" (confirmation) happens in the editor. Clicking an orange end of an interior wall, and pressing `Speichern` while interior walls still have orange ends, asks: `Innenwand <id>: Ende ohne Anschluss erlauben?`. Yes sets `free_ends`; No keeps the end orange (warning only, as before).
- Blue = `#42A5F5`. It is lighter than the selection blue `#1C69D4` so the two can be told apart.
- If the end gets connected later, its entry is dropped from `free_ends` automatically and the end turns green.

## Implementation steps
1. **Core spec** (`weingaerten-core.md`): add the optional field `free_ends` to the wall schema. Validation: it is only allowed for `interior_wall` (else an error), and its values are `start`/`end`. An open end listed in `free_ends` gives no `offenes Wandende` warning. Add a test bullet: an interior wall with a free end plus `free_ends` gives no warning.
2. **Web spec** (`weingaerten-web.md`): end points green / orange / **blue = interior wall end released without a connection**. Describe the confirmation on clicking and on `Speichern`. Panel line: `n offene Wandenden (orange), m freie Innenwandenden (blau)`. The 3D view and the wall view stay unchanged.
3. **Regenerate the code** from both spec sections, then run `scripts/rehash_cache.py`:
   - `plan.js`: include `free_ends` in `load()` (line 10). `openEnds()` returns `{p,c,free}`. The circle colour is `c ? green : free ? blue : orange`. Make the end circles clickable for interior walls (confirm dialog, toggle). In `save()`, run the confirmation loop and send `free_ends` (also in the change comparison `svPlain`). Clean up `free_ends` entries whose end has become connected.
   - Core: wall schema/validation and suppressing the warning in the geometry/validation module; let `WALLS_SAVE` pass the field through.
4. Restart the server via `start.cmd` (stop it before implementing, restart afterwards).

## Verification
- `scripts/check_clean_code.py` (file and function limits).
- Extend `scripts/smoke_eg_corrections.py` (temp copy): `iw-treppe-sued` with `free_ends:["end"]` gives no `offenes Wandende`; the same field on an exterior wall gives an error.
- Manual check in the floor plan: the end of `iw-treppe-sued` is orange; clicking it opens the confirmation; Yes turns it blue and the panel counter changes; `Speichern` and reload keep it blue; dragging the end onto another end point turns it green and removes the entry.

## Critical Files
- [code/weingaerten_web/static/plan.js](code/weingaerten_web/static/plan.js) - colours, confirmation, save payload
- [weingaerten-web.md](weingaerten-web.md) - editor spec (source of the generated code)
- [weingaerten-core.md](weingaerten-core.md) - wall schema, warning rule, tests
- [scripts/smoke_eg_corrections.py](scripts/smoke_eg_corrections.py) - regression test
