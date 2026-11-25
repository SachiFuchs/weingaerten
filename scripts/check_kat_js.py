"""Extract the inline scripts of catalog pages and syntax-check them with node."""
import re, subprocess, tempfile, urllib.request, os

fails = 0
for p in ("/katalog/aufbauten", "/katalog/bauteile", "/katalog/dokumente"):
    t = urllib.request.urlopen("http://localhost:8008" + p, timeout=60).read().decode("utf-8")
    js = [s for s in re.findall(r"<script>(.*?)</script>", t, re.S) if "katdata" in s]
    f = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
    f.write(js[0]); f.close()
    r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
    print(p, "syntax ok" if r.returncode == 0 else r.stderr[:500])
    fails += r.returncode != 0
    os.unlink(f.name)
print("FAILED: %d" % fails if fails else "ALL OK")
raise SystemExit(1 if fails else 0)
