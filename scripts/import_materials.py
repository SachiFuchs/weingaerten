"""Take building-material articles from catalog/imported_material into catalog/materials.

One material per article (id = slug of the import file), with a product block (manufacturer,
offers from the OBI/Hornbach receipts) and photos copied to catalog/photos/<id>/.
Companies (suppliers OBI/Hornbach, manufacturers) are created when missing.
Existing materials with the old `products` list are migrated to imported_from + offers.
The import folder stays untouched. Re-running skips articles already referenced in imported_from.

Usage: python scripts/import_materials.py            (dry run, prints the list)
       python scripts/import_materials.py --write    (writes files)
"""
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAT = ROOT / "catalog"
IMPORT = CAT / "imported_material"
MATERIALS = CAT / "materials"
COMPANIES = CAT / "companies"
PHOTOS = CAT / "photos"

CATEGORIES = {  # category_path segment -> (material category, appearance)
    "Wohnen/Farben": ("Farbe", {"color": "#F2F2EE", "roughness": 0.7, "hatch": "none"}),
    "Wohnen/Tapeten": ("Tapete", {"color": "#EFEAE0", "roughness": 0.8, "hatch": "none"}),
    "Bauen/Baustoffe": ("Baustoffe", {"color": "#B8B4AC", "roughness": 0.9, "hatch": "plaster"}),
    "Bauen/Bauholz": ("Holz", {"color": "#D8B991", "roughness": 0.7, "hatch": "wood"}),
    "Bauen/Fliesen": ("Fliesen", {"color": "#D9D4CC", "roughness": 0.3, "hatch": "none"}),
    "Bauen/Entwässerung": ("Entwässerung", {"color": "#6E6E6E", "roughness": 0.5, "hatch": "none"}),
}
SUPPLIERS = {"OBI Home and Garden GmbH": ("obi", "OBI", "Baumarkt OBI Home and Garden GmbH"),
             "HORNBACH Baumarkt AG": ("hornbach", "HORNBACH", "Baumarkt HORNBACH Baumarkt AG")}
RECEIPTS = {"obi": "obi_purchases.json", "hornbach": "hornbach_purchases.json"}
ACCESSORIES = ("Farben/Malerbedarf", "Baustoffe/Bauzubehör", "Tapeten/Tapezierzubehör")  # tools, tape, covers
HORNBACH_CATEGORIES = {  # Hornbach category_path (without "Sortiment/") -> key in CATEGORIES
    "Farben, Tapeten & Wandverkleidungen/Farben": "Wohnen/Farben",
    "Farben, Tapeten & Wandverkleidungen/Spachtelmasse": "Bauen/Baustoffe",
    "Farben, Tapeten & Wandverkleidungen/Kleber & Kleister": "Bauen/Baustoffe",
    "Baustoffe/Rohbau": "Bauen/Baustoffe",
    "Baustoffe/Fassadendämmung": "Bauen/Baustoffe",
    "Baustoffe/Dämmung": "Bauen/Baustoffe",
    "Baustoffe/Trockenbau": "Bauen/Baustoffe",
    "Baustoffe/Sanierung": "Bauen/Baustoffe",
    "Baustoffe/Bedachung": "Bauen/Baustoffe",
    "Baustoffe/Entwässerung": "Bauen/Entwässerung",
    "Holz, Fenster & Türen/Bauholz": "Bauen/Bauholz",
    "Holz, Fenster & Türen/Leisten": "Bauen/Bauholz",
    "Holz, Fenster & Türen/Möbelbau & Holzplatten": "Bauen/Bauholz",
    "Holz, Fenster & Türen/OSB Platten & Verlegeplatten": "Bauen/Bauholz",
    "Bodenbeläge & Fliesen/Fliesen": "Bauen/Fliesen",
    "Bodenbeläge & Fliesen/Fliesenzubehör/Entkopplungsmatten & Duschabdichtung": "Bauen/Fliesen",
    "Holz, Fenster & Türen/Fenster/Fenster - Montagezubehör": "Bauen/Baustoffe",
    "Holz, Fenster & Türen/Treppen/Geländer": "Bauen/Bauholz",
    "Bad & Sanitär/Sanitärinstallation/HT-Rohre": "Bauen/Entwässerung",
}
OBI_CATEGORIES = {  # further OBI category_path (without "Start/") -> key in CATEGORIES
    "Wohnen/Lacke": "Wohnen/Farben",
    "Bodenbeläge/Fußleisten": "Bauen/Bauholz",
    "Bauen/Möbelbau/Möbelbauplatten": "Bauen/Bauholz",
    "Bauen/Möbelbau/Arbeitsplatten": "Bauen/Bauholz",
    "Garten/Gartenbau/Terrasse": "Bauen/Bauholz",
    "Bauen/Fenster/Fensterdichtungen": "Bauen/Baustoffe",
    "Technik/Eisenwaren/Bleche": "Bauen/Baustoffe",
    "Technik/Eisenwaren/Profile": "Bauen/Baustoffe",
    "Bad/Sanitärinstallation/HT-Rohre": "Bauen/Entwässerung",
    "Bad/Sanitärinstallation/Wasserrohre": "Bauen/Entwässerung",
}
UNCATEGORIZED = {  # receipt lines without shop category -> key in CATEGORIES (file name prefix)
    "obi-3820776": "Bauen/Baustoffe", "obi-3820784": "Bauen/Baustoffe",  # XPS
    "obi-5039300": "Bauen/Bauholz", "obi-2106572497540": "Bauen/Bauholz",  # OSB, KVH
    "obi-6791222": "Wohnen/Farben", "obi-1882489": "Bauen/Baustoffe",  # Fassadenschutz, Montagekleber
    "obi-8867038": "Bauen/Baustoffe", "obi-8867145": "Bauen/Baustoffe",  # Holzleim
    "hornbach-5803381": "Bauen/Baustoffe", "hornbach-7196545": "Bauen/Baustoffe",  # Fensterkitt, Spachtel
    "hornbach-7196485": "Wohnen/Farben", "hornbach-10718039": "Wohnen/Farben",  # Grundierung, Silikatfarbe
    "hornbach-7773629": "Bauen/Bauholz", "hornbach-7773632": "Bauen/Bauholz",  # Plattenzuschnitt
}
UNITS = {"Kilogramm": "je kg", "M": "je m", "M2": "je m²", "QM": "je m²", "LM": "je m"}
NOT_MATERIAL = re.compile(r"big-bag|japanspachtel|malerband|sekundenkleber|giessharz|kunstharz|verglasungsfolie"
                          r"|precit-winkel|spruehlack-maston")  # tools/packaging/accessories in material categories
DIM_LABELS = {"weight": "Gewicht", "height": "Höhe", "width": "Breite", "depth": "Tiefe", "length": "Länge",
              "thickness": "Stärke", "diameter": "Durchmesser"}
LEGAL = re.compile(r"\b(gmbh|ag|se|kg|co|n\.?v\.?|s\.?r\.?o\.?|srl|spol|s\.r\.l\.|deutschland|europa|& co\.?)\b", re.I)


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def dump(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def slug(text):
    t = text.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def company_id(name):
    s = slug(LEGAL.sub(" ", name.replace(",", " ")))
    return s or slug(name)


def category_of(article, stem=""):
    path = article.get("category_path") or ""
    if not path:
        return UNCATEGORIZED.get(stem.split("_", 1)[0])
    if any(path.startswith("Start/Wohnen/" + a) or path.startswith("Start/Bauen/" + a) for a in ACCESSORIES):
        return None
    if path.startswith("Sortiment/"):
        sub = path[len("Sortiment/"):]
        return next((v for k, v in HORNBACH_CATEGORIES.items() if sub == k or sub.startswith(k + "/")), None)
    found = next((k for k in CATEGORIES if path.startswith("Start/" + k)), None)
    return found or next((v for k, v in OBI_CATEGORIES.items() if path.startswith("Start/" + k)), None)


def receipts():
    """article_number -> list of (supplier id, receipt)."""
    out = {}
    for sup, name in RECEIPTS.items():
        f = CAT / "imported_purchases" / name
        for r in (load(f) if f.exists() else []):
            if r.get("sub_type", "SALE") != "SALE":
                continue
            for it in r.get("items") or []:
                out.setdefault(str(it.get("article_number")), []).append((sup, r, it))
    return out


def offers(article, sup, by_article):
    found, seen = [], set()
    for s, r, it in by_article.get(str(article.get("article_number")), []):
        if s != sup or not isinstance(it.get("unit_price"), (int, float)):
            continue
        key = (r.get("date"), r.get("store"), it["unit_price"])
        if key in seen:
            continue
        seen.add(key)
        unit = UNITS.get(it.get("unit") or "")
        qty = it.get("quantity", 1)
        amount = "%s %s" % (qty, it["unit"]) if unit else "%s×" % qty
        found.append({"supplier": "company:" + sup, "price": it["unit_price"], "currency": "EUR",
                      "price_basis": "gross", "date": r["date"],
                      "source": "Kassenbon %s, %s, %s%s" % (r["date"], r.get("store", ""), amount,
                                                          ", Preis " + unit if unit else "")})
    if not found and isinstance(article.get("unit_price"), (int, float)):
        found.append({"supplier": "company:" + sup, "price": article["unit_price"], "currency": "EUR",
                      "price_basis": "gross", "source": "Import " + (article.get("receipt_name") or "")})
    return sorted(found, key=lambda o: o.get("date", ""))


def details_of(article):
    """Shop tables product_data / dimensions_weight; falls back to dimensions_and_weight."""
    d = {k: v for k, v in (article.get("details") or {}).items() if v}
    if "dimensions_weight" not in d and article.get("dimensions_and_weight"):
        d["dimensions_weight"] = [{"label": DIM_LABELS.get(k, k), "value": str(v)}
                                   for k, v in article["dimensions_and_weight"].items() if v]
    return d


def product(article, by_article, companies):
    sup = SUPPLIERS.get(article.get("supplier"), (None,))[0]
    p = {}
    if article.get("manufacturer"):
        p["manufacturer"] = "company:" + companies.need(article["manufacturer"], "manufacturer")
    if article.get("name"):
        p["model"] = article["name"]
    if article.get("article_number"):
        p["article_no"] = str(article["article_number"])
    if article.get("ean"):
        p["ean"] = str(article["ean"])
    if article.get("url"):
        p["url"] = article["url"]
    if details_of(article):
        p["details"] = details_of(article)
    if sup:
        companies.need(article["supplier"], "supplier")
        p["offers"] = offers(article, sup, by_article)
    return p


class Companies:
    """Existing companies plus the ones to create."""

    def __init__(self):
        self.data = {p.stem: load(p) for p in COMPANIES.glob("*.json")}
        self.new = {}

    def need(self, name, role):
        cid = SUPPLIERS[name][0] if role == "supplier" and name in SUPPLIERS else company_id(name)
        c = self.data.get(cid) or self.new.get(cid)
        if c is None:
            label = SUPPLIERS[name][1] if role == "supplier" and name in SUPPLIERS else name
            c = {"id": cid, "name": label, "roles": [role], "description": name}
            self.new[cid] = c
        elif role not in c["roles"]:
            c["roles"].append(role)
            if cid in self.data:
                self.new[cid] = c
        return cid


def photos_of(stem, mid):
    """Images in imported_material/images are named <prefix>-<number>_<n>.jpg after the import file."""
    return [(src, PHOTOS / mid / src.name) for src in sorted((IMPORT / "images").glob(stem.split("_", 1)[0] + "_*"))]


def main():
    write = "--write" in sys.argv
    by_article = receipts()
    companies = Companies()
    materials = {p.stem: load(p) for p in MATERIALS.glob("*.json")}
    used = {ref for m in materials.values() for ref in m.get("imported_from", []) + m.get("products", [])}
    changed, copies, rows = {}, [], []

    for mid, m in materials.items():  # migrate products -> imported_from + offers
        if "products" not in m:
            continue
        refs = m.pop("products")
        m["imported_from"] = refs
        p = m.setdefault("product", {})
        for ref in refs:
            art = load(IMPORT / (ref + ".json"))
            p.setdefault("offers", []).extend(product(art, by_article, companies).get("offers", []))
        changed[mid] = m
        rows.append((mid, "(bestehend, %d Angebote)" % len(p["offers"]), m["category"], ""))

    for mid, m in materials.items():  # refresh shop details of already imported materials, keep the rest
        refs = [r for r in m.get("imported_from", []) if (IMPORT / (r + ".json")).exists()]
        d = next((x for x in (details_of(load(IMPORT / (r + ".json"))) for r in refs) if x), None)
        if d and isinstance(m.get("product"), dict) and m["product"].get("details") != d:
            m = changed.get(mid, m)
            m["product"]["details"] = d
            changed[mid] = m
            rows.append((mid, "(bestehend, Details ergänzt)", m["category"], ""))

    for f in sorted(IMPORT.glob("*.json")):
        art = load(f)
        key = category_of(art, f.stem)
        if key is None or f.stem in used or NOT_MATERIAL.search(f.stem):
            continue
        mid = slug(f.stem.split("_", 1)[1])
        if mid in materials or mid in changed:
            mid = mid + "-" + (art.get("ean") or art.get("article_number") or "x")
        category, appearance = CATEGORIES[key]
        if category == "Farbe" and not re.search(r"wei(ss|ß)", art.get("name", ""), re.I):
            appearance = dict(appearance, color="#C8C2B8")
        pics = photos_of(f.stem, mid)
        m = {"id": mid, "name": art["name"], "category": category}
        if art.get("description"):
            m["description"] = art["description"]
        m.update({"conductivity": None, "values_source": "Baumarkt-Artikel, Kennwerte offen",
                  "imported_from": [f.stem], "product": product(art, by_article, companies),
                  "appearance": dict(appearance)})
        if pics:
            m["photos"] = [dst.name for _, dst in pics]
        changed[mid] = m
        copies += pics
        best = min((o["price"] for o in m["product"].get("offers", [])), default=None)
        rows.append((mid, art["name"], category, "" if best is None else "%.2f €" % best))

    for r in rows:
        print("%-60s | %-12s | %9s | %s" % (r[0][:60], r[2], r[3], r[1][:70]))
    print("%d Materialien, %d neue/geänderte Firmen, %d Fotos" % (len(rows), len(companies.new), len(copies)))
    print("Firmen: " + ", ".join(sorted(companies.new)))
    if not write:
        print("Dry run - mit --write schreiben")
        return
    for cid, c in companies.new.items():
        dump(COMPANIES / (cid + ".json"), c)
    for mid, m in changed.items():
        dump(MATERIALS / (mid + ".json"), m)
    for src, dst in copies:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    print("geschrieben")


if __name__ == "__main__":
    main()
