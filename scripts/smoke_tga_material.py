"""Product/offers of tga-components come from catalog_material; materials link back (temp copy, real data untouched)."""
import importlib, json, os, shutil, sys, tempfile

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(SRC, "code", "weingaerten_core")

tmp = tempfile.mkdtemp()
for d in ("catalog", "house"):
    shutil.copytree(os.path.join(SRC, d), os.path.join(tmp, d), ignore=shutil.ignore_patterns("imported_*", "photos"))
os.environ["WEINGAERTEN_HOME"] = tmp
sys.path.insert(0, os.path.dirname(CORE))
core = importlib.import_module("weingaerten_core")

fails = []
TGA = "tga-component:marley-ht-bogen-45-grad-dn-90"
MAT = "material:marley-ht-bogen-45-grad-dn-90"


def call(**kw):
    return json.loads(core.handle(json.dumps(kw)))


def check(name, cond, detail=""):
    print(("OK   " if cond else "FAIL ") + name + ("" if cond else "  " + str(detail)[:300]))
    if not cond:
        fails.append(name)


def raw(element):
    return {k: v for k, v in element.items() if k not in ("ref", "type", "file", "material_product")}


els = call(command="TGA_CATALOG")["elements"]
e = els[TGA]
check("TGA-Bauteil ohne eigenes product", "product" not in e, e.get("product"))
check("material_product aus Material", (e.get("material_product") or {}).get("offers"), e.get("material_product"))
check("keine material_product ohne catalog_material",
      all("material_product" not in x or x.get("catalog_material") for x in els.values()))

usage = call(command="USAGE", ref=MAT)
check("Material kennt TGA-Bauteil (USAGE)", TGA in usage.get("used_by", []), usage)
check("USAGE all enthält Rückverweis", TGA in call(command="USAGE", all=True)["usage"].get(MAT, []))
deleted = call(command="DELETE", ref=MAT)
check("Material mit TGA-Verwendung nicht löschbar", "error" in deleted, deleted)

bad = dict(raw(e), catalog_material="material:gibt-es-nicht")
answer = call(command="SAVE", ref=TGA, element=bad)
check("unbekanntes catalog_material = Fehler",
      any("catalog_material" in t for t in answer.get("errors") or [answer.get("error", "")]), answer)

material = call(command="ELEMENT", ref=MAT)
mat_product = (material.get("element") or material).get("product")
double = dict(raw(e), product=mat_product)
answer = call(command="SAVE", ref=TGA, element=double)
check("SAVE mit eigenem product erlaubt", not answer.get("errors") and not answer.get("error"), answer)
warnings = call(command="VALIDATE").get("warnings") or []
check("Warnung Angebote doppelt", any(w.get("where") == TGA and "Angebote doppelt" in w.get("message", "")
                                      for w in warnings), [w for w in warnings if w.get("where") == TGA])

errors = call(command="VALIDATE").get("errors") or []
check("VALIDATE ohne Fehler", not errors, errors[:3])

shutil.rmtree(tmp, ignore_errors=True)
print("FAILED: %s" % fails if fails else "ALL OK")
sys.exit(1 if fails else 0)
