"""Print the connection-related VALIDATE issues of the real data (read-only): errors and warnings of tga-* and runs."""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.join(r"c:\Development\weingaerten", "code"))
os.environ["WEINGAERTEN_HOME"] = os.environ.get("WEINGAERTEN_SMOKE_HOME", r"c:\Development\weingaerten")
import weingaerten_core as c

v = json.loads(c.handle(json.dumps({"command": "VALIDATE"})))
print("ok", v["ok"], "errors", len(v["errors"]), "warnings", len(v["warnings"]))
for level in ("errors", "warnings"):
    rows = [i for i in v[level] if str(i.get("where", "")).startswith(("tga-", "catalog/tga"))]
    counts = collections.Counter(i["message"].split(":")[0][:60] for i in rows)
    print("\n== %s (tga): %d" % (level, len(rows)))
    for message, n in counts.most_common(40):
        print("%4d  %s" % (n, message))
    for i in rows[: (60 if "-v" in sys.argv else 15)]:
        print("   ", i["where"], "|", i["message"])
