"""One-off: documents the TGA catalog tabs, the Darstellungs-Editor, port angle and folder filters (bytes, EOL kept).

python scripts/patch_spec_tga_draw.py [--write]
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CORE_ADD = (
    " Port `angle` right | any (`PartPorts.angle_of`: own value, else `any` for line power or ports with `cores`, else "
    "`right`); `seated` skips the opposite-direction test if one port is `any`. `install.layout.shapes[]` "
    "`{kind rect|circle|line|text, x, y, w, h, r, x2, y2, text, size, stroke, fill}` (local m, palette row `layout`). "
    "`cut.default_length` is required; errors `cut: Vorgabelänge größer als max. Länge`, `cut: Mindestlänge größer als "
    "Vorgabelänge`, `install.ports: id doppelt`, `install.ports <id>: Richtung ist kein Einheitsvektor` "
    "(`TgaTreeValidator.install_errors`). Tree folders may have `filter {class, query, abstract}` (only on folders, class "
    "must exist) = default filter of the object picker in the editor, inherited by sub-folders "
    "(`scripts/add_tree_filters.py`). Test `scripts/smoke_tga_draw.py`.")
WEB_ADD = (
    " Tabs `kattabs` `Liste` | `Baum` above `katgrid` (localStorage `weingaerten.katalog.tgatab`): Baum shows "
    "`kattree` = `KatTgaTree.sidebar` (trees / folders / `<konkret>` / `(abstrakt)`, link `bearbeiten` on the tree). "
    "Folder rows of the tree editor have a filter row (Klasse, Suchtext, nur abstrakt); each object input has its own "
    "datalist filtered by the inherited folder filters. The bottom area `katphotos` holds the **Darstellungs-Editor** "
    "(`katalog_tga_draw.js`, object `KatTgaDraw`, loaded after `katalog_tga_tree.js`): SVG in the wall plane (1 cm grid, "
    "1 mm snap, wheel zoom), tools Auswahl / Rechteck / Kreis / Linie / Text / Anschlusspunkt, drag to draw and move, "
    "property panel (mm; Körper B × H × T = install.size; port id, Lage x / y / Tiefe w, Richtung links / rechts / oben / "
    "unten / vorne / hinten, Winkel Standard / nur rechtwinklig / beliebig, Leitungssystem, DN / Adern, Art, Fluss, "
    "Adern und Kabeltypen der Einführung, Bezeichnung), read-only outside edit mode, `Darstellung anlegen` creates an "
    "install block; photos below it. Kürzung: Vorgabe is required (empty -> 1 m). In /waende `drawPart` draws "
    "`layout.shapes` instead of the default rectangle and snapping uses the port angle rule like the core.")


def patch(name, anchor, text):
    path = os.path.join(ROOT, name)
    with open(path, "rb") as f:
        data = f.read()
    if data.count(anchor) != 1:
        raise SystemExit("%s: anchor %d" % (name, data.count(anchor)))
    index = data.index(anchor)
    end = data.index(b"\n", index)
    cut = end - 1 if data[end - 1:end] == b"\r" else end
    return path, data[:cut] + text.encode("utf-8") + data[cut:]


def handbuch():
    path = os.path.join(ROOT, "weingaerten-handbuch.md")
    with open(path, "rb") as f:
        data = f.read()
    nl = "\r\n" if b"\r\n" in data else "\n"
    head = "### TGA – Verbindungsregeln".encode("utf-8")
    text = ("### TGA – Liste / Baum und Darstellung" + nl + nl +
            "- Oben die Reiter **Liste** (alle Einträge mit Suche und Filter) und **Baum** (die TGA-Bäume; Klick auf ein "
            "Objekt öffnet es, **bearbeiten** am Baum öffnet den Baum-Editor)." + nl +
            "- Jeder **Ordner** im Baum-Editor hat einen **Filter** (Klasse, Suchtext, nur abstrakt). Die Auswahlliste "
            "der Objekte darin zeigt nur passende Bauteile; Unterordner erben den Filter." + nl +
            "- Unten der **Darstellungs-Editor** (im Bearbeiten-Modus): vereinfachte Ansicht des Bauteils in der Wand "
            "zeichnen (Rechteck, Kreis, Linie, Text; Raster 1 cm, Fang 1 mm, Mausrad = Zoom) und **Anschlusspunkte** "
            "setzen. Je Anschlusspunkt Lage und Tiefe, Richtung, Leitungssystem, DN bzw. Adern und **Winkel**: *nur "
            "rechtwinklig* (Rohr in Rohr) oder *beliebig* (Leitungen; Standard bei Kabeln). So erscheint das Teil auf der "
            "Seite **Wände**." + nl +
            "- **Kürzungseigenschaft:** Bei einer max. Länge (z. B. 50 m) ist die **Vorgabe** Pflicht (z. B. 1 m) – mit "
            "dieser Länge wird die Leitung angelegt." + nl + nl).encode("utf-8")
    return path, data.replace(head, text + head)


def main():
    results = [patch("weingaerten-core.md", b"**Abstract TGA objects**", CORE_ADD),
               patch("weingaerten-web.md", b"- **TGA catalog** (`/katalog/tga`", WEB_ADD), handbuch()]
    for path, data in results:
        print(("schreibe " if "--write" in sys.argv else "ok ") + path)
        if "--write" in sys.argv:
            with open(path, "wb") as f:
                f.write(data)


if __name__ == "__main__":
    main()
