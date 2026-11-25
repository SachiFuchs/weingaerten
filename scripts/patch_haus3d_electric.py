"""One-off: hook Electric3d into static/haus3d.js (checkbox elektrik3d, pick kinds, build, onchange, tooltip)."""
import os
import sys

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "code", "weingaerten_web", "static", "haus3d.js")
REPLACE = [
    ("if(zuw)zuw.checked=localStorage.getItem('weingaerten.zuwasser')!=='0';",
     "if(zuw)zuw.checked=localStorage.getItem('weingaerten.zuwasser')!=='0';const elk=document.getElementById("
     "'elektrik3d');if(elk)elk.checked=localStorage.getItem('weingaerten.elektrik')!=='0';"),
    ("...Water3d.KINDS,", "...Water3d.KINDS,...Electric3d.KINDS,"),
    ("if(zuw&&zuw.checked)Water3d.build(THREE,wallGroup,pick,H.water_supply);",
     "if(zuw&&zuw.checked)Water3d.build(THREE,wallGroup,pick,H.water_supply);"
     "if(elk&&elk.checked)Electric3d.build(THREE,wallGroup,pick,H.electrical);"),
    ("if(zuw)zuw.onchange=()=>{localStorage.setItem('weingaerten.zuwasser',zuw.checked?'1':'0');buildWalls()};",
     "if(zuw)zuw.onchange=()=>{localStorage.setItem('weingaerten.zuwasser',zuw.checked?'1':'0');buildWalls()};"
     "if(elk)elk.onchange=()=>{localStorage.setItem('weingaerten.elektrik',elk.checked?'1':'0');buildWalls()};"),
    ("else if(Water3d.KINDS.includes(u.kind)){const t=Water3d.tip(u);showTip(e,t[0],t[1])}",
     "else if(Water3d.KINDS.includes(u.kind)){const t=Water3d.tip(u);showTip(e,t[0],t[1])}"
     "else if(Electric3d.KINDS.includes(u.kind)){const t=Electric3d.tip(u);showTip(e,t[0],t[1])}"),
]

text = open(PATH, encoding="utf-8").read()
if "Electric3d" in text:
    sys.exit("schon eingebaut")
for old, new in REPLACE:
    if text.count(old) != 1:
        sys.exit("nicht eindeutig (%d): %s" % (text.count(old), old[:50]))
    text = text.replace(old, new)
with open(PATH, "w", encoding="utf-8", newline="") as handle:
    handle.write(text)
print("haus3d.js angepasst")
