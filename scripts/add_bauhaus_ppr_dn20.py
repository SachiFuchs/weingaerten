"""Writes Bauhaus PP-R fittings DN 20 (round 3) into catalog/materials."""
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "catalog", "materials")
DATE = "2026-11-21"
COMMON = ("Unlösbare Muffenschweißverbindung an PP-R-Rohr DN 20, für Trinkwasser warm/kalt "
          "und Druckluft, korrosionsfrei, DVGW-zertifiziert, 10 Jahre Herstellergarantie.")

ITEMS = [
    ("pp-r-schweiss-uebergangsstueck-dn-20-ig-1-2", "Schweiß-Übergangsstück PP-R DN 20, Innengewinde ½″",
     "Übergang von PP-R-Schweißrohr DN 20 auf Innengewinde ½″ (Messing-Gewindeeinsatz). " + COMMON + " Werkstoff Polypropylen.",
     "Schweiß-Übergangsstück DN 20, Innengewinde ½″, Polypropylen", "26981420",
     "schweissfittings/schweiss-uebergangsstueck/p/26981420", 2.90, "#3E8E41"),
    ("pp-r-montageeinheit-dn-20-ig-1-2", "Montageeinheit PP-R DN 20, Innengewinde ½″",
     "Montageeinheit (Doppel-Wandanschluss) für den Übergang von Schweißrohr DN 20 auf Innengewinde ½″, Messinganschlüsse. " + COMMON + " Werkstoff Polypropylen.",
     "Montageeinheit DN 20, Innengewinde ½″, Polypropylen", "26317238",
     "schweissfittings/montageeinheit/p/26317238", 8.50, "#3E8E41"),
    ("pp-r-ventil-set-dn-20-handrad", "Ventil-Set PP-R DN 20, 2-tlg., mit Handradgriff",
     "Durchgangsventil zum Absperren und Regeln des Durchflusses, mit Handradgriff, 2-teilig (Messing, Kunststoff, Gummi). " + COMMON,
     "Ventil-Set 2-tlg., DN 20, mit Handradgriff", "26311966",
     "schweissfittings/ventil-set/p/26311966", 13.50, "#3E8E41"),
    ("pp-r-schweisswinkel-dn-20-90", "Schweißwinkel PP-R DN 20, 90°",
     "90°-Winkel zum Verlegen von PP-R-Leitungen DN 20 um Ecken. " + COMMON + " Werkstoff Polypropylen.",
     "Schweißwinkel DN 20, 90°, Polypropylen", "13562837",
     "schweissfittings/schweisswinkel/p/13562837", 1.60, "#3E8E41"),
    ("pp-r-schweiss-endkappe-dn-20", "Schweiß-Endkappe PP-R DN 20",
     "Endkappe zum Verschließen eines PP-R-Schweißrohres DN 20. " + COMMON + " Werkstoff Polypropylen.",
     "Schweiß-Endkappe DN 20, Polypropylen", "13563018",
     "schweissfittings/schweiss-endkappe/p/13563018", 1.15, "#3E8E41"),
    ("pp-baustopfen-1-2", "Baustopfen ½″ (Blindstopfen)",
     "Baustopfen mit ½″ Außengewinde zum Verschließen fertiger Leitungen (z. B. Wandscheiben DN 20), die noch keine Entnahmearmatur haben. DVGW-zertifiziert. Werkstoff Polypropylen.",
     "Baustopfen ½″, Polypropylen", "13563290",
     "schweissfittings/baustopfen/p/13563290", 1.30, "#3E8E41"),
]

for mid, name, desc, model, art, path, price, color in ITEMS:
    data = {
        "id": mid,
        "name": name,
        "category": "Entwässerung",
        "description": desc,
        "conductivity": None,
        "values_source": "Baumarkt-Artikel, Kennwerte offen",
        "product": {
            "model": model,
            "article_no": art,
            "url": "https://www.bauhaus.info/" + path,
            "offers": [{
                "supplier": "company:bauhaus",
                "price": price,
                "currency": "EUR",
                "price_basis": "gross",
                "date": DATE,
                "source": "bauhaus.info Produktseite %s, pro Stück inkl. MwSt." % DATE,
            }],
        },
        "appearance": {"color": color, "roughness": 0.5, "hatch": "none"},
    }
    with open(os.path.join(ROOT, mid + ".json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("written", mid)
