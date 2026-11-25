"""Checks the running server on port 8008: redirects, every page (status 200 and key elements), embed mode and the API
routes for house, walls and openings incl. rejected saves (data unchanged afterwards).

Teilweise veraltet: die Prüfung "opening outside" erwartet noch die Wand `w-south`.
"""
import json, re, urllib.request, urllib.error
B = "http://localhost:8008"
HOME = r"c:\Development\weingaerten"
fails = []
def get(p):
    try:
        with urllib.request.urlopen(urllib.request.Request(B + p), timeout=120) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, "", ""
def post(p, body):
    req = urllib.request.Request(B + p, json.dumps(body).encode(), {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, None
def chk(c, m):
    if not c: fails.append(m)
class NoRedir(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None
for src, dst in (("/", "/haus3d"), ("/katalog", "/katalog/materialien"), ("/doku", "/handbuch")):
    try:
        urllib.request.build_opener(NoRedir).open(B + src, timeout=5); chk(False, src + " no redirect")
    except urllib.error.HTTPError as e:
        chk(e.code == 302 and e.headers.get("Location") == dst, src + " redirect")
pages = ["/haus3d", "/grundriss", "/waende", "/katalog/materialien", "/katalog/aufbauten", "/katalog/bauteile", "/katalog/klassen",
         "/mengen", "/handbuch", "/techdoku", "/about", "/favicon.svg", "/katalog/dokumente"]
pg = {}
for p in pages:
    s, ct, t = get(p); pg[p] = t; chk(s == 200, p + " %s" % s)
h = pg["/haus3d"]; chk("Haus 3D" in h and "importmap" in h and '<script type="module"' in h and "geschoss3d-" in h, "haus3d")
chk(all(x in h for x in ("Stockwerke", "Technik", "details3d", "split3d", "detailframe", "detailtoggle", "tiplinks", "Detail3d")), "haus3d detail panel")
chk("weingaerten.scene3d.width" not in h, "haus3d width no longer stored")
for p, key in (("/waende?embed=1", "wanddata"), ("/katalog/bauteile?embed=1", "katdata"), ("/katalog/materialien?embed=1", "katdata")):
    s, ct, t = get(p); chk(s == 200 and key in t and "html.embed" in t, p + " embed")
s, hj = post("/api/house", {}); nops = sum(len(x["openings"]) for x in hj["storeys"][0]["walls"])
g = pg["/grundriss"]; chk('class="layer"' in g and g.count('class="opening"') == nops and all(x in g for x in ("planedit", "plandata", "planpanel")),
                         "grundriss openings %d/%d" % (g.count('class="opening"'), nops))
w = pg["/waende"]; chk(all(x in w for x in ("wanddata", "wallist", "wallsvg")), "waende")
s, ct, ra = get("/raeume"); chk(s == 200 and all(x in ra for x in ("raumdata", "roomlist", "roomsvg", "rtabs", "navtoggle")), "raeume")
s, _ = post("/api/room/save", {"storey": "../x", "room": {"id": "r"}, "create": False}); chk(s == 400, "room save bad storey 400")
s, _ = post("/api/shaft/delete", {"id": "../x"}); chk(s == 400, "shaft delete bad id 400")
for p in pages[3:7]:
    chk("katdata" in pg[p] and 'id="katnew"' in pg[p] and "<textarea" not in pg[p], "katalog " + p)
    chk(all('id="%s"' % x in pg[p] for x in ("katgrid", "katlist", "katdetail", "katedit", "katsplit", "katphotos")), "katalog layout " + p)
d = pg["/katalog/dokumente"]
chk("Katalog – Dokumente" in d and "KatDocs" in d and 'id="katnew"' not in d and "<textarea" not in d
    and all('id="%s"' % x in d for x in ("katgrid", "katlist", "katdetail")), "katalog dokumente")
for bad in ("/catalog-photo/x/..%2Fa.jpg", "/catalog-photo/../catalog/x.jpg", "/catalog-photo/a/b.txt", "/catalog-photo/nicht-da/x.jpg"):
    try:
        urllib.request.urlopen(B + bad, timeout=10); chk(False, "photo 404 " + bad)
    except urllib.error.HTTPError as ex:
        chk(ex.code == 404, "photo 404 " + bad)
chk("Fenster 2-flüglig" in pg["/katalog/bauteile"], "bauteile")
chk("Anzahl Flügel" in pg["/katalog/klassen"], "klassen")
m = pg["/mengen"]; chk(("Modell gültig" in m or "Modell ungültig" in m) and "Bauteile" in m, "mengen")
hb = pg["/handbuch"]; chk(all(x in hb for x in ['id="tdtree"', "Erste Schritte", "Haus 3D", "Grundriss", "Wände", "Katalog", "Mengen"]), "handbuch")
_, _, d = get("/techdoku?node=fachliches-modell"); chk(all(x in d for x in ["Referenzkette", "Öffnungen", "Regeln", "IFC-Zuordnung"]), "fachliches modell")
td = pg["/techdoku"]; chk(all(x in td for x in ['id="tdtree"', 'id="tdmain"', "Einführung", "Dokumentationsdateien", "Sicherheit",
                                              "AAA Security-Checks", "Schnittstellen", "Entwicklungsrichtlinien"]), "techdoku")
for node, keys in (("code-core", ("<svg", "ModelComputer")), ("code-web-klassen-rendering-pagelayout", ("render", "page_layout.py")),
                   ("code-web-web-parts-katalog-layout-js", ("KatLayout",)), ("code-scripte", ("check_web.py",)),
                   ("../x", ('class="on"',)), ("%3Cscript%3E", ('class="on"',))):
    s, ct, t = get("/techdoku?node=" + node); chk(s == 200 and all(k in t for k in keys) and "<script>alert" not in t, "techdoku " + node)
_, _, lg = get("/techdoku?node=code-core-klassen-compute-lininggeometry")
chk('node=code-core-klassen-compute-walldata"' in lg and "<dialog" in lg and 'class="k"' in lg and "<details open>" in lg, "techdoku links + source")
_, _, wd = get("/techdoku?node=code-core-klassen-compute-walldata")
chk("Wird verwendet von" in wd and "node=code-core-klassen-compute-lininggeometry" in wd, "techdoku used by")
_, _, cg = get("/techdoku?node=code-core-klassen-compute")
chk('class="tdgroup"' in cg and 'class="tdmod"' in cg and "data-expand" in cg, "techdoku group page")
_, _, ex = get("/techdoku?node=ausnahmeliste"); chk("HTTP server process" in ex and "Pygments" in ex and "House core package" in ex, "techdoku exceptions")
_, _, im = get("/techdoku?node=code-importierte-module"); chk("Standardbibliothek" in im and "pygments" in im and "unbekannt – prüfen</td>" not in im, "techdoku imports")
_, _, ki = get("/techdoku?node=schnittstellen-ki-module-und-modelle"); chk("keine KI" in ki, "techdoku ki")
_, _, gi = get("/techdoku?node=versionsverwaltung-git"); chk("bmw.ghe.com/Sachindra-Suri/weingaerten" in gi, "techdoku git")
a = pg["/about"]
chk(re.search(r">Haus 3D<.*>Grundriss<.*>Wände<.*>Katalog<.*>Materialien<.*>Aufbauten<.*>Bauteile<.*>Klassen<.*>Mengen<.*>Benutzerhandbuch<.*>Tech.Doku<.*>About<", a, re.S) is not None, "menu order")
chk(all("navtoggle" in pg[p] for p in pages[:-1]), "navtoggle")
for f in ["three.module.js", "OrbitControls.js"]:
    s, ct, _ = get("/lib/" + f); chk(s == 200 and "text/javascript" in ct, f)
chk(get("/lib/other.js")[0] == 404, "other.js")
chk(s == 200 and hj["storeys"][0]["walls"] and "outline" in hj["storeys"][0], "api house")
s, j = post("/api/resolve", {"ref": "assembly:exterior-wall-ew1"}); chk(s == 200 and len(j["layers"]) == 5, "api resolve")
chk(post("/api/resolve", {"ref": "../x"})[0] == 400, "resolve bad")
s, j = post("/api/validate", {}); chk(s == 200 and j["ok"], "validate %s" % (j or {}).get("errors"))
s, j = post("/api/usage", {"ref": "material:hollow-brick"}); chk(s == 200 and "assembly:exterior-wall-ew1" in j["used_by"], "usage")
fp = HOME + r"\catalog\materials\hollow-brick.json"; before = open(fp, encoding="utf-8").read()
s, j = post("/api/element/delete", {"ref": "material:hollow-brick"}); chk(s == 400 and "wird verwendet von" in j["error"], "delete used")
chk(open(fp, encoding="utf-8").read() == before, "brick unchanged")
chk(post("/api/element/save", {"ref": "material:../x", "element": {}, "create": True})[0] == 400, "save bad ref")
chk(post("/api/opening/save", {"storey": "../x", "wall": "w-south", "opening": {"id": "x"}, "create": True})[0] == 400, "opening bad storey")
gp = HOME + r"\house\storeys\ground.json"; gb = open(gp, encoding="utf-8").read()
op = {"id": "o-win1", "component": "component:window-w1", "offset": 10.5, "sill": 0.9, "joint": 0.01, "inset": 0.1, "reveal_material": "material:interior-plaster"}
s, j = post("/api/opening/save", {"storey": "ground", "wall": "w-south", "opening": op, "create": False})
chk(s == 400 and "Öffnung ragt über die Wand" in j["error"], "opening outside %s %s" % (s, j))
chk(open(gp, encoding="utf-8").read() == gb, "storey unchanged")
chk(post("/api/walls/save", {"storey": "../x", "upsert": []})[0] == 400, "walls bad storey")
w0 = {k: v for k, v in hj["storeys"][0]["walls"][0].items() if k in ("id", "name", "assembly", "start", "end", "reference", "outside")}
w0["end"] = [w0["end"][0] + 1, w0["end"][1] + 1]
s, j = post("/api/walls/save", {"storey": "ground", "upsert": [w0]})
chk(s == 400 and "90°-Raster" in json.dumps(j, ensure_ascii=False), "walls diagonal %s %s" % (s, j))
chk(open(gp, encoding="utf-8").read() == gb, "storey unchanged (walls)")
print("check=OK" if not fails else "check=FAILED\n" + "\n".join(fails))
raise SystemExit(1 if fails else 0)
