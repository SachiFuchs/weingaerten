"""Spec/handbook patch: 'Neue Gruppe beginnen' in the /waende installation palette (CRLF -> bytes)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATCHES = [
    ("weingaerten-handbuch.md",
     "**Esc** hebt die Auswahl auf und zeigt wieder alle.",
     "**Esc** oder die Schaltfläche **Neue Gruppe beginnen** (über der Palette) hebt die Auswahl auf – das Bestehende "
     "bleibt unverändert – und zeigt wieder alle Teile, so dass eine neue, nicht verbundene Gruppe (z. B. eine weitere "
     "Elektro-Gruppe oder Rohre) begonnen werden kann. Esc wirkt auch, wenn gerade ein Feld des Teil-Panels den Fokus hat."),
    ("weingaerten-web.md",
     "while a part is selected `(<fitt",
     "while a part is selected (or one is carried) a button `Neue Gruppe beginnen` above the tree clears the selection and "
     "the carried part (placed parts unchanged, focus leaves the panel) so the full palette is offered; Escape does the same "
     "even while a panel field has the focus (not while a dialog is open); `(<fitt"),
]

for name, old, new in PATCHES:
    path = ROOT / name
    data = path.read_bytes()
    o, n = old.encode("utf-8"), new.encode("utf-8")
    if n in data:
        print(name, "already patched")
    elif data.count(o) == 1:
        path.write_bytes(data.replace(o, n))
        print(name, "patched")
    else:
        raise SystemExit("%s: anchor not found (%d)" % (name, data.count(o)))
