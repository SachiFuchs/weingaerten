"""Sandbox for scenario tests: a temporary WEINGAERTEN_HOME built from a fixture house plus a COPY of the real catalog.

Usage in a test:
    from sandbox import Sandbox
    with Sandbox() as sb:
        h = sb.q("HOUSE")
        sb.edit_storey("ground", lambda d: ...)

Neither the original house nor the fixture is ever written.  The catalog elements the fixture uses (transitively)
are fingerprinted; when the user changes one of them the tests stop with a clear message instead of wrong numbers.
    python scripts/sandbox.py            -> check the fingerprint
    python scripts/sandbox.py --accept   -> accept the current catalog state (after checking the new values!)
"""
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from typing import Any, Callable, Dict, List, Set

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(SCRIPTS)
FIXTURES = os.path.join(PROJECT, "tests", "fixtures")
CATALOG = os.path.join(PROJECT, "catalog")
SKIP_CATALOG = ("imported_", "photos")
REF_RE = re.compile(r'"(material|assembly|assembly-class|class|component|company|document):([a-z0-9][a-z0-9-]*)"')
FOLDERS = {"material": "materials", "assembly": "assemblies", "assembly-class": "assembly-classes", "class": "classes",
           "component": "components", "company": "companies", "document": "documents"}
FOLLOW = {"material", "assembly", "assembly-class", "class", "component"}

sys.path.insert(0, os.path.join(PROJECT, "code"))


class CatalogFingerprint:
    """Hashes of the catalog files a fixture uses, followed through material/assembly/class/component refs."""

    def __init__(self, fixture: str) -> None:
        self._fixture = fixture
        self._file = os.path.join(FIXTURES, fixture, "catalog_fingerprint.json")

    @staticmethod
    def _refs(text: str) -> Set[str]:
        return {"%s:%s" % m for m in REF_RE.findall(text)}

    def used(self) -> Dict[str, str]:
        """Return {ref: sha256} of all catalog files reachable from the fixture house."""
        todo: Set[str] = set()
        for root, _, files in os.walk(os.path.join(FIXTURES, self._fixture, "house")):
            for name in files:
                with open(os.path.join(root, name), encoding="utf-8") as handle:
                    todo |= self._refs(handle.read())
        seen: Dict[str, str] = {}
        while todo:
            ref = todo.pop()
            if ref in seen:
                continue
            kind, ident = ref.split(":", 1)
            path = os.path.join(CATALOG, FOLDERS[kind], ident + ".json")
            if not os.path.isfile(path):
                seen[ref] = "fehlt"
                continue
            with open(path, "rb") as handle:
                data = handle.read()
            seen[ref] = hashlib.sha256(data).hexdigest()
            if kind in FOLLOW:
                todo |= self._refs(data.decode("utf-8")) - set(seen)
        return dict(sorted(seen.items()))

    def changed(self) -> List[str]:
        """Return the refs whose file differs from the accepted state (empty = unchanged)."""
        if not os.path.isfile(self._file):
            return ["(kein Fingerprint – python scripts/sandbox.py --accept)"]
        with open(self._file, encoding="utf-8") as handle:
            accepted = json.load(handle)
        now = self.used()
        return sorted(r for r in set(now) | set(accepted) if now.get(r) != accepted.get(r))

    def accept(self) -> int:
        """Store the current state and return the number of refs."""
        now = self.used()
        with open(self._file, "w", encoding="utf-8") as handle:
            json.dump(now, handle, indent=1)
        return len(now)


class Sandbox:
    """Temporary WEINGAERTEN_HOME = fixture house + catalog copy; the core is called in-process."""

    def __init__(self, fixture: str = "testhaus", check_catalog: bool = True) -> None:
        self.fixture = fixture
        self._check = check_catalog
        self.home = ""
        self._old_home = None

    def __enter__(self) -> "Sandbox":
        if self._check:
            changed = CatalogFingerprint(self.fixture).changed()
            if changed:
                raise SystemExit("Katalog geändert, Sollwerte prüfen und dann 'python scripts/sandbox.py --accept': "
                                 + ", ".join(changed))
        self.home = tempfile.mkdtemp(prefix="wg-sandbox-")
        shutil.copytree(os.path.join(FIXTURES, self.fixture, "house"), os.path.join(self.home, "house"))
        shutil.copytree(CATALOG, os.path.join(self.home, "catalog"),
                        ignore=lambda d, names: [n for n in names if d == CATALOG and n.startswith(SKIP_CATALOG)])
        self._old_home = os.environ.get("WEINGAERTEN_HOME")
        os.environ["WEINGAERTEN_HOME"] = self.home
        return self

    def __exit__(self, *exc: Any) -> None:
        if self._old_home is None:
            os.environ.pop("WEINGAERTEN_HOME", None)
        else:
            os.environ["WEINGAERTEN_HOME"] = self._old_home
        shutil.rmtree(self.home, ignore_errors=True)

    @staticmethod
    def q(command: str, **kw: Any) -> Dict[str, Any]:
        """Run one core command in the sandbox and return the decoded answer."""
        import weingaerten_core
        kw["command"] = command
        return json.loads(weingaerten_core.handle(json.dumps(kw)))

    def path(self, *parts: str) -> str:
        return os.path.join(self.home, *parts)

    def read(self, *parts: str) -> Any:
        with open(self.path(*parts), encoding="utf-8") as handle:
            return json.load(handle)

    def write(self, data: Any, *parts: str) -> None:
        with open(self.path(*parts), "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=1)

    def edit_storey(self, storey: str, fn: Callable[[Dict[str, Any]], None]) -> None:
        """Change a storey file in place: fn gets the storey dict."""
        data = self.read("house", "storeys", storey + ".json")
        fn(data)
        self.write(data, "house", "storeys", storey + ".json")


class Checks:
    """Collects failed checks; finish() prints the summary line and exits."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.fails: List[str] = []
        self.count = 0

    def ok(self, cond: Any, msg: str) -> bool:
        self.count += 1
        if not cond:
            self.fails.append(msg)
        return bool(cond)

    def near(self, value: Any, want: float, msg: str, tol: float = 0.001) -> bool:
        good = isinstance(value, (int, float)) and abs(value - want) <= tol
        return self.ok(good, "%s: %s statt %s" % (msg, value, want))

    def finish(self) -> None:
        if self.fails:
            print("\n".join(self.fails))
            print("%s=FAIL %d/%d" % (self.name, len(self.fails), self.count))
            raise SystemExit(1)
        print("%s=OK %d Prüfungen" % (self.name, self.count))
        raise SystemExit(0)


def main() -> int:
    fp = CatalogFingerprint(sys.argv[2] if len(sys.argv) > 2 else "testhaus")
    if "--accept" in sys.argv:
        print("Fingerprint gespeichert: %d Katalog-Elemente" % fp.accept())
        return 0
    changed = fp.changed()
    print("Katalog unverändert" if not changed else "geändert: " + ", ".join(changed))
    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
