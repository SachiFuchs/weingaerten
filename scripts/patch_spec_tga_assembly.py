"""One-off: documents TGA assemblies (Baugruppe), deprecated abstract objects and the strict suitability in the spec files
(bytes, line endings kept). python scripts/patch_spec_tga_assembly.py [--write]
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CORE_ASM = (
    "- **TGA trees and assemblies** (`compute/tga_tree.py` `TgaTree`, `compute/tga_assembly.py` `TgaAssembly`): "
    "`installation.trees` / `TGA_CATALOG.trees` = `[{ref, id, name, nodes}]`, object nodes `{id, name, ref, missing, "
    "assembly (bool), placement, deprecated?}`. **Abstract TGA objects** (`tga-component.abstract`) are DEPRECATED: "
    "files and schema stay readable, validation unchanged, `TGA_CATALOG.abstracts` still lists their concretisations "
    "(read-only), but tree nodes only carry `deprecated: true` and they are never offered (palette, tree editor). "
    "**Effective placement** (`TgaTree.placement_of`) = `{hosts, modes, derived, none}`: own block, else modes from "
    "connection.mounting (`derived`), else `none: true` with empty hosts / modes = no suitability (never offered in a "
    "palette tree, no placement warning). **TGA assembly** = tga-component with `assembly {main: tga-component, "
    "parts: [{ref, count? (default 1), role? L|L1|L2|L3|N|PE}]}`; `TgaAssembly.effective` = the assembly with "
    "`install`, `placement`, `connection`, `cut` of the main object (when not own) and main params below its own - used "
    "for the palette row (`assembly: true`, no box variant grouping), the installed part, the placement warning and "
    "`TGA_CATALOG.placement`. Parts with a role are the box clamps: an installed assembly part without own `clamps` "
    "gets `[{role, clamp: ref}]` (BoxClamps capacity = smallest pole count = max. connections); parts without role are "
    "`assembly_extras [{ref, count}]`. Part output adds `assembly_main`, `assembly_extras`; PartTally counts the main "
    "object (name / price of the main) instead of the assembly, plus the extras and the clamps. `TGA_CATALOG."
    "assemblies` = `{<ref>: {main, main_name, items [{ref, name, count, role, poles}], capacity}}`. Errors "
    "(`TgaAssembly.errors`, instead of the connection rules): `assembly.main: unbekannt` / `Baugruppe kann kein "
    "Hauptobjekt sein` / `Hauptobjekt ohne Einbaudaten`, `assembly.parts[i]: unbekannt` / `Baugruppe in Baugruppe nicht "
    "erlaubt` / `Leiter <r> nur bei Klemmen` / `Leiter <r> doppelt` / `Klemme mit Leiter hat Anzahl 1`; no warning "
    "`Verbindungsdaten fehlen`. Example `verteilerdose-up-3x-wago-3-polig` (UP-Abzweigkasten + 3 x WAGO 3-polig L/N/PE). "
    "Test `scripts/smoke_tga_assembly.py`.\r\n")

CORE = [
    (b"abstracts: {<ref>: abstract of TgaTree}, trees, placement: {<ref>: {hosts, modes, derived}}}`",
     b"abstracts: {<ref>: abstract of TgaTree} (deprecated), assemblies: {<ref>: TgaAssembly.summary}, trees, "
     b"placement: {<ref>: {hosts, modes, derived, none}}}`"),
    (b"- **Box clamps** (`BoxClamps`", CORE_ASM.encode() + b"- **Box clamps** (`BoxClamps`"),
    (b"(surface on, flush / hollow_wall in), else all (`derived`); palette rows",
     b"(surface on, flush / hollow_wall in), else none (see TGA trees and assemblies below); palette rows"),
    (b"`tga_tree.py` (`TgaTree`), `crossing", b"`tga_tree.py` (`TgaTree`), `tga_assembly.py` (`TgaAssembly`), `crossing"),
]

WEB = [
    ("trees and abstract objects - button `katnewtree` (`+ Baum`), filter options `Bäume` / `abstrakte Objekte`, pill "
     "`abstrakt`, tree view as nested list (object pill abstrakt/konkret + count of concretisations)",
     "trees and assemblies - buttons `katnewtree` (`+ Baum`) and `katnewasm` (`+ Baugruppe`, template class / KG / "
     "system of install-part, `assembly {main: '', parts: []}`), filter options `Bäume` / `Baugruppen` / ... / "
     "`veraltet (abstrakt)` (last), pills `Baugruppe`, `veraltet (abstrakt)` (grey) and `keine Eignung` (red, "
     "components whose effective placement is `none`), tree view as nested list (object pill konkret / Baugruppe / "
     "veraltet (abstrakt) + `Eignung: <text>` or red `keine Eignung – wird nicht angeboten`); read view of a component: "
     "row `Eignung` always shown (`<hosts> – <modes>` + ` (abgeleitet aus Montage)` / ` (vom Hauptobjekt)` / "
     "` (geschätzt)`, else bold red `keine Eignung – wird in keiner Palette angeboten`); assembly read view: block "
     "`Baugruppe` (Hauptobjekt link, `max. Anschlüsse` = capacity, table Bestandteil | Anzahl | Leiter | Pole), no "
     "`Verbindung` block, drawing editor note `Baugruppe – Darstellung kommt vom Hauptobjekt.`; assembly edit "
     "(`KatTgaTree.assemblyForm`): `Hinweis`, select `Hauptobjekt *` (concrete objects with install data, ` (keine "
     "Eignung)` appended; choosing copies class / din276 / system_type), list of parts (datalist, clamps first with "
     "pole count; Anzahl; Leiter select only for clamps - setting it removes count), `+ Bestandteil`, info line "
     "`Eignung: … · max. Anschlüsse: …`; save refused without main (`Hauptobjekt fehlt`); deprecated abstract objects "
     "are shown read-only (block `Abstraktes TGA-Objekt (veraltet)` with red note) and their edit form only offers "
     "`Abstraktion entfernen`"),
    ("component block `Abstraktion, Kürzung, Eignung` (abstract checkbox + axes from class parameters + Vorgabe, "
     "Kürzungseigenschaft",
     "component block `Kürzung, Eignung` (Kürzungseigenschaft"),
    ("katdata also has `abstracts`, `trees`, `placement`", "katdata also has `abstracts`, `assemblies`, `trees`, "
     "`placement`; tree editor: datalist without abstract objects (assemblies first as `[Baugruppe] `, ` (keine "
     "Eignung)` appended; folder filter class matches an assembly by its main class, query also searches the main "
     "params), folder filter only Klasse + Suchtext (a stored `abstract` flag is dropped), node status konkret / "
     "Baugruppe / veraltet (abstrakt) / unbekannt (red with `, keine Eignung`); sidebar tab Baum: every object as "
     "`<name>`, pills fehlt / Baugruppe / veraltet, deprecated or unsuited objects at opacity .5 with tooltip"),
    ("concrete objects as `<name>` buttons, abstract objects as `(name)` opening a dialog with one select per axis "
     "(values without a usable concretisation disabled; usable = in the palette catalog, placement suits wall + Einbau "
     "in/vor der Wand, fits a free port of the selected part), Einfügen starts the concrete part;",
     "only offered objects as `<name>` buttons (offered = in the palette catalog, not deprecated, effective placement "
     "not `none` with host wall and mode of the Einbau in/vor der Wand, fits a free port of the selected part; others "
     "are hidden), assemblies get tooltip ` – Baugruppe`, folder count `(n)` = offered objects, empty folder note "
     "`nichts Passendes`; no abstract dialog;"),
]

HANDBUCH = [
    ("### TGA – Bäume, abstrakte Objekte, Kürzung, Eignung", "### TGA – Bäume, Baugruppen, Kürzung, Eignung"),
    ("- **Abstraktes TGA-Objekt** (Filter **abstrakte Objekte**): Häkchen im Bauteil-Formular. Die Parameter oben sind "
     "die festen Werte (z. B. Kabeltyp NYY-J), unter **konkretisiert durch** stehen die Parameter, die beim Einbau "
     "gewählt werden (z. B. Adernanzahl, Querschnitt). Konkretisierungen sind alle Bauteile derselben Klasse mit den "
     "festen Werten; die Ansicht listet sie, **Vorgabe** wählt die vorbelegte.",
     "- **TGA-Baugruppe** (**+ Baugruppe**, Filter **Baugruppen**): ein **Hauptobjekt** (z. B. Unterputz-Abzweigkasten) "
     "mit **Bestandteilen** (z. B. 3 × WAGO-Klemme 3-polig). Bestandteile als Liste mit **Anzahl**; bei Klemmen wird "
     "der **Leiter** (L, N, PE …) gewählt. Einbaudaten, Darstellung und Eignung kommen vom Hauptobjekt; **max. "
     "Anschlüsse** = kleinste Polzahl der Klemmen (3 × WAGO 3-polig → 3 Leitungen). So gibt es mehrere „Versionen“ "
     "einer Dose. Eine Baugruppe wird als **ein Teil** eingebaut; die Stückliste zählt Hauptobjekt und Bestandteile. "
     "Baugruppen in Baugruppen sind nicht erlaubt.\r\n"
     "- **Abstrakte TGA-Objekte sind veraltet:** Sie bleiben lesbar (Filter **veraltet (abstrakt)**), werden aber "
     "nirgends mehr angeboten. Im Baum stattdessen die tatsächlich verwendeten konkreten Objekte (z. B. je Kabel "
     "Querschnitt / Adern) oder Baugruppen eintragen."),
    ("- **Eignung:** geeignet für Wand / Boden / Decke / Dach, Einbau in (eingelassen) / auf (aufliegend). Ohne Angabe "
     "gilt bei Dosen die Montage (Unterputz = in, Aufputz = auf). Ein unpassend eingebautes Teil gibt einen Hinweis.",
     "- **Eignung:** geeignet für Wand / Boden / Decke / Dach, Einbau in (eingelassen) / auf (aufliegend). Ohne Angabe "
     "gilt bei Dosen die Montage (Unterputz = in, Aufputz = auf, angezeigt als „abgeleitet aus Montage“). **Ohne "
     "Eignung wird ein Objekt in keiner Palette angeboten** – die Ansicht zeigt dann rot „keine Eignung“, die Liste "
     "die Markierung **keine Eignung**. Auf der Seite **Wände** (Reiter Baum) erscheinen nur Objekte, die für Wände und "
     "den gewählten Einbau (in / vor der Wand) geeignet sind. Ein unpassend eingebautes Teil gibt einen Hinweis."),
    ("hat einen **Filter** (Klasse, Suchtext, nur abstrakt).", "hat einen **Filter** (Klasse, Suchtext)."),
    ("Der Reiter **Baum** zeigt die im TGA-Katalog konfigurierten TGA-Bäume (z. B. Elektro > Kabel > (NYY-J), (NYM-J); "
     "Verteiler > (Unterputzdose); Endgeräte > <Lampenfassung E27>). <…> ist ein konkretes TGA-Objekt und hängt sofort "
     "an der Maus. (…) ist ein **abstraktes TGA-Objekt**: Ein Dialog fragt die fehlenden Parameter ab (z. B. Querschnitt "
     "und Pole). Werte ohne passendes Bauteil sind ausgegraut, nach der Auswahl wird das konkrete Bauteil eingefügt. "
     "Gefiltert wird nach dem **Einbau** (nur Teile, die für Wände und für in / vor der Wand geeignet sind) und nach "
     "dem gewählten Teil (nur, was an einen freien Anschluss passt).",
     "Der Reiter **Baum** zeigt die im TGA-Katalog konfigurierten TGA-Bäume (z. B. Elektro > Leitungen > <NYM-J 3 x "
     "1,5 mm²>; Verteiler > <Verteilerdose UP mit 3 × WAGO 3-polig>). <…> ist ein konkretes TGA-Objekt oder eine "
     "Baugruppe und hängt sofort an der Maus. Angeboten wird nur, was für Wände und den **Einbau** (in / vor der Wand) "
     "geeignet ist und an einen freien Anschluss des gewählten Teils passt; Objekte ohne Eignung erscheinen nicht."),
]


def patch(name, pairs, write):
    path = os.path.join(ROOT, name)
    data = open(path, "rb").read()
    for old, new in pairs:
        old_b, new_b = (old, new) if isinstance(old, bytes) else (old.encode(), new.encode())
        count = data.count(old_b)
        print("%s: %d x %s" % (name, count, old_b[:60]))
        if count != 1:
            raise SystemExit("not unique / missing in %s" % name)
        data = data.replace(old_b, new_b)
    if write:
        open(path, "wb").write(data)


if __name__ == "__main__":
    flag = "--write" in sys.argv
    patch("weingaerten-core.md", CORE, flag)
    patch("weingaerten-web.md", WEB, flag)
    patch("weingaerten-handbuch.md", HANDBUCH, flag)
    print("written" if flag else "dry run")
