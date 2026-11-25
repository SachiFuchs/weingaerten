"""One-off: TGA trees / abstract TGA objects in the user manual (bytes, CRLF kept).

python scripts/patch_handbuch_tga_tree.py [--write]
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "weingaerten-handbuch.md")

PALETTE = ("   **Reiter Baum / Katalog:** Der Reiter **Baum** zeigt die im TGA-Katalog konfigurierten TGA-Bäume "
           "(z. B. Elektro > Kabel > (NYY-J), (NYM-J); Verteiler > (Unterputzdose); Endgeräte > <Lampenfassung E27>). "
           "<…> ist ein konkretes TGA-Objekt und hängt sofort an der Maus. (…) ist ein **abstraktes TGA-Objekt**: Ein "
           "Dialog fragt die fehlenden Parameter ab (z. B. Querschnitt und Pole). Werte ohne passendes Bauteil sind "
           "ausgegraut, nach der Auswahl wird das konkrete Bauteil eingefügt. Gefiltert wird nach dem **Einbau** (nur "
           "Teile, die für Wände und für in / vor der Wand geeignet sind) und nach dem gewählten Teil (nur, was an einen "
           "freien Anschluss passt). Der Reiter **Katalog** zeigt den bisherigen, automatisch abgeleiteten Baum.")

CATALOG = ("### TGA – Bäume, abstrakte Objekte, Kürzung, Eignung\n\n"
           "- **+ Baum** legt einen TGA-Baum an (Filter **Bäume**). Im Baum-Editor: **+ Ordner**, **+ Objekt** "
           "(TGA-Objekt per Referenz, Vorschlagsliste), ↑ / ↓ verschieben, ✕ entfernen; **Reihenfolge** ordnet die Bäume "
           "in der Palette.\n"
           "- **Abstraktes TGA-Objekt** (Filter **abstrakte Objekte**): Häkchen im Bauteil-Formular. Die Parameter oben "
           "sind die festen Werte (z. B. Kabeltyp NYY-J), unter **konkretisiert durch** stehen die Parameter, die beim "
           "Einbau gewählt werden (z. B. Adernanzahl, Querschnitt). Konkretisierungen sind alle Bauteile derselben Klasse "
           "mit den festen Werten; die Ansicht listet sie, **Vorgabe** wählt die vorbelegte.\n"
           "- **Kürzungseigenschaft:** Das Teil ist in jeder Länge bis **bis … m** verfügbar (z. B. Kabel NYY 50 m → "
           "15 m), mit Vorgabelänge und Mindestlänge.\n"
           "- **Eignung:** geeignet für Wand / Boden / Decke / Dach, Einbau in (eingelassen) / auf (aufliegend). Ohne "
           "Angabe gilt bei Dosen die Montage (Unterputz = in, Aufputz = auf). Ein unpassend eingebautes Teil gibt einen "
           "Hinweis.\n"
           "- **Layout (Planung):** Ausmaße (falls nicht am Produkt), Anschlusspunkte je Seite, max. Anschlüsse (z. B. "
           "WAGO 3-polig → 3), Darstellung.\n\n")


def main():
    with open(PATH, "rb") as f:
        data = f.read()
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    anchor = "Esc** hebt die Auswahl auf und zeigt wieder alle.".encode("utf-8")
    end = data.index(anchor) + len(anchor)
    data = data[:end] + nl + PALETTE.encode("utf-8") + data[end:]
    head = "### TGA – Verbindungsregeln".encode("utf-8")
    if data.count(head) != 1:
        raise SystemExit("anchor TGA – Verbindungsregeln")
    data = data.replace(head, CATALOG.replace("\n", nl.decode()).encode("utf-8") + head)
    print(("schreibe " if "--write" in sys.argv else "ok ") + PATH)
    if "--write" in sys.argv:
        with open(PATH, "wb") as f:
            f.write(data)


if __name__ == "__main__":
    main()
