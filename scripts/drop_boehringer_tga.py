"""One-off: deletes the tga-components created for Böhringer 25-0023 (now materials, see HEATING_MATERIALS in
import_documents.py). pipe-bekotec-14 stays (used by the floor heating)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from import_documents import HEATING_MATERIALS  # noqa: E402

TGA = pathlib.Path(__file__).resolve().parent.parent / "catalog" / "tga-components"
gone = 0
for mid in HEATING_MATERIALS:
    p = TGA / (mid + ".json")
    if p.is_file():
        p.unlink()
        gone += 1
print("deleted", gone)
