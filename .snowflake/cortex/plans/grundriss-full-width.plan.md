# Grundriss: full width + editable wall name

## Context
- Width: [style.css](code/weingaerten_web/static/style.css) line 8 caps `main` at 1264px; Katalog lifts it via `main:has(#katgrid){max-width:none}` (line 28). Grundriss (`.planlay`) has no override.
- Wall name: [plan.js](code/weingaerten_web/static/plan.js) lines 157-165 already render a `Name` input for the selected wall (`nm.onchange` sets `w.name` and marks it changed), and the save path (plan.js:192-195, [walls_editor.py](code/weingaerten_core/editing/walls_editor.py) upsert) carries `name`. But: the panel header shows only `'Wand '+w.id`, the change fires only on blur (`onchange`), and nothing re-renders, so the edit is invisible. Need to confirm in the browser whether the field is actually missing/blocked for the user.

## Steps
1. style.css line 28: `main:has(#katgrid),main:has(.planlay){max-width:none}`.
2. Reproduce in browser: Grundriss -> Bearbeiten -> select wall; check if `Name` field is shown and if save persists it. If missing/blocked, fix the cause found.
3. plan.js: header `'Wand '+(w.name||w.id)` with id as note; use `oninput` to update `w.name` + `mark`, and update header text live (no full render, keeps focus).
4. Verify save writes the name into the model file and the wall list / Wand page show the new name after reload.
5. Sync the corresponding spec md section (generated-code convention) for both changes.

## Verification
- Wide window: Grundriss details panel reaches browser edge; other pages unchanged.
- Rename a wall, save, reload: new name in panel, wall list and Wand page.
- Run existing tests for walls_editor.

## Critical Files
- code/weingaerten_web/static/style.css - width rule
- code/weingaerten_web/static/plan.js - wall edit panel
- code/weingaerten_core/editing/walls_editor.py - save path (check only)
