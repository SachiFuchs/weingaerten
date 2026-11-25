"""Profile the catalog page rendering in-process (read-only, no server)."""
import cProfile, importlib.util, os, pstats, time

os.environ.setdefault("WEINGAERTEN_HOME", r"c:\Development\weingaerten")
C = os.path.join(r"c:\Development\weingaerten", "code")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


web = load("web", os.path.join(C, "weingaerten-web", "web_server.py"))
web.core = load("core", os.path.join(C, "weingaerten-core", "weingaerten_core.py"))
web.p_kat("firmen")
t = time.time()
pr = cProfile.Profile()
pr.enable()
web.p_kat("firmen")
pr.disable()
print("p_kat %.2fs" % (time.time() - t))
pstats.Stats(pr).sort_stats("cumulative").print_stats(12)
