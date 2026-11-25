"""Compare two result folders of refactor_baseline.py file by file; print the differences."""
import os
import sys

OLD, NEW = sys.argv[1], sys.argv[2]
old_files, new_files = set(os.listdir(OLD)), set(os.listdir(NEW))
differences = 0
for name in sorted(old_files | new_files):
    if name not in new_files or name not in old_files:
        print("only in", "old" if name in old_files else "new", name)
        differences += 1
        continue
    a = open(os.path.join(OLD, name), encoding="utf-8", newline="").read()
    b = open(os.path.join(NEW, name), encoding="utf-8", newline="").read()
    if a != b:
        differences += 1
        i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
        print("DIFF", name, "at", i)
        print("  old:", a[max(0, i - 120):i + 120])
        print("  new:", b[max(0, i - 120):i + 120])
print("compared", len(old_files & new_files), "files,", differences, "differences")
sys.exit(1 if differences else 0)
