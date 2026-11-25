---
name: "dg gable walls"
created: "2026-11-14T17:44:29.306Z"
status: pending
---

# Plan: Giebelwände im DG (Wandoberkante folgt der Dachschräge)

## Context

- Right now the DG walls are rectangles: knee walls via `wall.height` 1.25, all others 2.40. The core rejects `shape.kind: gable` ("gable noch nicht unterstützt", `compute/wall_parser.py:51`); the schema has `gable` with `ridge_height/ridge_offset` reserved.
- All wall geometry is "footprint x \[z0, z1]": `LayerPieceBuilder` (pieces), `WallFaceBuilder` (areas = length x height), `OpeningParser._check_fit` (zt <= height), `WallSerializer` (height/z1), `haus3d.js` `prism(footprint, z0, h)`, `wand.js` elevation as a rectangle.
- User decisions: ridge from 1.25 m + 30 deg (about 3.31 m above the DG floor, ridge at x 3.56). Following the roof: north wall, wall Schlafzimmer/Balkon, south wall Kammer 2, east wall Kammer 2 (rectangular, height = roof at x 2.72). Interior walls also go up to the roof.

## Model

Storey roof (replaces `roof_pitch` / `knee_wall_height`):

```json
"roof": { "kind": "gable", "pitch": 30, "knee_wall_height": 1.25, "ridge_direction": "south_north", "eaves": [0, 7.12] }
```

- Roof underside height (storey-local) at plan point (x, y): `h(x) = knee + tan(pitch) * min(x - eaves0, eaves1 - x)`, capped at `ridge = knee + tan(pitch) * (eaves1 - eaves0)/2` (3.305). Measured at the outer face line (as computed); `west_east` ridge uses y.
- Wall `shape: {"kind": "roof"}` -> top edge `z_top(u) = h(point on the reference line at u)`; walls parallel to the ridge are constant (knee walls 1.25 automatically, Kammer 2 east 2.82), walls across it get a gable / partial gable. `wall.height` stays for rect walls (DG knee walls switch to `roof`, height field dropped).
- `shape: roof` without `storey.roof` -> error `Dach fehlt für Dachwand`; `gable` keeps its current error.

## Implementation steps

1. **Core: RoofProfile** (new `compute/roof_profile.py`): `height_at(x, y)`, `ridge_u(wall)` (break point), `plane(wall, u0, u1)` -> absolute top plane `[a, b, c]` (z = a*x + b*y + c) of a slab, `profile(wall)` -> `[[u, z]]` top polyline over the outside u range. Parse `storey.roof` (pitch 0..90, knee > 0, eaves ascending, else `Dach ungültig`).

2. **Core: pieces, faces, openings, output.**

   - `LayerPieceBuilder`: extra break point at the ridge u; the top interval of a slab ends at the slab's top plane; piece gets `top_plane` (null for rect) and `z1` = max top, volume = area x (plane at the centroid - z\_low), exact for planar tops.
   - `WallFaceBuilder`: face area = integral of the profile over the face line minus holes; room segments likewise.
   - `OpeningParser`: `zt <= min top over [u0, u1]` (else `Öffnung höher als die Wand`).
   - `WallSerializer`: `height` = max top, `z1`, new `profile` (rect: two points at the height).
   - `StoreyBuilder`: build the RoofProfile, pass it on; storey output `roof` instead of `roof_pitch` / `knee_wall_height`.
   - Schema: `storey.roof`, `shape.kind` enum `rect|gable|roof`. Core spec (walls, output, tests).

3. **Data** `house/storeys/upper.json`: add the `roof` block, set every wall to `shape: {kind: "roof"}`, remove `height` / `roof_pitch` / `knee_wall_height`.

4. **Web.**

   - `haus3d.js`: `prism` gets an optional top plane (top vertices z = plane); layer pieces use `pc.top_plane`; section clipping unchanged.
   - `wand.js`: draw the elevation from `profile` (polygon instead of rectangle); the draft and drag limit for openings use the profile height at the opening.
   - `plan_svg.py`: 2 m line from `storey.roof` (x where h = 2, both sides, over the storey's bbox), instead of per knee wall.
   - `plan.js`: keep `shape` from the data instead of always `{kind:'rect'}` (and drop the `wh` field).
   - Web spec updated.

5. **Tests:** update `scripts/smoke_dg.py`: north wall profile 1.25 -> 3.305 -> 1.25 at u 3.56; Balkon wall ends 1.25 / about 2.82; Kammer 2 east wall 2.82 constant; volume of the north wall = area of the profile polygon x thickness (+/- 1e-6); door above the slope -> error; `shape roof` without roof -> error; WALLS\_SAVE keeps the shape. Rehash, `check_clean_code.py`, `smoke_eg_corrections.py` (EG unchanged), `check_haus3d_js.py`, restart and check the browser (3D, Wände DG, Grundriss DG).

6. **Memory** update.

## Verification

- `core_validate.py` ok; EG results unchanged (bom totals of the EG storey equal to before).
- `smoke_dg.py` all ok; 3D shows the gables up to the ridge; /waende?storey=upper shows the sloped elevation.

## Critical files

- `code/weingaerten_core/compute/roof_profile.py` (new), `layer_piece_builder.py`, `wall_face_builder.py`, `opening_parser.py`, `wall_serializer.py`, `storey_builder.py`, `wall_parser.py`
- house/storeys/upper.json, catalog/schema/storey.schema.json
- `code/weingaerten_web/static/haus3d.js`, `wand.js`, `plan.js`, `plan/plan_svg.py`
- weingaerten-core.md, weingaerten-web.md
