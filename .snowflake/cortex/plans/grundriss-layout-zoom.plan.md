
# Plan: Grundriss layout, zoom, storey and cut height

## Context
- The code is generated from the spec. The page is defined in [weingaerten-web.md](weingaerten-web.md) (section "Page `/grundriss`", lines ~141-162). Any change goes into the spec first, then the code, then `scripts/rehash_cache.py`.
- [grundriss_page.py](code/weingaerten_web/pages/grundriss_page.py) builds the heading, `StoreySelector.links` (button row), the `planedit` row, the server SVG `#planview`, the edit area `#planarea` (`.wlay` with `#planedsvg` and a fixed 350 px `#planpanel`), and `CornerDetail` ("Detail Ecke Nordwest").
- [plan_svg.py](code/weingaerten_web/plan/plan_svg.py) has a fixed `CUT_HEIGHT = 1.0`, which `LayerSvg`, `OpeningSvg` and `StructureSvg` use.
- [plan.js](code/weingaerten_web/static/plan.js) sets the `viewBox` in `frame()`, and `toWorld()` goes through `getScreenCTM`, so zooming through the viewBox keeps editing correct.
- The catalog pages already have a splitter (`katsplit` + `localStorage`) in [katalog_layout.js](code/weingaerten_web/static/katalog_layout.js), which I can reuse as a pattern.

## Assumptions (from the screenshot)
- "Detailsicht entfernen" removes the corner-detail drawing (the box marked "nicht notwendig"). The layer table "Material (außen → innen)" stays. Tell me if the table should go as well.
- "Detailansicht: Elemente gehen über rechten Rand hinaus" refers to the edit panel on the right. Inputs (Name, Aufbau) and buttons (`Bearbeiten beenden`) are cut off or overflow.

## Implementation steps
1. **Spec update** (`weingaerten-web.md`, /grundriss section): describe the toolbar, zoom, resize, splitter, cut height `?cut=<cm>` and the removal of the corner drawing. Update the expected checks (`planedit`, `plandata`, `planpanel` stay).
2. **Toolbar area** (`#plantools`, its own framed box under the heading):
   - Storey `<select id="storeysel">`, ordered by elevation, with an onchange handler that navigates to `?storey=<id>&cut=<cm>`. Add a dropdown variant to `StoreySelector`, so `/waende` keeps its own filter.
   - Number field `Schnitthöhe cm` (default 100, range 0 to the storey height). It reloads with `?cut=`, and the subtitle shows the value (`Horizontalschnitt bei 1,0 m`).
   - The `Bearbeiten` button and the hint text.
3. **Adjustable cut height on the server:** `GrundrissPage.render(storey_id, cut_cm)` parses and clamps the value. `PlanSvg(..., cut_height)` replaces the constant, and the route passes the query parameter through.
4. **Shared layout for view and edit mode:** one container `.planlay` = `#planbox` (plan) + splitter `#plansplit` + `#planpanel`.
   - The splitter can be dragged left/right. The panel width is stored in `localStorage` `weingaerten.grundriss.split` (min 260 px, max 60 %).
   - `#planbox` gets `resize: both; overflow: hidden` with a visible handle at the bottom-right corner. Its size is stored in `localStorage` `weingaerten.grundriss.size`.
5. **Zoom** (new `plan_zoom.js` for both `#planview svg` and `#planedsvg`; add it to the static asset list in the spec):
   - Mouse wheel zooms around the cursor by changing the viewBox.
   - Drag on empty space with the middle button or Space pans the view.
   - Buttons `+`, `-` and `Einpassen` in the toolbar.
   - In `plan.js`, `frame()` only sets the base viewBox, and the zoom keeps its own transform on top. `toWorld()` stays unchanged.
6. **Remove the corner detail:** remove the drawing from [corner_detail.py](code/weingaerten_web/plan/corner_detail.py) or its call, and keep the layer table.
7. **Fix the panel overflow:** in `style.css`, `#planpanel` gets `min-width: 0; overflow-x: hidden; box-sizing: border-box`. Inputs and selects get `width: 100%; max-width: 100%; min-width: 0`, and the button rows get `flex-wrap: wrap`.
8. Run `scripts/rehash_cache.py` and `scripts/check_clean_code.py` (256-line limit; `plan.js` is already large, so put the zoom code in its own file).

## Verification
- Stop the server, implement, then restart it with `start.cmd`.
- `scripts/check_web.py`: /grundriss returns 200 and contains `planedit`, `plandata`, `planpanel`, `class="layer"` and one `opening` symbol per opening.
- `?cut=220`: cut-dependent openings (high windows) change between full and dashed drawing.
- In the browser: the wheel zoom keeps the point under the cursor fixed, and selecting and dragging walls still work after zooming. Resize and splitter sizes survive a reload. The panel has no horizontal overflow at 260 px. The dropdown switches the storey and keeps the cut height.

## Critical Files
- [weingaerten-web.md](weingaerten-web.md) - spec source of the page
- [code/weingaerten_web/pages/grundriss_page.py](code/weingaerten_web/pages/grundriss_page.py) - page layout, toolbar, parameters
- [code/weingaerten_web/plan/plan_svg.py](code/weingaerten_web/plan/plan_svg.py) - cut height parameter
- [code/weingaerten_web/static/plan.js](code/weingaerten_web/static/plan.js) - edit SVG viewBox and zoom integration
- [code/weingaerten_web/static/style.css](code/weingaerten_web/static/style.css) - layout, splitter, resize, panel overflow
