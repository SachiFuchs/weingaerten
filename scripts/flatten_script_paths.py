"""One-off: point the helper scripts to the flat code folder (code\\weingaerten_core, code\\weingaerten_web)."""
import glob
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPLACEMENTS = [
    ('"code", "weingaerten-core", "weingaerten_core")', '"code", "weingaerten_core")'),
    ('"code", "weingaerten-core")', '"code")'),
    ('"code", "weingaerten-web", "weingaerten_web", "static")', '"code", "weingaerten_web", "static")'),
    ('os.path.join(CACHE, "weingaerten-core", "weingaerten_core")', 'os.path.join(CACHE, "weingaerten_core")'),
    ('os.path.join(CACHE, "weingaerten-web", "weingaerten_web")', 'os.path.join(CACHE, "weingaerten_web")'),
    # baseline: the old code now lives in scripts/old_code, the new packages directly in code\
    ('os.path.join(CACHE, "weingaerten-core", "weingaerten_core.py")', 'os.path.join(HERE, "old_code", "weingaerten_core.py")'),
    ('os.path.join(CACHE, "weingaerten-web", "web_server.py")', 'os.path.join(HERE, "old_code", "web_server.py")'),
    ('sys.path.insert(0, os.path.join(CACHE, "weingaerten-core"))', 'sys.path.insert(0, CACHE)'),
    ('sys.path.insert(0, os.path.join(CACHE, "weingaerten-web"))', 'sys.path.insert(0, CACHE)'),
    ('MODE, OUT = sys.argv[1], sys.argv[2]', 'MODE, OUT = sys.argv[1], sys.argv[2]\nHERE = os.path.dirname(os.path.abspath(__file__))'),
]

for path in sorted(glob.glob(os.path.join(HERE, "*.py"))):
    if os.path.basename(path).startswith(("move_", "flatten_")):
        continue
    text = io.open(path, encoding="utf-8", newline="").read()
    original = text
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    if text != original:
        io.open(path, "w", encoding="utf-8", newline="").write(text)
        print("updated", os.path.basename(path))
