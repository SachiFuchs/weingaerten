"""Scenario test web (Testhaus): starts its own server on a sandbox HOME (port 8019), loads the main pages and checks that the
test-house data shows up; the real server (8008) and the training server (8009) are not touched."""
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

from sandbox import PROJECT, Checks, Sandbox

T = Checks("scen_web")
PORT = 8019
BASE = "http://localhost:%d" % PORT
PAGES = {"/about": "", "/haus3d": "", "/grundriss": "w-north", "/waende": "iw-mitte", "/raeume": "Raum Süd (L)",
         "/mengen": "Dachfenster", "/katalog/aufbauten": "exterior-wall-ew1"}


def get(path, timeout=120):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as response:
        return response.status, response.read().decode("utf-8", errors="replace")


def wait_up(seconds=60):
    end = time.time() + seconds
    while time.time() < end:
        try:
            return get("/about", 5)[0] == 200
        except (urllib.error.URLError, OSError):
            time.sleep(0.5)
    return False


with Sandbox() as sb:
    env = dict(os.environ, WEINGAERTEN_HOME=sb.home, PYTHONIOENCODING="utf-8")
    server = subprocess.Popen([sys.executable, os.path.join(PROJECT, "code", "weingaerten_web"), str(PORT)], env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if T.ok(wait_up(), "Testserver auf %d gestartet" % PORT):
            for path, needle in PAGES.items():
                try:
                    status, body = get(path)
                except (urllib.error.URLError, OSError) as exc:
                    T.ok(False, "%s: %s" % (path, exc))
                    continue
                T.ok(status == 200, "%s Status %s" % (path, status))
                if needle:
                    T.ok(needle in body, "%s zeigt '%s'" % (path, needle))
            T.ok("Weingärten 8" not in get("/haus3d")[1], "Testserver zeigt nicht das echte Haus")
    finally:
        server.terminate()
        try:
            server.wait(10)
        except subprocess.TimeoutExpired:
            server.kill()

T.finish()
