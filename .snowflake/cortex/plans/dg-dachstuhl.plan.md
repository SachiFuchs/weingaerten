---
name: "dg dachstuhl"
created: "2026-11-14T18:22:30.563Z"
status: pending
---

# Plan: Dachstuhl (Pfettendach mit Mittelpfetten) im DG

## Context

- DG `storey:upper` has `roof` {gable, 30 deg, knee 1.25, ridge south\_north, eaves \[0, 7.12]}: roof underside `h(x) = 1.25 + tan30 * min(x, 7.12 - x)` (storey-local), ridge x 3.56 / 3.305. All DG walls already follow it.
- Existing patterns: joists of ceilings (spacing -> `n = max(1, round(span/spacing))`, centres `lo + (i+0.5)*span/n`), `structure[]` (beam/post boxes, BOM rows, 3D prisms, tooltips), `RoofProfile` (compute/roof\_profile.py), 3D `prism(pts, z0, h, plane)`, disabled 3D checkbox `Dachstuhl`.
- User decisions: west slope continues south over Kammer 2; members = rafters, 2 Mittelpfetten, Fusspfetten on the knee walls, Kehlbalken (no ridge purlin); sizes rafters 8x16 @0.80, Mittelpfette 14x20 at 2.10 m, Fusspfette 12x12, Kehlbalken 6x16 at 2.40 m, spruce, estimated; Mittelpfetten rest on gable and interior walls (no posts).

## Data (`house/storeys/upper.json`)

```json
"roof_structure": {
  "material": "material:spruce-wood", "estimated": true, "note": "Pfettendach mit Mittelpfetten, Maße aus Fotos geschätzt",
  "rafters":      { "width": 0.08, "height": 0.16, "spacing": 0.80 },
  "purlins":      { "width": 0.14, "height": 0.20, "z_top": 2.10 },
  "foot_purlins": { "width": 0.12, "height": 0.12 },
  "collars":      { "width": 0.06, "height": 0.16, "z": 2.40 },
  "slopes": [
    { "id": "west", "side": "west", "range": [2.08, 9.94] },
    { "id": "west-kammer", "side": "west", "range": [9.94, 13.13], "end": 2.72 },
    { "id": "east", "side": "east", "range": [2.08, 9.94] }
  ]
}
```

Assumption (to be confirmed): over Kammer 2 the west-slope rafters end at x 2.72 (outer face of the Kammer 2 east wall, its top 2.82 = roof line there), not at the ridge over the balcony. The Mittelpfette and Fusspfette of the west side run continuously from 2.08 to 13.13.

## Geometry (core, storey-local z, + elevation in the output)

- **Rafters** (Sparren) per slope segment: distributed along the ridge over `range` like the joists; each a strip of `width` along y; in plan from the eaves (x 0 or 7.12) to `end` (default ridge 3.56). Underside on the roof line, top = underside + `height / cos(pitch)`; length = plan length / cos(pitch); volume = width \* height \* length.
- **Mittelpfetten** (purlins), one per side: along y over the union of that side's segment ranges; the top touches the rafter underside, `z_top` 2.10 -> centre x = eaves +- (2.10 - knee)/tan(pitch) (1.472 / 5.648); box width x height, z 1.90..2.10.
- **Fusspfetten**, one per side: on the knee wall, centre = knee wall centre line (eaves +- wall thickness/2), z = knee .. knee + height, along the same y range.
- **Kehlbalken** (collars): one per rafter pair where both sides have a rafter reaching the ridge at the same y (main roof y 2.08..9.94): z 2.40..2.56, from the west to the east rafter (x where the roof line is at 2.40 + height/2), width 0.06 next to the rafter.
- Each member is output as `{id, kind: rafter|purlin|foot_purlin|collar, name (German), material, footprint, bottom_plane, top_plane, z0, z1, width, height, length, volume, estimated}`; planes `[a, b, c]` absolute (`z = a*x + b*y + c`; level members a = b = 0).
- Errors (`where` `<storey>.roof_structure`): no `storey.roof` -> `Dachstuhl ohne Dach`; unknown material -> `unbekannt: ...`; a size / spacing <= 0 -> `Maße ungültig`; side not west/east or range not ascending -> `Dachfläche ungültig`.

## Implementation steps

1. **Core**: new `compute/roof_structure_builder.py` (`RoofStructureBuilder`, a helper module if > 256 lines); `StoreyBuilder` adds `roof_structure: {members, counts} | null`; HOUSE `materials` includes its material; BOM `roof_structure: [{storey, kind, name, material, count, length, volume, estimated}]` (per kind) + `totals.roof_structure_volume`, member volumes added to the material volumes; VALIDATE count `roof_structure` (members). Schema `storey.roof_structure`; core spec (geometry, output, BOM, tests).
2. **Data**: add the block above to `upper.json`.
3. **Web**: `/haus3d` checkbox `Dachstuhl` enabled (`dachstuhl3d`, default on, localStorage, hidden with its storey); members as prisms with bottom and top plane (`prism` extended with a bottom plane), spruce colour, transparent option; tooltip: `Sparren` / `Mittelpfette` / `Fußpfette` / `Kehlbalken` i/n, `b x h cm`, length, `(geschätzt)`. `Dach` stays disabled. `/mengen`: table `Dachstuhl` (kind, count, length, volume) + total. Web spec.
4. **Tests**: new `scripts/smoke_roof_structure.py`: counts per kind (rafters 10/4/10 with spacing 0.8 over 7.86 / 3.19 m -> n = round(span/0.8)), rafter length = 3.56/cos30 (main) and 2.72/cos30 (Kammer), purlin z 1.90..2.10 at x 1.472, collars 10 at z 2.40, volume = sum of b*h*l, BOM row and material volume, error cases on a temp copy (no roof, bad material, spacing 0). Rehash, `smoke_dg.py`, `smoke_eg_corrections.py`, `check_clean_code.py`, `check_haus3d_js.py`, restart, browser check.
5. **Memory** update.

## Verification

- `core_validate.py` ok, counts include roof\_structure; EG unchanged.
- `/haus3d`: Dachstuhl visible over the DG, toggles; `/mengen` shows the Dachstuhl table.

## Critical files

- `code/weingaerten_core/compute/roof_structure_builder.py` (new), `storey_builder.py`, BOM builder
- house/storeys/upper.json, catalog/schema/storey.schema.json
- `code/weingaerten_web/static/haus3d.js`, `pages/haus3d_page.py`, `pages/mengen_page.py`
- weingaerten-core.md, weingaerten-web.md
