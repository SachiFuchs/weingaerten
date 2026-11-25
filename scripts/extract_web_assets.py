"""Extract the static assets of the old web_server.py byte-exactly into the new package's static folder."""
import ast
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OLD = os.path.join(HERE, "old_code", "web_server.py")
TARGET = os.path.join(r"c:\Development\weingaerten", "code", "weingaerten_web", "static")

spec = importlib.util.spec_from_file_location("web_old", OLD)
web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(web)

files = {"style.css": web.CSS, "tip.js": web.TIP_JS, "haus3d.js": web.JS3D, "hatch_defs.svg": web.HATCH_DEFS,
         "plan.js": web.PLAN_JS, "common.js": web.COMMON_JS, "front.js": web.FRONT_JS, "katalog.js": web.KAT_JS,
         "wand.js": web.WAND_JS, "roundel.svg": web.ROUNDEL}

tree = ast.parse(open(OLD, encoding="utf-8").read())
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "page":
        ret = [n for n in node.body if isinstance(n, ast.Return)][0]
        files["page.html"] = ret.value.left.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Constant) \
            and isinstance(node.left.value, str) and node.left.value.startswith("<script>%s\ndocument.querySelectorAll('polygon.layer"):
        literal = node.left.value
        assert literal.count("%") == 1 and literal.endswith("</script>")
        files["plan_tooltips.js"] = literal[len("<script>%s\n"):-len("</script>")]

assert files["page.html"].count("%s") == 7 and files["page.html"].count("%") == 7
os.makedirs(TARGET, exist_ok=True)
for name, text in files.items():
    with open(os.path.join(TARGET, name), "w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    print("%-18s %6d chars" % (name, len(text)))
