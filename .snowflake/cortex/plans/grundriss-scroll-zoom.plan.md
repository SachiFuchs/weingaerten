# Plan: Grundriss vergrößern mit Slidern und Verschieben per rechter Maustaste

## Kontext
- [plan_zoom.js](code/weingaerten_web/static/plan_zoom.js) zoomt heute über die `viewBox`.
  - Der Ausschnitt wird innerhalb der festen `#planbox` verkleinert; die Box hat `overflow:hidden` ([style.css:38](code/weingaerten_web/static/style.css)).
  - Die Grafik wird dadurch nie größer als die Box, es gibt also nichts zu scrollen.
  - Verschieben geht nur mit der mittleren Maustaste oder der Leertaste.
- [plan.js:35](code/weingaerten_web/static/plan.js) ruft in `frame()` `PlanZoom.base(svg,W,H)` auf.
  - `toWorld()` rechnet über `getScreenCTM` und bleibt bei jeder CSS-Größe und jeder Scrollposition korrekt.
- Spezifikation: [weingaerten-web.md:144](weingaerten-web.md), Punkt „Zoom“.
  - Die Reihenfolge ist immer: zuerst die Spezifikation, dann der Code, dann `scripts/rehash_cache.py`.

## Ansatz
Statt über die viewBox zu zoomen, wird künftig die Größe der Grafik geändert.
- Die viewBox zeigt immer die ganze Zeichnung.
- Das SVG bekommt per CSS die Pixelgröße `Einpassgröße × z`, wobei `z` der Zoomfaktor ist.
- `#planbox` erhält `overflow:auto`. Der Browser zeigt den horizontalen und/oder vertikalen Slider nur dann an, wenn der Grundriss über den Rand ragt.

## Umsetzungsschritte
1. **Spezifikation** (`weingaerten-web.md`, Punkt „Zoom“ und Hinweistext in der Toolbar):
   - Mausrad und `+`/`−` vergrößern bzw. verkleinern die Grafik um die Cursorposition. Bereich 0,2 … 20×, Faktor 1,15.
   - Bei Überstand zeigt die Box Slider.
   - Ziehen mit der rechten Maustaste verschiebt den Grundriss; das Kontextmenü ist in der Box unterdrückt.
   - Mittlere Maustaste und Leertaste bleiben als Alternative.
   - `Einpassen` zeigt die ganze Zeichnung in der Box, ohne Slider.
2. **CSS** (`style.css`):
   - `#planbox{overflow:auto}`.
   - `width/height:100%` bei `#planview svg,#planedsvg` entfernen, weil JS die Größe setzt.
   - `resize:both` bleibt; Slider und Größen-Griff funktionieren nebeneinander.
3. **plan_zoom.js**:
   - `apply(svg)`:
     - Die viewBox ist immer `0 0 bw bh`.
     - Den Einpassfaktor `f = min(BoxBreite/bw, BoxHöhe/bh)` berechnen.
     - Breite und Höhe auf `bw·f·z` bzw. `bh·f·z` px setzen.
   - `zoomAt()`:
     - Zuerst den Inhaltspunkt unter dem Cursor merken.
     - Dann die neue Größe setzen.
     - Zuletzt `scrollLeft/Top` so anpassen, dass dieser Punkt unter dem Cursor bleibt.
   - Verschieben:
     - Auslöser ist `button===2`, alternativ die mittlere Maustaste oder Leertaste + linke Maustaste.
     - Beim Ziehen werden `box.scrollLeft/Top` angepasst.
     - Die Handler laufen in der Capture-Phase mit `stopPropagation`. So lösen sie keine Bearbeitungsaktionen in `plan.js` aus.
     - `contextmenu` wird mit `preventDefault` unterdrückt.
   - `fit()`: `z=1` setzen und auf 0/0 scrollen.
   - Beim Ändern der Boxgröße neu anwenden; dafür den vorhandenen `ResizeObserver` nutzen.
   - `base()` behält seine Signatur, daher muss `plan.js` nicht geändert werden.
4. **Hinweistext** in [grundriss_page.py:75](code/weingaerten_web/pages/grundriss_page.py): „Mausrad = Zoom, rechte Maustaste ziehen = Verschieben, Slider bei Überstand“.
5. `scripts/rehash_cache.py` und `scripts/check_clean_code.py` ausführen. Die Datei muss unter 256 Zeilen bleiben.

## Verifikation
- Server stoppen, umsetzen, mit `start.cmd` neu starten.
- `scripts/check_web.py`: /grundriss liefert 200 und enthält `planedit`, `plandata` und `planpanel`.
- Im Browser prüfen:
  - Mehrmals `+` → die Slider erscheinen.
  - Beim Mausrad bleibt der Punkt unter dem Cursor fest.
  - Ziehen mit der rechten Maustaste verschiebt den Grundriss, ohne dass das Kontextmenü erscheint.
  - `Einpassen` entfernt die Slider.
  - Im Bearbeitungsmodus treffen Auswählen und Ziehen von Wänden nach Zoom und Scrollen weiterhin die richtige Wand.
  - Boxgröße und Splitter funktionieren weiter und bleiben nach dem Neuladen erhalten.

## Kritische Dateien
- [code/weingaerten_web/static/plan_zoom.js](code/weingaerten_web/static/plan_zoom.js) – Zoom-, Scroll- und Verschiebe-Logik
- [code/weingaerten_web/static/style.css](code/weingaerten_web/static/style.css) – overflow:auto, SVG-Größe
- [weingaerten-web.md](weingaerten-web.md) – Spezifikation, Punkt „Zoom“
- [code/weingaerten_web/pages/grundriss_page.py](code/weingaerten_web/pages/grundriss_page.py) – Hinweistext
