"""Convert the TGA runs (house/tga/runs) into installed parts (house/tga/parts) and compare the bill of materials.

Default = dry run on a temp copy: the runs are removed there, the generated parts added, and the BOM of both
variants is compared (pipe length and piece count per component). `--write` writes the parts into the project
(the runs stay; then both are counted until the runs are archived by hand).

Free parts: every cut piece of a straight stretch becomes a pipe part along the segment, every resolved fitting a
part at its position with the fitting's direction as local x. Ports of migrated bends/branches are placed by the
catalog geometry, so they only seat where the run geometry matches the catalog angles exactly.
"""
import json
import math
import os
import shutil
import sys
import tempfile

ROOT = r"c:\Development\weingaerten"
sys.path.insert(0, os.path.join(ROOT, "code"))
import weingaerten_core  # noqa: E402

SYSTEMS = ("waste_water", "water_supply", "electrical")
CONDUIT_PIPE = {"electrical": "installationsrohr-m20-starr-lichtgrau-dr"}


def ask(command):
    return json.loads(weingaerten_core.handle(json.dumps(command)))


def unit(v):
    length = math.sqrt(sum(c * c for c in v))
    return [c / length for c in v] if length > 1e-9 else None


def up_for(x):
    # any vector perpendicular to x: vertical pipes take +y of the plan, others the world z
    return [0.0, 1.0, 0.0] if abs(x[2]) > 0.9 else [0.0, 0.0, 1.0]


def storey_of(house, z):
    storeys = sorted(house["storeys"], key=lambda s: s["elevation"])
    found = storeys[0]
    for storey in storeys:
        if z >= storey["elevation"] - 1e-6:
            found = storey
    return found["id"]


def pipe_parts(house, system, block, catalog):
    runs = {r["id"]: r for r in block["runs"]}
    parts = []
    for cut in block["cuts"]:
        run = runs[cut["run"]]
        segment = run["segments"][cut["segment"]]
        x = unit([segment["to"][i] - segment["from"][i] for i in range(3)])
        component = CONDUIT_PIPE.get(system) if system == "electrical" else run["component"]
        if x is None or "tga-component:" + component.split(":")[-1] not in catalog:
            continue
        component = "tga-component:" + component.split(":")[-1]
        offset = (cut["length"] - cut["net_length"]) / 2.0 if cut.get("length") else 0.0
        for n, piece in enumerate(cut["pieces"]):
            start = [segment["from"][i] + x[i] * offset for i in range(3)]
            parts.append({"id": "m-%s-%d-%d" % (cut["run"], cut["segment"], n + 1), "component": component,
                          "storey": storey_of(house, start[2]), "host": None, "position": start,
                          "axes": {"x": x, "y": up_for(x)}, "length": round(piece, 4), "system": run.get("system"),
                          "medium": run.get("medium"), "estimated": True,
                          "note": "migriert aus tga-run:%s" % cut["run"]})
            offset += piece
    return parts


def fitting_parts(house, block, catalog):
    parts = []
    for n, fitting in enumerate(block["parts"]):
        if not fitting.get("position") or fitting.get("component") not in catalog:
            continue
        x = unit(fitting.get("direction") or [1, 0, 0]) or [1.0, 0.0, 0.0]
        parts.append({"id": "m-%s-f%d" % (fitting["run"], n + 1), "component": fitting["component"],
                      "storey": storey_of(house, fitting["position"][2]), "host": None,
                      "position": fitting["position"], "axes": {"x": x, "y": up_for(x)}, "estimated": True,
                      "note": "migriert aus tga-run:%s" % fitting["run"]})
    return parts


def summary(bom):
    block = bom.get("installation") or {}
    return {r["component"]: (r["count"], round(r["length"] or 0.0, 2)) for r in block.get("components") or []}


def run_summary(bom):
    result = {}
    for system in SYSTEMS:
        block = bom.get(system) or {}
        for row in block.get("stock") or []:
            entry = result.setdefault(row["component"], [0, 0.0])
            if row["kind"] == "pipe":
                entry[1] += (row["length"] or 0.0) * row["count"]
            else:
                entry[0] += row["count"]
    return result


def main(write):
    os.environ["WEINGAERTEN_HOME"] = ROOT
    house = ask({"command": "HOUSE"})
    catalog = {c["ref"] for c in house["installation"]["catalog"]}
    parts = []
    for system in SYSTEMS:
        block = house.get(system)
        if block:
            parts += pipe_parts(house, system, block, catalog) + fitting_parts(house, block, catalog)
    for n, part in enumerate(parts):
        part["id"] = "m-%d" % (n + 1)
    before = run_summary(ask({"command": "BOM"}))
    temp = tempfile.mkdtemp()
    try:
        for folder in ("catalog", "house"):
            shutil.copytree(os.path.join(ROOT, folder), os.path.join(temp, folder),
                            ignore=shutil.ignore_patterns("imported_*"))
        shutil.rmtree(os.path.join(temp, "house", "tga", "runs"))
        os.environ["WEINGAERTEN_HOME"] = temp
        answer = ask({"command": "PART_SAVE", "upsert": parts, "delete": []})
        if "error" in answer:
            print("Fehler:", answer.get("errors") or answer["error"])
            return
        after = summary(ask({"command": "BOM"}))
        open_ports = ask({"command": "HOUSE"})["installation"]["open_ports"]
    finally:
        os.environ["WEINGAERTEN_HOME"] = ROOT
        shutil.rmtree(temp, ignore_errors=True)
    print("%d Teile erzeugt, %d offene Anschlüsse" % (len(parts), open_ports))
    print("%-48s %22s %22s" % ("Komponente", "Leitungen (Stk / Stangen-m)", "Teile (Stk / m)"))
    for ref in sorted(set(before) | set(after)):
        print("%-48s %22s %22s" % (ref.split(":")[-1][:48], before.get(ref), after.get(ref)))
    if write:
        folder = os.path.join(ROOT, "house", "tga", "parts")
        os.makedirs(folder, exist_ok=True)
        for part in parts:
            with open(os.path.join(folder, part["id"] + ".json"), "w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(part, ensure_ascii=False, indent=2) + "\n")
        print("geschrieben nach", folder)


if __name__ == "__main__":
    main("--write" in sys.argv)
