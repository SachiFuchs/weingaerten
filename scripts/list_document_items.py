"""Read-only: list all items of catalog/documents with doc type, supplier and existing ref."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent / "catalog" / "documents"
for f in sorted(root.glob("*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    print(f"## {d['id']} | {d.get('doc_type')} | {d.get('supplier')} | {d.get('category')}")
    for it in d.get("items", []):
        desc = " ".join(str(it.get("description", "")).split())[:110]
        print(f"  {it.get('position','')}\t{it.get('quantity','')} {it.get('unit','')}\t{it.get('unit_price','')}\t{it.get('ref','-')}\t{desc}")
