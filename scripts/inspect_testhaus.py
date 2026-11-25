"""Prints VALIDATE errors/warnings and key numbers of the test house (read-only, runs in a sandbox)."""
import json
import sys

from sandbox import Sandbox


def main() -> int:
    with Sandbox(check_catalog=False) as sb:
        v = sb.q("VALIDATE")
        print("ok", v.get("ok"), "counts", v.get("counts"))
        for e in v.get("errors", []):
            print("ERR ", e.get("where"), e.get("message"))
        for w in v.get("warnings", []):
            print("WARN", w.get("where"), w.get("message"))
        if "--walls" in sys.argv:
            for st in sb.q("HOUSE")["storeys"]:
                for w in st["walls"]:
                    small = {k: w[k] for k in w if k not in ("layers", "openings", "profile", "pieces", "band", "polygon")}
                    print(st["id"], json.dumps(small, ensure_ascii=False)[:600])
                    print("   layers", [(L.get("material"), len(L.get("pieces", [])), L.get("area_outside"), L.get("volume"))
                                        for L in w.get("layers", [])][:6])
                    print("   layer keys", sorted(w["layers"][0]) if w.get("layers") else None)
            b = sb.q("BOM")
            print("bom walls", json.dumps(b["walls"][:2], ensure_ascii=False)[:1500])
        if "--full" in sys.argv:
            h = sb.q("HOUSE")
            b = sb.q("BOM")
            print(json.dumps({"house_keys": sorted(h), "bom_keys": sorted(b), "totals": b.get("totals")},
                             ensure_ascii=False, indent=1)[:6000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
