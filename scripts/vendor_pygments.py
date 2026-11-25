"""Vendor Pygments (Exception #4 of weingaerten-web.md): download the pinned wheel, check its SHA-256, unpack `pygments/`."""
import hashlib
import io
import os
import shutil
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, "code", "weingaerten_web", "vendor")
URL = ("https://files.pythonhosted.org/packages/f4/7e/a72dd26f3b0f4f2bf1dd8923c85f7ceb43172af56d63c7383eb62b332364/"
       "pygments-2.20.0-py3-none-any.whl")
SHA256 = "81a9e26dd42fd28a23a2d169d86d7ac03b46e2f8b59ed4698fb4785f946d0176"


def main() -> None:
    data = urllib.request.urlopen(URL, timeout=60).read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != SHA256:
        raise SystemExit("hash mismatch: %s" % digest)
    target = os.path.join(VENDOR, "pygments")
    shutil.rmtree(target, ignore_errors=True)
    root = os.path.realpath(VENDOR)
    with zipfile.ZipFile(io.BytesIO(data)) as wheel:
        for member in wheel.namelist():
            licence = member.endswith(".dist-info/licenses/LICENSE")
            if not (member.startswith("pygments/") or licence) or member.endswith("/"):
                continue
            name = "pygments-LICENSE" if licence else member
            path = os.path.realpath(os.path.join(VENDOR, name))
            # zip slip guard: every written file must stay inside vendor/
            if os.path.commonpath([root, path]) != root:
                raise SystemExit("unsafe entry: " + member)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as handle:
                handle.write(wheel.read(member))
    print("pygments 2.20.0 vendored to", target)


if __name__ == "__main__":
    main()
