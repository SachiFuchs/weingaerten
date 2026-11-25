"""Print core VALIDATE result for the real data (read-only)."""
import json
import os
import sys

sys.path.insert(0, os.path.join(r"c:\Development\weingaerten", "code"))
os.environ["WEINGAERTEN_HOME"] = os.environ.get("WEINGAERTEN_SMOKE_HOME", r"c:\Development\weingaerten")
import weingaerten_core as c

v = json.loads(c.handle(json.dumps({"command": "VALIDATE"})))
print(json.dumps({k: v[k] for k in ("ok", "errors", "warnings", "counts")}, ensure_ascii=False, indent=1))
