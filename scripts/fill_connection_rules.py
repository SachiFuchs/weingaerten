"""Fill the connection rules of the TGA classes and the connection blocks of the existing TGA components.

Rules (catalog/tga-classes): HT/KG Steckmuffe with flow direction, PP-R only via welded fittings, cables only with
clamps of the same conductor role in boxes or at terminals. Components (catalog/tga-components): ends with DN, gender
and flow (derived from params), clamp poles and cross-sections, box mounting, terminal conductors. Existing install
ports of HT/KG parts get `flow`. Values that are not printed on the article are marked in connection.note.

    python scripts/fill_connection_rules.py          # dry run
    python scripts/fill_connection_rules.py --write
"""
import json
import os
import re
import sys

ROOT = r"c:\Development\weingaerten"
CLASSES = os.path.join(ROOT, "catalog", "tga-classes")
COMPONENTS = os.path.join(ROOT, "catalog", "tga-components")

DRAIN = ("pipe", "fitting")
RULES = {
    "pipe": [
        {"line": "ht", "medium": "waste_water", "method": "push", "partners": ["pipe", "fitting"], "directed": True,
         "note": "Spitzende in Muffe, Muffe gegen die Fließrichtung; gleiche DN direkt, andere DN nur über Übergang oder Abzweig"},
        {"line": "kg", "medium": "waste_water", "method": "push", "partners": ["pipe", "fitting"], "directed": True,
         "note": "Spitzende in Muffe, Muffe gegen die Fließrichtung; gleiche DN direkt, andere DN nur über Übergang oder Abzweig"},
        {"line": "ppr", "medium": "water_supply", "method": "weld", "partners": ["fitting", "part", "terminal"],
         "note": "Rohr nur über Formteile (Muffe, Winkel, T-Stück, Kappe, Übergang) verbinden"},
        {"line": "alu_composite", "medium": "heating", "method": "press", "partners": ["fitting"],
         "note": "Alu-Verbundrohr (11,6 / 16 mm) nur über Presskupplungen gleichen Durchmessers verbinden"},
    ],
    "pipe-fitting": [
        {"line": "ht", "medium": "waste_water", "method": "push", "partners": ["pipe", "fitting"], "directed": True,
         "note": "Formteil in Fließrichtung einbauen; DN-Wechsel nur über Übergang (auch Abzweig)"},
        {"line": "kg", "medium": "waste_water", "method": "push", "partners": ["pipe", "fitting"], "directed": True,
         "note": "Formteil in Fließrichtung einbauen; DN-Wechsel und KG/HT nur über Übergang (auch Abzweig)"},
        {"line": "ppr", "medium": "water_supply", "method": "weld", "partners": ["pipe", "part", "terminal"],
         "note": "Schweißmuffen nehmen PP-R-Rohre auf; Gewindeseite nur an Gewinde"},
        {"line": "alu_composite", "medium": "heating", "method": "press", "partners": ["pipe", "terminal"],
         "note": "Presskupplung nimmt Verbundrohr 11,6 / 16 mm bzw. Rohrende der Heizplatte auf; "
                 "Durchmesserwechsel nur über Übergang 11,6/16"},
    ],
    "cable": [
        {"line": "power", "medium": "power", "method": "clamp", "partners": ["clamp", "terminal"],
         "locations": ["box", "terminal"],
         "note": "Litzen nur mit Klemmen (WAGO) gleicher Leiterart (L, N, PE) verbinden; Verbindungen nur in Dosen (Aufputz/Unterputz) oder an Steckdosen, Lampenfassungen, Schaltern"},
    ],
    "install-part": [
        {"types": ["clamp"], "medium": "power", "method": "clamp", "partners": ["cable"], "locations": ["box", "terminal"],
         "note": "nur Adern gleicher Farbe/Leiterart; darf Endstück sein; nicht alle Eingänge müssen belegt sein"},
        {"types": ["box"], "medium": "power", "method": "clamp", "partners": ["cable", "clamp", "terminal"],
         "note": "Verbindungsort für Kabel (Klemmen in der Dose)"},
        {"types": ["valve", "thread_fitting"], "line": "ppr", "medium": "water_supply", "method": "weld",
         "partners": ["pipe", "fitting"], "note": "PP-R-Schweißmuffe an Rohr"},
    ],
    "terminal": [
        {"types": ["socket", "switch", "light", "distribution_board", "radiator", "heat_pump"], "medium": "power",
         "method": "clamp", "partners": ["cable"], "note": "Kabelende am Gerät; nur die aufgeführten Leiter anschließen"},
        {"types": ["wall_plate"], "line": "ppr", "medium": "water_supply", "method": "weld", "partners": ["pipe", "fitting"],
         "note": "Wandscheibe: PP-R-Muffe von hinten, Gewinde zur Armatur"},
    ],
}
CLASS_OPTIONS = {"pipe-fitting": {"fitting_type": ["coupling"], "system_line": ["alu_composite"],
                                  "line_to": ["alu_composite", "thread", "metal", "other"]},
                 "install-part": {"part_type": ["clamp"]}}

CLAMPS = {  # id -> (poles, cross_section, note)
    "wago-hebelklemme-0-2-4-mm2-5-polig-5-stueck": (5, [0.2, 4.0], None),
    "wago-hebelklemme-2-polig-100-stueck": (2, [0.2, 4.0], "Querschnitt nach WAGO 221 angenommen"),
    "wago-hebelklemme-25-stueck": (3, [0.2, 4.0], "Sortiment 2/3/5-polig, Polzahl gemischt (3 angenommen)"),
    "wago-hebelklemme-50-stueck": (3, [0.2, 4.0], "Sortiment 2/3/5-polig, Polzahl gemischt (3 angenommen)"),
    "wago-hebelklemmen-set-10-teilig": (3, [0.2, 4.0], "Set 2/3/5-polig, Polzahl gemischt (3 angenommen)"),
    "wago-durchgangsverbinder-mit-hebel-60-stueck": (2, [0.2, 4.0], "Durchgangsverbinder (WAGO 221-2411)"),
    "wago-durchgangsverbinder-transparent-0-2-mm2-4-mm2-10-stueck": (2, [0.2, 4.0], None),
    "wago-verbindungsdosenklemme-3-polig-0-5-mm-2-5-mm-orange": (3, [0.5, 2.5], "Steckklemme, war als Dose eingetragen"),
    "luesterklemme-2-5-mm-weiss-2-stueck": (2, [0.5, 2.5], "Lüsterklemme: je Klemmstelle 2 Adern"),
    "luesterklemmen-12-polig-1-5-mm-4-mm-10-stueck": (2, [1.5, 4.0], "12er-Leiste, je Klemmstelle 2 Adern"),
}
NOT_BOXES = ("federdeckel", "signaldeckel")
ACCEPTS = {"socket": ["L", "N", "PE"], "switch": ["L"], "light": ["L", "N"], "radiator": ["L", "N", "PE"],
           "distribution_board": ["L1", "L2", "L3", "L", "N", "PE"], "heat_pump": ["L1", "L2", "L3", "N", "PE"]}
ACCEPTS_BY_ID = {"schalterkombination-aufputz-weiss": (["L", "N", "PE"], "Schalter mit Steckdose angenommen")}
POWER_CABLES = re.compile(r"NYM|NYY|H0[357]V|Einzelader", re.I)


def _end(eid, dn, gender, flow=None, line=None):
    end = {"id": eid}
    if line:
        end["line"] = line
    end.update({"dn": dn, "gender": gender})
    if flow:
        end["flow"] = flow
    return end


def drain_ends(cls, params, directed):
    """Ends of a HT/KG/PP-R pipe or fitting from its params (HT/KG: socket = in, spigot = out)."""
    f = (lambda v: v) if directed else (lambda v: None)
    ppr = params.get("system_line") == "ppr"
    if cls == "pipe":
        dn = params.get("nominal_size_dn")
        if ppr:
            return [_end("a", dn, "spigot"), _end("b", dn, "spigot")]
        return [_end("a", dn, "socket", f("in")), _end("b", dn, "spigot", f("out"))]
    kind, dn = params.get("fitting_type"), params.get("dn")
    socket = "socket"
    if kind == "bend":
        return [_end("a", dn, socket, f("in")), _end("b", dn, socket if ppr else "spigot", f("out"))]
    if kind == "coupling":
        return [_end("a", dn, socket, f("in")), _end("b", dn, socket, f("out"))]
    if kind == "branch":
        return [_end("a", dn, socket, f("in")), _end("b", dn, socket if ppr else "spigot", f("out")),
                _end("c", params.get("dn_branch"), socket, f("in"))]
    if kind == "plug":
        return [_end("a", dn, socket if ppr else "spigot", f("none"))]
    if kind == "adapter":
        line, line_to, dn_to = params.get("system_line"), params.get("line_to"), params.get("dn_to")
        other = None if line_to == line else line_to
        if ppr:  # PP-R socket, thread on the other side (IG = socket, AG = spigot) - set per article below
            return [_end("a", dn, "socket"), _end("b", dn_to, "socket", line=other)]
        # flow from the smaller (or foreign) side into the larger HT/KG spigot
        return [_end("a", dn_to, "any" if line_to in ("metal", "other") else "socket", f("in"), line=other),
                _end("b", dn, "spigot", f("out"))]
    return None


def component_connection(cid, element):
    cls = element["class"].split(":")[1]
    params = element.get("params") or {}
    line = params.get("system_line")
    if cid.startswith("naturbo-alu-verbundrohr"):
        d = round(params["outer_diameter"] * 1000, 1)
        return {"line": "alu_composite", "ends": [_end("a", d, "spigot"), _end("b", d, "spigot")]}
    if cid.startswith("naturbo-presskupplung-"):
        sizes = [float(s.replace("-", ".")) for s in re.findall(r"(11-6|16)(?=-|$)", cid[len("naturbo-presskupplung-"):])]
        sizes = (sizes + sizes)[:2] if len(sizes) == 1 else sizes[:2]
        return {"line": "alu_composite", "ends": [_end("a", sizes[0], "socket"), _end("b", sizes[1], "socket")]}
    if cls in ("pipe", "pipe-fitting") and line in ("ht", "kg", "ppr"):
        ends = drain_ends("pipe" if cls == "pipe" else "fitting", params, line in ("ht", "kg"))
        if not ends:
            return None
        if cid.endswith("-ag-1-2"):
            ends[1]["gender"] = "spigot"
        conn = {"line": line, "ends": ends}
        if params.get("line_to") in ("metal", "other"):
            conn["note"] = "Fremdanschluss (Metallrohr / Gummimanschette), Richtung angenommen"
        return conn
    if cls == "cable":
        if not POWER_CABLES.search(str(params.get("cable_type", "")) + " " + element.get("name", "")):
            return None
        conn = {"line": "power"}
        if params.get("cable_type") == "Einzelader" and params.get("cores") == 1:
            conn["conductors"] = [{"role": "PE", "color": "#9ACD32"}]
            conn["note"] = "Einzelader 10 mm² als Potentialausgleich (PE) angenommen"
        return conn
    if cls == "install-part":
        ptype = params.get("part_type")
        if cid in CLAMPS:
            poles, cross, note = CLAMPS[cid]
            conn = {"line": "power", "poles": poles, "cross_section": cross, "may_be_end": True, "partial_use": True}
            if note:
                conn["note"] = note
            return conn
        if ptype == "box" and str(element.get("din276", "")).startswith("44"):
            return box_connection(cid, element)
        if cid.startswith(("ppr-", "pp-r-")) and ptype in ("valve", "thread_fitting"):
            if "rohrclip" in cid:
                return None
            ends = [_end("a", 20, "socket"), _end("b", 20, "socket")]
            if "uebergangsmuffe" in cid:
                ends = [_end("a", 20, "socket"), _end("b", 15, "socket", line="thread")]
            elif "t-stueck" in cid:
                ends = [_end("a", 20, "socket"), _end("b", 20, "socket"), _end("c", 15, "socket", line="thread")]
            return {"line": "ppr", "ends": ends}
        return None
    if cls == "terminal":
        ttype = params.get("terminal_type")
        if ttype == "wall_plate" and ("ppr" in cid or "pp-r" in cid):
            return {"line": "ppr", "ends": [_end("a", 20, "socket"), _end("out", 15, "socket", line="thread")]}
        if ttype in ACCEPTS and str(element.get("din276", "")).startswith("44"):
            accepts, note = ACCEPTS_BY_ID.get(cid, (ACCEPTS[ttype], None))
            conn = {"line": "power", "accepts": accepts}
            if ttype == "light":
                note = "Fassung ohne Schutzleiteranschluss angenommen (PE in Klemme als Endstück)"
            if note:
                conn["note"] = note
            return conn
    return None


def box_connection(cid, element):
    text = (cid + " " + element.get("name", "")).lower()
    mounting = "hollow_wall" if "hohlwand" in text else (
        "flush" if re.search(r"unterputz|geraetedose|-up-|iso-abzweigdose|herdanschlussdose", text) else (
            "surface" if re.search(r"aufputz|ip5[45]|abzweigkasten", text) else "flush"))
    function = "junction" if re.search(r"abzweig|verbindung|klemm|herdanschluss|verteiler", text) else "device"
    conn = {"line": "power", "mounting": mounting, "box_function": function}
    if mounting == "surface" and not re.search(r"aufputz", text):
        conn["note"] = "Montageart aus Schutzart/Bauform angenommen"
    return conn


def fix_params(cid, element):
    """Correct part types the import guessed wrong; returns True when params changed."""
    params = element.setdefault("params", {})
    old = dict(params)
    if cid in CLAMPS:
        params["part_type"] = "clamp"
    elif any(word in cid for word in NOT_BOXES) and params.get("part_type") == "box":
        params["part_type"] = "other"
    elif params.get("part_type") == "other" and re.search(r"abzweigkasten|geraeteverbindun|hohlwand-abzweig", cid):
        params["part_type"] = "box"
    return params != old


def flow_ports(element):
    install = element.get("install") or {}
    changed = False
    kind = (element.get("params") or {}).get("fitting_type")
    for port in install.get("ports") or []:
        if port.get("line") in ("ht", "kg"):
            flow = "none" if kind == "plug" else ("out" if port["gender"] == "spigot" else "in")
            if port.get("flow") != flow:
                port["flow"] = flow
                changed = True
    return changed


def dump(path, element, write, label):
    print(("write " if write else "would write ") + label)
    if write:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(element, ensure_ascii=False, indent=2) + "\n")


def main(write):
    changed = 0
    pipe16 = os.path.join(COMPONENTS, "naturbo-alu-verbundrohr-16.json")
    if not os.path.isfile(pipe16):
        with open(os.path.join(COMPONENTS, "naturbo-alu-verbundrohr-11-6.json"), encoding="utf-8") as handle:
            base = json.load(handle)
        new = {k: v for k, v in base.items() if k not in ("product", "imported_from", "photos", "install", "connection")}
        new.update({"id": "naturbo-alu-verbundrohr-16", "name": "Naturbo Alu-Verbundrohr Ø 16 mm", "estimated": True,
                    "note": "angelegt für die Presskupplungen 11,6/16 (Bauherr: Verbundrohre 11 und 16 vorhanden) - Produktdaten offen"})
        new["params"] = dict(base["params"], outer_diameter=0.016, nominal_size_dn=12)
        changed += 1
        dump(pipe16, new, write, "new naturbo-alu-verbundrohr-16")
    for cid, rules in RULES.items():
        path = os.path.join(CLASSES, cid + ".json")
        with open(path, encoding="utf-8") as handle:
            element = json.load(handle)
        before = json.dumps(element, sort_keys=True)
        element["connection_rules"] = rules
        for key, extra in CLASS_OPTIONS.get(cid, {}).items():
            param = next(p for p in element["parameters"] if p["key"] == key)
            param["options"] = param["options"] + [o for o in extra if o not in param["options"]]
        if json.dumps(element, sort_keys=True) != before:
            changed += 1
            dump(path, element, write, "class " + cid)
    missing = []
    for name in sorted(os.listdir(COMPONENTS)):
        cid = name[:-5]
        path = os.path.join(COMPONENTS, name)
        with open(path, encoding="utf-8") as handle:
            element = json.load(handle)
        before = json.dumps(element, sort_keys=True)
        fix_params(cid, element)
        flow_ports(element)
        conn = component_connection(cid, element)
        if conn is not None:
            element["connection"] = conn
        elif str(element.get("din276", "")).startswith("44") and element["class"] in (
                "tga-class:cable", "tga-class:terminal"):
            missing.append(cid)
        if json.dumps(element, sort_keys=True) != before:
            changed += 1
            dump(path, element, write, cid + " " + json.dumps(element.get("connection"), ensure_ascii=False))
    print("%d files changed; electrical cables/terminals without connection block: %s" % (changed, ", ".join(missing)))


if __name__ == "__main__":
    main("--write" in sys.argv)
