"""Capture core answers and page HTML for a byte-exact old/new comparison of the refactoring.

Usage: python refactor_baseline.py <old|new> <out_dir>
"""
import importlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile

SRC = r"c:\Development\weingaerten"
CACHE = os.path.join(r"c:\Development\weingaerten", "code")
MODE, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))


def load_core():
    if MODE == "old":
        spec = importlib.util.spec_from_file_location("core_old", os.path.join(HERE, "old_code", "weingaerten_core.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    sys.path.insert(0, CACHE)
    return importlib.import_module("weingaerten_core")


def fresh_home():
    tmp = tempfile.mkdtemp()
    for d in ("catalog", "house"):
        shutil.copytree(os.path.join(SRC, d), os.path.join(tmp, d))
    shutil.copy(os.path.join(SRC, "weingaerten-doku.md"), tmp)
    os.environ["WEINGAERTEN_HOME"] = tmp
    return tmp


def ask(core, **req):
    return core.handle(json.dumps(req))


def read_tree(home):
    out = {}
    for sub in ("catalog", "house"):
        for root, _, files in os.walk(os.path.join(home, sub)):
            for f in sorted(files):
                p = os.path.join(root, f)
                out[os.path.relpath(p, home)] = open(p, encoding="utf-8", newline="").read()
    return out


def read_only(core, res):
    fresh_home()
    res["invalid_json"] = core.handle("{x")
    res["unknown"] = ask(core, command="NOPE")
    for cmd in ("VALIDATE", "HOUSE", "BOM", "CATALOG"):
        res[cmd] = ask(core, command=cmd)
    for t in ("material", "assembly", "class", "component", "company"):
        res["CATALOG " + t] = ask(core, command="CATALOG", type=t)
    refs = [e["ref"] for e in json.loads(res["CATALOG"])["elements"]] + ["storey:ground", "material:nope"]
    for r in refs:
        for cmd in ("ELEMENT", "RESOLVE", "USAGE"):
            res["%s %s" % (cmd, r)] = ask(core, command=cmd, ref=r)
    res["RESOLVE noref"] = ask(core, command="RESOLVE")
    res["USAGE bad"] = ask(core, command="USAGE", ref="../x")


def storey(home):
    return json.load(open(os.path.join(home, "house", "storeys", "ground.json"), encoding="utf-8"))


def edits(core, res):
    scenarios = []
    home = fresh_home()
    mat = json.load(open(os.path.join(home, "catalog", "materials", "hollow-brick.json"), encoding="utf-8"))
    new_mat = dict(mat, id="test-mat", name="Test")
    scenarios += [("save update", dict(command="SAVE", ref="material:hollow-brick", element=mat, create=False)),
                  ("save create", dict(command="SAVE", ref="material:test-mat", element=new_mat, create=True)),
                  ("save dup", dict(command="SAVE", ref="material:test-mat", element=new_mat, create=True)),
                  ("save mismatch", dict(command="SAVE", ref="material:x", element=new_mat, create=True)),
                  ("save badref", dict(command="SAVE", ref="material:../x", element=new_mat, create=True)),
                  ("delete used", dict(command="DELETE", ref="material:hollow-brick")),
                  ("delete new", dict(command="DELETE", ref="material:test-mat")),
                  ("delete missing", dict(command="DELETE", ref="material:test-mat"))]
    cls = json.load(open(os.path.join(home, "catalog", "classes", "window.json"), encoding="utf-8"))
    bad_cls = json.loads(json.dumps(cls))
    for p in bad_cls.get("parameters", []):
        if p.get("key") == "width":
            p["min"], p["default"] = 2.0, 2.5
    scenarios.append(("save class bad", dict(command="SAVE", ref="class:window", element=bad_cls, create=False)))
    for f in sorted(os.listdir(os.path.join(home, "catalog", "companies"))):
        co = json.load(open(os.path.join(home, "catalog", "companies", f), encoding="utf-8"))
        scenarios.append(("save company noroles " + f, dict(command="SAVE", ref="company:" + co["id"], element=dict(co, roles=["supplier"]), create=False)))
        scenarios.append(("delete company " + f, dict(command="DELETE", ref="company:" + co["id"])))
    run(core, res, home, "catalog", scenarios)

    home = fresh_home()
    st = storey(home)
    flur = next(o for w in st["walls"] for o in w.get("openings", []) if o["id"] == "o-flur")
    moved = dict(flur, offset=flur["offset"] + 0.1)
    test = {"id": "o-test", "component": flur["component"], "offset": 5.5, "sill": 1.0}
    run(core, res, home, "openings", [
        ("update", dict(command="OPENING_SAVE", storey="ground", wall="w-north", opening=moved, create=False)),
        ("create", dict(command="OPENING_SAVE", storey="ground", wall="w-west-wz", opening=test, create=True)),
        ("create dup", dict(command="OPENING_SAVE", storey="ground", wall="w-west-wz", opening=test, create=True)),
        ("too far", dict(command="OPENING_SAVE", storey="ground", wall="w-west-wz", opening=dict(test, offset=7.5), create=False)),
        ("bad id", dict(command="OPENING_SAVE", storey="ground", wall="w-west-wz", opening=dict(test, id="X Y"), create=False)),
        ("delete", dict(command="OPENING_DELETE", storey="ground", wall="w-west-wz", id="o-test")),
        ("delete missing", dict(command="OPENING_DELETE", storey="ground", wall="w-west-wz", id="o-test")),
        ("unknown wall", dict(command="OPENING_DELETE", storey="ground", wall="w-x", id="o-test")),
        ("unknown storey", dict(command="OPENING_DELETE", storey="x", wall="w-x", id="o-test"))])

    home = fresh_home()
    st = storey(home)
    walls = {w["id"]: w for w in st["walls"]}
    north = dict(walls["w-north"], start=[0.9, 0])
    north.pop("openings", None)
    west = dict(walls["w-west-eingang"], end=[0.9, 0], start=[0.9, 2.08])
    west.pop("openings", None)
    diag = dict(walls["w-north"], end=[7.12, 1])
    split_a = dict(walls["w-south-wz"], end=[2.0, 9.94])
    split_b = dict(walls["w-south-wz"], id="w-s2", start=[2.0, 9.94], end=[0, 9.94], take_openings=["o-terrassenfenster"])
    for w in (diag, split_a, split_b):
        w.pop("openings", None)
    run(core, res, home, "walls", [
        ("diagonal", dict(command="WALLS_SAVE", storey="ground", upsert=[diag])),
        ("move", dict(command="WALLS_SAVE", storey="ground", upsert=[north])),
        ("height", dict(command="WALLS_SAVE", storey="ground", height=2.0)),
        ("height back", dict(command="WALLS_SAVE", storey="ground", height=2.75)),
        ("height bad", dict(command="WALLS_SAVE", storey="ground", height=-1)),
        ("split", dict(command="WALLS_SAVE", storey="ground", upsert=[split_a, split_b])),
        ("rooms", dict(command="WALLS_SAVE", storey="ground", rooms={"upsert": [dict(st["rooms"][0], name="X")], "delete": ["room-bad"]})),
        ("delete wall", dict(command="WALLS_SAVE", storey="ground", delete=["iw-wz-z2"])),
        ("bad wall id", dict(command="WALLS_SAVE", storey="ground", upsert=[dict(north, id="A B")]))])
    del west


def run(core, res, home, group, scenarios):
    for name, req in scenarios:
        res["%s/%s" % (group, name)] = ask(core, **req)
        res["%s/%s VALIDATE" % (group, name)] = ask(core, command="VALIDATE")
    res["%s/files" % group] = json.dumps(read_tree(home), ensure_ascii=False)
    res["%s/HOUSE" % group] = ask(core, command="HOUSE")
    res["%s/BOM" % group] = ask(core, command="BOM")


def pages(res):
    fresh_home()
    if MODE == "old":
        spec = importlib.util.spec_from_file_location("web_old", os.path.join(HERE, "old_code", "web_server.py"))
        web = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(web)
        for path, fn in web.PAGES.items():
            res["PAGE " + path] = fn().replace(web.STARTED, "<started>")
        res["PAGE 404"] = web.page("404", "", "<h1>404</h1><p>Seite nicht gefunden.</p>")
        res["PAGE roundel"] = web.ROUNDEL
        return
    sys.path.insert(0, CACHE)
    app_mod = importlib.import_module("weingaerten_web.web_application")
    app = app_mod.WebApplication(app_mod.ServerSettings.from_arguments([]))
    for path in app.pages.paths():
        res["PAGE " + path] = app.pages.render(path).replace(app.settings.started, "<started>")
    res["PAGE 404"] = app.pages.render_not_found()
    res["PAGE roundel"] = app.assets.text("roundel.svg")


def main():
    core = load_core()
    res = {}
    read_only(core, res)
    edits(core, res)
    try:
        pages(res)
    except ModuleNotFoundError as error:
        print("pages skipped:", error)
    os.makedirs(OUT, exist_ok=True)
    for k, v in res.items():
        v = v.replace(os.environ["WEINGAERTEN_HOME"], "<home>")
        name = "".join(c if c.isalnum() or c in "-_." else "_" for c in k)
        open(os.path.join(OUT, name + ".txt"), "w", encoding="utf-8", newline="").write(v)
    print(len(res), "results written to", OUT)


main()
