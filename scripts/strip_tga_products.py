"""Remove the product block of tga-components whose catalog_material carries the product (Lösung 1: material = single source).

Usage: python scripts/strip_tga_products.py [--write]
Without --write only lists what would change. Components without a material product (placeholders) keep theirs.
Offers that exist only at the component are moved to the material first (nothing is lost).
"""
import json
import os
import sys

ROOT = r"c:\Development\weingaerten"
MATERIALS = os.path.join(ROOT, "catalog", "materials")
TARGET = os.path.join(ROOT, "catalog", "tga-components")


def _read(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _offer_keys(product):
    return sorted((o.get("supplier"), o.get("price"), o.get("date")) for o in product.get("offers") or [])


def main(write):
    changed, kept, differs = 0, 0, 0
    for name in sorted(os.listdir(TARGET)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(TARGET, name)
        element = _read(path)
        if not isinstance(element.get("product"), dict):
            continue
        ref = element.get("catalog_material") or ""
        material_path = os.path.join(MATERIALS, ref.split(":", 1)[-1] + ".json")
        material = _read(material_path) if ref.startswith("material:") and os.path.isfile(material_path) else {}
        if not isinstance(material.get("product"), dict):
            kept += 1
            continue
        own, theirs = element["product"], material["product"]
        missing = set(_offer_keys(own)) - set(_offer_keys(theirs))
        if missing or own.get("article_no") != theirs.get("article_no"):
            differs += 1
            print("ABWEICHUNG %s: Angebote nur am TGA-Bauteil %s (werden ans Material übertragen), Artikelnr %s / %s"
                  % (name[:-5], sorted(missing), own.get("article_no"), theirs.get("article_no")))
        if missing:
            theirs.setdefault("offers", []).extend(
                o for o in own.get("offers") or [] if (o.get("supplier"), o.get("price"), o.get("date")) in missing)
            theirs["offers"].sort(key=lambda o: o.get("date") or "")
            if write:
                with open(material_path, "w", encoding="utf-8", newline="\n") as handle:
                    handle.write(json.dumps(material, ensure_ascii=False, indent=2) + "\n")
        del element["product"]
        changed += 1
        if write:
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(element, ensure_ascii=False, indent=2) + "\n")
    print("%s %d, behalten (kein Material-Produkt) %d, mit Abweichung %d"
          % ("entfernt" if write else "würde entfernen", changed, kept, differs))


if __name__ == "__main__":
    main("--write" in sys.argv)
