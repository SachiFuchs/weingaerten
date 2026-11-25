"""Convert scripts/hornbach_raw.json (Hornbach account API dump) into
catalog/imported_material/hornbach-<article>_<slug>.json and
catalog/imported_purchases/hornbach_purchases.json (same shape as the OBI import)."""
import html
import json
import re
import unicodedata
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = Path(__file__).with_name("hornbach_raw.json")
DETAILS = Path(__file__).with_name("hornbach_details.json")
GALLERY = Path(__file__).with_name("hornbach_gallery.json")
MAT_DIR = ROOT / "catalog" / "imported_material"
IMG_DIR = MAT_DIR / "images"
DIMENSION_KEYS = {"gewicht": "weight", "höhe": "height", "breite": "width", "tiefe": "depth",
                  "länge": "length", "stärke": "thickness", "durchmesser": "diameter"}
PUR_FILE = ROOT / "catalog" / "imported_purchases" / "hornbach_purchases.json"
SUPPLIER = "HORNBACH Baumarkt AG"
STORES = {"582": "HORNBACH Göppingen, Ulmer Straße 95-97, 73037 Göppingen"}
MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]


def slug(text):
    t = text.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:40].strip("-") or "artikel"


def plain(text):
    if not text:
        return None
    t = re.sub(r"<br\s*/?>", "\n", text)
    return html.unescape(re.sub(r"<[^>]+>", "", t)).strip()


def dimensions(attrs):
    out = {}
    for key, value in attrs.items():
        k = key.lower()
        for word, name in DIMENSION_KEYS.items():
            if k.startswith(word) and name not in out:
                out[name] = value
    return out


def sections(attrs):
    """Split the attributes like the shop tables: dimensions_weight (Maße & Gewicht), product_data (rest)."""
    out = {}
    for key, value in attrs.items():
        dim = any(key.lower().startswith(w) for w in DIMENSION_KEYS)
        out.setdefault("dimensions_weight" if dim else "product_data", []).append({"label": key, "value": str(value)})
    return out


def download(url, art, n):
    IMG_DIR.mkdir(exist_ok=True)
    path = IMG_DIR / f"hornbach-{art}_{n}.jpg"
    if not path.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            path.write_bytes(r.read())
    return f"images/{path.name}"


def enrich(m, d):
    """Merge scraped product page data (Artikeldetails, JSON-LD) into material m."""
    if not d or not d.get("name"):
        m["details_status"] = "not_available" if d else m["details_status"]
        return
    m["name"] = d["name"]
    m["description"] = plain(d.get("description"))
    m["manufacturer"] = d.get("brand")
    m["category_path"] = d.get("category")
    m["attributes"] = d.get("attributes") or {}
    m["dimensions_and_weight"] = dimensions(m["attributes"])
    m["details"] = sections(m["attributes"])
    m["image_urls"] = d.get("images") or m["image_urls"]
    if d.get("image_alts"):
        m["image_alts"] = d["image_alts"]
    images = []
    for n, url in enumerate(m["image_urls"], 1):
        try:
            images.append(download(url, m["article_number"], n))
        except OSError as e:
            print("image failed", m["article_number"], url, e)
    m["images"] = images


def date_text(iso):
    d = date.fromisoformat(iso)
    return f"{d.day}. {MONTHS[d.month - 1]} {d.year}"


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    raw.sort(key=lambda p: (p["receiptDate"], p["receiptId"] or ""), reverse=True)
    materials, purchases = {}, []
    for p in raw:
        items = []
        for pos in p["positions"]:
            art = pos["articleId"]
            name = pos["articleName"] or pos["text"] or art
            items.append({"article_number": art, "quantity": pos["quantity"], "unit": pos["unit"],
                          "unit_price": pos["pricePerUnit"], "total_price": pos["priceTotalGross"]})
            if art in materials:
                continue  # raw is newest first: keep the latest price
            url = "https://www.hornbach.de" + pos["url"] if pos["url"] else None
            materials[art] = {
                "article_number": art, "ean": pos["ean"], "name": name,
                "receipt_name": pos["text"], "unit_price": pos["pricePerUnit"], "unit": pos["unit"],
                "url": url, "description": None, "dimensions_and_weight": {}, "images": [],
                "image_urls": [pos["image"]] if pos["image"] else [],
                "details_status": "ok" if url else "no_url", "manufacturer": None,
                "supplier": SUPPLIER,
            }
        subtotal = round(sum(i["total_price"] or 0 for i in items), 2)
        total = p["totalPrice"] if p["totalPrice"] is not None else subtotal
        purchases.append({
            "date": p["receiptDate"], "date_text": date_text(p["receiptDate"]),
            "store": STORES.get(p["storeId"], p["storeName"]),
            "kind": {"EBON": "ebon", "ORDER": "order"}.get(p["purchaseType"], p["purchaseType"]),
            "sub_type": p["subType"], "receipt_id": p["receiptId"],
            "return_of": p["refId"] or None, "payment": p["payment"] or None,
            "subtotal": subtotal, "discount": round(total - subtotal, 2), "total": total,
            "items": items,
        })
    details = json.loads(DETAILS.read_text(encoding="utf-8"))["res"] if DETAILS.exists() else {}
    gallery = json.loads(GALLERY.read_text(encoding="utf-8"))["res"] if GALLERY.exists() else {}
    for url, g in gallery.items():
        d = details.get(url)
        if d and d.get("name"):
            if g["media"]:
                d["images"] = [x["url"] for x in g["media"]]
                d["image_alts"] = [x["alt"] for x in g["media"]]
            d["category"] = g["category"] or d.get("category")
    for art, m in materials.items():
        fname = f"hornbach-{art}_{slug(m['name'])}.json"
        enrich(m, details.get(m["url"]))
        (MAT_DIR / fname).write_text(
            json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PUR_FILE.write_text(json.dumps(purchases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(purchases)} purchases, {len(materials)} materials, "
          f"sum {round(sum(p['total'] for p in purchases), 2)}")


if __name__ == "__main__":
    main()
