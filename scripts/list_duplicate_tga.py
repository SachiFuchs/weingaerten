"""List duplicate tga-components (same name, or same id apart from an EAN / pack suffix) and where they are used."""
import json
import os
import re
from collections import defaultdict

ROOT = r"c:\Development\weingaerten"
FOLDER = os.path.join(ROOT, "catalog", "tga-components")

elements = {}
for name in sorted(os.listdir(FOLDER)):
    if name.endswith(".json"):
        with open(os.path.join(FOLDER, name), encoding="utf-8") as handle:
            elements[name[:-5]] = json.load(handle)


def key(cid, element):
    base = re.sub(r"-\d{6,14}$", "", cid)  # EAN suffix of a second receipt import
    return (element.get("name") or "").strip().lower(), base


by_name, by_base = defaultdict(list), defaultdict(list)
for cid, element in elements.items():
    name, base = key(cid, element)
    by_name[name].append(cid)
    by_base[base].append(cid)

texts = {}
for root, _, files in os.walk(ROOT):
    if any(part in root for part in ("imported_", "\\code", "\\scripts", ".snowflake", "\\hashes")):
        continue
    for name in files:
        if name.endswith(".json"):
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as handle:
                texts[os.path.relpath(path, ROOT)] = handle.read()

groups = {tuple(sorted(v)) for v in list(by_name.values()) + list(by_base.values()) if len(v) > 1}
for group in sorted(groups):
    print("==", elements[group[0]].get("name"))
    for cid in group:
        e = elements[cid]
        users = [p for p, t in texts.items() if '"tga-component:%s"' % cid in t and not p.endswith(cid + ".json")]
        print("   %-60s install=%-5s offers=%d used=%s" % (cid, "install" in e, len((e.get("product") or {}).get("offers") or []),
                                                          users))
