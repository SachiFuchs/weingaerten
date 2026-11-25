"""One-off: switches the Böhringer 25-0023 item refs in import_documents.py from tga-component to material and
cuts out the NEW_TGA block of those parts (replaced by HEATING_MATERIALS). Idempotent."""
import pathlib

P = pathlib.Path(__file__).resolve().parent / "import_documents.py"
t = P.read_text(encoding="utf-8")
a = t.index("    # Böhringer Angebot 25-0023, all positions")
b = t.index("    (r\"^Bosch Luftwärmepumpen")
refs = t[a:b].replace("\"tga-component:", "\"material:").replace(
    "\"material:pipe-bekotec-14\"", "\"material:schlueter-bekotec-therm-hr-14x2\"")
t = t[:a] + refs + t[b:]
marker = "# Böhringer Angebot 25-0023 (heat pump plant"
if marker in t:
    c, d = t.index(marker), t.index("def load(p):")
    t = t[:c] + "#HEATING_BLOCK\n\n\n" + t[d:]
P.write_text(t, encoding="utf-8")
print("refs:", refs.count("material:"))
