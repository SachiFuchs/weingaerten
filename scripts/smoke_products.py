"""Product/company checks of the core on a temp copy of the project data."""
import importlib, json, os, shutil, sys, tempfile

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(r"c:\Development\weingaerten", "code", "weingaerten_core")

tmp = tempfile.mkdtemp()
for d in ("catalog", "house"):
    shutil.copytree(os.path.join(SRC, d), os.path.join(tmp, d))
os.environ["WEINGAERTEN_HOME"] = tmp
sys.path.insert(0, os.path.dirname(CORE))
core = importlib.import_module("weingaerten_core")


def call(**kw):
    return json.loads(core.handle(json.dumps(kw)))


fails = []


def check(name, cond):
    print(("OK   " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


v = call(command="VALIDATE")
prod_errs = [e for e in v["errors"] if "Firma" in e["message"] or "product" in e["message"] or "company" in e["where"]]
check("VALIDATE no product/company errors %s" % prod_errs, not prod_errs)
N_COMPANIES = len([f for f in os.listdir(os.path.join(SRC, "catalog", "companies")) if f.endswith(".json")])
check("counts.companies == %d" % N_COMPANIES, v["counts"].get("companies") == N_COMPANIES)
cat = call(command="CATALOG", type="company")
check("CATALOG company", len(cat["elements"]) == N_COMPANIES and cat["elements"][0]["category"])

comp = call(command="ELEMENT", ref="component:window-kammer")
for k in ("ref", "type", "file"):
    comp.pop(k, None)
bad = json.loads(json.dumps(comp))
bad["product"]["manufacturer"] = "company:neuffer"
r = call(command="SAVE", ref="component:window-kammer", element=bad, create=False)
check("manufacturer without role", "Firma ist kein Hersteller" in r.get("error", ""))
bad = json.loads(json.dumps(comp))
bad["product"]["offers"][0]["supplier"] = "company:aluplast"
r = call(command="SAVE", ref="component:window-kammer", element=bad, create=False)
check("supplier without role", "Firma ist kein Lieferant" in r.get("error", ""))
r = call(command="DELETE", ref="company:neuffer")
check("delete used company", "wird verwendet von: component:" in r.get("error", ""))
co = call(command="ELEMENT", ref="company:neuffer")
for k in ("ref", "type", "file"):
    co.pop(k, None)
co["roles"] = ["manufacturer"]
r = call(command="SAVE", ref="company:neuffer", element=co, create=False)
check("remove used role", "Bauteile/Materialien passen nicht mehr zur Firma" in r.get("error", ""))
r = call(command="SAVE", ref="company:test-firma", element={"id": "test-firma", "name": "Test", "roles": ["supplier"]}, create=True)
check("create company", r.get("file") == "catalog/companies/test-firma.json")
r = call(command="DELETE", ref="company:test-firma")
check("delete unused company", r.get("deleted") is True)

# cheaper second offer -> unit_price = lowest
two = json.loads(json.dumps(comp))
two["product"]["offers"].append({"supplier": "company:schuck-dach", "price": 200.0, "currency": "EUR"})
r = call(command="SAVE", ref="component:window-kammer", element=two, create=False)
check("save 2 offers", "error" not in r)
bom = call(command="BOM")
row = [c for c in bom["components"] if c["component"] == "component:window-kammer"]
if row:
    c = row[0]
    check("unit_price lowest", c["unit_price"] == 200.0 and abs(c["total_price"] - 200.0 * c["count"]) < 1e-6)
    check("manufacturer name", c["manufacturer"] == "aluplast")
else:
    print("SKIP window-kammer not used in house")
check("totals.component_price", bom["totals"]["component_price"] > 0)
shutil.rmtree(tmp, ignore_errors=True)
print("FAILED: %d" % len(fails) if fails else "ALL OK")
raise SystemExit(1 if fails else 0)
