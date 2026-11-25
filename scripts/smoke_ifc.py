"""IFC mapping checks of the core (schemas) on a temp copy of the project data."""
import importlib, json, os, shutil, sys, tempfile

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(SRC, "code", "weingaerten_core")

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


def element(ref):
    e = call(command="ELEMENT", ref=ref)
    for k in ("ref", "type", "file"):
        e.pop(k, None)
    return e


def save(ref, e):
    return call(command="SAVE", ref=ref, element=e, create=False)


v = call(command="VALIDATE")
check("VALIDATE without ifc errors", not [x for x in v["errors"] if "ifc" in x["where"] + x["message"]])
check("class window has ifc", element("class:window").get("ifc") == {"entity": "IfcWindow", "predefined_type": "WINDOW"})
check("assembly iw1 PARTITIONING", element("assembly:interior-wall-iw1")["ifc"]["predefined_type"] == "PARTITIONING")
check("component velux SKYLIGHT override", element("component:roof-window-velux-ck04")["ifc"]["predefined_type"] == "SKYLIGHT")

cases = [("class:door", {"entity": "IfcDoor", "predefined_type": "GATE"}, True),
         ("assembly:roof-r1", {"entity": "IfcCovering", "predefined_type": "USERDEFINED", "object_type": "Dachhaut"}, True),
         ("component:window-small", {"entity": "IfcWindow"}, True),
         ("class:door", {"entity": "Door"}, False),
         ("class:door", {"entity": "IfcDoor", "predefined_type": "door"}, False),
         ("assembly:roof-r1", {"predefined_type": "ROOF"}, False),
         ("component:window-small", {"entity": "IfcWindow", "colour": "red"}, False)]
for ref, ifc, valid in cases:
    e = element(ref)
    e["ifc"] = ifc
    r = save(ref, e)
    ok = not r.get("errors") and not r.get("error")
    check("SAVE %s ifc=%s %s" % (ref, ifc, "accepted" if valid else "rejected"), ok == valid)
    if ok:
        check("  stored", element(ref)["ifc"] == ifc)

e = element("class:door")
e.pop("ifc")
check("SAVE without ifc removes it", not save("class:door", e).get("errors") and "ifc" not in element("class:door"))

shutil.rmtree(tmp, ignore_errors=True)
print("FAILS:", fails if fails else "none")
sys.exit(1 if fails else 0)
