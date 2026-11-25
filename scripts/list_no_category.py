"""List names/sources of imported articles without category_path (read-only)."""
import json
import pathlib

INBOX = pathlib.Path(__file__).resolve().parent.parent / "catalog" / "imported_material"
for p in sorted(INBOX.glob("*.json")):
    a = json.loads(p.read_text(encoding="utf-8"))
    if not a.get("category_path"):
        print(p.stem.split("_")[0][:22].ljust(22), (a.get("name") or "")[:90])
