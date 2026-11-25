"""Tree paths of the installation palette on /waende (trade > system/size > group)."""
from typing import Any, Dict, List

LINE_NAMES = {"ht": "HT", "kg": "KG", "ppr": "PPR", "alu_composite": "Alu-Verbund"}
# fixed nodes shown even without parts (placeholders)
ROOTS = [["Abwasser"], ["Zuwasser"], ["Zuwasser", "Endteile"], ["Elektro", "Rohre"], ["Elektro", "Leitungen"],
         ["Elektro", "Verteiler"], ["Elektro", "Endgeräte"]]
WATER_END_GROUPS = ("Armaturen", "Hähne", "Schläuche", "Endteile")
TERMINAL_GROUPS = ("Steckdosen", "Schalter", "Fassungen", "Leuchten")


class PaletteTree:
    """Derives the palette paths of a catalog part; `install.palette` (list or list of lists) overrides them."""

    @staticmethod
    def paths(element: Dict[str, Any], install: Dict[str, Any]) -> List[List[str]]:
        own = install.get("palette")
        if isinstance(own, list) and own:
            return [list(p) for p in own] if isinstance(own[0], list) else [list(own)]
        group = install.get("group") or "Sonstiges"
        trade = install.get("trade")
        if trade == "waste_water":
            return PaletteTree._sizes(["Abwasser"], install, group)
        if trade == "water_supply":
            if group in WATER_END_GROUPS:
                return [["Zuwasser", "Endteile", group]]
            return PaletteTree._sizes(["Zuwasser"], install, group, split=True)
        if trade == "electrical":
            return [PaletteTree._electrical(element, install, group)]
        return [[trade or "Sonstiges", group]]

    @staticmethod
    def _sizes(root: List[str], install: Dict[str, Any], group: str, split: bool = False) -> List[List[str]]:
        # one path per line/DN of the ports: a reducer or a KG/HT adapter appears under every size it joins
        seen, out = set(), []
        for port in install.get("ports") or []:
            line, dn = port.get("line"), port.get("dn")
            if line not in LINE_NAMES or (line, dn) in seen:
                continue
            seen.add((line, dn))
            size = "DN %s" % PaletteTree._num(dn)
            out.append(root + ([LINE_NAMES[line], size] if split else ["%s %s" % (LINE_NAMES[line], size)]) + [group])
        out.sort(key=lambda p: (p[1], -PaletteTree._dn(p)))
        return out or [root + [group]]

    @staticmethod
    def _electrical(element: Dict[str, Any], install: Dict[str, Any], group: str) -> List[str]:
        shape = install.get("shape")
        if shape == "cable":
            return ["Elektro", "Leitungen", (element.get("params") or {}).get("cable_type") or "Leitungen"]
        if shape == "insert" or group in TERMINAL_GROUPS:
            return ["Elektro", "Endgeräte", group]
        if shape == "box":
            return ["Elektro", "Verteiler", group]
        return ["Elektro", "Rohre", group]

    @staticmethod
    def _num(v: Any) -> str:
        return ("%g" % v) if isinstance(v, (int, float)) else str(v)

    @staticmethod
    def _dn(path: List[str]) -> float:
        for part in path:
            if part.startswith("DN ") or " DN " in part:
                try:
                    return float(part.split("DN ")[1])
                except ValueError:
                    return 0.0
        return 0.0
