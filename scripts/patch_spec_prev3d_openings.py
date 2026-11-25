"""Spec patch: openings in the /waende 3D preview (layers cut at the rough openings; CRLF -> bytes)."""
from pathlib import Path

SPEC = Path(__file__).resolve().parent.parent / "weingaerten-web.md"
OLD = b"scene = the wall layers as translucent prisms (opacity 0.22, material colours) with the wall edges,"
NEW = ("scene = the wall layers as translucent prisms (opacity 0.22, material colours) with the rough openings cut out "
       "(each layer footprint sliced at every opening `u0` / `u1` by half-plane clips along the wall; a slice keeps the "
       "height intervals outside the openings covering its middle, `z0 + zb .. z0 + zt` left free), each piece with its "
       "edges,").encode("utf-8")
PREVIOUS = ("scene = the wall layers as translucent prisms (opacity 0.22, material colours) built from the layer `pieces` "
            "(so openings stay open; full footprint `z0..z1` when a layer has no pieces), each with its edges,").encode("utf-8")

data = SPEC.read_bytes()
if NEW in data:
    print("already patched")
else:
    for old in (OLD, PREVIOUS):
        if data.count(old) == 1:
            SPEC.write_bytes(data.replace(old, NEW))
            print("patched")
            break
    else:
        raise SystemExit("anchor not found")
