"""Check materials (incl. products[] links) and imported products against their schemas using the core validator."""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "code"))
from weingaerten_core.validation.schema_validator import SchemaValidator  # noqa: E402


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    cat = ROOT / "catalog"
    errors = []
    products = {p.stem for p in (cat / "imported_material").glob("*.json")}
    pv = SchemaValidator(load(cat / "schema" / "product.schema.json"))
    for p in sorted((cat / "imported_material").glob("*.json")):
        errors += pv.check(load(p), p.name)
    mv = SchemaValidator(load(cat / "schema" / "material.schema.json"))
    companies = {"company:" + p.stem: load(p) for p in (cat / "companies").glob("*.json")}
    links = 0
    for p in sorted((cat / "materials").glob("*.json")):
        data = load(p)
        errors += mv.check(data, p.name)
        for ref in data.get("imported_from", []):
            links += 1
            if ref not in products:
                errors.append((p.name, "Artikel fehlt: " + ref))
        product = data.get("product") or {}
        refs = [(product.get("manufacturer"), "manufacturer")] + [(o.get("supplier"), "supplier") for o in product.get("offers", [])]
        for ref, role in refs:
            if ref is not None and role not in (companies.get(ref) or {}).get("roles", []):
                errors.append((p.name, "Firma fehlt oder ohne Rolle %s: %s" % (role, ref)))
    for path, message in errors:
        print("FEHLER", path, message)
    print(f"{len(products)} Artikel, {links} Verknüpfungen, {len(errors)} Fehler")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
