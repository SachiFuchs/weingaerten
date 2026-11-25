"""List choice options of catalog/tga-classes without a German label in catalog/reference/labels-de.json.

Usage: python scripts/check_labels_de.py   (exit code 1 if something is missing)
"""
import json
import pathlib
import sys

HOME = pathlib.Path(__file__).resolve().parent.parent
LABELS = HOME / "catalog" / "reference" / "labels-de.json"


def table(labels, key):
    key = labels.get("aliases", {}).get(key, key)
    return labels.get("values", {}).get(key, {})


def main():
    labels = json.loads(LABELS.read_text(encoding="utf-8")) if LABELS.exists() else {}
    missing = []
    for path in sorted((HOME / "catalog" / "tga-classes").glob("*.json")):
        cls = json.loads(path.read_text(encoding="utf-8"))
        for q in cls.get("parameters", []):
            if q.get("type") != "choice":
                continue
            t = table(labels, q["key"])
            for o in q.get("options", []):
                if isinstance(o, str) and o not in t:
                    missing.append("%s %s: %s" % (path.stem, q["key"], o))
    for m in missing:
        print("fehlt", m)
    print("%d fehlende Übersetzungen" % len(missing))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
