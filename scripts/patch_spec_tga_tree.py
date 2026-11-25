"""One-off: documents TGA trees / abstract TGA objects in the spec files (bytes, line endings kept).

python scripts/patch_spec_tga_tree.py [--write]
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CORE_TREE = (
    " **TGA trees** (`compute/tga_tree.py`, `TgaTree`; catalog folder `catalog/tga-trees`, ref `tga-tree:`, schema "
    "`tga-tree`, loaded by TgaLoader into `tga.elements`, editable via SAVE / DELETE): `{id, name, order?, description?, "
    "nodes}`; a node is a folder `{id, name, nodes}` or an object `{id, ref (tga-component), name?}`; errors: unknown ref, "
    "node with ref and nodes / with neither, folder without name, duplicate sibling id (`TgaTreeValidator.tree_errors`). "
    "**Abstract TGA objects**: a tga-component with `abstract {axes [{param, label?, unit?}], default?}`; its `params` are "
    "the fixed values; a concretisation is every non-abstract tga-component of the same class with all fixed params "
    "(`TgaTreeValidator.concretises`); axes must be class parameters not fixed in params, default must concretise; "
    "abstract objects skip connection / product rules and never appear in the palette catalog or `cables`. "
    "`installation.trees` = `[{ref, id, name, nodes}]` (by order, name), object nodes `{id, name, ref, missing}` + "
    "`abstract {axes, fixed, candidates [{ref, name, values, placement}], default}` (candidates sorted by axis values). "
    "tga-component `cut {max_length, default_length?, min_length?}` = Kürzungseigenschaft, wins over install.stretch and "
    "the derived cable limit (50 m); `placement {hosts wall|floor|ceiling|roof, modes in|on, estimated?}`, effective "
    "placement = own block, else modes from connection.mounting (surface on, flush / hollow_wall in), else all "
    "(`derived`); palette rows carry `placement` and `layout`; install.layout `{size, points {top, bottom, left, right, "
    "back}, max_connections, symbol}`. Warning (where `tga-part:<id>`) for wall-hosted parts with explicit placement or "
    "mounting: `TGA-Teil nicht für Wände geeignet` / `TGA-Teil nicht geeignet für Einbau in|Montage auf der Wand` "
    "(mode in: box / insert depth < own depth, others depth < 0). Data: `scripts/build_tga_tree.py [--write]` "
    "(install-part params mounting / box_function, box params, cable cut from ring length, abstract objects "
    "abstrakt-kabel-<type>, abstrakt-aufputz|unterputz|hohlwand|herd-anschlussdose, trees elektro / abwasser / zuwasser). "
    "Test `scripts/smoke_tga_tree.py`.")

CORE = [
    (b"| `TGA_CATALOG` | `{elements: {<ref>: element + {ref, type}}, conductors: {<ref>: [{role, color}]} (cables), "
     b"issues: [{where, message, level}]}`",
     b"| `TGA_CATALOG` | `{elements: {<ref>: element + {ref, type}}, conductors: {<ref>: [{role, color}]} (cables), "
     b"issues: [{where, message, level}], abstracts: {<ref>: abstract of TgaTree}, trees, placement: {<ref>: "
     b"{hosts, modes, derived}}}` (tga-trees included in elements)"),
    (b"`tga_loader.py` (`TgaLoader`)", b"`tga_loader.py` (`TgaLoader`, also `catalog/tga-trees`)"),
    (b"`connection_validator.py` (`ConnectionValidator`) |",
     b"`connection_validator.py` (`ConnectionValidator`), `tga_tree_validator.py` (`TgaTreeValidator`) |"),
    (b"`part_builder.py` (`PartBuilder`)", b"`part_builder.py` (`PartBuilder`), `tga_tree.py` (`TgaTree`)"),
]

WEB = [
    (b"- **TGA catalog** (`/katalog/tga`, class `TgaKatalogPage` in `pages/tga_katalog_page.py`, browser module "
     b"`katalog_tga.js`, object `KatTga`;",
     b"- **TGA catalog** (`/katalog/tga`, class `TgaKatalogPage` in `pages/tga_katalog_page.py`, browser module "
     b"`katalog_tga.js`, object `KatTga`, plus `katalog_tga_tree.js` (object `KatTgaTree`, loaded before it): trees and "
     b"abstract objects - button `katnewtree` (`+ Baum`), filter options `B\xc3\xa4ume` / `abstrakte Objekte`, pill "
     b"`abstrakt`, tree view as nested list (object pill abstrakt/konkret + count of concretisations), tree editor "
     b"(folders / objects with datalist `tgarefs`, up / down / remove, `+ Ordner`, `+ Objekt`, Reihenfolge), component "
     b"block `Abstraktion, K\xc3\xbcrzung, Eignung` (abstract checkbox + axes from class parameters + Vorgabe, "
     b"K\xc3\xbcrzungseigenschaft bis / Vorgabe / ab in m, geeignet f\xc3\xbcr Wand/Boden/Decke/Dach, Einbau in/auf, "
     b"Layout: Ausma\xc3\x9fe mm, Anschlusspunkte je Seite, max. Anschl\xc3\xbcsse, Darstellung); katdata also has "
     b"`abstracts`, `trees`, `placement`;"),
    (b"- **Installation** (Einbauteile, script `static/install.js` after `lining.js`,",
     b"- **Installation** (Einbauteile, script `static/install.js` after `lining.js` and `install_tree.js` (object "
     b"`InstallTree`: palette tabs `Baum` | `Katalog`, localStorage `weingaerten.waende.paltab`, open folders "
     b"`weingaerten.waende.tgatree`; tab Baum renders `HOUSE.installation.trees`, concrete objects as `<name>` buttons, "
     b"abstract objects as `(name)` opening a dialog with one select per axis (values without a usable concretisation "
     b"disabled; usable = in the palette catalog, placement suits wall + Einbau in/vor der Wand, fits a free port of the "
     b"selected part), Einf\xc3\xbcgen starts the concrete part; tab Katalog = the derived tree below),"),
    (b"`katalog_docs.js`, `katalog_tga.js`, `wand.js`", b"`katalog_docs.js`, `katalog_tga_tree.js`, `katalog_tga.js`, `wand.js`"),
    (b"`raum.js`, `install.js`, `parts3d.js`", b"`raum.js`, `install_tree.js`, `install.js`, `parts3d.js`"),
]


def patch(name, pairs, append_after=None, append=None):
    path = os.path.join(ROOT, name)
    with open(path, "rb") as f:
        data = f.read()
    for old, new in pairs:
        if data.count(old) != 1:
            raise SystemExit("%s: anchor found %d times: %r" % (name, data.count(old), old[:60]))
        data = data.replace(old, new)
    if append_after:
        index = data.index(append_after)
        end = data.index(b"\n", index)
        cut = end - 1 if data[end - 1:end] == b"\r" else end
        data = data[:cut] + append + data[cut:]
    return path, data


def main():
    results = [patch("weingaerten-core.md", CORE, b"**Palette tree** (`PaletteTree.paths`", CORE_TREE.encode("utf-8")),
               patch("weingaerten-web.md", WEB)]
    for path, data in results:
        print(("schreibe " if "--write" in sys.argv else "ok ") + path)
        if "--write" in sys.argv:
            with open(path, "wb") as f:
                f.write(data)


if __name__ == "__main__":
    main()
