"""Prices of the TGA BOM blocks (installation, electrical) + issue counts, to compare before/after strip_tga_products.

Usage: python scripts/snapshot_tga_prices.py <out.json>   (reads the real data, read-only)
"""
import importlib, json, os, sys

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["WEINGAERTEN_HOME"] = SRC
sys.path.insert(0, os.path.join(SRC, "code"))
core = importlib.import_module("weingaerten_core")


def call(**kw):
    return json.loads(core.handle(json.dumps(kw)))


bom = call(command="BOM")
val = call(command="VALIDATE")
rows = {}
for r in ((bom.get("installation") or {}).get("components") or []):
    rows["installation:" + r["component"]] = r.get("unit_price")
for r in ((bom.get("electrical") or {}).get("rows") or (bom.get("electrical") or {}).get("materials") or []):
    if isinstance(r, dict) and r.get("component"):
        rows["electrical:" + r["component"]] = r.get("unit_price")
totals = {k: v for k, v in (bom.get("totals") or {}).items() if "price" in k}
out = {"totals": totals, "unit_prices": rows,
       "errors": len(val.get("errors") or []), "warnings": len(val.get("warnings") or [])}
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(out, handle, ensure_ascii=False, indent=1, sort_keys=True)
print(json.dumps({"totals": totals, "unit_prices": len(rows), "errors": out["errors"], "warnings": out["warnings"]}))
