"""Print a compact overview of a storey: walls (start/end, thickness, height, assembly), rooms, openings, linings.

    python scripts/dump_storey.py upper
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(name):
    data = json.loads((ROOT / "house" / "storeys" / (name + ".json")).read_text(encoding="utf-8"))
    print("keys:", list(data.keys()))
    for key, value in data.items():
        if isinstance(value, list) and value and isinstance(value[0], dict):
            print("\n==", key, len(value))
            for item in value:
                print(json.dumps(item, ensure_ascii=False)[:400])
        elif not isinstance(value, (list, dict)):
            print(key, "=", value)
        elif isinstance(value, dict):
            print("\n==", key, json.dumps(value, ensure_ascii=False)[:600])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "upper")
