"""Validate catalog/house JSON files against catalog/schema (incl. new TGA/DIN-276 schemas)."""
import json
import pathlib
import sys

import jsonschema

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "catalog" / "schema"

MAP = {
    "catalog/materials": "material",
    "catalog/assemblies": "assembly",
    "catalog/classes": "class",
    "catalog/components": "component",
    "catalog/tga-classes": "tga-class",
    "catalog/tga-components": "tga-component",
    "catalog/reference": "din276",
    "house/storeys": "storey",
}


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    errors = 0
    for schema_file in sorted(SCHEMA.glob("*.schema.json")):
        jsonschema.Draft202012Validator.check_schema(load(schema_file))
    checks = [(ROOT / "house" / "house.json", "house")]
    for folder, name in MAP.items():
        checks += [(p, name) for p in sorted((ROOT / folder).glob("*.json"))]
    for path, name in checks:
        validator = jsonschema.Draft202012Validator(load(SCHEMA / f"{name}.schema.json"))
        data = load(path)
        errs = list(validator.iter_errors(data))
        if path.stem != data.get("id"):
            errs.append(f"id {data.get('id')} != Dateiname")
        for e in errs:
            errors += 1
            print(f"FEHLER {path.relative_to(ROOT)}: {getattr(e, 'message', e)}")
    print(f"{len(checks)} Dateien geprüft, {errors} Fehler")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
