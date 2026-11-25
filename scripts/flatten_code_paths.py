"""One-off: flatten the code paths (code\\weingaerten-core\\weingaerten_core -> code\\weingaerten_core etc.) in specs, doku and start.cmd."""
import io

ROOT = "c:\\Development\\weingaerten\\"
REPLACEMENTS = [
    # code folder locations
    ("- Location: `<folder of this prompt>\\code\\weingaerten-core\\` (own folder – never shared with other prompts).",
     "- Location: `<folder of this prompt>\\code\\` – the package `weingaerten_core\\` is this prompt's own folder (never shared with other prompts); the hash goes to `code\\.hash\\`."),
    ("- Location: `<folder of this prompt>\\code\\weingaerten-web\\` (own folder – never shared with other prompts).",
     "- Location: `<folder of this prompt>\\code\\` – the package `weingaerten_web\\` (with `static\\` and `lib\\`) is this prompt's own folder (never shared with other prompts); the hash goes to `code\\.hash\\`."),
    # sys.path wording
    ("with `code\\weingaerten-core` on `sys.path`", "with the `code` folder on `sys.path`"),
    ("puts the `weingaerten-web` code folder on `sys.path`", "puts the `code` folder on `sys.path`"),
    ("(`weingaerten-core` folder put on `sys.path`,", "(`code` folder put on `sys.path`,"),
    # paths
    ("\\code\\weingaerten-core\\weingaerten_core", "\\code\\weingaerten_core"),
    ("\\code\\weingaerten-web\\weingaerten_web", "\\code\\weingaerten_web"),
    ("\\code\\weingaerten-core\\.hash\\", "\\code\\.hash\\"),
    ("\\code\\weingaerten-web\\.hash\\", "\\code\\.hash\\"),
    ("\\code\\weingaerten-web\\lib\\", "\\code\\weingaerten_web\\lib\\"),
    ("code\\weingaerten-web\\weingaerten_web", "code\\weingaerten_web"),
    ("code\\weingaerten-core\\weingaerten_core", "code\\weingaerten_core"),
    ("code\\weingaerten-web\\lib\\", "code\\weingaerten_web\\lib\\"),
    ("(`code\\weingaerten-core`, `code\\weingaerten-web`)", "(`code\\weingaerten_core`, `code\\weingaerten_web`)"),
    ("| `lib\\three.module.js`, `lib\\OrbitControls.js` |", "| `weingaerten_web\\lib\\three.module.js`, `weingaerten_web\\lib\\OrbitControls.js` |"),
]

for name in ("weingaerten-core.md", "weingaerten-web.md", "weingaerten-doku.md", "start.cmd"):
    path = ROOT + name
    text = io.open(path, encoding="utf-8", newline="").read()
    for old, new in REPLACEMENTS:
        if old in text:
            print("%-20s %2d x %s" % (name, text.count(old), old[:60]))
            text = text.replace(old, new)
    io.open(path, "w", encoding="utf-8", newline="").write(text)
    left = [line for line in text.splitlines() if "weingaerten-core\\" in line or "weingaerten-web\\" in line]
    for line in left:
        print("  LEFT:", line[:150])
