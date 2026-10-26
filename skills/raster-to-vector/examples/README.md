# Example part specs

Each folder holds the `parts.json` that produced the reference results in `SKILL.md`. They show the styles the workflow handles:

| Example | Style | What it shows |
|---|---|---|
| `uterus/` | Flat tones, rims, backdrop circle, leaders | Seeds for every colour zone, nested `tones`, `stroke` outline colours, `fine` smoothing for scalloped edges, the `grey_text` drop, the fitted `circle` and `leaders` primitives |
| `heart/` | Line art (black ink, white arrows) | `colors` parts, ink as `"draw": "strokes"` with `fill_holes: false`, white arrows fitted as `arrows` primitives, `sharp` smoothing for valve tips |
| `cell_animal/` | Dense, textured (organelles) | The structure as named parts, with texture as `"draw": "trace"` on textured parts |
| `nephron/` | Thin tubes with a 1 px outline, small arrows | Written by a blind agent with only the skill. Shows:<br>- a `stroke` given as `{"color", "width"}`, with the outline colours added to the part's `colors` so its region reaches the outline;<br>- 2–3 px vessels selected by `colors` + `box` (too thin to seed);<br>- extra background seeds in small white gaps;<br>- arrows too small to measure given explicitly. |

The heart, cell and nephron sources are in the development test set (`testset/png/`). The uterus source is the anatomy plate from the gold-standard case study (`references/case_study_uterus.md`).

The uterus and nephron builds from these specs were rated "great" by the user (2026-10-26), so they are the reference for regressions.

Coordinates are source pixels of those images, so a spec only fits its own image. Use them as patterns, not templates.
