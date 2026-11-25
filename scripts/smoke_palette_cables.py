"""Smoke test of the palette tree paths (installation.catalog[].paths) and of cables as parts with bend points.

Runs on a temp copy of catalog + house (WEINGAERTEN_HOME), the project data stays unchanged.
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

failures = []


def ask(command):
    return json.loads(weingaerten_core.handle(json.dumps(command)))


def check(name, condition, detail=""):
    print(("ok   " if condition else "FAIL ") + name + ("" if condition else "  " + str(detail)))
    if not condition:
        failures.append(name)


temp = tempfile.mkdtemp()
try:
    for folder in ("catalog", "house"):
        shutil.copytree(os.path.join(ROOT, folder), os.path.join(temp, folder), ignore=shutil.ignore_patterns("imported_*"))
    os.environ["WEINGAERTEN_HOME"] = temp
    house = ask({"command": "HOUSE"})
    inst = house["installation"]
    cat = {c["ref"]: c for c in inst["catalog"]}
    paths = lambda ref: cat.get("tga-component:" + ref, {}).get("paths") or []
    check("jedes Teil hat einen Pfad", all(c.get("paths") for c in inst["catalog"]))
    check("Reducer unter HT DN 90 und HT DN 50", {p[1] for p in paths("ht-reducer-90-50")} == {"HT DN 90", "HT DN 50"},
          paths("ht-reducer-90-50"))
    check("PPR-Rohr unter Zuwasser > PPR > DN 20", paths("ppr-rohr-dn-20-x-2-m")[:1] == [["Zuwasser", "PPR", "DN 20", "Rohre"]],
          paths("ppr-rohr-dn-20-x-2-m"))
    check("Steckdose unter Endgeräte", paths("jung-steckdose-1-stueck")[0][:2] == ["Elektro", "Endgeräte"])
    check("UP-Dose unter Verteiler", paths("kaiser-up-geraetedose")[0][:2] == ["Elektro", "Verteiler"])
    check("NYM unter Leitungen (ohne Unterordner)", paths("cable-nym-3x15") == [["Elektro", "Leitungen"]], paths("cable-nym-3x15"))
    shown_cables = [c for c in inst["catalog"] if c["shape"] == "cable" and c.get("palette") is not False]
    types = [c.get("cable_type") for c in shown_cables]
    check("je Kabeltyp ein Eintrag", len(types) == len(set(types)), types)
    check("Leitung abgeleitet (shape cable, 2 Ports)", cat["tga-component:cable-nym-3x15"]["shape"] == "cable"
          and len(cat["tga-component:cable-nym-3x15"]["ports"]) == 2)
    check("Platzhalter Endteile", ["Zuwasser", "Endteile"] in inst["palette_roots"])
    for cable_type in ("NYM-J", "NYY-J"):
        shown = [c for c in inst["catalog"] if c.get("cable_type") == cable_type and c.get("palette") is not False]
        check("%s genau einmal in der Palette" % cable_type, len(shown) == 1, [c["ref"] for c in shown])
        if shown:
            sizes = [v["key"] for v in shown[0]["variants"]]
            check("%s Varianten eindeutig" % cable_type, len(sizes) == len(set(sizes)) and sizes, sizes)
            # Kürzungseigenschaft: Vorgabe 1 m, max = Ringlänge des Bauteils (cut), sonst 50 m
            check("%s Länge Vorgabe 1 m, max = Ringlänge (<= 50 m)" % cable_type,
                  shown[0]["stretch"].get("default_length") == 1.0 and 0 < shown[0]["stretch"]["max_length"] <= 50.0,
                  shown[0]["stretch"])
    nym = next(c for c in inst["catalog"] if c.get("variants") and c["cable_type"] == "NYM-J")
    check("NYM-J Vertreter 3 x 1,5", nym["ref"] == "tga-component:cable-nym-3x15", nym["ref"])
    boxes = [c for c in inst["catalog"] if c.get("variant_group") == "Aufputzdose"]
    shown = [c for c in boxes if c["palette"]]
    check("Aufputzdose genau einmal in der Palette", len(shown) == 1 and len(boxes) >= 9,
          (len(shown), len(boxes)))
    if shown:
        labels = [v["label"] for v in shown[0]["variants"]]
        check("Aufputzdose Vertreter 80 x 80, Größen eindeutig",
              shown[0]["ref"].endswith("80-mm-x-80-mm-x-37-mm-ip55") and len(labels) == len(set(labels)), labels)
    verteiler = sorted(c.get("group_name") or c["name"] for c in inst["catalog"] if c.get("palette") is not False
                       and any(p[:2] == ["Elektro", "Verteiler"] for p in c["paths"]))
    check("Verteiler: nur Aufputz-, Unterputz-, Herd-Anschlussdose",
          verteiler == ["Aufputzdose", "Herd-Anschlussdose", "Unterputzdose"], verteiler)
    up = next(c for c in inst["catalog"] if c.get("group_name") == "Unterputzdose")
    check("Unterputzdose Vertreter Kaiser, mit Hohlwand-Varianten", up["ref"].endswith("kaiser-up-geraetedose")
          and any(v["label"].startswith("Hohlwand-") for v in up["variants"]), [v["label"] for v in up["variants"]])

    storey = next(s for s in house["storeys"] if s["id"] == "ground")
    wall = next(w for w in storey["walls"] if w["category"] == "exterior_wall")
    base = {"component": "tga-component:cable-nym-3x15", "storey": "ground", "host": {"wall": wall["id"], "face": "inside"},
            "u": 0.5, "z": 1.0, "depth": -0.01}
    answer = ask({"command": "PART_SAVE", "upsert": [dict(base, id="t-cab", length=1.2),
                                                       dict(base, id="t-bent", z=0.5, path=[[0.5, 0, 0], [0.5, 0.4, 0], [1.0, 0.4, 0]])],
                  "delete": []})
    check("PART_SAVE Leitungen", "error" not in answer, answer)
    parts = {p["id"]: p for p in ask({"command": "HOUSE"})["installation"]["parts"]}
    straight, bent = parts.get("t-cab"), parts.get("t-bent")
    check("gerade Leitung: 1 Stück, Länge 1.2", straight and len(straight["legs"]) == 1 and abs(straight["length"] - 1.2) < 1e-6, straight)
    check("geknickt: 3 Stücke, Länge 1.4", bent and len(bent["legs"]) == 3 and abs(bent["length"] - 1.4) < 1e-6,
          bent and (len(bent["legs"]), bent["length"]))
    if bent:
        b = next(q for q in bent["ports"] if q["id"] == "b")
        a = next(q for q in bent["ports"] if q["id"] == "a")
        check("Port b am letzten Punkt", math.dist(b["position"], bent["legs"][-1][1]) < 1e-6)
        check("Port b Richtung = letztes Stück (waagerecht)", abs(b["direction"][2]) < 1e-6)
        check("Port a gegen erstes Stück", math.dist(a["position"], bent["origin"]) < 1e-6)
    bad = ask({"command": "PART_SAVE", "upsert": [dict(base, id="t-bad", path=[[1, 2]])], "delete": []})
    check("ungültiger path abgelehnt", "error" in bad, bad)

    # connection rules: a cable leaves the top entry of a box upwards (rot plane 90: local x = up, port a points down)
    def joined(box_ref, cable_ref, pid, u, conduit_cable=None, port="top"):
        box = dict(base, id=pid + "-box", component="tga-component:" + box_ref, u=u, z=0.4, depth=0.0, rot={})
        top_pos = next(q["pos"] for q in cat["tga-component:" + box_ref]["ports"] if q["id"] == port)
        line = dict(base, id=pid + "-cab", component="tga-component:" + cable_ref, u=u + top_pos[0], z=0.4 + top_pos[1],
                    depth=top_pos[2], rot={"plane": {"top": 90, "bottom": -90, "right": 0}[port]}, length=0.5)
        if conduit_cable:
            line["cable"] = "tga-component:" + conduit_cable
        answer = ask({"command": "PART_SAVE", "upsert": [box, line], "delete": []})
        out = {p["id"]: p for p in ask({"command": "HOUSE"})["installation"]["parts"]}
        top = next((q for q in out.get(pid + "-box", {}).get("ports", []) if q["id"] == port), {})
        return "error" not in answer and top.get("connected_to") == pid + "-cab.a"

    check("NYM 3-adrig an Gerätedose", joined("kaiser-up-geraetedose", "cable-nym-3x15", "j1", 1.5))
    check("NYM 5-adrig nicht an Gerätedose", not joined("kaiser-up-geraetedose", "cable-nym-j-5x16", "j2", 2.0))
    nym5 = "mantelleitung-nym-j-5-x-2-5-grau-5-m"
    check("NYM-J 5 x 2,5 Zulauf an Herd-Anschlussdose", joined("herd-anschlussdose", nym5, "j3", 2.5))
    check("NYM-J 5 x 16 nicht an Herd-Anschlussdose", not joined("herd-anschlussdose", "cable-nym-j-5x16", "j3b", 5.0))
    check("Herdanschlussleitung nicht als Zulauf", not joined("herd-anschlussdose", "herdanschlussleitung-h05vv-f-5g2-5-weiss-3-m", "j3c", 5.5))
    check("Herdanschlussleitung am Abgang Herd", joined("herd-anschlussdose", "herdanschlussleitung-h05vv-f-5g2-5-weiss-3-m", "j3d", 6.0, port="bottom"))
    check("NYM-J 5 x 2,5 nicht am Abgang Herd", not joined("herd-anschlussdose", nym5, "j3e", 6.5, port="bottom"))
    check("NYM-J 3 x 2,5 am Abgang einphasig (Aufputz)", joined("herd-anschlussdose-aufputz", "emskabel-feuchtraumleitung-nym-j-3-x-2-5-mm2-50-m", "j3f", 7.0, port="right"))
    check("NYM-J 3 x 1,5 nicht am Abgang einphasig", not joined("herd-anschlussdose", "cable-nym-3x15", "j3g", 7.5, port="right"))
    herd = [c for c in inst["catalog"] if c.get("variant_group") == "Herd-Anschlussdose"]
    check("Herd-Anschlussdose einmal, Unterputz/Aufputz/Pollmann", sum(c["palette"] for c in herd) == 1 and
          sorted(v["label"] for c in herd if c["palette"] for v in c["variants"]) == ["Aufputz", "Unterputz", "Unterputz (Pollmann, mit WAGO)"],
          [v["label"] for c in herd for v in c.get("variants", [])])
    check("NYM 3-adrig an Lampenfassung", joined("lampenfassung-e27", "cable-nym-3x15", "j4", 3.0))
    check("Leerrohr mit NYM 3 an Abzweigdose", joined("abzweigkasten-80-mm-x-80-mm-x-37-mm-ip55",
                                                      "installationsrohr-m20-starr-lichtgrau-dr", "j5", 3.5, "cable-nym-3x15"))
    check("Leerrohr mit NYM 5 nicht an Gerätedose", not joined("kaiser-up-geraetedose",
                                                              "installationsrohr-m20-starr-lichtgrau-dr", "j6", 4.0, "cable-nym-j-5x16"))
    check("Leerrohr mit NYM 5 x 2,5 an Herd-Anschlussdose", joined("herd-anschlussdose",
                                                            "installationsrohr-m20-starr-lichtgrau-dr", "j7", 4.5, nym5))
finally:
    os.environ.pop("WEINGAERTEN_HOME", None)
    shutil.rmtree(temp, ignore_errors=True)
print("alles ok" if not failures else "FEHLER: %s" % failures)
sys.exit(1 if failures else 0)
