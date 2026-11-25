# Aufbauten <-> Wände verlinken

## Context
- Data link already exists: each wall in `house/storeys/<id>.json` has `assembly: "assembly:<id>"` (Wand -> Aufbau). No data/schema change needed.
- Reverse direction is already computed by the core: `USAGE` ([code/weingaerten_core/queries/usage_finder.py](code/weingaerten_core/queries/usage_finder.py)) returns users like `storey:ground.w-north`; the catalog embeds it as `D.usage`.
- Gap is UI only:
  - [code/weingaerten_web/static/katalog.js](code/weingaerten_web/static/katalog.js) line 122 prints `Verwendet von: storey:ground.w-north, ...` as plain text.
  - [code/weingaerten_web/pages/waende_page.py](code/weingaerten_web/pages/waende_page.py) embeds only `material, class, component` - the wall header (`wtitle` in [static/wand.js](code/weingaerten_web/static/wand.js) line 50) does not show the Aufbau at all.
- Wände page already supports deep links `/waende?storey=<id>#<wall-id>` (hashchange -> pickWall); catalog supports `/katalog/aufbauten#assembly:<id>`.

## Implementation steps
1. **katalog.js usage links**: extend `link()` / the `Verwendet von` line: a user `storey:<s>.<wall>` becomes `<a href="/waende?storey=<s>#<wall>">` with wall name (resolve name from embedded house data; fall back to id), catalog refs use existing `link()`, `house` stays text. Keeps delete-guard logic unchanged.
2. **Aufbau detail section** (PAGE==='assembly'): add `h4 Wände` table [Geschoss, Wand (link), Länge] listing wall users, so the Aufbau shows its walls clearly. Needs wall names/storey names: add a small `walls` map `{ "storey:<s>.<w>": {name, storey_name, length} }` to `katdata` in [pages/katalog_page.py](code/weingaerten_web/pages/katalog_page.py) built from `HOUSE` (only for the assembly page).
3. **Wände page**: add `assembly` to `EMBEDDED_TYPES`; in wand.js show `Aufbau: <a href="/katalog/aufbauten#assembly:<id>">Name</a> (Dicke cm)` in the head next to `wtitle`.
4. **Wall list** in wand.js: show Aufbau name as second line/note per row and include it in the `wsearch` filter (e.g. search "iw1" finds all walls of that Aufbau).
5. Run `scripts/rehash_cache.py`, restart via `start.cmd`, verify.

## Verification
- `/katalog/aufbauten#assembly:exterior-wall-ew1`: walls listed and clickable -> opens `/waende?storey=ground#w-...` with that wall selected.
- `/waende`: header shows Aufbau link -> jumps back to the catalog with the assembly selected.
- `scripts/check_kat_js.py` (node syntax), `scripts/check_web.py` (known w-south failure is preexisting).

## Critical Files
- [code/weingaerten_web/static/katalog.js](code/weingaerten_web/static/katalog.js) - usage links + Wände section
- [code/weingaerten_web/pages/katalog_page.py](code/weingaerten_web/pages/katalog_page.py) - embed wall names
- [code/weingaerten_web/pages/waende_page.py](code/weingaerten_web/pages/waende_page.py) - embed assemblies
- [code/weingaerten_web/static/wand.js](code/weingaerten_web/static/wand.js) - Aufbau link in head and list
