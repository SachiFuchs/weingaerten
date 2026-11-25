"""Read the tables "Produktdaten" and "Maße & Gewicht" from the OBI product pages into
catalog/imported_material/*.json as details = {product_data: [...], dimensions_weight: [...]}
(rows {label, value} in the shop's wording). Pages are cached in scripts/obi_pages/.

Usage: python scripts/fetch_obi_details.py [--write] [--force] [--only <ean|article>]
"""
import html.parser
import json
import pathlib
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMPORT = ROOT / "catalog" / "imported_material"
CACHE = pathlib.Path(__file__).with_name("obi_pages")
SECTIONS = {"produktdaten": "product_data", "maße & gewicht": "dimensions_weight", "maße und gewicht": "dimensions_weight"}
DIM_LABELS = {"weight": "Gewicht", "height": "Höhe", "width": "Breite", "depth": "Tiefe", "length": "Länge"}
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
           "Accept": "text/html", "Accept-Language": "de-DE"}


class TechnicalData(html.parser.HTMLParser):
    """Collects the PdpTechnicalDataTable blocks: h3 heading followed by th/td rows."""

    def __init__(self):
        super().__init__()
        self.tables, self._depth, self._mode, self._text, self._label = [], 0, None, "", None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("data-component") == "PdpTechnicalDataTable":
            self.tables.append(["", []])
            self._depth = 1
            return
        if not self._depth:
            return
        if tag == "div":
            self._depth += 1
        if tag in ("h3", "th", "td"):
            self._mode, self._text = tag, ""

    def handle_endtag(self, tag):
        if not self._depth:
            return
        if tag == "div":
            self._depth -= 1
        elif tag == self._mode:
            text = " ".join(self._text.split())
            if tag == "h3":
                self.tables[-1][0] = text
            elif tag == "th":
                self._label = text
            elif self._label:
                self.tables[-1][1].append({"label": self._label, "value": text})
                self._label = None
            self._mode = None

    def handle_data(self, data):
        if self._mode:
            self._text += data


def details_of(page):
    p = TechnicalData()
    p.feed(page)
    out = {}
    for title, rows in p.tables:
        key = SECTIONS.get(title.lower())
        if key and rows:
            out.setdefault(key, []).extend(rows)
    return out


def page_of(url, article, force):
    CACHE.mkdir(exist_ok=True)
    f = CACHE / (article + ".html")
    if f.exists() and not force:
        return f.read_text(encoding="utf-8")
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as r:
        text = r.read().decode("utf-8", "replace")
    f.write_text(text, encoding="utf-8")
    time.sleep(1)
    return text


def main():
    args = sys.argv[1:]
    write, force = "--write" in args, "--force" in args
    only = args[args.index("--only") + 1] if "--only" in args else None
    ok = missing = 0
    for f in sorted(IMPORT.glob("*.json")):
        art = json.loads(f.read_text(encoding="utf-8"))
        url = art.get("url") or ""
        if "obi.de" not in url or (only and only not in (art.get("ean"), art.get("article_number"))):
            continue
        try:
            d = details_of(page_of(url, str(art.get("article_number") or f.stem), force))
        except OSError as e:
            print("FEHLER", f.stem, e)
            d = {}
        if "dimensions_weight" not in d and art.get("dimensions_and_weight"):
            d["dimensions_weight"] = [{"label": DIM_LABELS.get(k, k), "value": v}
                                      for k, v in art["dimensions_and_weight"].items() if v]
        art["details"] = d
        art["details_status"] = "ok" if d else "missing"
        ok, missing = ok + bool(d), missing + (not d)
        print("%-70s %2d Produktdaten, %2d Maße" % (f.stem[:70], len(d.get("product_data", [])), len(d.get("dimensions_weight", []))))
        if write:
            f.write_text(json.dumps(art, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("%d mit Details, %d ohne%s" % (ok, missing, "" if write else " - Dry run, mit --write schreiben"))


if __name__ == "__main__":
    main()
