"""List category paths of imported articles not picked up by import_materials.py (read-only)."""
import collections
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import import_materials as im  # noqa: E402

INBOX = pathlib.Path(__file__).resolve().parent.parent / "catalog" / "imported_material"
counts = collections.Counter()
samples = collections.defaultdict(list)
for p in sorted(INBOX.glob("*.json")):
    a = json.loads(p.read_text(encoding="utf-8"))
    if im.category_of(a):
        continue
    path = "/".join((a.get("category_path") or "").split("/")[:4])
    counts[path] += 1
    if len(samples[path]) < 3:
        samples[path].append(a.get("name") or p.stem)
for path, n in counts.most_common():
    print(f"{n:4d}  {path}  | {'; '.join(samples[path])}")
