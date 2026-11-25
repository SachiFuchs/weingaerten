# Plan: Decke EG

## Context
- Assembly classes live in `catalog/assembly-classes/`. `slab.json` ("Decke", KG 350) requires a thickness of 0.10-0.60 m, but the lining is only about 0.045 m, so it would warn.
- `catalog/schema/storey.schema.json` has `ceilings[]` (id, name, assembly, z, outline) marked VORSCHLAG. The core ignores it.
- Existing materials: `interior-paint-white` and `softwood-battens`. Plasterboard is missing.
- Your decisions: the beams are a **separate element**. Battens and plasterboard sit **under** the beams, so the beams are hidden (new state). Beam size is 12 x 18 cm at 80 cm spacing (an estimate).
- Assembly layers are stored `top_down`, so your bottom-to-top list is stored in reverse.

## Implementation steps
1. **Material** `catalog/materials/gypsum-board-gkb.json`: "Gipskartonplatte GKB 12,5 mm", category Platten, conductivity 0.25, density 680, vapour_resistance 8, fire_class A2, values_source DIN EN ISO 10456 / DIN 18180.
2. **Assembly class** `catalog/assembly-classes/ceiling-lining.json`: "Deckenbekleidung", category `slab`, din276 `354`, thickness 0.005-0.10, layers 1-6. This is a lining class, so the 0.10 m slab minimum does not apply.
3. **Assembly** `catalog/assemblies/ceiling-lining-cl1.json`: "Deckenbekleidung EG: Lattung 30 mm, GKB 12,5 mm, weiß gestrichen", class `assembly-class:ceiling-lining`, `layer_order: top_down`. Layers:
   - softwood-battens 0.03, `direction: south_north` (description: screwed to the underside of the beams)
   - gypsum-board-gkb 0.0125
   - interior-paint-white 0.002
4. **Schema extension** in `storey.schema.json` `ceilings[].items`:
   - `joists` object (separate element, KG 351): `material` (ref), `width`, `height`, `spacing` (centre-to-centre), `direction` (`west_east|south_north`), `estimated` (bool), `note`.
   - Optional `direction` on assembly layers in `assembly.schema.json` (enum south_north|west_east).
5. **Data** in `house/storeys/ground.json`: `ceilings: [{ id: "c-eg", name: "Decke EG", assembly: "assembly:ceiling-lining-cl1", outline: "storey", joists: { material: "material:spruce-wood", width: 0.12, height: 0.18, spacing: 0.80, direction: "west_east", estimated: true, note: "Bestandsbalken, Maße geschätzt (Fotos Nov 2026)" } }]`. The lining hangs below the beams: the lining's top edge = beam bottom edge = z (default height 2.75).
6. Check the core and the catalog page to confirm that `direction` and `ceilings` don't produce errors. The core ignores unknown fields according to the conventions. If the core's assembly check rejects `direction`, extend it in the cache minimally, then run `scripts/rehash_cache.py`.
7. Update the memory conventions with the ceiling-lining class, the joists model and the direction field.

## Verification
- `scripts/core_validate.py`: no new errors, and the "Aufbau ohne Klasse" warning does not appear for cl1.
- `scripts/smoke_assembly_classes.py`, `scripts/smoke_core.py` (known w-s2 failure excepted).
- Browser: /katalog/aufbauten shows cl1 with 3 layers (about 44.5 mm), /katalog/aufbauklassen shows "Deckenbekleidung", /katalog/materialien shows GKB.

## Critical Files
- `catalog/assemblies/ceiling-lining-cl1.json`: new assembly
- `catalog/assembly-classes/ceiling-lining.json`: new class
- `catalog/schema/storey.schema.json`: joists element
- `house/storeys/ground.json`: the ceiling entry
- `catalog/materials/gypsum-board-gkb.json`: new material
