"""One-off: point both specs from the %LOCALAPPDATA% cache to <project>\\code (dilbert-web stays)."""
import io

for path in (r"c:\Development\weingaerten\weingaerten-core.md", r"c:\Development\weingaerten\weingaerten-web.md"):
    text = io.open(path, encoding="utf-8", newline="").read()
    original = text
    text = text.replace("$env:LOCALAPPDATA\\non-code-cache\\weingaerten-", "$(Split-Path '<this prompt>')\\code\\weingaerten-")
    text = text.replace("%LOCALAPPDATA%\\non-code-cache\\weingaerten-", "<folder of this prompt>\\code\\weingaerten-")
    text = text.replace("*non-code-cache\\weingaerten-web\\weingaerten_web*", "*code\\weingaerten-web\\weingaerten_web*")
    io.open(path, "w", encoding="utf-8", newline="").write(text)
    print(path, "changed" if text != original else "unchanged", "remaining non-code-cache:", text.count("non-code-cache"))
