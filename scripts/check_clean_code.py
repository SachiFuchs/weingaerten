"""Check the clean-code rules of skills/clean-code.instructions.md on the generated packages.

Checks: file <= 256 lines, function <= 80 lines, module docstring, module logger, one top-level class
per module, docstrings on classes and public functions/methods, type hints (args + return).
"""
import ast
import os
import sys

CACHE = os.path.join(r"c:\Development\weingaerten", "code")
PACKAGES = [os.path.join(CACHE, "weingaerten_core"),
            os.path.join(CACHE, "weingaerten_web")]
problems, files, functions = [], 0, 0


def report(path, line, text):
    problems.append("%s:%s %s" % (os.path.relpath(path, CACHE), line, text))


def check_function(path, node, owner):
    global functions
    functions += 1
    length = node.end_lineno - node.lineno + 1
    if length > 80:
        report(path, node.lineno, "function %s has %d lines" % (node.name, length))
    public = not node.name.startswith("_") or node.name in ("__init__",)
    if public and not node.name == "__init__" and ast.get_docstring(node) is None:
        report(path, node.lineno, "missing docstring: %s.%s" % (owner, node.name))
    args = node.args.args + node.args.kwonlyargs + node.args.posonlyargs
    for arg in args:
        if arg.arg not in ("self", "cls") and arg.annotation is None:
            report(path, node.lineno, "untyped argument %s of %s" % (arg.arg, node.name))
    for extra in (node.args.vararg, node.args.kwarg):
        if extra is not None and extra.annotation is None:
            report(path, node.lineno, "untyped *%s of %s" % (extra.arg, node.name))
    if node.returns is None:
        report(path, node.lineno, "missing return type: %s" % node.name)
    for child in ast.walk(node):
        if child is not node and isinstance(child, (ast.FunctionDef, ast.ClassDef)) and isinstance(child, ast.ClassDef):
            report(path, child.lineno, "nested class %s" % child.name)


for package in PACKAGES:
    for root, dirs, names in os.walk(package):
        # vendored third-party code (Exception #4) is not ours to check
        dirs[:] = [d for d in dirs if d != "vendor"]
        for name in sorted(names):
            if not name.endswith(".py"):
                continue
            files += 1
            path = os.path.join(root, name)
            source = open(path, encoding="utf-8").read()
            lines = source.count("\n") + (0 if source.endswith("\n") else 1)
            if lines > 256:
                report(path, 1, "file has %d lines" % lines)
            tree = ast.parse(source)
            if ast.get_docstring(tree) is None:
                report(path, 1, "missing module docstring")
            if name != "__init__.py" and "logging.getLogger(" not in source:
                report(path, 1, "no module logger")
            classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
            if len(classes) > 1:
                report(path, 1, "%d classes in one module" % len(classes))
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    check_function(path, node, "<module>")
                if isinstance(node, ast.ClassDef):
                    if ast.get_docstring(node) is None:
                        report(path, node.lineno, "missing class docstring: %s" % node.name)
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            check_function(path, item, node.name)

print("%d files, %d functions checked" % (files, functions))
print("\n".join(problems) if problems else "no problems")
sys.exit(1 if problems else 0)
