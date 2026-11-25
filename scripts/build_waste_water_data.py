"""Writes the waste water catalog (pipes, fittings, terminals) and the EG/KG waste water data.

Positions are estimated (sketch Nov 2026). z values are derived from the minimum slopes
(HT 2 %, KG 1 %) so that every run falls in flow direction. Run: python scripts/build_waste_water_data.py
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPONENTS = os.path.join(ROOT, "catalog", "tga-components")
TGA = os.path.join(ROOT, "house", "tga")
DIN = "411"
GIVEN = "Sortiment laut Bauherr (Nov 2026)"
MISSING = "Platzhalter: nicht im gemeldeten Sortiment, wird für den Leitungsverlauf gebraucht - bitte bestätigen"


def write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # the install block (ports for the wall view) comes from scripts/build_ports.py and is kept
    if path.startswith(COMPONENTS) and os.path.isfile(path):
        with open(path, encoding="utf-8") as handle:
            install = json.load(handle).get("install")
        if install and "install" not in data:
            data = dict(data, install=install)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def pipe(cid, name, line, dn, od, lengths, estimated=False):
    data = {"id": cid, "name": name, "description": "Abwasserrohr %s DN %d" % (line.upper(), dn),
            "class": "tga-class:pipe", "din276": DIN, "system_type": "Abwasser",
            "params": {"nominal_size_dn": dn, "outer_diameter": od, "medium": "waste_water", "system_line": line},
            "stock": {"lengths": lengths, "cuttable": True}, "note": MISSING if estimated else GIVEN}
    if estimated:
        data["estimated"] = True
    return data


def fitting(cid, name, kind, line, dn, estimated=False, **params):
    values = {"fitting_type": kind, "system_line": line, "dn": dn,
              "z_length": params.pop("z_length", 0.05 if line == "kg" else 0.03)}
    values.update(params)
    data = {"id": cid, "name": name, "class": "tga-class:pipe-fitting", "din276": DIN, "system_type": "Abwasser",
            "params": values, "note": MISSING if estimated else GIVEN}
    if estimated:
        data["estimated"] = True
    return data


def terminal(cid, name, kind, **params):
    values = {"terminal_type": kind, "mounting": "free"}
    values.update(params)
    return {"id": cid, "name": name, "class": "tga-class:terminal", "din276": DIN, "system_type": "Abwasser",
            "params": values}


def catalog():
    items = [
        pipe("kg-pipe-110", "KG-Rohr DN 110", "kg", 110, 0.110, [2.0, 1.0, 0.5]),
        pipe("ht-pipe-50", "HT-Rohr DN 50", "ht", 50, 0.050, [1.0, 0.5, 0.25]),
        pipe("ht-pipe-90", "HT-Rohr DN 90", "ht", 90, 0.090, [1.0, 0.5, 0.25], estimated=True),
        fitting("kg-bend-110-30", "KG-Bogen DN 110 30°", "bend", "kg", 110, angle=30),
        fitting("kg-bend-110-45", "KG-Bogen DN 110 45°", "bend", "kg", 110, angle=45),
        fitting("kg-adapter-110-ht90", "Übergang KG DN 110 auf HT DN 90", "adapter", "kg", 110, line_to="ht", dn_to=90),
        fitting("kg-adapter-110-ht50", "Übergang KG DN 110 auf HT DN 50", "adapter", "kg", 110, line_to="ht", dn_to=50),
        fitting("kg-branch-110-110-45", "KG-Abzweig DN 110/110 45°", "branch", "kg", 110, estimated=True,
                angle=45, dn_branch=110),
        fitting("kg-plug-110", "KG-Muffenstopfen DN 110 (Reinigung)", "plug", "kg", 110, estimated=True, z_length=0.0),
        fitting("ht-bend-50-15", "HT-Bogen DN 50 15°", "bend", "ht", 50, angle=15),
        fitting("ht-bend-50-30", "HT-Bogen DN 50 30°", "bend", "ht", 50, angle=30),
        fitting("ht-bend-50-45", "HT-Bogen DN 50 45°", "bend", "ht", 50, angle=45),
        fitting("ht-branch-50-50-45", "HT-Abzweig DN 50/50 45°", "branch", "ht", 50, angle=45, dn_branch=50),
        fitting("ht-branch-50-50-90", "HT-Abzweig DN 50/50 87°", "branch", "ht", 50, angle=90, dn_branch=50),
        fitting("ht-branch-90-50-45", "HT-Abzweig DN 90/50 45°", "branch", "ht", 90, angle=45, dn_branch=50),
        fitting("ht-branch-90-50-90", "HT-Abzweig DN 90/50 87°", "branch", "ht", 90, angle=90, dn_branch=50),
        fitting("ht-bend-90-15", "HT-Bogen DN 90 15°", "bend", "ht", 90, estimated=True, angle=15),
        fitting("ht-bend-90-30", "HT-Bogen DN 90 30°", "bend", "ht", 90, estimated=True, angle=30),
        fitting("ht-bend-90-45", "HT-Bogen DN 90 45°", "bend", "ht", 90, estimated=True, angle=45),
        fitting("ht-plug-90", "HT-Muffenstopfen DN 90", "plug", "ht", 90, estimated=True, z_length=0.0),
        fitting("ht-plug-50", "HT-Muffenstopfen DN 50", "plug", "ht", 50, estimated=True, z_length=0.0),
        terminal("sanitary-wc", "WC (Abgang DN 90)", "sanitary"),
        terminal("sanitary-shower-drain", "Duschablauf (DN 50)", "sanitary"),
        terminal("sanitary-washbasin", "Waschbecken (Siphon DN 50)", "sanitary"),
        terminal("sanitary-sink", "Spülbecken (Siphon DN 50)", "sanitary"),
        terminal("waste-stub", "Anschlussstutzen verschlossen", "stub"),
        terminal("sewage-transfer", "Übergabe Kläranlage", "transfer"),
    ]
    for item in items:
        write(os.path.join(COMPONENTS, item["id"] + ".json"), item)
    return len(items)


class Path:
    """Builds a falling polyline: each `run` step moves in plan and falls by slope * plan length."""

    def __init__(self, start):
        self.points = [list(start)]

    def to(self, x, y, slope):
        last = self.points[-1]
        plan = math.hypot(x - last[0], y - last[1])
        self.points.append([x, y, round(last[2] - slope * plan, 4)])
        return self

    def down(self, z):
        last = self.points[-1]
        self.points.append([last[0], last[1], round(z, 4)])
        return self


MAIN_START, MAIN_SLOPE, MAIN_X = (0.40, -0.70), 0.01, 7.92


def main_z(y):
    return round(MAIN_START[1] - MAIN_SLOPE * (y - MAIN_START[0]), 4)


def kg_branch(start, y_main):
    # vertical down outside, then 45° in plan towards the flow direction into the main line
    plan = math.hypot(MAIN_X - start[0], y_main - start[1])
    path = Path(start).down(main_z(y_main) + MAIN_SLOPE * plan)
    path.points.append([MAIN_X, y_main, main_z(y_main)])
    return path.points


def run(rid, name, component, points, installation, **extra):
    data = {"id": rid, "name": name, "component": "tga-component:" + component, "system": "waste-water-eg",
            "installation": installation, "points": points, "estimated": True}
    data.update(extra)
    return data


def runs():
    wc = Path([6.45, 0.65, 0.20]).to(7.30, 0.65, 0.02).down(-0.30).points
    sammel = Path([7.30, 1.50, 0.03]).to(7.30, 1.90, 0.02).down(-0.30).points
    shower = Path([6.40, 1.68, 0.06]).points + [[7.30, 1.68, round(0.03 - 0.02 * 0.18, 4)]]
    # washbasin at the wall to the kitchen next to the door (west), in the floor east and 45° into the shower line
    join_x = 6.70
    join_z = shower[0][2] + (shower[1][2] - shower[0][2]) * (join_x - 6.40) / 0.90
    basin = Path([4.65, 1.98, 0.45]).down(join_z + 0.02 * (1.75 + math.hypot(0.30, 0.30))).to(6.40, 1.98, 0.02).points
    basin.append([join_x, 1.68, round(join_z, 4)])
    # riser in the south-east corner of the kitchen; y 5.00 keeps it inside the basement (south wall inner face 5.08)
    fall = Path([6.65, 5.00, 3.05]).down(-0.40).to(6.80, 5.00, 0.02).points
    fall_kg = Path(fall[-1]).to(7.30, 5.00, 0.02).points
    fall_kg += kg_branch(fall_kg[-1], 5.67)[1:]
    sink = Path([6.55, 3.90, 0.45]).to(6.55, 5.00, 0.02).points
    sink.append([6.65, 5.00, round(sink[-1][2] - 0.02 * 0.10, 4)])
    return [
        run("aw-grund-ost", "Grundleitung KG Ost zur Kläranlage", "kg-pipe-110",
            [[MAIN_X, MAIN_START[0], MAIN_START[1]], [MAIN_X, 14.50, main_z(14.50)]], "buried",
            to="tga-terminal:uebergabe-klaeranlage", note="Tiefe und Lage geschätzt (Skizze), 1 % Gefälle"),
        run("aw-bad-wc", "WC Bad EG", "ht-pipe-90", wc, "outside", **{"from": "tga-terminal:wc-bad-eg"},
            into={"run": "tga-run:aw-bad-wc-kg", "kind": "continue"}),
        run("aw-bad-wc-kg", "WC Bad EG – Anschluss KG", "kg-pipe-110", kg_branch(wc[-1], 1.32), "buried",
            into={"run": "tga-run:aw-grund-ost", "kind": "branch"}),
        run("aw-bad-sammel", "Sammelleitung Dusche/Waschbecken Bad EG", "ht-pipe-90", sammel, "outside",
            into={"run": "tga-run:aw-bad-sammel-kg", "kind": "continue"}),
        run("aw-bad-sammel-kg", "Sammelleitung Bad EG – Anschluss KG", "kg-pipe-110", kg_branch(sammel[-1], 2.57),
            "buried", into={"run": "tga-run:aw-grund-ost", "kind": "branch"}),
        run("aw-bad-dusche", "Dusche Bad EG", "ht-pipe-50", shower, "screed", **{"from": "tga-terminal:dusche-bad-eg"},
            into={"run": "tga-run:aw-bad-sammel", "kind": "branch"}),
        run("aw-bad-wb", "Waschbecken Bad EG", "ht-pipe-50", basin, "screed", **{"from": "tga-terminal:wb-bad-eg"},
            into={"run": "tga-run:aw-bad-dusche", "kind": "branch"},
            note="Waschbecken an der Wand zur Küche auf der Türseite; im Bodenaufbau zur Duschleitung"),
        run("aw-kueche-fall", "Fallleitung Küche (Stutzen DG bis Keller)", "ht-pipe-90", fall, "concealed",
            **{"from": "tga-terminal:stutzen-dg-kueche"}, into={"run": "tga-run:aw-kueche-kg", "kind": "continue"},
            note="Durch EG-Decke, Bodenplatte und Keller; im DG verschlossener Stutzen für späteres Bad"),
        run("aw-kueche-kg", "Küche – KG durch Kellerwand Ost", "kg-pipe-110", fall_kg, "surface",
            into={"run": "tga-run:aw-grund-ost", "kind": "branch"}),
        run("aw-kueche-spuele", "Spüle Küche EG", "ht-pipe-50", sink, "concealed",
            **{"from": "tga-terminal:spuele-kueche-eg"}, into={"run": "tga-run:aw-kueche-fall", "kind": "branch"}),
    ]


def terminals():
    def term(tid, name, component, storey, room, position):
        return {"id": tid, "name": name, "component": "tga-component:" + component, "storey": "storey:" + storey,
                "room": room, "position": position, "estimated": True}
    return [
        term("wc-bad-eg", "WC Bad EG", "sanitary-wc", "ground", "room-bad", [6.45, 0.65, 0.20]),
        term("dusche-bad-eg", "Duschablauf Bad EG", "sanitary-shower-drain", "ground", "room-bad", [6.40, 1.68, 0.06]),
        term("wb-bad-eg", "Waschbecken Bad EG", "sanitary-washbasin", "ground", "room-bad", [4.65, 1.98, 0.45]),
        term("spuele-kueche-eg", "Spüle Küche EG", "sanitary-sink", "ground", "room-kueche", [6.55, 3.90, 0.45]),
        term("stutzen-dg-kueche", "Stutzen DG über Küche (verschlossen)", "waste-stub", "upper",
             "room-dg-bad", [6.65, 5.00, 3.05]),
        term("uebergabe-klaeranlage", "Übergabe Kläranlage", "sewage-transfer", "ground", "room-bad",
             [MAIN_X, 14.50, main_z(14.50)]),
    ]


def house_data():
    items = runs()
    for item in items:
        write(os.path.join(TGA, "runs", item["id"] + ".json"), item)
    for item in terminals():
        item = dict(item)
        if item["id"] == "uebergabe-klaeranlage":
            item.pop("room")
        write(os.path.join(TGA, "terminals", item["id"] + ".json"), item)
    penetrations = os.path.join(ROOT, "house", "penetrations.json")
    if not os.path.isfile(penetrations):
        write(penetrations, {"items": []})
    return len(items)


if __name__ == "__main__":
    print("components:", catalog())
    print("runs:", house_data())
