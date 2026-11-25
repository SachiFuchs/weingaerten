# Plan: Katalog master-detail layout

## Context
- Catalog pages `/katalog/{materialien,aufbauten,bauteile,klassen,firmen}` are specified in [weingaerten-web.md](weingaerten-web.md) (section "Catalog sub pages", lines ~168-181) and generated into [code/weingaerten_web/pages/katalog_page.py](code/weingaerten_web/pages/katalog_page.py) + [code/weingaerten_web/static/katalog.js](code/weingaerten_web/static/katalog.js) (32 KB, one `<details class="card">` per element, toolbar with search/expand all/collapse all).
- Code is a cache of the spec: changes go into the spec first, then code, then `scripts/rehash_cache.py`.
- A splitter pattern already exists on `/haus3d` (`split3d`, pointer capture, min/max width, `<|>` toggle) - reuse its behaviour.
- **No photo data exists** in the catalog today. Assumption: optional field `photos: [<file name>]` per element, files in `catalog/photos/<element id>/`, served read-only by a new route `GET /catalog-photo/<id>/<file>` (whitelisted extensions jpg/jpeg/png/webp, no path traversal). Without photos the strip is hidden. Upload/editing of photos is not part of this change.

## Layout
```
+------+-----------+------------------------------+
|      | filter    |                 [Bearbeiten] |
| nav  +-----------+                              |
|      |           |   details                    |
|      | list      |                              |
|      | (v-scroll)+------------------------------+ <- splitter (vertical)
|      |           |   photos (h-scroll, opt.)    |
+------+-----------+------------------------------+
            ^ splitter (horizontal)
```

## Implementation steps
1. **Spec** - rewrite "Catalog sub pages" in `weingaerten-web.md`:
   - `main` without max-width, full window height grid `katgrid`: column `katside` (toolbar `katnew` + search `Suchen …` + count; below list `katlist`, `overflow-y:auto`), splitter `katsplit` (drag, min 200 px / max 60 %, width in `localStorage weingaerten.katalog.split.<page>`), column `katmain`.
   - List rows = existing summary lines (swatch / layer bar / mini front view, name, category, ref); click selects (highlight BMW blue), sets `location.hash`; arrow up/down keyboard navigation; `Alle aufklappen/einklappen` removed.
   - `katmain`: header with name + button `katedit` `Bearbeiten` (and `Löschen`) top right; `katdetail` = existing view-mode content (scrollable); edit mode replaces `katdetail` with the existing forms (dirty check on selection change).
   - Photo strip `katphotos` below, separated by splitter `katvsplit` (height stored in `localStorage weingaerten.katalog.photos.<page>`, min 80 px), images left to right, `overflow-x:auto`, click opens the image in a new tab; hidden when the element has no photos.
   - Empty selection -> note `Eintrag links auswählen`; hash links (`#<ref>` from 3D popup, embed=1) select that element. In embed mode the list column starts collapsed.
   - Schema: optional `photos` in material/assembly/component/class/company schemas; route `/catalog-photo/...`; check_web expectations updated (`katlist`, `katdetail`, `katedit`, still no `<textarea`).
2. **Server** - `katalog_page.py`: new page skeleton; new photo handler class (one class per module) registered in the router; schemas in `catalog/schema/`.
3. **Client** - `katalog.js`: split into list/detail/splitter modules if it exceeds 256 lines per file limit (e.g. `katalog_list.js`, `katalog_split.js` added to the static asset whitelist); reuse view/edit renderers unchanged; replace card open state with selection state.
4. **CSS** - `style.css`: grid, splitters, selected row, photo strip.
5. **Rehash + restart** via `scripts/rehash_cache.py` and `start.cmd`.

## Verification
- `scripts/check_web.py` (updated expectations), `scripts/check_kat_js.py` (node syntax), `scripts/check_clean_code.py`.
- Manual in browser on all five pages: select, keyboard nav, both splitters drag + persist, Bearbeiten/Speichern/Abbrechen/Löschen, search filter, `/katalog/bauteile?embed=1#<ref>` from the 3D popup, a test element with 2 photos shows the strip and scrolls horizontally.

## Critical Files
- [weingaerten-web.md](weingaerten-web.md) - spec section to rewrite
- [code/weingaerten_web/static/katalog.js](code/weingaerten_web/static/katalog.js) - list/detail logic
- [code/weingaerten_web/pages/katalog_page.py](code/weingaerten_web/pages/katalog_page.py) - page skeleton
- [code/weingaerten_web/static/style.css](code/weingaerten_web/static/style.css) - layout
- [scripts/check_web.py](scripts/check_web.py) - page expectations
