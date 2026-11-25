"""Recompute the spec-section hashes of the core and web packages (after a code edit) and compile both."""
import compileall
import hashlib
import os
import re

ROOT = r"c:\Development\weingaerten"
CODE = os.path.join(ROOT, "code")
ITEMS = [("weingaerten-core.md", "Core specification", "weingaerten_core"),
         ("weingaerten-web.md", "Server specification", "weingaerten_web")]

for md, section, package in ITEMS:
    # same as the PowerShell check in the prompt: match on the raw text, then normalise line endings
    raw = open(os.path.join(ROOT, md), encoding="utf-8", newline="").read()
    match = re.search(r"(?s)\n## " + re.escape(section) + r".*?(?=\n## |\Z)", raw)
    digest = hashlib.sha256(match.group(0).replace("\r\n", "\n").encode("utf-8")).hexdigest()
    if not compileall.compile_dir(os.path.join(CODE, package), quiet=1):
        raise SystemExit("compile failed: " + package)
    os.makedirs(os.path.join(CODE, ".hash"), exist_ok=True)
    open(os.path.join(CODE, ".hash", package + ".sha256"), "w").write(digest)
    print(package, digest)
