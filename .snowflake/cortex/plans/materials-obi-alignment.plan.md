---
name: "materials obi alignment"
created: "2026-11-20T13:40:19.014Z"
status: pending
---

# Plan: Materialien an OBI-Importe angleichen

## Kontext

- `catalog/materials` (29): Baustoffe mit Kennwerten; IDs werden von Bauteilaufbauten referenziert.
- `catalog/imported_material` (754): OBI-Artikel als `ean-<EAN>_<slug>.json`, ohne EAN als `obi-<Artikelnr>_<slug>.json`.

## Freigegebene Zuordnung

| Material             | products                                                   |
| -------------------- | ---------------------------------------------------------- |
| exterior-paint-white | ean-4001244709106, ean-4001244753734, obi-6791222          |
| interior-paint-white | ean-4001244791934                                          |
| softwood-battens     | ean-4005014000790, ean-4005014000882                       |
| spruce-wood          | ean-4005014000288, ean-4005014000394                       |
| pu-white             | keine Verknüpfung, bleibt getrennt von den Soudal-Artikeln |

## Schritte

1. Namensregel in den Projekt-Konventionen dokumentieren: Material-IDs bleiben; Import `ean-<EAN>_<slug>` oder `obi-<Artikelnr>_<slug>`.
2. `catalog/schema/product.schema.json` anlegen (beide Präfixe, Pflichtfelder name, url, supplier sowie ean oder article\_number).
3. `material.schema.json` um ein optionales `products` erweitern (Pattern `^(ean-[0-9]{8,14}|obi-[0-9]+)$`).
4. Die vier Materialien verknüpfen: `products` eintragen und `values_source`/`description` um „OBI-Einkauf“ ergänzen. Die Kennwerte bleiben.
5. Optional: Bilder der verknüpften Artikel als `photos` übernehmen (nur auf Wunsch).

## Verifikation

- Schema-Validierung beider Ordner.
- Jede `products`-Referenz zeigt auf eine existierende Datei.
- Referenzen auf Material-IDs bleiben unverändert (grep vorher und nachher).
- Bestehende Tests und Baseline-Vergleiche laufen durch.

## Kritische Dateien

- catalog/schema/material.schema.json
- catalog/schema/product.schema.json (neu)
- catalog/materials/{exterior-paint-white,interior-paint-white,softwood-battens,spruce-wood}.json
