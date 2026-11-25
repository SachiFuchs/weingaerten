"""Syntax-check the module script of /haus3d with node (read-only against the running server)."""
import os
import re
import subprocess
import tempfile
import urllib.request

html = urllib.request.urlopen("http://localhost:8008/haus3d", timeout=120).read().decode("utf-8")
scripts = re.findall(r'<script type="module">(.*?)</script>', html, re.S)
print("module scripts:", len(scripts), "decke3d" in html)
fails = 0 if scripts else 1
for i, s in enumerate(scripts):
    s = re.sub(r"^\s*import .*?;\s*$", "", s, flags=re.M)
    p = os.path.join(tempfile.gettempdir(), "haus3d_%d.mjs" % i)
    open(p, "w", encoding="utf-8").write(s)
    r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
    print(i, "syntax ok" if r.returncode == 0 else r.stderr[:800])
    fails += r.returncode != 0
print("FAILED: %d" % fails if fails else "ALL OK")
raise SystemExit(1 if fails else 0)
