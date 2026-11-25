"""Checks the documents catalog (catalog/documents) through the core and, if running, the web page.

- 75 documents, all of object weingaerten-8, VALIDATE without errors and without `Belegsumme weicht ab`
- every supplier is a company with role supplier, every item ref / related / offer document resolves
- SAVE and DELETE of a document are refused (read-only type)
- USAGE of schuck-dach and of the VELUX CK04 window lists the Schuck invoice 1783
- web (optional, http://localhost:8008): /katalog/dokumente 200 with KatDocs and without katnew

Usage: python scripts/check_documents.py
"""
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["WEINGAERTEN_HOME"] = ROOT
import weingaerten_core as core  # noqa: E402

failures = []


def ask(command, **args):
    return json.loads(core.handle(json.dumps(dict(command=command, **args))))


def check(ok, text):
    print(("ok   " if ok else "FAIL ") + text)
    if not ok:
        failures.append(text)


validate = ask("VALIDATE")
# other parts of the model may be invalid while they are edited; only document-related errors count here
related = [e for e in validate["errors"] if "document" in e["where"] + e["message"]]
check(not related, "no document-related errors %s (model errors overall: %d)" % (related[:3], len(validate["errors"])))
check(validate["counts"].get("documents") == 75, "75 documents (%s)" % validate["counts"].get("documents"))
sums = [w for w in validate["warnings"] if "Belegsumme" in w["message"]]
check(not sums, "no sum warnings %s" % sums[:3])
doc_errors = [e for e in validate["errors"] if e["where"].startswith("document:")]
check(not doc_errors, "no document errors %s" % doc_errors[:3])

elements = {e["ref"]: e for e in ask("CATALOG", full=True)["elements"]}
docs = {r: e for r, e in elements.items() if r.startswith("document:")}
check(all(d.get("object") == "weingaerten-8" for d in docs.values()), "all documents of weingaerten-8")
check(all("supplier" in elements.get(d["supplier"], {}).get("roles", []) for d in docs.values()),
      "every supplier has role supplier")
refs = [i["ref"] for d in docs.values() for i in d["items"] if i.get("ref")]
tga_ids = {f[:-5] for f in os.listdir(os.path.join(ROOT, "catalog", "tga-components"))}
check(refs and all(r in elements or (r.startswith("tga-component:") and r[14:] in tga_ids) for r in refs),
      "%d item refs resolve" % len(refs))
offers = [o["document"] for e in elements.values() for o in (e.get("product") or {}).get("offers") or []
          if o.get("document")]
check(offers and all(r in docs for r in offers), "%d offer documents resolve" % len(offers))

invoice = "document:2023-07-17-schuck-1783-schlussrechnung-dach"
doc = {"id": invoice.split(":")[1], "name": "x"}
check("error" in ask("SAVE", ref=invoice, element=doc), "SAVE of a document refused")
check("error" in ask("DELETE", ref=invoice), "DELETE of a document refused")
usage = ask("USAGE", all=True)["usage"]
check(invoice in usage.get("company:schuck-dach", []), "schuck-dach used by invoice 1783")
check(invoice in usage.get("component:roof-window-velux-ck04", []), "VELUX CK04 used by invoice 1783")

try:
    html = urllib.request.urlopen("http://localhost:8008/katalog/dokumente", timeout=60).read().decode("utf-8")
    check("Katalog – Dokumente" in html and "KatDocs" in html and 'id="katnew"' not in html
          and "<textarea" not in html, "web /katalog/dokumente")
except OSError as exc:
    print("skip web (%s)" % exc)

print("FAILED: %d" % len(failures) if failures else "all checks passed")
sys.exit(1 if failures else 0)
