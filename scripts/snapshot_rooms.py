"""Snapshot of the room-dependent core answers (floors, heating, rooms, BOM totals, messages) for before/after checks.

Usage: python snapshot_rooms.py <out.json>   (WEINGAERTEN_HOME defaults to the project)
       python snapshot_rooms.py --compare <before.json> <after.json>
"""
import json
import os
import sys

HOME = os.environ.setdefault("WEINGAERTEN_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(HOME, "code"))


def snapshot():
    import weingaerten_core
    house = json.loads(weingaerten_core.handle(json.dumps({"command": "HOUSE"})))
    bom = json.loads(weingaerten_core.handle(json.dumps({"command": "BOM"})))
    result = {"totals": bom.get("totals"), "errors": sorted(e["message"] for e in house.get("errors", [])),
              "storeys": {}}
    validate = json.loads(weingaerten_core.handle(json.dumps({"command": "VALIDATE"})))
    result["warnings"] = sorted(w["where"].split(".")[0] + ": " + w["message"] for w in validate.get("warnings", []))
    for storey in house["storeys"]:
        rooms = {}
        for room in storey["rooms"]:
            entry = rooms.setdefault(room["name"], {"area": 0.0, "wall_area": 0.0})
            entry["area"] = round(entry["area"] + room["area"], 4)
            entry["wall_area"] = round(entry["wall_area"] + room["wall_area"], 4)
        result["storeys"][storey["id"]] = {
            "rooms": rooms,
            "floors": [{"id": f["id"], "area": f["area"], "edge_length": f["edge_length"],
                        "rooms": [(r["name"], r["area"], r["edge_length"]) for r in f["rooms"]]} for f in storey["floors"]],
            "heating": None if not storey.get("heating") else
            [(c["id"], c["area"], c["length"]) for c in storey["heating"]["circuits"]]}
    return result


def compare(before_path, after_path):
    with open(before_path, encoding="utf-8") as handle:
        before = json.load(handle)
    with open(after_path, encoding="utf-8") as handle:
        after = json.load(handle)
    differences = 0
    for key in ("totals",):
        for name in sorted(set(before[key]) | set(after[key])):
            a, b = before[key].get(name), after[key].get(name)
            if a != b:
                differences += 1
                print("totals.%s: %s -> %s" % (name, a, b))
    for storey in before["storeys"]:
        for part in ("rooms", "floors", "heating"):
            a, b = before["storeys"][storey][part], after["storeys"].get(storey, {}).get(part)
            if a != b:
                differences += 1
                print("%s.%s:\n  vorher  %s\n  nachher %s" % (storey, part, a, b))
    for key in ("errors", "warnings"):
        gone = sorted(set(before[key]) - set(after[key]))
        new = sorted(set(after[key]) - set(before[key]))
        for message in gone:
            print("%s weg: %s" % (key, message))
        for message in new:
            print("%s neu: %s" % (key, message))
    print("%d Unterschiede in Summen/Räumen/Böden/Heizung" % differences)


if __name__ == "__main__":
    if sys.argv[1] == "--compare":
        compare(sys.argv[2], sys.argv[3])
    else:
        with open(sys.argv[1], "w", encoding="utf-8") as out:
            json.dump(snapshot(), out, ensure_ascii=False, indent=1)
        print("written", sys.argv[1])
