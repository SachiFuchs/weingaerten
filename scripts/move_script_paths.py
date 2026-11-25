"""One-off: point the helper scripts from the %LOCALAPPDATA% cache to <project>\\code."""
import glob
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OLD = 'os.path.join(os.environ["LOCALAPPDATA"], "non-code-cache"'
NEW = 'os.path.join(r"c:\\Development\\weingaerten", "code"'

for path in sorted(glob.glob(os.path.join(HERE, "*.py"))):
    if os.path.basename(path) in ("move_code_paths.py", "move_script_paths.py"):
        continue
    text = io.open(path, encoding="utf-8", newline="").read()
    if OLD in text:
        io.open(path, "w", encoding="utf-8", newline="").write(text.replace(OLD, NEW))
        print("updated", os.path.basename(path))
