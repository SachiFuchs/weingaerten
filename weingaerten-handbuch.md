# Benutzerhandbuch – Haus Weingärten

## Erste Schritte

### Starten

1. Im Projektordner `start.cmd` ausführen (Doppelklick oder in der Konsole). Ein anderer Port: `start.cmd -port 8010`.
2. Im Browser `http://localhost:8008` öffnen – die Seite **Haus 3D** erscheint.
3. Beenden: das minimierte Fenster „Weingaerten web“ schließen.

Die Anwendung läuft nur auf dem eigenen Rechner; andere Rechner im Netz können sie nicht aufrufen.

### Bildschirmaufbau

- **Kopfzeile** mit Haus-Symbol und „Haus Weingärten“; links davon ☰ zum Ein- und Ausklappen des Menüs (der Zustand bleibt gespeichert; bei schmalen Fenstern startet das Menü eingeklappt).
- **Menü links:** Haus 3D, Grundriss, Wände, Katalog (Materialien, Aufbauten, Bauteile, Klassen, Firmen, Dokumente), Mengen, Benutzerhandbuch, Tech.Doku, About.
- **Roter Balken** „Modell ungültig – n Fehler, siehe Mengen“: das Modell hat Fehler; die Liste steht auf der Seite **Mengen**.

### Grundregeln

- Alles wird über **Formulare** bearbeitet – nie direkt in JSON.
- **Längen** werden in **cm** eingegeben.
- Gespeichert wird nur, was **gültig** ist; sonst erscheint die Fehlermeldung rot neben dem Formular und nichts wird geändert.
- Ungespeicherte Änderungen: beim Verlassen der Seite oder beim Wechsel des Elements fragt die Anwendung „Änderungen verwerfen?“.
- Änderungen an den Daten sind beim nächsten Seitenaufruf sichtbar, ein Neustart ist nicht nötig.

## Haus 3D

Das ganze Haus als 3D-Modell mit allen Schichten, Öffnungen, Decken, Dach und Technik.

### Ansicht steuern

| Aktion | Bedienung |
|---|---|
| drehen | linke Maustaste ziehen |
| verschieben | rechte Maustaste ziehen |
| zoomen | Mausrad (jede Raste ±10 %) |
| vorwärts / rückwärts bewegen | Strg + Mausrad (jede Raste 0,5 m in Blickrichtung, ohne Zoom) |
| umschauen (um die eigene Position drehen) | Alt + linke Maustaste ziehen |
| Höhe der Ansicht | Ecke unten rechts des Bildes ziehen |

Unter dem Bild stehen nebeneinander zwei aufklappbare Kästen: **Legende Materialien** und **Bedienung 3D-Ansicht** (diese Tasten- und Mausübersicht).

### Was wird angezeigt

Die Kästen über dem Bild schalten Teile ein und aus (die Auswahl bleibt gespeichert):

- **Stockwerke:** ein Kästchen je Geschoss (KG, EG, DG …), dazu **Decke**, **Dachstuhl**, **Dach**, **Innendämmung**, **Beläge** (Boden- und Wandbeläge), **Schächte** (violett, durch alle Geschosse des Schachts). Ausgegraute Kästchen: „noch nicht vorhanden“.
- **Technik:** **Heizung** zeigt die Fußbodenheizung (orange Rohre, Verteiler); darüber liegende Bodenschichten werden dann ausgeblendet. **Abwasser** zeigt die Abwasserleitungen (HT grau, KG braun), Formteile als kurze Muffen (orange = Platzhalter, nicht im gemeldeten Sortiment), Durchbrüche als rote Ringe und Anschlüsse (WC, Dusche …) als blaue Kugeln. **Wandheizung** zeigt die Lehm-Wandheizung im DG: die Heizplatten (Typ D–L) als helle Platten vor der Wand, die Rohrschleifen und Anbindeleitungen orange, den Verteiler als graue Box.
- **Details:** **transparent** (Wände durchsichtig), **Beschriftungen** (Raumnamen), **Details** (Detailfenster rechts).

### Informationen zu einem Objekt

1. Mit der Maus über ein Objekt fahren – ein Hinweisfeld zeigt z. B. Wand, Aufbau, Schicht und Material.
2. Bleibt die Maus kurz stehen, „friert“ das Feld ein; jetzt kann man auf die Links **Wände**, **Material** oder **Bauteil** klicken.
3. Der Link öffnet das Objekt im **Detailfenster** rechts. Die Breite des Fensters lässt sich am Trennbalken ziehen, `<|>` klappt es ein und aus.
4. **Doppelklick** auf ein Fenster oder eine Tür öffnet das Bauteil im Katalog.
5. **Esc** schließt das Hinweisfeld.

Die Legende unter dem Bild zeigt die Farbe jedes Materials.

## Grundriss

Horizontalschnitt durch ein Geschoss mit allen Schichten, Fenstern, Türen, Maßketten und Räumen.

### Ansicht

- **Geschoss** in der Werkzeugleiste wählen; **Schnitthöhe cm** ändert die Schnitthöhe (Standard 100 cm).
- **Raumnamen** und **Wandnamen** blenden die Beschriftungen ein und aus.
- **Zoomen:** Mausrad oder `+`/`−`; **Einpassen** zeigt den ganzen Plan. **Verschieben:** rechte oder mittlere Maustaste ziehen oder Leertaste halten.
- Die Maus über einer Schicht oder Öffnung zeigt deren Daten.

### Wände bearbeiten

1. **Bearbeiten** klicken – rechts erscheint das Bearbeitungsfeld.
2. Eine Wand anklicken (sie wird blau) und sie dann wie unten beschrieben ändern.
3. **+ Wand:** danach auf dem Plan ziehen; die neue Wand rastet an anderen Wänden ein.
4. **Räume:** in einen Raum klicken. Ein Raum ist ein Vieleck mit rechten Winkeln: **Ecken** (Kreise) und **Kanten** (Quadrate) ziehen – sie rasten an den Wandinnenseiten ein. **Doppelklick auf eine Kante** teilt sie; die zweite Hälfte ziehen ergibt einen Versprung (L-Form). Eine Stufe, die man wieder gerade zieht, verschwindet. **+ Raum** zieht einen neuen rechteckigen Raum auf. Nummer, Nutzung und Beläge stehen auf der Seite **Räume**.
5. **Speichern** übernimmt alle Änderungen, **Verwerfen** macht sie rückgängig. Die Liste **Änderungen** zeigt, was noch nicht gespeichert ist.

Möglichkeiten bei einer gewählten Wand:

- **verschieben:** Wand ziehen (nur quer zur Wand); mit **Ecken mitziehen** werden anschließende Wände verlängert oder gekürzt.
- **Länge ändern:** Endpunkt ziehen oder im Feld **Länge** eintragen.
- **Pfeiltasten** verschieben um 1 cm, mit Umschalt um 10 cm.
- Knöpfe **Drehen 90° links/rechts**, **Teilen**, **Versprung** (z. B. für einen Erker), **Außenseite tauschen**, **Löschen**.
- **Name** und **Aufbau** im Feld ändern.

Farben der Endpunkte: **grün** = verbunden, **orange** = offenes Ende, **blau** = Innenwand-Ende bewusst ohne Anschluss (Klick auf ein oranges Ende einer Innenwand gibt es frei). **Rot** markiert Überlappungen und Öffnungen, die nicht mehr in ihre Wand passen. Eine Fehlermeldung anklicken markiert die betroffenen Elemente im Plan.

## Wände

Ansicht einer einzelnen Wand mit ihren Fenstern und Türen, der Innendämmung und den Einbauteilen (Elektro, Abwasser, Zuwasser).

### Wand auswählen

- Die Seite hat vier Bereiche: **Wandliste** | **Wandansicht** (darunter die Tabelle **Einbauteile dieser Wandseite**) | **Einbauteile-Baum** (darunter die **3D-Vorschau**). Alle Trennlinien (auch die zum Menü) lassen sich mit der Maus ziehen; die Größen bleiben gespeichert.
- Links die **Wandliste**; oben nach **Geschoss** filtern oder im Feld **Suchen …** nach Name suchen.
- **Außenansicht / Innenansicht** wechselt die Seite der Wand.
- **Pfeile um die Wand:** über der Ansicht links **◀ <Wand>** und rechts **<Wand> ▶** – je angrenzender Wand ein Pfeil – wechseln zur Nachbarwand (die Seite bleibt). **▲ Decke** ist vorgesehen, aber noch nicht umgesetzt. Unter der Ansicht führt **▼ <Raum>** zum Raum vor dieser Wandseite (bei Außenwänden nur in der Innenansicht).
- **Wand im Grundriss bearbeiten** springt zur Wand im Grundriss.

### Öffnungen (Fenster, Türen, Durchgänge)

1. **Bearbeiten** klicken.
2. **+ Öffnung:** Bauteil wählen, **Abstand links** oder **Abstand rechts**, **Brüstung**, **Fuge**, **Einbautiefe**, **Laibung** eintragen. Die Öffnung erscheint gestrichelt in der größten freien Lücke.
3. Eine vorhandene Öffnung anklicken und mit der Maus oder den Pfeiltasten verschieben (Umschalt = 10 cm); die Werte im Feld laufen mit.
4. Rot = Problem (z. B. „Öffnung ragt über die Wand“, „Öffnung im Anschluss von …“); solange etwas rot ist, ist **Speichern** gesperrt.
5. **Speichern und zurück** übernimmt alle Änderungen der Wand (während des Speicherns grau mit Speichert ) und kehrt in die Ansicht zurück, **Abbrechen** verwirft sie.

Die Tabelle unter der Ansicht listet alle Öffnungen; **in 3D zeigen** springt zur Öffnung in Haus 3D.

### Innendämmung

1. **Innenansicht** wählen (bei Außenwänden).
2. **+ Dämmbereich:** Aufbau, Abstand links, Breite, Unter- und Oberkante eintragen – oder **ganze Wandseite**.
3. **Speichern** bzw. **Löschen**. Fenster und Türen werden automatisch ausgespart.

### Wandheizung

In der Innenansicht zeigt die Wand die Heizplatten der Wandheizung (hellbraun, orange umrandet, mit Typbuchstabe D–L); das magentafarbene Dreieck markiert den Anschluss des Plattenfelds. Die Maus über einer Platte zeigt Typ, Heizkreis, Feld, Größe und Unterkante. Die Platten werden hier nur angezeigt, nicht bearbeitet.

### Installation einbauen (Elektro, Abwasser, Zuwasser)

Leitungen werden aus Einzelteilen des Katalogs zusammengesteckt: gerade Rohre (Länge frei bis 2 m, Leerrohr bis 3 m, wird abgeschnitten), Bögen, Abzweige, Übergänge (z. B. HT DN 90 > 50), Stopfen, Endkappen, Ventile, Wandscheiben, Geräte- und Verteilerdosen, Steckdosen.

1. **Installation bearbeiten** klicken. Oben erscheint die **Palette** als aufklappbarer **Baum**: **Abwasser** (je System und Größe, z. B. KG DN 110, HT DN 90, HT DN 50 – Übergangsstücke stehen unter beiden Größen), **Zuwasser** (PPR > DN 20, Endteile), **Elektro** (Rohre, Leitungen, Verteiler, Endgeräte). Welche Zweige offen sind, merkt sich der Browser. Ist ein Teil ausgewählt, sind nur die Teile anklickbar, die an einen seiner freien Anschlüsse passen (der Rest ist grau, passende Zweige klappen auf); **Esc** oder die Schaltfläche **Neue Gruppe beginnen** (über der Palette) hebt die Auswahl auf – das Bestehende bleibt unverändert – und zeigt wieder alle Teile, so dass eine neue, nicht verbundene Gruppe (z. B. eine weitere Elektro-Gruppe oder Rohre) begonnen werden kann. Esc wirkt auch, wenn gerade ein Feld des Teil-Panels den Fokus hat.
   **Reiter Baum / Katalog:** Der Reiter **Baum** zeigt die im TGA-Katalog konfigurierten TGA-Bäume (z. B. Elektro > Leitungen > <NYM-J 3 x 1,5 mm²>; Verteiler > <Verteilerdose UP mit 3 × WAGO 3-polig>). <…> ist ein konkretes TGA-Objekt oder eine Baugruppe und hängt sofort an der Maus. Angeboten wird nur, was für Wände und den **Einbau** (in / vor der Wand) geeignet ist und an einen freien Anschluss des gewählten Teils passt; Objekte ohne Eignung erscheinen nicht. Der Reiter **Katalog** zeigt den bisherigen, automatisch abgeleiteten Baum.
   **Zoom:** In beiden Bearbeiten-Modi (Öffnungen und Installation) über der Wand **− / + / Einpassen** oder **Strg+Mausrad** (zoomt um den Mauszeiger, die Ansicht scrollt). Beim Verlassen des Modus wird wieder eingepasst.
2. **Einbau** wählen: **in der Wand (Unterputz)** oder **vor der Wand (Aufputz)**.
3. Teil in der Palette anklicken – es hängt an der Maus – und in die Wand klicken. Kommt ein Anschluss in die Nähe eines passenden freien Anschlusses, **rastet das Teil ein** und dreht sich bei Bedarf passend. Wie nah das sein muss, stellt der Schieber **Magnet** oben ein (aus bis 30 cm, Standard 5 cm; größer = rastet leichter ein).
4. Teile **ziehen** (1-cm-Raster, Umschalt = 1 mm). Verbundene Teile wandern mit; mit **Alt** wird nur das eine Teil gezogen.
5. Tasten für das gewählte Teil – sie wirken auf das Teil **und alle damit verbundenen Teile** (als ein Stück, Drehpunkt = gewähltes Teil); mit gedrückter **Alt**-Taste nur auf das eine Teil:

| Taste | Wirkung |
|---|---|
| R / Umschalt+R | in der Wandebene drehen (15°) |
| Q / E | um die Senkrechte schwenken (15°) – waagerechtes Rohr in die Wand / zur Nachbarseite |
| A / D | um die Waagerechte kippen (15°) – senkrechtes Rohr in die Wand |
| T | spiegeln (z. B. Abzweig links / rechts) |
| Pfeiltasten | 1 cm verschieben (Umschalt = 1 mm) |
| + / − | gerades Rohr 1 cm länger / kürzer (Umschalt = 1 mm) |
| Bild↑ / Bild↓ | Tiefe ±5 mm (vor / in die Wand) |
| Entf | löschen |
| Strg+D | duplizieren |
| Esc | abbrechen |

6. **Tiefe** auch im Wandschnitt unter der Ansicht: hineinklicken oder ziehen; die Marke rastet an der Wandseite, an Schichtgrenzen und Schichtmitten ein. Im Feld steht, in welcher Schicht das Teil liegt.
7. **Gerade Rohre kürzen/verlängern:** Feld **Länge cm**, ein **Rohrende ziehen** (das andere Ende bleibt stehen; in der Nähe eines passenden Anschlusses rastet das Ende ein) oder **+ / −** (1 cm, Umschalt = 1 mm). Felder lassen sich nur nach **Installation bearbeiten** ändern.
   **Leitungen (NYM …)** aus *Elektro > Leitungen* werden zuerst gerade gelegt (1 m). Ein **Klick auf die ausgewählte Leitung** setzt dort einen **Knickpunkt** (weißes Quadrat) – gleich weiterziehen; Knickpunkte lassen sich ziehen, **Doppelklick** oder Rechtsklick entfernt sie. Die Länge ist dann die Summe der Stücke.
8. Die **3D-Vorschau** rechts unter dem Einbauteile-Baum zeigt die Wand durchscheinend mit allen Teilen – so sind Schwenken und Kippen gut zu sehen. Maus links ziehen = drehen, Rad = zoomen, **Ansicht zurücksetzen**.
9. **Speichern** übernimmt alle Teile der Wand, **Verwerfen** verwirft sie.

**Fließrichtung:** Die Muffe ist als Verdickung gezeichnet; HT-Rohre haben die Muffe oben (zulaufseitig), dazu zeigt ein Pfeil die Fließrichtung Muffe → Spitzende.

**Anschlüsse (Punkte an den Enden):** rot = offen, grün = verbunden (passt: gleiches System, gleiche DN, Spitzende in Muffe), blau = bewusst offen oder Übergabe in einen Nachbarraum. An jedem Anschluss sitzt **genau ein Teil**, und nur **in einer Flucht** (Richtungswechsel nur über Bögen, Abzweige, T-Stücke). **W** (Shift+W zurück) dreht ein Rohr, einen Bogen oder Abzweig in sich um 15° um die Achse eines Anschlusses (bei genau einer Verbindung um diese). Wie bei R, Q/E, A/D und T drehen alle verbundenen Teile mit; mit gedrückter Alt-Taste nur das markierte Teil (an einer Verbindung bleibt es dabei verbunden). Liegen zwei passende Anschlüsse übereinander (näher als 1 cm), richtet sich das ausgewählte Teil (mit allen daran hängenden Teilen) **automatisch** richtig aus und rastet ein. Liegt ein Teil schräg oder doppelt an einem Anschluss, wird er **rot umkreist** und **Speichern** ist gesperrt, bis das Teil richtig eingerastet oder weggerückt ist. Rechtsklick auf einen Anschluss: **bewusst offen**, **trennen**, **auf der anderen Wandseite weiterbauen** oder **im Geschoss oben/unten weiterbauen**.

**Nachbarräume:** Ein Rohr, das durch die Wand bis zur anderen Seite reicht (Q/E), oder ein Anschluss an Decke bzw. Boden wird zur Übergabe. Auf der anderen Wandseite bzw. in der Wand des Geschosses darüber/darunter erscheint der Anschluss als gestrichelter Kreis; dort ein Teil ansetzen – es rastet ein. Durchbrüche (Kernbohrungen) werden automatisch berechnet.

**Schlitze:** Liegt ein Teil in der Wand, berechnet das Programm Schlitz bzw. Dosen-Aussparung je Schicht (Mengen). Zu tiefe Schlitze in der tragenden Schicht werden gewarnt (Richtwerte senkrecht 3 cm, waagerecht 1,5 cm – geschätzt, statisch prüfen lassen).

In **Haus 3D** zeigt **Technik › Einbauteile** alle Teile mit ihren Anschlüssen; der Link **Wände** im Hinweisfeld öffnet das Teil in der Wandansicht.

## Räume

Raumdaten, Beläge und Schächte eines Raums. Die Form des Raums wird im **Grundriss** bearbeitet.

### Raum auswählen

- Links die **Raumliste** aller Geschosse (Nummer, Name, Fläche, Nutzung); oben nach **Geschoss** filtern oder **Suchen …**.
- Oben stehen Fläche, Umfang, lichte Höhe und Volumen. Die Höhe ergibt sich aus Geschosshöhe minus Bodenaufbau, wenn keine eigene eingetragen ist.
- Der Plan zeigt den Raum mit den Wänden, den Belägen (farbig) und den Schächten (violett schraffiert).

### Raumdaten ändern

1. **Bearbeiten** klicken.
2. **Nummer** (im Haus eindeutig), **Name**, **Nutzung (DIN 277)**, **Lichte Höhe cm** (leer = automatisch), **Notiz** eintragen.
3. **Speichern und zurück** übernimmt Raumdaten, Beläge und Schächte zusammen (während des Speicherns grau mit Speichert ) und kehrt in die Ansicht zurück; **Abbrechen** verwirft alles.

### Bodenbeläge

- **+ Belag ganzer Raum:** ein Belag für den ganzen Raum, z. B. Parkett.
- **+ Teilfläche:** danach ein Rechteck im Plan ziehen, z. B. ein Fliesenfeld; die Teilfläche ersetzt dort den Belag des ganzen Raums. Teilflächen dürfen sich nicht überlappen.
- Im Feld rechts **Aufbau** wählen (Aufbauten der Kategorie **Belag** im Katalog) und bei Teilflächen x / y / Breite / Tiefe korrigieren.
- Schächte werden aus allen Belägen ausgespart.

### Wandbeläge (Fliesenspiegel, Sockelleiste)

- **+ Wandbelag:** zunächst eine Sockelleiste an allen Wänden (0–6 cm).
- **alle Wände des Raums** abwählen, um einzelne Wände anzukreuzen; je Wand optional einen Bereich **von / bis cm** entlang der Wand.
- **Höhe von / bis cm** über dem Geschossboden, leer = ganze Wandhöhe. Türen und Fenster werden ausgespart.

### Schächte

- **+ Schacht:** ein Rechteck im Plan ziehen. Dann **oberstes Geschoss** (dessen Boden geöffnet wird) und **unterstes Geschoss** (dessen Decke geöffnet wird, der Boden bleibt zu) wählen.
- **Leitungen im Schacht** ankreuzen (Abwasser, Zuwasser); eine Leitung, die nicht im Schacht verläuft, wird beim Speichern abgelehnt.
- Ein Schacht gehört zum ganzen Haus; er erscheint in jedem Raum, den er berührt.

**Möblierung** folgt später.

## Katalog

Der Katalog enthält alle Bausteine des Hauses. Jede Unterseite ist gleich aufgebaut: links die Liste mit Suche, rechts das ausgewählte Element.

| Seite | Inhalt |
|---|---|
| Materialien | Baustoffe mit Farbe, Schraffur, Kennwerten, optional Produkt mit Preisen |
| Aufbauten | Schichtfolgen von Wänden, Decken, Böden |
| Bauteile | Fenster, Türen, Dachbauteile …, gebildet aus einer Klasse |
| Klassen | Vorlagen der Bauteile: Parameter und Materialrollen |
| Firmen | Hersteller und Lieferanten |
| Dokumente | Rechnungen und Angebote (nur ansehen) |

### Element ansehen

- Eintrag in der Liste anklicken; Pfeil hoch/runter wechselt den Eintrag.
- Den Trennbalken zwischen Liste und Details kann man ziehen; vorhandene Fotos erscheinen unten (Klick öffnet das Foto groß).
- **Dokumente:** Über der Liste filtern Typ, Kategorie, Firma und Jahr (zusammen mit der Suche, die auch Positionstexte durchsucht). Die Details zeigen Kopfdaten, Positionen mit Link zum Material/Bauteil, Summen und zugehörige Dokumente. Firmen, Materialien und Bauteile zeigen ihre **Belege**; in der Angebotstabelle führt die Spalte „Beleg“ zum Dokument.

### Anlegen, ändern, kopieren, löschen

1. **+ Material** (bzw. **+ Aufbau**, **+ Bauteil** …) legt ein neues Element an; die `id` wird aus dem Namen vorgeschlagen und ist danach nicht mehr änderbar.
2. **Bearbeiten** öffnet das Formular des gewählten Elements (Hinweise je Typ unten).
3. **Speichern** – bei Erfolg erscheint unten rechts „Gespeichert: …“.
4. **Kopieren** (Bauteile, Klassen) legt eine Kopie zum Anpassen an.
5. **Löschen** fragt nach und geht nur, wenn das Element nirgends verwendet wird; sonst nennt die Meldung die Verwender.

- **Aufbau:** Schichten mit **+ Schicht** hinzufügen, mit ↑ ↓ umsortieren, mit ✕ entfernen; die Gesamtdicke wird live angezeigt.
- **Bauteil:** zuerst die **Klasse** wählen; das Formular zeigt dann genau deren Parameter. Die Vorschau zeigt das Bauteil live.
- **Produkt:** Häkchen setzen, Hersteller, Modell und Angebote (Lieferant, Preis, Datum) eintragen.

### TGA – Bäume, Baugruppen, Kürzung, Eignung

- **+ Baum** legt einen TGA-Baum an (Filter **Bäume**). Im Baum-Editor: **+ Ordner**, **+ Objekt** (TGA-Objekt per Referenz, Vorschlagsliste), ↑ / ↓ verschieben, ✕ entfernen; **Reihenfolge** ordnet die Bäume in der Palette.
- **TGA-Baugruppe** (**+ Baugruppe**, Filter **Baugruppen**): ein **Hauptobjekt** (z. B. Unterputz-Abzweigkasten) mit **Bestandteilen** (z. B. 3 × WAGO-Klemme 3-polig). Bestandteile als Liste mit **Anzahl**; bei Klemmen wird der **Leiter** (L, N, PE …) gewählt. Einbaudaten, Darstellung und Eignung kommen vom Hauptobjekt; **max. Anschlüsse** = kleinste Polzahl der Klemmen (3 × WAGO 3-polig → 3 Leitungen). So gibt es mehrere „Versionen“ einer Dose. Eine Baugruppe wird als **ein Teil** eingebaut; die Stückliste zählt Hauptobjekt und Bestandteile. Baugruppen in Baugruppen sind nicht erlaubt.
- **Abstrakte TGA-Objekte sind veraltet:** Sie bleiben lesbar (Filter **veraltet (abstrakt)**), werden aber nirgends mehr angeboten. Im Baum stattdessen die tatsächlich verwendeten konkreten Objekte (z. B. je Kabel Querschnitt / Adern) oder Baugruppen eintragen.
- **Kürzungseigenschaft:** Das Teil ist in jeder Länge bis **bis … m** verfügbar (z. B. Kabel NYY 50 m → 15 m), mit Vorgabelänge und Mindestlänge.
- **Eignung:** geeignet für Wand / Boden / Decke / Dach, Einbau in (eingelassen) / auf (aufliegend). Ohne Angabe gilt bei Dosen die Montage (Unterputz = in, Aufputz = auf, angezeigt als „abgeleitet aus Montage“). **Ohne Eignung wird ein Objekt in keiner Palette angeboten** – die Ansicht zeigt dann rot „keine Eignung“, die Liste die Markierung **keine Eignung**. Auf der Seite **Wände** (Reiter Baum) erscheinen nur Objekte, die für Wände und den gewählten Einbau (in / vor der Wand) geeignet sind. Ein unpassend eingebautes Teil gibt einen Hinweis.
- **Layout (Planung):** Ausmaße (falls nicht am Produkt), Anschlusspunkte je Seite, max. Anschlüsse (z. B. WAGO 3-polig → 3), Darstellung.

### TGA – Liste / Baum und Darstellung

- Oben die Reiter **Liste** (alle Einträge mit Suche und Filter) und **Baum** (die TGA-Bäume; Klick auf ein Objekt öffnet es, **bearbeiten** am Baum öffnet den Baum-Editor).
- Jeder **Ordner** im Baum-Editor hat einen **Filter** (Klasse, Suchtext). Die Auswahlliste der Objekte darin zeigt nur passende Bauteile; Unterordner erben den Filter.
- Unten der **Darstellungs-Editor** (im Bearbeiten-Modus): vereinfachte Ansicht des Bauteils in der Wand zeichnen (Rechteck, Kreis, Linie, Text, **Kabel**; Raster 1 cm, Fang 1 mm, Mausrad = Zoom) und **Anschlusspunkte** setzen. Vorhandene Formen und Anschlusspunkte mit jedem Werkzeug anklicken = auswählen (blau hervorgehoben, gestrichelter Rahmen, Griffe zum Ändern der Größe bzw. der Linienenden), ziehen = verschieben, **Entf** = löschen, Pfeiltasten = 1 mm (Shift 1 cm), Esc = Auswahl aufheben. **Kabel**: Werkzeug Kabel, ersten und zweiten Anschlusspunkt anklicken; das Kabel ist flexibel und folgt den Anschlusspunkten. Klick auf die Kurve des ausgewählten Kabels fügt einen Biegepunkt ein (ziehen = Kurve formen, Doppelklick = entfernen). Wird ein Anschlusspunkt gelöscht, werden seine Kabel nach Rückfrage mitgelöscht. Je Anschlusspunkt Lage und Tiefe, Richtung, Leitungssystem, DN bzw. Adern und **Winkel**: *nur rechtwinklig* (Rohr in Rohr) oder *beliebig* (Leitungen; Standard bei Kabeln). So erscheint das Teil auf der Seite **Wände**.
- **Kürzungseigenschaft:** Bei einer max. Länge (z. B. 50 m) ist die **Vorgabe** Pflicht (z. B. 1 m) – mit dieser Länge wird die Leitung angelegt.

### TGA – Verbindungsregeln

Die Seite **Katalog – TGA** zeigt Rohre, Formteile, Kabel, Klemmen, Dosen und Endgeräte mit ihren Verbindungsdaten. Die Filter wählen eine Klasse oder **nur mit Hinweisen**.

- **Klasse → Verbindungsregeln:** je Leitungssystem (HT, KG, PP-R, Alu-Verbund, Strom) Medium, Verbindungsart (Steckmuffe, Schweißen, Pressen, Klemme), erlaubte Partner, bei Kabeln die Orte (Dose, Endgerät) und ob die Fließrichtung gilt.
- **Rohr / Formteil → Anschlüsse:** DN, Muffe oder Spitzende und bei Abwasser der Fluss. Regel HT/KG: Muffe gegen die Fließrichtung (Muffe = rein, Spitzende = raus); andere DN nur über Übergang oder Abzweig. PP-R und Alu-Verbundrohr (11,6 / 16 mm): Rohr nur über Formteile bzw. Presskupplungen.
- **Kabel → Leiter:** ohne Eintrag gilt der Standard aus der Aderzahl (3G: L braun, N blau, PE grün-gelb; 5G: L1 braun, L2 schwarz, L3 grau, N, PE); eigene Belegung über **+ Leiter**.
- **Klemme:** Pole, Querschnitt min/max, *Endstück erlaubt*, *Teilbelegung erlaubt*. **Dose:** Aufputz, Unterputz oder Hohlwand. **Endgerät** (Steckdose, Schalter, Lampenfassung …): welche Leiter es aufnimmt.
- Kabel dürfen nur in Dosen oder an Endgeräten enden; in der Dose wird jede Ader über eine Klemme gleicher Leiterart geführt (in der Leitungsdatei unter `joints`). Verstöße erscheinen als Hinweis auf der Seite und unter **Mengen**.

## Mengen

- Oben das **Prüfergebnis**: grün „Modell gültig“ oder rot „Modell ungültig“ mit der Liste der Fehler (Ort und Meldung); Warnungen orange.
- Darunter die **Mengen**: Materialien (Volumen, Flächen, Laibungen), Wände, Bauteile mit Preisen, Räume (mit Nummer, Nutzung, Höhe und Volumen, darunter die Flächen nach DIN 277), Beläge, Schächte, Decken, Tragwerk, Dachstuhl, Dach, Treppe, Böden und Fußbodenheizung, **Wandheizung** (Heizkreise mit Auslegung, Plattenfelder je Wand, Stückliste der Platten und Presskupplungen mit Preisen, Schichten), **Abwasser** (Leitungen mit Gefälle, Durchbrüche mit Kernbohrung, Stückliste der Formteile und Stangen, Zuschnitt), Fassade, Innendämmung und die **Summen**.

So behebt man einen Fehler: Meldung lesen → Ort (z. B. `storey:ground.w-west`) auf der Seite **Grundriss** oder **Wände** bzw. im **Katalog** öffnen → korrigieren → speichern → Mengen neu laden.

## Dokumentation

- **Benutzerhandbuch** (diese Seite): Bedienung der Anwendung.
- **Tech.Doku:** fachliches Modell, Aufbau, Architektur, Sicherheit, Schnittstellen und die automatisch erzeugte Code-Dokumentation.
- Beide haben links einen **Baum**: ▸ klappt einen Abschnitt auf, ein Klick auf den Titel öffnet die Seite. Die Breite des Baums lässt sich am Trennbalken ziehen.
- **About** zeigt Port, Startzeit und Datenordner des laufenden Servers.

## Häufige Fragen

| Frage | Antwort |
|---|---|
| Die Seite lädt nicht | Server läuft nicht – `start.cmd` ausführen; läuft er doppelt, alle Fenster „Weingaerten web“ schließen und neu starten |
| „Weingärten-Core fehlt“ | der Server wurde ohne `start.cmd` gestartet oder der Code fehlt – mit `start.cmd` neu starten |
| „Speichern“ ist grau | es gibt keine Änderung oder noch einen roten Fehler |
| Meldung „wird verwendet von …“ | das Element wird noch benutzt; zuerst die Verwender ändern |
| „Wand nicht im 90°-Raster“ | Wände müssen waagerecht oder senkrecht liegen |
| Haus 3D bleibt leer | three.js fehlt – `weingaerten-web.md` einmal ausführen lassen |
