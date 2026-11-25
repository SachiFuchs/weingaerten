"""Move the naturbo press couplings from install-part to pipe-fitting (line alu_composite) and add the
Pressfenster-Einleger and Innenkalibrierer of invoice 13202600675 (idempotent).

    python scripts/move_naturbo_press_fittings.py
"""
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parent.parent / "catalog"
DOC = "document:2026-06-16-naturbo-13202600675-lehmplatten-wandhzg"
PRESS_RULE = {"line": "alu_composite", "medium": "heating", "method": "press", "partners": ["pipe", "terminal"],
              "note": "Presskupplung nimmt Verbundrohr 11,6 / 16 mm bzw. Rohrende der Heizplatte auf; "
                      "Durchmesserwechsel nur über Übergang 11,6/16"}

# id suffix -> (fitting_type, angle, dn_to)
FITTINGS = {"": ("coupling", None, None), "-90": ("bend", 90, None),
            "-16": ("adapter", None, 16.0), "-16-90": ("adapter", 90, 16.0)}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("wrote", path.relative_to(CATALOG))


def update_class():
    path = CATALOG / "tga-classes" / "pipe-fitting.json"
    data = load(path)
    for p in data["parameters"]:
        if p["key"] in ("system_line", "line_to") and "alu_composite" not in p["options"]:
            p["options"].insert(3, "alu_composite")
        if p["key"] in ("dn", "dn_branch", "dn_to"):
            p["min"] = 10
    if not any(p["key"] == "connection_method" for p in data["parameters"]):
        data["parameters"].insert(2, {"key": "connection_method", "name": "Verbindungsart", "type": "choice",
                                      "options": ["push", "weld", "press"], "required": False})
    data["description"] = ("Formteil einer Rohrleitung: Bogen, Abzweig, Übergang (z. B. KG auf HT, Verbundrohr "
                           "11,6 auf 16), Kupplung oder Stopfen")
    data["connection_rules"] = [r for r in data["connection_rules"] if r.get("line") != "alu_composite"]
    data["connection_rules"].append(PRESS_RULE)
    save(path, data)


def update_fittings():
    for suffix, (fitting_type, angle, dn_to) in FITTINGS.items():
        path = CATALOG / "tga-components" / ("naturbo-presskupplung-11-6%s.json" % suffix)
        data = load(path)
        params = {"fitting_type": fitting_type, "system_line": "alu_composite", "connection_method": "press",
                  "dn": 11.6}
        if angle:
            params["angle"] = angle
        if dn_to:
            params.update(line_to="alu_composite", dn_to=dn_to)
        data["class"] = "tga-class:pipe-fitting"
        data["params"] = params
        data["note"] = "aus Beleg (catalog/documents); Pressfitting für naturbo Wandheizung"
        save(path, data)


def part(key, name, pos, price, note):
    return {"id": key, "name": name, "class": "tga-class:install-part", "din276": "420", "system_type": "Wandheizung",
            "params": {"part_type": "other", "unit": "pcs"}, "note": note,
            "product": {"manufacturer": "company:naturbo", "model": name, "offers": [
                {"supplier": "company:naturbo", "price": price, "currency": "EUR", "price_basis": "net",
                 "date": "2026-06-16", "source": "Rechnung 13202600675, Pos. %d, je Stk" % pos, "document": DOC}]}}


def add_parts():
    for data in (part("naturbo-pressfenster-einleger", "Naturbo Pressfenster-Einleger", 21, 0.0,
                      "Einleger für das Sichtfenster der Presskupplung (je Pressstelle)"),
                 part("naturbo-innenkalibrierer", "Naturbo Innenkalibrierer 11,6 / 16 mm", 22, 19.0,
                      "Werkzeug: kalibriert und entgratet das Verbundrohr vor dem Pressen")):
        save(CATALOG / "tga-components" / (data["id"] + ".json"), data)


if __name__ == "__main__":
    update_class()
    update_fittings()
    add_parts()
