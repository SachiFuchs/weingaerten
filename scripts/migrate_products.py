"""One-off migration: companies, component products, material glass (Nov 2026)."""
import json, os, re

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(HOME, "catalog")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(p, d):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
        f.write("\n")


COMPANIES = [
    {"id": "neuffer", "name": "Neuffer Fenster + Türen", "roles": ["supplier"],
     "description": "Fensterhändler; Bestellungen/Rechnungen 2023–2025 für die Kunststofffenster"},
    {"id": "aluplast", "name": "aluplast", "roles": ["manufacturer"],
     "description": "Hersteller der Kunststofffenster-Systeme IDEAL 4000 / IDEAL 8000"},
    {"id": "koemmerling", "name": "Kömmerling", "roles": ["manufacturer"],
     "description": "Hersteller des Kunststofffenster-Systems Trocal 70 AD"},
    {"id": "velux", "name": "VELUX", "roles": ["manufacturer"],
     "description": "Hersteller von Dachfenstern und Eindeckrahmen"},
    {"id": "schuck-dach", "name": "Schuck Dach", "roles": ["supplier"],
     "description": "Dachdecker; Endrechnung vom 17.07.2023"},
]

# component id -> (manufacturer, model, article_no, supplier, date, source)
PRODUCTS = {
    "window-kammer":       ("aluplast", "IDEAL 4000", None, "neuffer", "2023-07-30", "Best. 3308385, Pos. 1"),
    "window-balkonkammer": ("koemmerling", "Trocal 70 AD", None, "neuffer", "2023-11-16", "Best. 3320751, Pos. 1"),
    "window-schlafzimmer": ("aluplast", "IDEAL 8000", None, "neuffer", "2023-11-16", "Best. 3320751, Pos. 3"),
    "window-wz-gross":     ("aluplast", "IDEAL 8000", None, "neuffer", "2024-10-06", "RE 3358369, Pos. 1"),
    "window-wz-terrasse":  ("aluplast", "IDEAL 8000", None, "neuffer", "2024-10-06", "RE 3358369, Pos. 2"),
    "window-eg-kueche":    ("aluplast", "IDEAL 8000", None, "neuffer", "2025-11-03", "RE 3417279, Pos. 1"),
    "window-eg-bad":       ("aluplast", "IDEAL 8000", None, "neuffer", "2025-11-03", "RE 3417279, Pos. 2"),
    "window-eg-flur":      ("aluplast", "IDEAL 8000", None, "neuffer", "2025-11-03", "RE 3417279, Pos. 3"),
    "window-eg-kammer":    ("aluplast", "IDEAL 8000", None, "neuffer", "2025-11-03", "RE 3417279, Pos. 4"),
    "window-wz-klein":     ("aluplast", "IDEAL 8000", None, "neuffer", "2025-11-03", "RE 3417279, Pos. 5"),
    "roof-window-velux-ck04":   ("velux", "GGU CK04 Energy Plus", "GGU CK04 0066", "schuck-dach", "2023-07-17", "RE 17.07.2023, Titel 06"),
    "roof-window-velux-fk06":   ("velux", "GGU FK06 Energy Plus Favorit Everfinish", None, "schuck-dach", "2023-07-17", "RE 17.07.2023, Titel 06"),
    "roof-flashing-velux-ck04": ("velux", "EDZ 2000 CK04", None, "schuck-dach", "2023-07-17", "RE 17.07.2023, Titel 06"),
    "roof-flashing-velux-fk06": ("velux", "EDZ FK06", None, "schuck-dach", "2023-07-17", "RE 17.07.2023, Titel 06"),
}

PRICE_RE = re.compile(r";\s*([\d.]+,\d{2}) €")


def main():
    os.makedirs(os.path.join(CAT, "companies"), exist_ok=True)
    for c in COMPANIES:
        save(os.path.join(CAT, "companies", c["id"] + ".json"), c)

    save(os.path.join(CAT, "materials", "glass.json"), {
        "id": "glass", "name": "Glas", "category": "Glas",
        "description": "Floatglas (Kalk-Natron-Silikatglas); Scheibenanzahl und Ug-Wert sind Eigenschaften des Fensters",
        "conductivity": 1.0, "density": 2500, "fire_class": "A1",
        "values_source": "Richtwert Floatglas (DIN EN ISO 10456)",
        "appearance": {"color": "#A9D6EE", "roughness": 0.05, "hatch": "none"},
    })

    cls_p = os.path.join(CAT, "classes", "window.json")
    cls = load(cls_p)
    for r in cls["material_roles"]:
        if r["key"] == "glazing":
            r["default"] = "material:glass"
    save(cls_p, cls)

    comp_dir = os.path.join(CAT, "components")
    for fn in sorted(os.listdir(comp_dir)):
        p = os.path.join(comp_dir, fn)
        d = load(p)
        cid = d["id"]
        if d.get("materials", {}).get("glazing", "").startswith("material:glass-"):
            d["materials"]["glazing"] = "material:glass"
        if cid in PRODUCTS:
            man, model, art, sup, date, src = PRODUCTS[cid]
            m = PRICE_RE.search(d["description"])
            if not m:
                raise SystemExit("kein Preis in " + cid)
            price = float(m.group(1).replace(".", "").replace(",", "."))
            prod = {"manufacturer": "company:" + man, "model": model}
            if art:
                prod["article_no"] = art
            prod["offers"] = [{"supplier": "company:" + sup, "price": price, "currency": "EUR",
                               "date": date, "source": src}]
            d["product"] = prod
            d["description"] = d["description"][:m.start()] + d["description"][m.end():]
        save(p, d)
        print(cid, d.get("product", {}).get("offers", [{}])[0].get("price", "-"))

    for old in ("glass-double", "glass-triple"):
        os.remove(os.path.join(CAT, "materials", old + ".json"))


if __name__ == "__main__":
    main()
