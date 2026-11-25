"""Read-only checks of the product/company web features against the running server."""
import json, os, re, subprocess, tempfile, urllib.request

B = "http://127.0.0.1:8008"


def get(p):
    with urllib.request.urlopen(B + p, timeout=90) as r:
        return r.read().decode("utf-8")


ok = True
f = get("/katalog/firmen")
for s in ("+ Firma", "katdata", "Firmen"):
    if s not in f:
        print("FAIL firmen missing", s); ok = False
if "<textarea" in f:
    print("FAIL textarea"); ok = False
m = get("/mengen")
for s in ("Stückpreis", "Bauteile Preis", "Hersteller", "€"):
    if s not in m:
        print("FAIL mengen missing", s); ok = False
b = get("/katalog/bauteile")
scripts = re.findall(r"<script>(.*?)</script>", b, re.S)
js = max(scripts, key=len)
tmp = os.path.join(tempfile.gettempdir(), "kat_check.js")
open(tmp, "w", encoding="utf-8").write(js)
try:
    r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True)
    print("node --check:", "OK" if r.returncode == 0 else r.stderr[:800])
    ok = ok and r.returncode == 0
except FileNotFoundError:
    print("node not installed - JS syntax not checked")
os.remove(tmp)
print("ALL OK" if ok else "FAILED")
raise SystemExit(0 if ok else 1)
