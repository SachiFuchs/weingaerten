# Plan: /haus3d rework – option boxes, object popup, detail panel

## Context
- Spec: [weingaerten-web.md](weingaerten-web.md) section **Page `/haus3d`** (lines 114-135). The code is a cache of the spec, so the spec changes first, then the cache code, then `scripts/rehash_cache.py`, then a server restart via `start.cmd` (stop the server before implementing).
- [haus3d_page.py](code/weingaerten_web/pages/haus3d_page.py) renders the checkbox row (`geschoss3d-<id>`, `dachstuhl3d`, `heizung3d`, `dach3d`, `transp3d`, `decke3d`) and `scene3d`.
- [haus3d.js](code/weingaerten_web/static/haus3d.js): localStorage per toggle, `buildWalls()` rebuilds everything, the hover tooltip comes from the raycast `userData.kind` (layer/part/reveal/ceil/struct/...), double click → `/katalog/bauteile#id`, the `ResizeObserver` stores height and width.
- Today there's no click popup and no detail panel.

## Layout
```
+-----+------------------------------------------+---+-------------+
|     | [Stockwerke] [Technik] [Details]          |   |             |
| nav |------------------------------------------|<|>|  detail     |
|     |                 3D                        |   |  (iframe)   |
+-----+------------------------------------------+---+-------------+
```
- `main` becomes a flex row: `view3d` (boxes, `scene3d`, legend) | splitter `split3d` | `detail3d` (sticky, height 100vh).
- `scene3d` takes the width of its column. The height stays resizable and stored. The width resize and `weingaerten.scene3d.width` go away.

## Implementation steps
1. **Spec**: rewrite the toggle paragraph and add popup, detail panel and embed mode to the `/haus3d` section and the page frame section.
2. **Option boxes** (`fieldset.opt3d` with `legend`, in one row):
   - **Stockwerke:** `KG` `EG` `DG` (existing `geschoss3d-<id>`, bottom up, each on its own), then `Decke`, `Dachstuhl`, `Dach` (existing ids and the disabled / `noch nicht vorhanden` rules unchanged).
   - **Technik:** `Heizung` (`heizung3d`). Built from a list in `haus3d_page.py`, so Elektrik, Abwasser and Zuwasser can be added later as entries (not shown yet).
   - **Details:** `transparent` (existing `transp3d`, label shortened) and `Details` (`details3d`, shows/hides the panel and splitter, default off, not stored).
   - The localStorage keys and the behaviour stay the same.
3. **Click popup** `pop3d` in `haus3d.js`:
   - A click counts when pointerdown→pointerup moves less than 5 px and takes less than 400 ms (so a drag doesn't open it).
   - The popup at the cursor shows the tooltip title and the links that apply:
     - `Wände` → `/waende?storey=<sid>&embed=1#<wall id>`
     - `Material` → `/katalog/materialien?embed=1#<material id>`
     - `Bauteil` → `/katalog/bauteile?embed=1#<component id>`
   - All text goes in via `textContent`.
   - A link opens it in the panel: it sets the iframe src, ticks `details3d` and expands the panel.
   - Esc, a click on empty space or a drag close it. Double click keeps working.
4. **Detail panel**:
   - `<iframe id="detailframe">` with the note `Objekt anklicken`.
   - Splitter drag with pointer capture (iframe `pointer-events:none` during the drag), min 280 px, max 70 % of the width.
   - Button `<|>` (`detailtoggle`) collapses to 0 and expands to the last width.
   - Nothing is stored: it starts hidden, at 40 % width.
5. **Embed mode** `?embed=1` in the page frame (`model_page`), generic for every page: no sidebar, header or banner, compact `main`. `common.js` appends `embed=1` to same-origin links on embedded pages. Deep links and saving stay unchanged.
6. **Cache + restart**: run `scripts/rehash_cache.py`, then `start.cmd`.

## Verification
- `scripts/check_haus3d_js.py` (node syntax).
- `scripts/check_web.py`, extended:
  - `/haus3d` contains `geschoss3d-`, `Stockwerke`, `Technik`, `details3d`, `split3d`, `detailframe`, `pop3d`.
  - `/waende?embed=1` and `/katalog/bauteile?embed=1` contain no `navtoggle` but still contain `wanddata` / `katdata`.
- Manual browser check: click vs drag, the three links, splitter, `<|>`, each floor toggle on its own, transparent.

## Critical files
- [weingaerten-web.md](weingaerten-web.md) - spec of /haus3d and the page frame
- [code/weingaerten_web/pages/haus3d_page.py](code/weingaerten_web/pages/haus3d_page.py) - boxes, layout, panel markup
- [code/weingaerten_web/static/haus3d.js](code/weingaerten_web/static/haus3d.js) - popup, splitter, sizing
- page frame / `model_page` + `static/page.html`, `static/common.js` - embed mode
- [scripts/check_web.py](scripts/check_web.py) - checks

## Assumptions
- "Details: transparent" = the Details box holds `transparent` plus the panel toggle.
- If `/waende` can't jump to an opening by hash, the Wände link goes to the wall only.
