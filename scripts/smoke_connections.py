"""Connection rules of the TGA catalog (HT/KG flow, PP-R welding, cables/clamps/boxes/terminals) on a temp copy."""
import copy, importlib, json, os, shutil, sys, tempfile

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(SRC, "code", "weingaerten_core")

tmp = tempfile.mkdtemp()
for d in ("catalog", "house"):
    shutil.copytree(os.path.join(SRC, d), os.path.join(tmp, d),
                    ignore=shutil.ignore_patterns("imported_*", "photos"))
os.environ["WEINGAERTEN_HOME"] = tmp
sys.path.insert(0, os.path.dirname(CORE))
core = importlib.import_module("weingaerten_core")

fails = []


def call(**kw):
    return json.loads(core.handle(json.dumps(kw)))


def check(name, cond, detail=""):
    print(("OK   " if cond else "FAIL ") + name + ("" if cond else "  " + str(detail)[:300]))
    if not cond:
        fails.append(name)


tga = call(command="TGA_CATALOG")
els = tga["elements"]


def raw(ref):
    e = copy.deepcopy(els[ref])
    for k in ("ref", "type", "file", "material_product"):
        e.pop(k, None)
    return e


def save(ref, e, create=False):
    return call(command="SAVE", ref=ref, element=e, create=create)


def errs(answer):
    return answer.get("errors") or ([answer["error"]] if "error" in answer else [])


v = call(command="VALIDATE")
check("VALIDATE without tga errors", not [x for x in v["errors"] if x["where"].startswith(("tga-", "catalog/tga"))],
      [x for x in v["errors"] if x["where"].startswith("tga-")][:3])
check("TGA_CATALOG lists classes and components", "tga-class:pipe" in els and "tga-component:ht-pipe-50" in els)
check("pipe class has HT/KG/PPR rules", {r.get("line") for r in els["tga-class:pipe"]["connection_rules"]} >= {"ht", "kg", "ppr"})
check("cable conductors derived 3G", [c["role"] for c in tga["conductors"]["tga-component:cable-nym-3x15"]] == ["L", "N", "PE"])
check("cable conductors derived 5G", [c["role"] for c in tga["conductors"]["tga-component:cable-nym-j-5x16"]]
      == ["L1", "L2", "L3", "N", "PE"])
check("Marley bend migrated with angle", els["tga-component:marley-ht-bogen-45deg-dn-50-grau"]["params"]["angle"] == 45)
check("WAGO 5-polig clamp", els["tga-component:wago-hebelklemme-0-2-4-mm2-5-polig-5-stueck"]["connection"]["poles"] == 5)

# HT: reversed flow is rejected
ref = "tga-component:ht-bend-50-45"
e = raw(ref)
e["connection"]["ends"][1]["flow"] = "in"
check("HT spigot with flow in rejected", any("Fließrichtung" in m for m in errs(save(ref, e))))
e = raw(ref)
del e["connection"]["ends"][0]["flow"]
check("HT end without flow rejected", any("Fließrichtung fehlt" in m for m in errs(save(ref, e))))
e = raw(ref)
e["connection"]["ends"][1]["dn"] = 90
check("HT bend with wrong DN rejected", any("DN 90" in m for m in errs(save(ref, e))))
e = raw(ref)
e["connection"]["ends"].pop()
check("bend with one end rejected", any("2 Anschlüsse" in m for m in errs(save(ref, e))))
check("unchanged HT bend saves", "error" not in save(ref, raw(ref)), save(ref, raw(ref)))
e = raw("tga-component:kg-ueberschiebmuffe-dn-110-mm")
check("KG coupling socket out allowed", "error" not in save("tga-component:kg-ueberschiebmuffe-dn-110-mm", e))
e = raw("tga-component:kg-adapter-110-ht90")
check("KG/HT adapter saves (other line end)", "error" not in save("tga-component:kg-adapter-110-ht90", e))

# PP-R: pipe ends must be spigots, fittings sockets
ref = "tga-component:ppr-rohr-dn-20-x-2-m"
e = raw(ref)
e["connection"]["ends"][0]["gender"] = "socket"
check("PP-R pipe with socket rejected", any("PP-R" in m for m in errs(save(ref, e))))
ref = "tga-component:pp-r-schweissmuffe-dn-20"
e = raw(ref)
e["connection"]["ends"][0]["gender"] = "spigot"
check("PP-R fitting with spigot rejected", any("PP-R" in m for m in errs(save(ref, e))))
e = raw("tga-component:pp-r-schweiss-uebergangsstueck-dn-20-ag-1-2")
check("PP-R adapter with thread spigot saves", "error" not in save("tga-component:pp-r-schweiss-uebergangsstueck-dn-20-ag-1-2", e))

# electrical
ref = "tga-component:cable-nym-3x15"
e = raw(ref)
e["connection"]["conductors"] = [{"role": "L"}, {"role": "N"}]
check("cable conductors != cores rejected", any("Aderzahl" in m for m in errs(save(ref, e))))
e["connection"]["conductors"] = [{"role": "L"}, {"role": "PE"}, {"role": "PE"}]
check("double PE rejected", any("PE doppelt" in m for m in errs(save(ref, e))))
e["connection"]["conductors"] = [{"role": "L", "color": "#000000"}, {"role": "N"}, {"role": "PE"}]
check("own conductors save", "error" not in save(ref, e))
check("own conductor colour returned", call(command="TGA_CATALOG")["conductors"][ref][0]["color"] == "#000000")
ref = "tga-component:wago-hebelklemme-2-polig-100-stueck"
e = raw(ref)
del e["connection"]["poles"]
check("clamp without poles rejected", any("Polzahl" in m for m in errs(save(ref, e))))
e = raw(ref)
e["connection"]["cross_section"] = [4, 1]
check("clamp min > max rejected", any("min > max" in m for m in errs(save(ref, e))))
ref = "tga-component:kaiser-up-geraetedose"
e = raw(ref)
del e["connection"]["mounting"]
check("box without mounting rejected", any("Montageart" in m for m in errs(save(ref, e))))
ref = "tga-component:jung-steckdose-1-stueck"
e = raw(ref)
del e["connection"]["accepts"]
check("socket without accepts rejected", any("Leiterarten" in m for m in errs(save(ref, e))))

# runs: cable to a switch (takes only L) warns, rising drain warns
house = os.path.join(tmp, "house", "tga")
with open(os.path.join(house, "terminals", "el-dose-kueche.json"), encoding="utf-8") as f:
    term = json.load(f)
term["component"] = "tga-component:aus-wechselschalter-aufputz-weiss"
with open(os.path.join(house, "terminals", "el-dose-kueche.json"), "w", encoding="utf-8") as f:
    json.dump(term, f)
with open(os.path.join(house, "runs", "aw-bad-wb.json"), encoding="utf-8") as f:
    run = json.load(f)
run["points"][-1][2] = 0.5
with open(os.path.join(house, "runs", "aw-bad-wb.json"), "w", encoding="utf-8") as f:
    json.dump(run, f)
w = call(command="VALIDATE")["warnings"]
check("cable at switch warns about N PE", any(x["where"] == "tga-run:el-kueche-dose" and "N PE" in x["message"] for x in w),
      [x for x in w if "el-kueche" in x["where"]])
check("rising drain warns", any(x["where"] == "tga-run:aw-bad-wb" and "Gefälle" in x["message"] for x in w))
term["component"] = "tga-component:hohlwanddose"
with open(os.path.join(house, "terminals", "el-dose-kueche.json"), "w", encoding="utf-8") as f:
    json.dump(term, f)
w = call(command="VALIDATE")["warnings"]
check("cable in box ok", not [x for x in w if x["where"] == "tga-run:el-kueche-dose"], [x for x in w if "el-kueche" in x["where"]])
term["component"] = "tga-component:ppr-valve-20"
with open(os.path.join(house, "terminals", "el-dose-kueche.json"), "w", encoding="utf-8") as f:
    json.dump(term, f)
w = call(command="VALIDATE")["warnings"]
check("cable at non-electrical end warns", any(x["where"] == "tga-run:el-kueche-dose" and "nicht in Dose" in x["message"] for x in w))

# class save checks its components; create / delete of a component
cls = raw("tga-class:pipe-fitting")
for rule in cls["connection_rules"]:
    if rule.get("line") == "ppr":
        rule["directed"] = True
check("class change breaking components refused", "nicht mehr zur Klasse" in str(save("tga-class:pipe-fitting", cls)))
new = {"id": "test-klemme", "name": "Testklemme", "class": "tga-class:install-part", "din276": "440",
       "system_type": "Stromkreis", "params": {"part_type": "clamp"},
       "connection": {"line": "power", "poles": 3, "cross_section": [0.5, 2.5]}}
check("create tga component", "error" not in save("tga-component:test-klemme", new, True))
check("created file exists", os.path.isfile(os.path.join(tmp, "catalog", "tga-components", "test-klemme.json")))
check("delete used class refused", "wird verwendet" in str(call(command="DELETE", ref="tga-class:install-part")))
check("delete component", call(command="DELETE", ref="tga-component:test-klemme").get("deleted") is True)

run_path = os.path.join(house, "runs", "el-kueche-dose.json")
with open(run_path, encoding="utf-8") as f:
    cable_run = json.load(f)
term["component"] = "tga-component:hohlwanddose"
with open(os.path.join(house, "terminals", "el-dose-kueche.json"), "w", encoding="utf-8") as f:
    json.dump(term, f)
cable_run["joints"] = cable_run["joints"][:2]
cable_run["joints"][1] = dict(cable_run["joints"][1], clamp="tga-component:wago-hebelklemme-2-polig-100-stueck", wires=3)
with open(run_path, "w", encoding="utf-8") as f:
    json.dump(cable_run, f)
w = [x["message"] for x in call(command="VALIDATE")["warnings"] if x["where"] == "tga-run:el-kueche-dose"]
check("unclamped PE warns", any("PE" in m and "nicht geklemmt" in m for m in w), w)
check("too many wires warns", any("3 Adern, aber nur 2 Pole" in m for m in w), w)
check("naturbo pipe 16 exists", "tga-component:naturbo-alu-verbundrohr-16" in els)
ref = "tga-component:naturbo-presskupplung-11-6-16"
e = raw(ref)
check("naturbo coupling saves", "error" not in save(ref, e))
e["connection"]["ends"][1]["gender"] = "spigot"
check("naturbo coupling spigot rejected", any("Verbundrohr" in m for m in errs(save(ref, e))))

shutil.rmtree(tmp, ignore_errors=True)
print("\n%d failed" % len(fails) if fails else "\nall OK")
sys.exit(1 if fails else 0)
