"""Read-only check of ceiling output (HOUSE + BOM) for the real data."""
import json
import os
import sys

sys.path.insert(0, os.path.join(r"c:\Development\weingaerten", "code"))
os.environ["WEINGAERTEN_HOME"] = os.environ.get("WEINGAERTEN_SMOKE_HOME", r"c:\Development\weingaerten")
import weingaerten_core as c

h = json.loads(c.handle(json.dumps({"command": "HOUSE"})))
fails = 0
for st in h["storeys"]:
    for ce in st.get("ceilings", []):
        j = ce["joists"]
        print(st["id"], ce["id"], "area", round(ce["area"], 3), "z", round(ce["z_bottom"], 4), round(ce["z_top"], 4),
              "layers", [(L["material"], round(L["z0"], 4), round(L["z1"], 4)) for L in ce["layers"]])
        if j:
            print("  joists", j["count"], "len", round(j["length"], 2), "vol", round(j["volume"], 3),
                  "spacing", round(j["spacing_actual"], 3), "z", j["z0"], round(j["z1"], 3))
        if abs(ce["layers"][0]["z1"] - ce["z_top"]) > 1e-9 or (j and abs(j["z0"] - ce["z_top"]) > 1e-9):
            print("FAIL z chain"); fails += 1
        if j and (j["count"] < 1 or j["volume"] <= 0):
            print("FAIL joists"); fails += 1
b = json.loads(c.handle(json.dumps({"command": "BOM"})))
print("BOM ceilings", b["ceilings"])
print("totals", b["totals"])
v = json.loads(c.handle(json.dumps({"command": "VALIDATE"})))
print("ok", v["ok"], "errors", v["errors"][:3], "counts", v["counts"])
print("FAILED: %d" % fails if fails else "ALL OK")
raise SystemExit(1 if fails else 0)
