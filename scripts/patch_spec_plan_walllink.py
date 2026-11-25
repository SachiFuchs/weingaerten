"""Spec patch: wall link in the /grundriss layer tooltip (weingaerten-web.md, CRLF -> bytes)."""
from pathlib import Path

SPEC = Path(__file__).resolve().parent.parent / "weingaerten-web.md"
OLD = ("- Each layer polygon has `data-wall`, `data-material`, `data-thickness`; a small inline script shows the same "
       "tooltip as on `/haus3d` on hover (`textContent`).").encode("utf-8")
NEW = ("- Each layer polygon has `data-wall`, `data-wid` (wall id), `data-storey`, `data-material`, `data-thickness`; a small "
       "inline script shows the same tooltip as on `/haus3d` on hover (`textContent`). The wall tooltip ends with a link "
       "\"Wand anzeigen / bearbeiten\" to `/waende?storey=<storey>#<wall id>`; like on `/haus3d` the tooltip freezes when "
       "the pointer rests 300 ms (`#tip.live`, pointer events on) and stays while the pointer is within 40 px; Escape "
       "closes it.").encode("utf-8")

data = SPEC.read_bytes()
if NEW in data:
    print("already patched")
elif data.count(OLD) == 1:
    SPEC.write_bytes(data.replace(OLD, NEW))
    print("patched")
else:
    raise SystemExit("anchor not found")
