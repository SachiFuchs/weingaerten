---
name: "add dilbert cast"
created: "2026-11-03T07:10:03.662Z"
status: pending
---

# Plan: Dilbert-Ensemble hinzufügen

## Context

- Personen = `people/<id>.md` mit JSON-Block `## Person data` (siehe people/wally.md); Core liest sie per `PEOPLE`, Startposition `start.seat` oder `{x,y,heading}`.
- Gezeichnet werden Personen nur in `/buero3d-live` (dilbert-web.md Abschnitt "Persons"): heute nur Menschen (Beine, Torso, Krawatte, Kopf, `hair_style` cap/fringe, `build` round, `mug`).
- Für Hund, Katze, Ratte und Frisuren wie Hörner/Haarbusch/Bob reicht das Schema nicht -> `look` wird erweitert.
- Hinweis: „/consense contex“ habe ich als „Projektkontext laden“ gelesen (kein Cortex-Sense-Kontext nötig). Die Bilder im Anhang dienen als Vorlage für die Skizzen; sie werden nicht ins Repo kopiert.

## Erweiterung Personendaten

Neues optionales Feld `traits` (nur Daten, wird noch nirgends ausgewertet):

```json
"traits": {"role": "Personalchefin (HR)", "summary": "...", "keywords": ["sadistisch", "Katze", "quält Belegschaft"]}
```

Für Dilbert und Wally ebenfalls ergänzt.

Erweitertes `look` (alles optional, Default = heutiges Verhalten):

- `species`: `human` (Default) | `dog` | `cat` | `rat`
- `hair_style` neu: `horns` (2 spitze Haarbüschel seitlich nach oben, Chef), `puff` (großer dreieckiger Haarbusch, Alice), `bob` (schwarzer Pilzkopf, Carol), `side` (kurzes schwarzes Haar, Asok), `none`
- `glasses`: `null` = keine Brille
- `outfit`: `shirt_tie` (Default) | `blouse` (Alice, pink, ohne Krawatte) | `dress` (Carol, langes lila Kleid statt Beinen sichtbar) | `suit` (Chef: Sakko-Farbe `jacket`)
- `fur`, `accent` (Tierfarben; z. B. Nase/Ohren)

## Skizzen (three.js, Toon + Tuschekontur, im Comic-Stil der Bilder)

| Person     | Erkennung                                                                                                                            |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Dogbert    | kleiner weißer Hund, ovaler Körper, runder Kopf mit runder Brille, 2 Hängeohren, hält rotes Buch/Becher-Prop; aufrecht stehend 0.9 m |
| Alice      | pinke Bluse, braun-roter großer `puff`-Haarbusch, keine Brille, rechte Hand als Faust (Kugel) erhoben = „Todesfaust“                 |
| Chef (PHB) | dunkelblaues Sakko, weißes Hemd, rote Krawatte, Glatze mit `horns`, keine Brille                                                     |
| Catbert    | rote Katze, aufrecht, spitze Ohren, langer Schwanz nach oben, gelbe Augen; 1.0 m                                                     |
| Ratbert    | gelb-orange Ratte, birnenförmiger Körper, Rattenschwanz, große Ohren; 0.6 m                                                          |
| Asok       | junger Mann, kurzes schwarzes Haar (`side`), Brille, weißes Hemd mit dunkler Krawatte, etwas kleiner (1.65 m)                        |
| Carol      | schwarzer Bob, langes lila Kleid, keine Brille, sehr schlank                                                                         |

Tiere: eigener Körperaufbau (Rumpf-Ellipsoid, Kopf, Ohren, Schwanz), Beine kurz; Gehen = Beinwippen wie bei Menschen, Sitzen = Rumpf auf Sitzhöhe abgesenkt. Höhe weiterhin `height` × 1.25.

## Verteilung im Büro (Startplätze)

| Person                                                                                                | Start                                                                                                |
| ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Chef                                                                                                  | Boss-Büro, `boss_chair`                                                                              |
| Catbert                                                                                               | HR-Büro, Stuhl hinter dem Schreibtisch                                                               |
| Alice                                                                                                 | Büro 1, freier Platz gegenüber Dilbert (nördliche Reihe)                                             |
| Asok                                                                                                  | Büro 1, vierter Platz (Praktikant beim Team)                                                         |
| Carol                                                                                                 | Sales-Büro, kleiner Schreibtisch nahe Flur (Vorzimmer-Ersatz – es gibt keinen eigenen Raum; Annahme) |
| Dogbert                                                                                               | Besprechungsraum, stehend am Whiteboard (Berater-Pose), `{x,y,heading}`                              |
| Ratbert                                                                                               | Büro 2, Platz am Ostfenster (Freelancer-Schreibtisch)                                                |
| Konkrete Stuhl-IDs werden vor dem Schreiben aus `LAYOUT` gelesen (keine Kollision mit Dilbert/Wally). |                                                                                                      |

## Implementation steps

1. `LAYOUT` abfragen, Stuhl-IDs für die obigen Plätze ermitteln.
2. 7 Dateien `people/<id>.md` (dogbert, alice, boss, catbert, ratbert, asok, carol) nach Wally-Vorlage anlegen, inkl. Documentation-Tabelle, `look`, `traits`; `traits` in dilbert.md / wally.md ergänzen.
3. dilbert-core.md: Person model um `traits` (durchgereicht, ungenutzt) und erweiterte `look`-Felder ergänzen; Smoke-Test-Erwartung auf 9 Personen mit Startplätzen; Code patchen, py\_compile, sha256 neu.
4. dilbert-web.md: Persons-Abschnitt um `species`, neue Frisuren, `outfit`, `glasses: null`, Tierkörper erweitern; Prüfung `/api/people` -> 9 Personen; Web-Code patchen, sha256 neu.
5. dilbert-doku.md: Abschnitt „Personen“ mit allen 9 Figuren und Startraum.
6. Server stoppen, neu starten, visuell prüfen.

## Verification

- `scripts\smoke_core.py`: `PEOPLE` liefert 9 Personen, alle sitzend/stehend am erwarteten Platz, keine zwei auf demselben Stuhl; `MOVE` alice auf Dilberts Stuhl -> `Stuhl besetzt von Dilbert`.
- `/buero3d-live` im Browser: jede Figur per Screenshot gegen die Vorlagen prüfen; Auswahl + Bewegung für ein Tier (Ratbert) und einen Menschen (Alice) testen, Sitzen eines Tiers sieht plausibel aus.
- Hover-Sprechblasen zeigen die neuen Namen.

## Critical Files

- people/\*.md - neue Personendaten + traits
- dilbert-core.md - Person model, Smoke-Test
- dilbert-web.md - Figuren-Rendering in three.js
- dilbert-doku.md - Doku
