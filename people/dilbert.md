---
name: dilbert
description: Person Dilbert – engineer in Büro 1 of Dilbert & Co. Describes who he is and how he looks; how persons walk, turn and sit is defined once for all persons in dilbert-core.md.
usage: (data prompt – read by dilbert-core.md, not run on its own)
arguments: []
---

# Dilbert – Ingenieur in Büro 1

> **This is a non-code program.** This prompt contains **no source code** – only the description and the person data.
> The core (`dilbert-core.md`) reads the JSON block under **Person data** at runtime.
> Positions change all the time and are therefore **not** stored here, but in `state\dilbert.json` (written only by the core).

## Documentation

| | |
|---|---|
| **Who** | Dilbert, Software-Ingenieur. Weißes Kurzarmhemd, rot-schwarze Krawatte, deren Spitze immer nach oben gebogen ist, Brille, schwarze Hose. |
| **Where** | Sitzt zu Beginn in Büro 1 auf dem ersten Stuhl am Schreibtisch-Block (`buero1-chair-1`). |
| **Abilities** | Wie alle Personen: gehen (geradeaus, Kurven 30, 60, 90, 120, 180° nach links oder rechts), stehen, sitzen (hinsetzen und aufstehen in 3 Schritten, seitlich – nie durch die Lehne), drehen im Sitzen (45°, 90°), weicht Hindernissen aus und geht auf direktem Weg durch Türen – definiert im **Person model** von `dilbert-core.md`. |
| **Control** | In `Büro 3D live`: zuerst Dilbert anklicken (blauer Ring), dann Zielort oder Möbel → Dilbert geht dorthin; bei einem Stuhl setzt er sich. Esc oder erneuter Klick hebt die Auswahl auf. |
| **Character** | Talentierter, aber oft frustrierter Ingenieur mit Brille und hochstehender Haarkrause, meist ohne sichtbaren Mund. (`traits` – bestimmen, wie die Person in den Runden redet und handelt.) |
| **Drawing** | Zunächst einfach: Beine, Rumpf, Kopf, Brille, Krawatte (Farben unten). |

## Person data
```json
{
  "id": "dilbert",
  "name": "Dilbert",
  "height": 1.75,
  "radius": 0.25,
  "speed": 1.56,
  "turn_speed": 180,
  "sit_step": 0.4,
  "start": {"seat": "buero1-chair-1"},
  "look": {
    "shirt": "#FFFFFF",
    "pants": "#333333",
    "tie": "#C62828",
    "skin": "#F2C9A0",
    "hair": "#5D4037",
    "glasses": "#1A1A1A",
    "hair_style": "cap"
  },
  "traits": {
    "role": "Ingenieur (Protagonist)",
    "summary": "Talentierter, aber oft frustrierter Ingenieur mit Brille und hochstehender Haarkrause, meist ohne sichtbaren Mund.",
    "keywords": ["talentiert", "frustriert", "Ingenieur", "Protagonist"]
  }
}
```
