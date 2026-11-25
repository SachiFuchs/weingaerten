"""Check that CATALOG full / USAGE all give the same answers as the per-element ELEMENT / USAGE calls, and time them."""
import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.environ.setdefault("WEINGAERTEN_HOME", str(ROOT))
sys.path.insert(0, str(ROOT / "code"))
import weingaerten_core  # noqa: E402


def ask(command, **arguments):
    arguments["command"] = command
    return json.loads(weingaerten_core.handle(json.dumps(arguments)))


def main():
    t = time.time()
    old_elements = {e["ref"]: ask("ELEMENT", ref=e["ref"]) for e in ask("CATALOG")["elements"]}
    old_usage = {ref: ask("USAGE", ref=ref)["used_by"] for ref in old_elements}
    t_old = time.time() - t
    t = time.time()
    new_elements = {e["ref"]: e for e in ask("CATALOG", full=True)["elements"]}
    new_usage = ask("USAGE", all=True)["usage"]
    t_new = time.time() - t
    diff = [r for r in old_elements if old_elements[r] != new_elements.get(r)]
    diff += [r for r in old_usage if old_usage[r] != new_usage.get(r, [])]
    print("%d Elemente, alt %.1f s, neu %.2f s, Abweichungen: %s" % (len(old_elements), t_old, t_new, diff or "keine"))
    sys.exit(1 if diff or set(old_elements) != set(new_elements) else 0)


if __name__ == "__main__":
    main()
