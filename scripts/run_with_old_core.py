"""Run a script with the OLD single-file core (scripts/old_code) registered as `weingaerten_core`.

Usage: python run_with_old_core.py <script.py>
"""
import importlib.util
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("weingaerten_core", os.path.join(HERE, "old_code", "weingaerten_core.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.modules["weingaerten_core"] = module
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
