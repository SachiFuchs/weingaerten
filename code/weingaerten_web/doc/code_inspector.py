"""Reads the source files for /techdoku: Python with `ast` (never imported), JS and scripts as text."""
import ast
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

JS_FUNCTION_RE = re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(")
JS_OBJECT_RE = re.compile(r"^(?:const|var|let)\s+([A-Z][\w$]*)\s*=\s*\(", re.M)
JS_RETURN_RE = re.compile(r"return\s*\{([\w$,\s:]+)\}\s*\}\)\(\)")
JS_LINE_START_RE = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?$")
NO_DESCRIPTION = "(keine Beschreibung)"


class CodeInspector:
    """Facts of modules, classes, JS files and scripts; cached per file by modification time."""

    def __init__(self) -> None:
        self._cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    def package(self, package_dir: str) -> List[Dict[str, Any]]:
        """Return one entry per Python module of a package, sorted by sub package and module name."""
        name = os.path.basename(package_dir)
        modules = []
        for folder, dirs, files in os.walk(package_dir):
            dirs[:] = sorted(d for d in dirs if not d.startswith(("__", ".")) and d not in ("static", "lib", "vendor"))
            for file in sorted(f for f in files if f.endswith(".py") and f != "__init__.py"):
                relative = os.path.relpath(os.path.join(folder, file), package_dir)
                parts = relative[:-3].replace(os.sep, "/").split("/")
                info = self._cached(os.path.join(folder, file), self._python)
                modules.append(dict(info, package=name, module=".".join(parts), path=os.path.join(folder, file),
                                    group=parts[0] if len(parts) > 1 else "", file=name + "/" + "/".join(parts) + ".py"))
        return sorted(modules, key=lambda m: (m["group"], m["module"]))

    def scripts(self, folder: str, extension: str) -> List[Dict[str, Any]]:
        """Return file, lines, description (and for JS functions/objects) of every file with that extension."""
        if not os.path.isdir(folder):
            return []
        reader = self._javascript if extension == ".js" else self._python
        return [dict(self._cached(os.path.join(folder, f), reader), file=f)
                for f in sorted(os.listdir(folder)) if f.endswith(extension)]

    def source(self, path: str) -> str:
        """Return the text of a file found by `package` (callers pass only paths from its entries)."""
        with open(path, encoding="utf-8", errors="replace") as handle:
            return handle.read()

    def _cached(self, path: str, reader: Any) -> Dict[str, Any]:
        stamp = os.path.getmtime(path)
        entry = self._cache.get(path)
        if entry is None or entry[0] != stamp:
            with open(path, encoding="utf-8", errors="replace") as handle:
                text = handle.read()
            entry = (stamp, reader(text))
            self._cache[path] = entry
        return entry[1]

    def _python(self, text: str) -> Dict[str, Any]:
        lines = text.count("\n") + 1
        try:
            tree = ast.parse(text)
        except SyntaxError as error:
            logger.warning("cannot parse: %s", error)
            return {"lines": lines, "doc": NO_DESCRIPTION, "doc_full": NO_DESCRIPTION, "classes": [], "constants": [],
                    "imports": [], "externals": [], "functions": []}
        classes = [self._class(node) for node in tree.body if isinstance(node, ast.ClassDef)]
        constants = [target.id for node in tree.body if isinstance(node, ast.Assign)
                     for target in node.targets if isinstance(target, ast.Name) and target.id.isupper()]
        functions = [{"name": node.name, "line": node.lineno, "signature": self._signature(node),
                      "doc": self._summary(ast.get_docstring(node))}
                     for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        return {"lines": lines, "doc": self._summary(ast.get_docstring(tree)),
                "doc_full": (ast.get_docstring(tree) or NO_DESCRIPTION).strip(), "classes": classes, "functions": functions,
                "constants": constants, "imports": self._imports(tree), "externals": self._externals(tree)}

    def _class(self, node: ast.ClassDef) -> Dict[str, Any]:
        methods, attributes = [], []
        for item in node.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if item.name == "__init__":
                attributes = self._attributes(item)
            if not item.name.startswith("_") or item.name == "__init__":
                methods.append({"name": item.name, "signature": self._signature(item),
                                "doc": self._summary(ast.get_docstring(item))})
        return {"name": node.name, "doc": self._summary(ast.get_docstring(node)),
                "bases": [ast.unparse(base) for base in node.bases], "methods": methods, "attributes": attributes}

    @staticmethod
    def _attributes(init: ast.FunctionDef) -> List[str]:
        names = []
        for node in ast.walk(init):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
            for target in targets:
                if (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self"
                        and not target.attr.startswith("_") and target.attr not in names):
                    names.append(target.attr)
        return names

    @staticmethod
    def _signature(function: ast.FunctionDef) -> str:
        arguments = ast.unparse(function.args)
        returns = " -> " + ast.unparse(function.returns) if function.returns else ""
        return "%s(%s)%s" % (function.name, arguments, returns)

    @staticmethod
    def _imports(tree: ast.Module) -> List[Tuple[int, str]]:
        # relative imports only: (level, module) – they are the dependencies inside the package
        return [(node.level, node.module or "") for node in tree.body
                if isinstance(node, ast.ImportFrom) and node.level > 0]

    @staticmethod
    def _externals(tree: ast.Module) -> List[str]:
        # top-level names of all absolute imports, also inside functions and try blocks (optional imports)
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
        return sorted(names)

    @staticmethod
    def _summary(doc: Optional[str]) -> str:
        if not doc:
            return NO_DESCRIPTION
        return " ".join(doc.strip().split("\n\n")[0].split())

    @staticmethod
    def _javascript(text: str) -> Dict[str, Any]:
        comment = []
        for line in text.lstrip("\n").split("\n"):
            if not line.startswith("//"):
                break
            comment.append(line[2:].strip())
        members = [m.split(":")[0].strip() for found in JS_RETURN_RE.findall(text) for m in found.split(",") if m.strip()]
        return {"lines": text.count("\n") + 1, "doc": " ".join(comment) or NO_DESCRIPTION,
                "functions": sorted(set(JS_FUNCTION_RE.findall(text))), "objects": JS_OBJECT_RE.findall(text),
                "members": members, "function_docs": CodeInspector._function_docs(text)}

    @staticmethod
    def _function_docs(text: str) -> List[Dict[str, Any]]:
        # description = the `//` lines directly above a function that starts its line; in source order
        lines = text.split("\n")
        found = []
        for match in JS_FUNCTION_RE.finditer(text):
            number = text.count("\n", 0, match.start()) + 1
            before = lines[number - 1][:match.start() - (text.rfind("\n", 0, match.start()) + 1)]
            comment: List[str] = []
            if JS_LINE_START_RE.match(before):
                index = number - 2
                while index >= 0 and lines[index].strip().startswith("//"):
                    comment.insert(0, lines[index].strip()[2:].strip())
                    index -= 1
            found.append({"name": match.group(1), "line": number, "doc": " ".join(comment) or NO_DESCRIPTION})
        return found
