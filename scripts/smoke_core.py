"""Smoke test of the core commands (HOUSE, BOM, VALIDATE, wall/opening save and split) on a temporary copy of the house.

Veraltet: erwartet noch das alte 4-Wand-Beispiel (`w-south`) und schlägt daher mit den aktuellen Hausdaten fehl.
"""
import json, os, shutil, sys, tempfile
sys.path.insert(0, os.path.join(r"c:\Development\weingaerten", "code"))
HOME = os.environ.get("WEINGAERTEN_SMOKE_HOME", r"c:\Development\weingaerten")
os.environ["WEINGAERTEN_HOME"] = HOME
import weingaerten_core as c

def q(cmd, **kw):
    kw["command"] = cmd
    return json.loads(c.handle(json.dumps(kw)))

fails = []
def check(cond, msg):
    if not cond:
        fails.append(msg)
near = lambda a, b: abs(a - b) <= 0.001
rd = lambda p: json.load(open(p, encoding="utf-8"))
wr = lambda p, d: json.dump(d, open(p, "w", encoding="utf-8"))

v = q("VALIDATE")
check(v["ok"] and not v["errors"] and not v["warnings"], "validate: %s %s" % (v["errors"], v["warnings"]))
check(v["counts"] == {"materials": 9, "assemblies": 2, "classes": 2, "components": 3, "storeys": 1, "walls": 4,
                      "openings": 4, "rooms": 1}, "counts %s" % v["counts"])
r = q("RESOLVE", ref="assembly:exterior-wall-ew1")
check([L["material"]["name"] for L in r["layers"]] == ["Fassadenfarbe weiß", "Außenputz", "Hohlraumziegel", "Innenputz", "Innenfarbe weiß"], "layers")
check(near(r["thickness"], 0.328) and [L["offset"] for L in r["layers"]] == [0, 0.005, 0.015, 0.315, 0.325], "offsets")
r = q("RESOLVE", ref="component:window-w1")
check(isinstance(r["class"], dict) and isinstance(r["materials"]["frame"], dict), "resolve component")
h = q("HOUSE")
ws = {w["id"]: w for w in h["storeys"][0]["walls"]}
check(h["bbox"] == [0, 0, 11, 7], "bbox")
for w in ws.values():
    check(w["length"] in (11, 7) and near(w["thickness"], 0.328) and w["height"] == 2.75, "dims " + w["id"])
check(len(ws["w-south"]["openings"]) == 2 and all(near(o["rough"]["width"], 1.22) and near(o["rough"]["height"], 1.37) and o["sill"] == 0.9
                                                  for o in ws["w-south"]["openings"]), "south openings")
check(all(len(L["pieces"]) == 7 for L in ws["w-south"]["layers"]), "south pieces")
check(all(len(L["pieces"]) == 3 for L in ws["w-north"]["layers"]), "north pieces")
for w in ws.values():
    for o in w["openings"]:
        check(any(p["kind"] in ("glass", "leaf") for p in o["parts"]), "parts " + o["id"])
b = q("BOM")
bm = {m["material"]: m for m in b["materials"]}
check(near(bm["material:hollow-brick"]["volume"], 26.863), "brick %s" % bm["material:hollow-brick"]["volume"])
check(near(b["totals"]["wall_volume"], 29.377), "wall vol %s" % b["totals"]["wall_volume"])
check(near(bm["material:concrete-c25"]["volume"], 19.25), "concrete")
check(near(bm["material:exterior-paint-white"]["area_outside"], 93.172), "out area")
check(near(bm["material:interior-paint-white"]["area_inside"], 85.956), "in area")
check(near(bm["material:interior-plaster"]["area_reveal"], 4.407), "reveal")
cc = {x["component"]: x["count"] for x in b["components"]}
check(cc == {"component:window-w1": 2, "component:door-d1": 1, "component:window-small": 1}, "components %s" % cc)
check("error" in q("NOPE") and "error" in json.loads(c.handle("{x")), "unknown/invalid")

def tmpcopy():
    tmp = tempfile.mkdtemp()
    shutil.copytree(os.path.join(HOME, "catalog"), os.path.join(tmp, "catalog"))
    shutil.copytree(os.path.join(HOME, "house"), os.path.join(tmp, "house"))
    return tmp

def variant(edit):
    tmp = tmpcopy()
    edit(tmp)
    os.environ["WEINGAERTEN_HOME"] = tmp
    res = q("VALIDATE"), q("HOUSE")
    os.environ["WEINGAERTEN_HOME"] = HOME
    shutil.rmtree(tmp)
    return res

def edit_storey(fn):
    def f(tmp):
        p = os.path.join(tmp, "house", "storeys", "ground.json")
        d = rd(p)
        fn({w["id"]: w for w in d["walls"]})
        wr(p, d)
    return f

def has(v, text, where=None):
    return any(text in e["message"] and (where is None or where in e["where"]) for e in v["errors"])

v, hh = variant(edit_storey(lambda W: W["w-east"].update(assembly="assembly:missing")))
check(has(v, "assembly:missing", "w-east") and hh.get("valid") is False and "storeys" in hh, "missing ref")
v, _ = variant(edit_storey(lambda W: W["w-east"].pop("outside")))
check(has(v, "outside fehlt"), "outside fehlt")
v, _ = variant(edit_storey(lambda W: W["w-east"].update(end=[11, 6])))
check(any("offenes Wandende" in x["message"] for x in v["warnings"]), "open end")
def badid(tmp):
    p = os.path.join(tmp, "catalog", "materials", "hollow-brick.json"); d = rd(p); d["id"] = "other"; wr(p, d)
v, _ = variant(badid); check(not v["ok"], "bad id")
v, _ = variant(edit_storey(lambda W: W["w-south"]["openings"][0].update(offset=10.5)))
check(has(v, "Öffnung ragt über die Wand"), "opening outside")
v, _ = variant(edit_storey(lambda W: W["w-south"]["openings"][1].update(offset=2.5)))
check(has(v, "Öffnungen überlappen"), "overlap")
def notcap(tmp):
    p = os.path.join(tmp, "catalog", "components", "window-small.json"); d = rd(p); d["opening_capable"] = False; wr(p, d)
v, _ = variant(notcap); check(has(v, "nicht für Öffnungen geeignet"), "not capable")
def small(tmp):
    p = os.path.join(tmp, "catalog", "components", "window-small.json"); d = rd(p); d["params"]["width"] = 0.1; wr(p, d)
v, _ = variant(small); check(has(v, "kleiner als Minimum"), "min width")

# editing on a temp copy
tmp = tmpcopy()
os.environ["WEINGAERTEN_HOME"] = tmp
mat = {"id": "test-mat", "name": "Testmaterial", "category": "Test", "conductivity": None,
       "appearance": {"color": "#123456", "roughness": 0.5, "hatch": "none"}}
fp = os.path.join(tmp, "catalog", "materials", "test-mat.json")
r = q("SAVE", ref="material:test-mat", element=mat, create=True)
check("error" not in r and os.path.isfile(fp), "save create %s" % r)
check(q("VALIDATE")["counts"]["materials"] == 10, "after create")
check("existiert bereits" in q("SAVE", ref="material:test-mat", element=mat, create=True).get("error", ""), "dup create")
before = open(fp, encoding="utf-8").read()
check("error" in q("SAVE", ref="material:test-mat", element=dict(mat, appearance={"color": "rot"}), create=False)
      and open(fp, encoding="utf-8").read() == before, "bad update")
wall = {"id": "test-wall", "name": "Testwand", "category": "interior_wall", "layer_order": "left_right",
        "layers": [{"material": "material:test-mat", "thickness": 0.1}]}
check("error" not in q("SAVE", ref="assembly:test-wall", element=wall, create=True), "save wall")
check(q("USAGE", ref="material:test-mat")["used_by"] == ["assembly:test-wall"], "usage")
check("wird verwendet von: assembly:test-wall" in q("DELETE", ref="material:test-mat").get("error", ""), "delete used")
check(q("DELETE", ref="assembly:test-wall").get("deleted") and q("DELETE", ref="material:test-mat").get("deleted") and not os.path.exists(fp), "delete")
check("error" in q("DELETE", ref="material:hollow-brick"), "delete brick")
check("error" in q("SAVE", ref="material:../x", element=mat, create=True), "bad ref")
check("error" in q("SAVE", ref="material:other", element=mat, create=True), "id mismatch")
ew = rd(os.path.join(tmp, "catalog", "assemblies", "exterior-wall-ew1.json")); ew["category"] = "interior_wall"
check("error" in q("SAVE", ref="assembly:exterior-wall-ew1", element=ew, create=False), "layer_order mismatch")
cw = rd(os.path.join(tmp, "catalog", "classes", "window.json"))
c2 = json.loads(json.dumps(cw)); c2["parameters"] = [p for p in c2["parameters"] if p["key"] != "sashes"]
check("Rezept window braucht Parameter sashes" in json.dumps(q("SAVE", ref="class:window", element=c2, create=False), ensure_ascii=False), "recipe")
c3 = json.loads(json.dumps(cw)); [p.update(min=2.0, default=2.5) for p in c3["parameters"] if p["key"] == "width"]
r = q("SAVE", ref="class:window", element=c3, create=False)
check("component:window-small" in r.get("error", "") and "component:window-w1" in r.get("error", ""), "class breaks components %s" % r)
check("wird verwendet von: storey:ground.w-south" in q("DELETE", ref="component:window-w1").get("error", ""), "delete used component")
gp = os.path.join(tmp, "house", "storeys", "ground.json")
op = {"id": "o-test", "component": "component:window-small", "offset": 3, "sill": 1, "joint": 0.01, "inset": 0.1,
      "reveal_material": "material:interior-plaster"}
r = q("OPENING_SAVE", storey="ground", wall="w-west", opening=op, create=True)
check("error" not in r and any(o["id"] == "o-test" for w in rd(gp)["walls"] for o in w["openings"]), "opening create %s" % r)
check(any(o["id"] == "o-test" for w in q("HOUSE")["storeys"][0]["walls"] for o in w["openings"]), "house shows opening")
check("existiert bereits" in q("OPENING_SAVE", storey="ground", wall="w-west", opening=op, create=True).get("error", ""), "dup opening")
before = open(gp, encoding="utf-8").read()
r = q("OPENING_SAVE", storey="ground", wall="w-west", opening=dict(op, offset=6.9), create=False)
check("error" in r and open(gp, encoding="utf-8").read() == before, "bad opening update %s" % r)
check(q("OPENING_DELETE", storey="ground", wall="w-west", id="o-test").get("deleted")
      and not any(o["id"] == "o-test" for w in rd(gp)["walls"] for o in w["openings"]), "opening delete")
os.environ["WEINGAERTEN_HOME"] = HOME
shutil.rmtree(tmp)

# stepped outline (user sketch) and WALLS_SAVE, on temp copies
def stepped(tmp, reverse_west=False):
    p = os.path.join(tmp, "house", "storeys", "ground.json")
    d = rd(p)
    base = {k: v for k, v in d["walls"][0].items() if k not in ("id", "name", "start", "end", "openings")}
    pts = [((0, 0), (11, 0)), ((11, 0), (11, 2)), ((11, 2), (12, 2)), ((12, 2), (12, 7)), ((12, 7), (0, 7)), ((0, 7), (0, 0))]
    d["walls"] = []
    for i, (a, b) in enumerate(pts):
        w = dict(base, id="w-%d" % (i + 1), name="Wand %d" % (i + 1), start=list(a), end=list(b), outside="left", openings=[])
        if reverse_west and i == 5:
            w.update(start=[0, 0], end=[0, 7], outside="right")
        d["walls"].append(w)
    d["rooms"] = [{"id": "r-1", "name": "Raum 1", "rect": [0.328, 0.328, 10.344, 6.344]},
                  {"id": "r-2", "name": "Raum 2", "rect": [10.672, 2.328, 1.0, 4.344]}]
    wr(p, d)

for rev in (False, True):
    tmp = tmpcopy()
    stepped(tmp, rev)
    os.environ["WEINGAERTEN_HOME"] = tmp
    v = q("VALIDATE")
    hard = [e for e in v["errors"] if "Raum" not in e["message"]]
    check(not hard, "stepped errors %s" % hard)
    check(not any("offenes Wandende" in x["message"] for x in v["warnings"]), "stepped open ends %s" % v["warnings"])
    h = q("HOUSE")
    st = h["storeys"][0]
    check(len(st["outline"]) == 1 and len(st["outline"][0]["points"]) == 6, "outline %s" % st.get("outline"))
    check(near(h["foundation"]["area"], 82.0), "foundation area %s" % h["foundation"].get("area"))
    b = q("BOM")
    check(near(b["totals"]["foundation_volume"], 20.5), "foundation vol %s" % b["totals"]["foundation_volume"])
    os.environ["WEINGAERTEN_HOME"] = HOME
    shutil.rmtree(tmp)

tmp = tmpcopy()
os.environ["WEINGAERTEN_HOME"] = tmp
gp = os.path.join(tmp, "house", "storeys", "ground.json")
W = {w["id"]: w for w in rd(gp)["walls"]}
def wall(i, **kw):
    w = {k: v for k, v in W[i].items() if k != "openings"}
    w.update(kw)
    return w
rooms = {"upsert": [{"id": "room-1", "name": "Raum", "rect": [0.328, 0.328, 10.344, 6.844]}]}
r = q("WALLS_SAVE", storey="ground", upsert=[wall("w-south", start=[11, 7.5], end=[0, 7.5]), wall("w-east", end=[11, 7.5]),
                                             wall("w-west", start=[0, 7.5])], rooms=rooms)
check("error" not in r, "move south %s" % r)
ws = {w["id"]: w for w in rd(gp)["walls"]}
check([o["offset"] for o in ws["w-south"]["openings"]] == [o["offset"] for o in W["w-south"]["openings"]], "south offsets kept")
door0 = next(o["offset"] for o in W["w-north"]["openings"] if o["id"] == "o-door")
r = q("WALLS_SAVE", storey="ground", upsert=[wall("w-north", start=[-1, 0]), wall("w-west", start=[0, 7.5], end=[-1, 0])])
# w-west becomes diagonal -> must be rejected; then do it properly
check("Wand nicht im 90°-Raster" in json.dumps(r, ensure_ascii=False), "diagonal rejected %s" % r)
W = {w["id"]: w for w in rd(gp)["walls"]}
r = q("WALLS_SAVE", storey="ground", upsert=[wall("w-north", start=[-1, 0]), wall("w-west", start=[-1, 7.5], end=[-1, 0]),
                                             wall("w-south", end=[-1, 7.5])])
door1 = next(o["offset"] for o in rd(gp)["walls"][0]["openings"] if o["id"] == "o-door")
check("error" not in r and near(door1, door0 + 1.0), "door offset absolute %s -> %s %s" % (door0, door1, r.get("error")))
before = open(gp, encoding="utf-8").read()
W = {w["id"]: w for w in rd(gp)["walls"]}
r = q("WALLS_SAVE", storey="ground", upsert=[dict(wall("w-north"), id="w-dup", openings=[])])
check("error" in r and open(gp, encoding="utf-8").read() == before, "overlap rejected %s" % r.get("error"))
r = q("WALLS_SAVE", storey="ground", upsert=[wall("w-south", start=[3, 7.5])])
check("error" not in r and any(c["opening"] == "o-win1" for c in r["opening_conflicts"]), "conflict allowed %s" % r)
r = q("WALLS_SAVE", storey="ground", height=2.0)
check("error" not in r and any(c["opening"] == "o-door" for c in r["opening_conflicts"]) and rd(gp)["height"] == 2.0, "height %s" % r)
r = q("WALLS_SAVE", storey="ground", delete=["w-east"])
check("error" not in r and not any(w["id"] == "w-east" for w in rd(gp)["walls"]), "delete wall %s" % r)
os.environ["WEINGAERTEN_HOME"] = HOME
shutil.rmtree(tmp)

# split w-south (11,7)->(0,7) at x=5: o-win2 (offset 7 -> x 4..2.78) moves to the new part w-s2 (5,7)->(0,7)
tmp = tmpcopy()
os.environ["WEINGAERTEN_HOME"] = tmp
gp = os.path.join(tmp, "house", "storeys", "ground.json")
W = {w["id"]: w for w in rd(gp)["walls"]}
s1 = {k: v for k, v in W["w-south"].items() if k != "openings"}; s1["end"] = [5, 7]
s2 = dict(s1, id="w-s2", name="Außenwand Süd 2", start=[5, 7], end=[0, 7], take_openings=["o-win2"])
r = q("WALLS_SAVE", storey="ground", upsert=[s1, s2])
ws = {w["id"]: w for w in rd(gp)["walls"]}
check("error" not in r and [o["id"] for o in ws["w-s2"]["openings"]] == ["o-win2"] and near(ws["w-s2"]["openings"][0]["offset"], 1.0)
      and [o["id"] for o in ws["w-south"]["openings"]] == ["o-win1"] and not r["opening_conflicts"], "split %s %s" % (r, ws.get("w-s2")))
check("take_openings" not in ws["w-s2"], "take_openings not stored")
os.environ["WEINGAERTEN_HOME"] = HOME
shutil.rmtree(tmp)

print("smoke=OK" if not fails else "smoke=FAIL\n" + "\n".join(fails))
raise SystemExit(1 if fails else 0)
