"""Time core calls as the catalog page does them (read-only)."""
import importlib, json, os, sys, time

os.environ.setdefault("WEINGAERTEN_HOME", r"c:\Development\weingaerten")
sys.path.insert(0, os.path.join(r"c:\Development\weingaerten", "code"))
core = importlib.import_module("weingaerten_core")
from weingaerten_core.model.model_loader import ModelLoader
q = lambda **kw: json.loads(core.handle(json.dumps(kw)))
t = time.time(); q(command="VALIDATE"); print("first load %.2fs" % (time.time() - t))
t = time.time(); [ModelLoader.file_signature(os.environ["WEINGAERTEN_HOME"]) for _ in range(20)]; print("scan %.3fs" % ((time.time() - t) / 20))
els = q(command="CATALOG")["elements"]
t = time.time()
for e in els:
    q(command="ELEMENT", ref=e["ref"]); q(command="USAGE", ref=e["ref"])
print("%d elements, ELEMENT+USAGE %.2fs" % (len(els), time.time() - t))
