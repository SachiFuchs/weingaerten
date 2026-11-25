"""Merge duplicate tga-components (same name, second id = first id + EAN suffix): the first keeps both offers and
both import sources, the second file is deleted. Refuses when the second one is referenced anywhere.

    python scripts/merge_duplicate_tga.py          # dry run
    python scripts/merge_duplicate_tga.py --write
"""
import json
import os
import re
import sys

ROOT = r"c:\Development\weingaerten"
FOLDER = os.path.join(ROOT, "catalog", "tga-components")


def load(cid):
    with open(os.path.join(FOLDER, cid + ".json"), encoding="utf-8") as handle:
        return json.load(handle)


def used(cid):
    needle = '"tga-component:%s"' % cid
    for root, _, files in os.walk(os.path.join(ROOT, "house")):
        for name in files:
            if name.endswith(".json") and needle in open(os.path.join(root, name), encoding="utf-8").read():
                return os.path.join(root, name)
    for root, _, files in os.walk(os.path.join(ROOT, "catalog")):
        if "imported_" in root:
            continue
        for name in files:
            if name.endswith(".json") and name != cid + ".json" and needle in open(os.path.join(root, name), encoding="utf-8").read():
                return os.path.join(root, name)
    return None


def main(write):
    ids = {n[:-5] for n in os.listdir(FOLDER) if n.endswith(".json")}
    pairs = []
    for cid in sorted(ids):
        base = re.sub(r"-\d{6,14}$", "", cid)
        if base != cid and base in ids and load(base).get("name") == load(cid).get("name"):
            pairs.append((base, cid))
    for keep, drop in pairs:
        where = used(drop)
        if where:
            print("übersprungen (verwendet in %s): %s" % (where, drop))
            continue
        first, second = load(keep), load(drop)
        product = first.setdefault("product", {})
        offers = product.setdefault("offers", [])
        offers += [o for o in (second.get("product") or {}).get("offers") or [] if o not in offers]
        first["imported_from"] = sorted(set(first.get("imported_from") or []) | set(second.get("imported_from") or []))
        print(("zusammengeführt " if write else "würde zusammenführen ") + "%s <- %s" % (keep, drop))
        if write:
            with open(os.path.join(FOLDER, keep + ".json"), "w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(first, ensure_ascii=False, indent=2) + "\n")
            os.remove(os.path.join(FOLDER, drop + ".json"))


if __name__ == "__main__":
    main("--write" in sys.argv)
