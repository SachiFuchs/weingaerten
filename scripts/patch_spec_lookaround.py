from pathlib import Path
p = Path(r"C:\Development\weingaerten\weingaerten-web.md")
b = p.read_bytes()
old = "vorwärts/rückwärts (Strg + Rad) – Höhe".encode()
new = "vorwärts/rückwärts (Strg + Rad), umschauen (Alt + links ziehen) – Höhe".encode()
assert b.count(old) == 1, b.count(old)
p.write_bytes(b.replace(old, new))
h = Path(r"C:\Development\weingaerten\weingaerten-handbuch.md").read_bytes()
print("ok", h.count(b"\r\n"), h.count(b"\n"))
