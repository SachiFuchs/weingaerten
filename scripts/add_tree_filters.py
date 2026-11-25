"""Sets default filters on the folders of the TGA trees (object picker in the tree editor stays short).

python scripts/add_tree_filters.py [--write]
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(ROOT, "catalog", "tga-trees")
# (tree, folder path) -> filter; only folders without an own filter are set
FILTERS = {
    ("elektro", "Leitungen"): {"class": "tga-class:cable"},
    ("elektro", "Rohre"): {"class": "tga-class:install-part", "query": "m20"},
    ("elektro", "Endgeräte"): {"class": "tga-class:terminal"},
    ("elektro", "Verteiler"): {"class": "tga-class:install-part", "query": "\"part_type\":\"box\""},
    ("abwasser", "HT DN 50"): {"query": "ht 50"},
    ("abwasser", "HT DN 50/Rohre"): {"class": "tga-class:pipe"},
    ("abwasser", "HT DN 90"): {"query": "ht 90"},
    ("abwasser", "HT DN 90/Rohre"): {"class": "tga-class:pipe"},
    ("zuwasser", "PPR"): {"query": "ppr"},
    ("zuwasser", "PPR/DN 20/Rohre"): {"class": "tga-class:pipe"},
}


def walk(tree_id, nodes, path, changed):
    for node in nodes:
        if "nodes" not in node:
            continue
        key = (tree_id, (path + "/" if path else "") + node["name"])
        if key in FILTERS and "filter" not in node:
            node["filter"] = FILTERS[key]
            changed.append(key[1])
        walk(tree_id, node["nodes"], key[1], changed)


def main():
    for name in sorted(os.listdir(FOLDER)):
        path = os.path.join(FOLDER, name)
        with open(path, encoding="utf-8") as f:
            tree = json.load(f)
        changed = []
        walk(tree["id"], tree["nodes"], "", changed)
        print(name, changed)
        if changed and "--write" in sys.argv:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(tree, f, ensure_ascii=False, indent=2)
                f.write("\n")


if __name__ == "__main__":
    main()
