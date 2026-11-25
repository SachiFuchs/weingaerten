"""Copy electrical/sanitary installation parts and building components from catalog/imported_material.

TGA parts -> catalog/tga-components (terminal | cable | install-part), door + frame -> catalog/components.
Dry run by default; --write writes components, new companies and photos. Existing files are only refreshed
in their product block (shop data + offers), user edits elsewhere are kept.
"""
import re
import shutil
import sys

import import_materials as im

TGA = im.CAT / "tga-components"
COMPONENTS = im.CAT / "components"

ELECTRIC = ("Start/Technik/Elektroinstallation/Elektroinstallationsmaterial",
            "Start/Technik/Elektroinstallation/Schalterprogramme", "Start/Technik/Elektroinstallation/Kabelverlegung",
            "Start/Technik/Elektroinstallation/Steckdosen", "Start/Technik/Elektroinstallation/Lampeninstallation",
            "Start/Technik/Haustechnik/Telefone",
            "Sortiment/Leuchten & Elektro/Schalterprogramme", "Sortiment/Leuchten & Elektro/Elektroinstallation",
            "Sortiment/Leuchten & Elektro/Kabel & Kabelschutz/Kabelverlegung",
            "Sortiment/Leuchten & Elektro/Kabel & Kabelschutz/Kabel")
SANITARY = ("Start/Bad/Sanitärinstallation", "Start/Bad/Badarmaturen/Ersatzteile für Armaturen",
            "Start/Küche/Küchenarmaturen", "Start/Küche/Küchenausstattung/Ersatzteile Küchenarmatur",
            "Start/Bad/Toiletten", "Start/Technik/Heizung/Heizungstechnik",
            "Sortiment/Bad & Sanitär/Sanitärinstallation", "Sortiment/Bad & Sanitär/Badarmaturen",
            "Sortiment/Bad & Sanitär/HORNBACH Badkonzepte", "Sortiment/Bad & Sanitär/Duschen/Duschwannen",
            "Sortiment/Bad & Sanitär/Duschen/Ersatzteile & Zubehör für Duschen",
            "Sortiment/Bad & Sanitär/Spülkästen & Vorwandelemente",
            "Start/Garten/Pools/Pooltechnik/Poolzubehör/Pool Verrohrung")  # PPR-Rohr d20 (Trinkwasser)
UNCATEGORIZED = {  # receipt lines without shop category (file name prefix) -> "electric" | "sanitary"
    "obi-2572816": "electric", "obi-6574354": "electric", "obi-6575203": "electric", "hornbach-6060645": "electric",
    "hornbach-6571502": "sanitary", "hornbach-6571503": "sanitary", "hornbach-6636315": "sanitary",
    "hornbach-6636316": "sanitary", "hornbach-6648256": "sanitary", "hornbach-6648257": "sanitary",
    "hornbach-6605373": "sanitary",
}
NOT_PART = re.compile(r"gleitmittel|maleracryl|abzieher|eckrohrzange|rohrreinigung|sanitaerwerkzeug|campingtoilette"
                      r"|sanitaerfluessigkeit|abisolier|spannungspruef|reparaturband")
CABLE = re.compile(r"\b(NYM-J|NYY-J|H05VV-F|H03VVH2-F|H03VV-F|JY\(ST\)Y|A-2YF\(L\)2Y)", re.I)
CORES = re.compile(r"(\d+)\s*[xXG]\s*(\d+(?:[.,]\d+)?)(?:\s*x\s*(\d+(?:[.,]\d+)?))?")
DOORS = {"hornbach-1418742", "hornbach-1420822"}  # Pertura Landhaustür + Komplettzarge -> one component

# (pattern on slug, class, params, din276, system_type) - first match wins
RULES = (
    (r"steckdose", "terminal", {"terminal_type": "socket", "mounting": "flush"}, "440", "Stromkreis"),
    (r"schalter|wippschalter|taster", "terminal", {"terminal_type": "switch", "mounting": "flush"}, "440", "Stromkreis"),
    (r"lampenfassung", "terminal", {"terminal_type": "light", "mounting": "surface"}, "440", "Beleuchtung"),
    (r"dose|federdeckel|signaldeckel", "install-part", {"part_type": "box"}, "440", "Stromkreis"),
    (r"kabelkanal|leitungsfuehrungskanal", "install-part", {"part_type": "cable_duct", "unit": "m"}, "440", "Stromkreis"),
    (r"isolierrohr|steckmuffe-m20|steckbogen-m20", "install-part", {"part_type": "conduit"}, "440", "Stromkreis"),
    (r"sicherung", "install-part", {"part_type": "fuse"}, "440", "Stromkreis"),
    (r"nagelschelle|isolierband|klemme|kabelbinder", "install-part", {"part_type": "cable_fixing"}, "440", "Stromkreis"),
    (r"", "install-part", {"part_type": "other"}, "440", "Stromkreis"),
    (r"wc-set|stand-wc", "terminal", {"terminal_type": "sanitary", "mounting": "free"}, "412", "Sanitär"),
    (r"spuelkasten", "terminal", {"terminal_type": "sanitary", "mounting": "surface"}, "412", "Sanitär"),
    (r"duschwanne", "terminal", {"terminal_type": "sanitary", "mounting": "free"}, "412", "Sanitär"),
    (r"ppr-rohr-dn-20", "pipe", {"nominal_size_dn": 15, "outer_diameter": 0.020, "pressure_bar": 10,
                                  "medium": "cold_water", "system_line": "none"}, "412", "Trinkwasser"),
    (r"armatur|mischer|brause", "install-part", {"part_type": "tap"}, "412", "Trinkwasser"),
    (r"duschablauf|siphon|geruchverschluss|wc-anschluss", "install-part", {"part_type": "drain"}, "411", "Abwasser"),
    (r"montagerahmen", "install-part", {"part_type": "mounting"}, "412", "Sanitär"),
    (r"ventil|kugelhahn|eckventil", "install-part", {"part_type": "valve"}, "412", "Trinkwasser"),
    (r"schlauch|flex", "install-part", {"part_type": "hose"}, "412", "Trinkwasser"),
    (r"dichtung|gummi-ringe|dichtungssortiment", "install-part", {"part_type": "seal"}, "412", "Trinkwasser"),
    (r"schelle", "install-part", {"part_type": "pipe_clamp"}, "412", "Trinkwasser"),
    (r"", "install-part", {"part_type": "thread_fitting"}, "412", "Trinkwasser"),
)


def kind_of(article, stem):
    path = article.get("category_path") or ""
    if not path:
        return UNCATEGORIZED.get(stem.split("_", 1)[0])
    if any(path.startswith(p) for p in ELECTRIC):
        return "electric"
    if any(path.startswith(p) for p in SANITARY):
        return "sanitary"
    return None


def rule_of(slug_text, kind):
    for pattern, cls, params, din, system in RULES:
        if din.startswith("44") or din.startswith("45"):
            if kind != "electric":
                continue
        elif kind != "sanitary":
            continue
        if re.search(pattern, slug_text):
            return cls, dict(params), din, system
    return None


def cable_params(name):
    """NYM-J 3 x 1,5 -> cores 3, 1.5 mm2; telecom 2 x 2 x 0,6 (pairs x wires x diameter mm) -> 4 cores, 0.28 mm2."""
    m = CORES.search(name.replace("mm²", "").replace("mm2", ""))
    cores, size = int(m.group(1)), float(m.group(2).replace(",", "."))
    if m.group(3):  # pairs x 2 x conductor diameter
        d = float(m.group(3).replace(",", "."))
        cores, size = cores * int(size), round(3.14159 * d * d / 4, 2)
    return {"cable_type": CABLE.search(name).group(1).upper(), "cores": cores, "cross_section_mm2": size}


def merge(existing, new):
    """Keep user edits of an existing file; refresh only the imported product data."""
    if existing is None:
        return new
    out = dict(existing)
    out["product"] = new["product"]
    out["imported_from"] = sorted(set(existing.get("imported_from", [])) | set(new["imported_from"]))
    return out


def door(articles, by_article, companies):
    leaf, frame = articles["hornbach-1418742"], articles["hornbach-1420822"]
    p_leaf, p_frame = im.product(leaf, by_article, companies), im.product(frame, by_article, companies)
    offers = p_leaf.get("offers", []) + p_frame.get("offers", [])
    product = {k: v for k, v in p_leaf.items() if k != "offers"}
    product["model"] = "%s + %s" % (leaf["name"], frame["name"])
    product["offers"] = offers
    return {
        "id": "door-pertura-fengur-86", "name": "Zimmertür Pertura Fengur Kiefer 86 × 198,5 mit Komplettzarge",
        "description": "Landhaustür Fengur Kiefer 86,0 × 198,5 cm DIN links mit Pertura Komplettzarge Kiefer "
                       "198,5 × 86,0 × 20,5 cm (Wandstärke 20,5 cm); Angebote = Türblatt + Zarge einzeln. "
                       "Rahmenbreite und Material Kiefer geschätzt (KVH Kiefer als Ersatz)",
        "class": "class:door", "opening_capable": True,
        "params": {"width": 0.86, "height": 1.985, "depth": 0.205, "frame_width": 0.06, "swing": "left",
                   "leaf_type": "solid", "frame_type": "wrap"},
        "materials": {"frame": "material:kvh-nsi-kiefer-geh", "leaf": "material:kvh-nsi-kiefer-geh"},
        "imported_from": [],
        "product": product,
    }


def main():
    write = "--write" in sys.argv
    by_article = im.receipts()
    companies = im.Companies()
    files = {f.stem: im.load(f) for f in sorted(im.IMPORT.glob("*.json"))}
    out, copies, rows = {}, [], []
    as_material = {r for p in im.MATERIALS.glob("*.json") for r in im.load(p).get("imported_from", [])}

    for stem, art in files.items():
        prefix = stem.split("_", 1)[0]
        kind = kind_of(art, stem)
        if prefix in DOORS or kind is None or "_" not in stem or stem in as_material:
            continue
        # a second receipt line of the same article is stored as "<name>_<article no>": same part
        sid = im.slug(re.sub(r"_\d+$", "", stem.split("_", 1)[1]))
        if NOT_PART.search(sid):
            continue
        cls, params, din, system = rule_of(sid, kind)
        if kind == "electric" and CABLE.search(art["name"]) and CORES.search(art["name"]):
            cls, params, din = "cable", cable_params(art["name"]), "450" if "Y(ST)" in art["name"] or "2YF" in art["name"] else "440"
            system = "Fernmelde" if din == "450" else "Stromkreis"
        if sid in out and out[sid][1]["name"].strip().lower() == art["name"].strip().lower():
            # same article name bought under a second article number: one part with both offers
            first = out[sid][1]
            first["imported_from"].append(stem)
            first["product"].setdefault("offers", []).extend(im.product(art, by_article, companies).get("offers", []))
            continue
        cid = sid if sid not in out else sid + "-" + (art.get("ean") or str(art.get("article_number")))
        c = {"id": cid, "name": art["name"], "class": "tga-class:" + cls, "din276": din, "system_type": system,
             "params": params, "note": "Baumarkt-Artikel (Import), Maße/Parameter offen",
             "imported_from": [stem], "product": im.product(art, by_article, companies)}
        if cls == "pipe":
            c["stock"] = {"lengths": [2.0], "cuttable": True}
        pics = im.photos_of(stem, cid)
        if pics:
            c["photos"] = [dst.name for _, dst in pics]
        out[cid] = (TGA, c)
        copies += pics
        rows.append((cid, cls, c["product"]))

    articles = {s: a for s, a in files.items() if s.split("_", 1)[0] in DOORS}
    d = door({s.split("_", 1)[0]: a for s, a in articles.items()}, by_article, companies)
    d["imported_from"] = sorted(articles)
    out[d["id"]] = (COMPONENTS, d)
    rows.append((d["id"], "component door", d["product"]))

    new = 0
    for cid, (folder, c) in out.items():
        path = folder / (cid + ".json")
        existing = im.load(path) if path.exists() else None
        new += existing is None
        out[cid] = (folder, merge(existing, c))
    for cid, cls, p in rows:
        best = min((o["price"] for o in p.get("offers", [])), default=None)
        print("%-58s | %-14s | %9s" % (cid[:58], cls, "" if best is None else "%.2f €" % best))
    print("%d Teile (%d neu), %d neue/geänderte Firmen, %d Fotos" % (len(out), new, len(companies.new), len(copies)))
    print("Firmen: " + ", ".join(sorted(companies.new)))
    if not write:
        print("Dry run - mit --write schreiben")
        return
    for cid, c in companies.new.items():
        im.dump(im.COMPANIES / (cid + ".json"), c)
    for cid, (folder, c) in out.items():
        im.dump(folder / (cid + ".json"), c)
    for src, dst in copies:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    print("geschrieben")


if __name__ == "__main__":
    main()
