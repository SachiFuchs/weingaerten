# Plan: EG-Boden + Fußbodenheizung (7 Heizkreise)

## Context
- Rooms from `house/storeys/ground.json`: Flur, Bad, Treppe, Küche, Kammer, Wohnzimmer, Zimmer 2.
- **Wohnzimmer is one room.** It is L-shaped, and the current data stores it as 3 rects with the same name (room-wohnzimmer, -nord, -ost; convention "L-rooms split into rects with same name"). The same goes for Flur (2 rects). Floor, heating, BOM and labels always refer to the room by its name, never to a single sub-rect.
- Heating circuits: HK1-HK4 Wohnzimmer, HK5 Küche, HK6 Bad, HK7 Flur. Treppe, Kammer and Zimmer 2 have none.
- Riempp offer 25-0235 pos. 2-6 (60 m² each): Heizestrich S38 33.60 EUR/m², Noppenplatte Bekotec EN 23F 26.80, Randdämmstreifen 1.95, PUR/PIR 023 30 mm 10.20, Abstellungen 5 m at 4.90/m. Pipe Ø 14 mm.
- Patterns: ceilings (storey.ceilings[] -> core, BOM, 3D checkbox, /mengen), products/offers (catalog/companies), prepared TGA schemas (tga-classes kind pipe, house/tga).

## Sketch (Nord oben)
```
            ┌─────────────────────┬──────────────────────┐
            │  Flur        HK7 [V]?  Bad          HK6    │
      ┌─────┴──────────────┬──┬──┼──────────────────────┤
      │ Treppe   (kein HK) │  │║║│  Küche        HK5    │
      ├────────────────────┘  │║║│                      │
      │                        ║║├──────────────────────┤
      │  Wohnzimmer   HK1      ║║│  Kammer   (kein HK)  │
      │                        ║ └──────────────────────┤
      │    HK2      │    HK3   ║═══   HK4               │
      └─────────────┴──────────┴──┬─────────────────────┤
                                  │ Zimmer 2   (kein HK)│
                                  └─────────────────────┘
 Wohnzimmer = ein L-förmiger Raum mit HK1-HK4; ║ = Zuleitungen
```

## Assumptions
1. The build-up covers all EG rooms (about 60 m²). Pipes run only in the 7 circuits. Old floor top = z 0, and the build-up adds +11.5 cm.
2. Manifold at the north end of the Flur passage (photo 6), estimated.
3. Pipe spacing 15 cm, edge distance 10 cm, pattern spiral or meander, estimated.
4. Oberbelag stays open.

## Implementation steps
1. Catalog: add the materials Dielen, Kork, Laminat grau, PUR/PIR 023, Bekotec plate, Heizestrich and PE edge strip. Add the company `riempp-estriche` with the offer prices, and the tga-class `pipe-bekotec-14`.
2. Assembly `floor-eg-fbh` (bottom-up: Dielen 3 / Kork 0.5 / Laminat 0.2 / PUR 3.0 / plate + pipe / screed S38). Add `storey.floors[] {id, assembly, rooms: [<room name>...]}`: a name resolves to all rects of that room, merged into one outline per room.
3. `house/tga/heating.json`: `manifold {position}` and `circuits[] {id hk1..hk7, name, room (name, e.g. "Wohnzimmer"), area rect inside the room, pattern, spacing, edge, feed_path[], estimated}`. HK1-HK4 each cover their own part of the one room Wohnzimmer. Their areas must not overlap and must lie inside the room outline.
4. Core: floor_builder (merged room outline, layers, area, edge strip = room perimeter minus doors) and heating_builder (spiral/meander generator plus feed line, length per circuit). Validation: circuit inside room, no overlap, spacing >= 7.5 cm, length > 100 m warning. BOM: floors per room, heating per circuit, totals, offer prices and a comparison with the 60 m².
5. Web: in /haus3d, floor slabs per room plus a new checkbox `Heizung` (`heizung3d`, localStorage, disabled without heating). Pipes in one colour per circuit, tooltip `HK n`, room, length. In /mengen: tables Boden (per room: Wohnzimmer as one row) and Fußbodenheizung.
6. Update the spec in core/web md, regenerate the cache, rehash, restart the server.

## Verification
- `scripts/smoke_floor_heating.py`: 7 circuits, 4 of them in room Wohnzimmer, the floor table lists Wohnzimmer exactly once, area sum about 60 m², thickness 0.115 m.
- `check_haus3d_js.py`, `check_web.py`, and a manual check of the Heizung toggle and /mengen.

## Critical Files
- [house/storeys/ground.json](house/storeys/ground.json) - rooms, floors[]
- house/tga/heating.json (new)
- [weingaerten-core.md](weingaerten-core.md) - floor/heating builder, room merge by name
- [weingaerten-web.md](weingaerten-web.md) - Heizung toggle, tables
- catalog/materials, catalog/assemblies, catalog/companies/riempp-estriche.json
