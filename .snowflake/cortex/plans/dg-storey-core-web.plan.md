---
name: "dg storey core web"
created: "2026-11-14T17:14:32.246Z"
status: pending
---

# Plan: Dachgeschoss (DG) in Core und Web

## Context

- `house/house.json` has only `storey:ground`; `ground.json` holds EG (7.12 x 13.13 m, outer faces x 0..7.12, y 0..13.13; old north wall 0.30 at y 2.08..2.38; flat roof `c-flachdach` north of it; terrace SW, Zimmer 2 SE).
- Core already supports several storeys (`elevation`, `height`), interior walls, rooms, `outdoor_areas`, ceilings. Walls always get storey height -> no knee walls yet.
- Web Grundriss draws only the **first storey** (`weingaerten-web.md` line 135).
- Code is generated from the spec sections, so changes go into spec + code + `scripts/rehash_cache.py`.

User decisions: align to EG, knee walls + Abseiten as rooms (roof later), elevation 2.95, height 2.40, **knee wall 1.25 m, roof pitch 30 deg**, layout as drawn, no windows.

## Knee wall / slope

- Slope height at distance d from the inner face of the knee wall: h(d) = 1.25 + d \* tan(30 deg) = 1.25 + 0.577 d.
- 2 m line: d = 0.75 / 0.577 = **1.30 m**. The plan dimensions the 2 m line at **0.85 m** (h(0.85) = 1.74 m). Assumption: Abseiten strips from the computed 1.30 m (consistent with 1.25 / 30 deg); the plan value is mentioned in the room description. Can be switched to 0.85 if the plan is the measured truth.
- Store on the storey as data only: `roof_pitch: 30`, `knee_wall_height: 1.25` (core passes through, roof geometry later).

## DG geometry (m, EG coordinates, outer faces)

- North wall exterior 0.30: y 2.08..2.38, x 0..7.12, full height 2.40 (assumed).
- Durchgangszimmer y 2.38..5.40; interior wall 0.15 y 5.40..5.55; Schlafzimmer y 5.55..9.64; wall Schlafzimmer/Balkon 0.30 y 9.64..9.94, x 2.72..7.12, exterior (outside south), full height.
- West knee wall 0.30 x 0..0.30, y 2.08..9.94, `height` 1.25; east knee wall 0.30 x 6.82..7.12, height 1.25.
- Kammer 2: west 0.20 (knee 1.25), south 0.20, east 0.20 (x 2.52..2.72, towards balcony, full height); room 0.20..2.52 x 9.94..12.93.
- Balkon = `outdoor_areas` \[2.72, 9.94, 4.40, 3.19].
- Rooms: Durchgangszimmer, Schlafzimmer, Kammer 2 (main area), Abseite West/Ost per room (1.30 m strips), Treppe 2.37 x 1.09 (stair hole not modelled).
- Assemblies: exterior `exterior-wall-ew1`, interior `interior-wall-iw1` (noted as approximation of 0.15).
- Doors (new components, estimated 0.80 x 2.00 / 0.76 x 2.00): Durchgangszimmer->Schlafzimmer, 2x Schlafzimmer->Balkon, Kammer 2->Balkon.
- No DG ceiling/roof yet.

## Implementation steps

1. **Core: per-wall height.** Optional `wall.height` (> 0, <= storey height, else `Wandhöhe ungültig`); `z1 = z0 + (wall.height ?? storey.height)`; opening check against wall height; WALLS\_SAVE keeps it; schema updated. Storey fields `roof_pitch`, `knee_wall_height` passed through.
2. **Core: upper storeys.** Foundation rule only for ground storey; spec test counts storeys 2.
3. **Data:** door components, `house/storeys/upper.json`, `house.json` storeys += `storey:upper`.
4. **Web:** storey select on Grundriss / Wände / edit (`?storey=`); knee walls (below 1.0 m cut? no, 1.25 > 1.0, cut normally); `/haus3d` all storeys at elevation; Grundriss draws the 2 m line dashed if `roof_pitch` set.
5. **Rehash + restart** (`scripts/rehash_cache.py`, `start.cmd`).
6. **Memory** update.

## Verification

- `scripts/core_validate.py` ok, storeys 2.
- New `scripts/smoke_dg.py`: knee wall z1 = 2.95 + 1.25; wall height > storey -> error; door higher than knee wall -> error; WALLS\_SAVE keeps `height`.
- Existing checks (`smoke_eg_corrections.py`, `check_ceilings.py`, `check_haus3d_js.py`, `check_kat_js.py`, `check_clean_code.py`) still pass.
- Browser: /grundriss?storey=upper, /haus3d, /waende.

## Critical files

- weingaerten-core.md, weingaerten-web.md
- house/storeys/upper.json, house/house.json
- `code/weingaerten_core/compute/wall_parser.py`, `storey_checks.py`
