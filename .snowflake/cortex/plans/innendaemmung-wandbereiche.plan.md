# Innendämmung: Bereiche auf Wandseiten

## Context
- Walls (`catalog/schema/storey.schema.json:146-193`, `additionalProperties:false`) have whole-wall layers only. Openings are cut in `compute/layer_piece_builder.py`. The face area comes from `wall_face_builder.py`.
- Template: `compute/facade_builder.py`. It runs last in `storey_builder.py:99` on the serialized walls (`u_range`, `profile`, `normal_in`, `openings[].rough`) and has its own BOM rows (`bill_of_materials.py:74-89`), a `/mengen` table and 3D parts.
- Inside face: for an exterior wall it is t = thickness (`faces.inside`). For an interior wall both sides can be room sides, so a region needs `face: left|right`.
- Catalog: Lehmkleber, Holzfaserplatte and Lehmfarbe are missing. Naturbo and Fesche Farbe are also missing as companies.
- Decisions:
  - A region is a rectangle in u/z on one side of a wall.
  - It is a lining in front of the face: wall axes and rooms stay unchanged.
  - Openings are cut out; there is no reveal treatment.

## Data model
- Catalog:
  - `company:naturbo` (manufacturer)
  - `company:fesche-farbe` (manufacturer)
  - materials:
    - `lehmkleber-naturbo`
    - `holzfaserplatte-naturbo`
    - `lehmputz-naturbo`
    - `lehmfarbe-fesche-farbe`
    
    Each has `product.manufacturer` and is marked `values_source` estimated.
- Assembly `interior-insulation-ii1`:
  - new category `interior_lining`, din276 `345` (Innenwandbekleidung)
  - `layer_order: wall_out`, meaning from the wall surface towards the room
  - layers: 0.003 / 0.06 / 0.003 / 0.001, giving 6.7 cm in total
- Wall field `linings[]`: `{id, assembly, face: inside|left|right, u0, u1, z0?, z1?, note?}`.
  - u is measured from the wall start on the reference line, the same convention as `opening.offset`.
  - z defaults to the floor and the wall top (or the roof profile).
  - Schema: `storey.schema.json` wall properties, and the assembly category enum in `assembly.schema.json`.

## Implementation steps
1. **Catalog:** add the 2 companies, the 4 materials and the assembly. Extend the category in the schemas and in the catalog UI category list (katalog).
2. **Spec, core (`weingaerten-core.md`):**
   - New section "Innendämmung":
     - validation: u within `u_range` of the face, z0 < z1, assembly category `interior_lining`, `face` allowed by wall type, no overlap of regions on the same face
     - errors kind `lining`
   - Geometry, BOM and HOUSE output.
   - Code structure: `compute/lining_builder.py`, `editing/lining_editor.py`, and the command `LINING_SAVE`/`LINING_DELETE`.
3. **Core implementation:**
   - `LiningBuilder`, modelled on the FacadeBuilder frame (`_frame/_point`):
     - It works per layer band t = thickness + offset (or a negative offset on the left face).
     - It subtracts opening rough rectangles in u/z, the same way as `LayerPieceBuilder._free_intervals`, which gives real holes.
     - It clips at the top using the roof profile.
     - Parts are `{id <wall>-<lining>-<layer>-<n>, wall, lining, layer, material, footprint, z0, z1, top_plane, area, volume, color}`.
   - Call it in `storey_builder.py` after the facade, and add a `linings` output per storey.
   - BOM:
     - new `linings[]` rows per region: net area, area of the openings removed, volume per layer
     - totals `lining_area` and `lining_volume`
     - material tally: volume plus `area_inside` per layer
   - Update `element_counter` and `house_summary` (materials used).
   - Editor (`LiningEditor`), the same as `opening_editor`: it edits a deep copy, uses `StoreyChangeCheck.new_errors`, then writes the file. Register it in `command_handler._write`, `constants.WRITE_COMMANDS` and `walls_editor` (keep `linings` when walls are saved, and move/drop them on split as `take_openings` does).
4. **Spec, web (`weingaerten-web.md`):**
   - API `/api/lining/save|delete`
   - page `/waende`: section "Innendämmung"
   - 3D checkbox `daemmung3d`
   - `/mengen` table "Innendämmung"
5. **Web implementation:**
   - Add the entries to `constants.API_COMMANDS`.
   - `waende_page.py`: a panel and a table of regions for the selected face (in the inside view; on interior walls, the inside view = right face and the outside view = left face, matching `faceRange`).
   - `wand.js`:
     - Draw the region as a hatched rectangle with the openings cut out.
     - Selecting a region opens a form: assembly select, von/bis Länge, von/bis Höhe in cm (empty = full height).
     - Buttons: "Neuer Dämmbereich", Speichern, Löschen. Dragging the edges is optional, like openings.
     - Browser-side checks: overlap and range.
   - `haus3d.js`: draw the lining parts (Technik/Stockwerke checkbox `daemmung3d`).
   - Add `pages/lining_table.py` to `/mengen`.
6. **Rehash and restart:** run `scripts/rehash_cache.py`, end the old server processes, then `start.cmd`.

## Verification
- New `scripts/smoke_linings.py` on a temp copy (WEINGAERTEN_HOME):
  - Region on an EG exterior wall that contains a window: area = rectangle minus the rough opening, 4 layers, volume 0.06·area for the wood fibre layer.
  - Interior wall, face left and face right.
  - DG roof wall clipped at the roof profile.
  - Errors on overlap, outside the range, or wrong face.
  - LINING_SAVE/DELETE.
  - WALLS_SAVE keeps the linings.
- `scripts/check_clean_code.py`, `check_haus3d_js.py`, a node syntax check of wand.js, and `check_web.py` (read-only, server running).
- Manual check: /waende, create a region on w-north with o-flur, then look at it in 3D and in /mengen.

## Critical Files
- [code/weingaerten_core/compute/facade_builder.py](code/weingaerten_core/compute/facade_builder.py) - template for frame, clipping and parts
- [code/weingaerten_core/compute/storey_builder.py](code/weingaerten_core/compute/storey_builder.py) - integration
- [code/weingaerten_core/queries/bill_of_materials.py](code/weingaerten_core/queries/bill_of_materials.py) - BOM
- [code/weingaerten_web/static/wand.js](code/weingaerten_web/static/wand.js) - editing in the elevation
- [catalog/schema/storey.schema.json](catalog/schema/storey.schema.json) - wall field linings
- weingaerten-core.md / weingaerten-web.md - spec sections (hash)
