"""Render one web page in-process and print the time (diagnosis of slow pages); stack dump after 60 s.

Usage: python scripts/time_page.py /grundriss
"""
import faulthandler
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "code"))
os.environ["WEINGAERTEN_HOME"] = ROOT
from weingaerten_web.web_application import ServerSettings, WebApplication  # noqa: E402

faulthandler.dump_traceback_later(60, exit=True)
app = WebApplication(ServerSettings.from_arguments(["8099"]))
for path in sys.argv[1:] or ["/grundriss"]:
    start = time.time()
    html = app.pages.render(path, {})
    print(path, round(time.time() - start, 1), "s", len(html))
