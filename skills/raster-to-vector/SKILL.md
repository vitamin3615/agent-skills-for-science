---
name: raster-to-vector
description: Redraw a raster figure (PNG/JPG) as a clean, layered, editable vector drawn in VectorCraft (a .vectorcraft document plus SVG and PNG), the way a designer would. You name the parts, a local toolkit measures and stacks them, and zoomed side-by-side checks catch the errors. Use whenever the user wants to vectorize, trace, redraw or "convert to SVG" a scientific illustration, anatomy plate, diagram, BioRender-style figure, icon or schematic; wants an editable or scalable version of a figure; or complains that an auto-trace looks jagged, patchy, banded or lost its outlines. Not for photographs.
---

# Raster to vector: redraw, don't trace

The raster is a **template**. It supplies coordinates and colours, and the deliverable is a clean illustration built from named parts, **not a pixel copy**. This workflow reproduces the method behind a redraw that a user rated "very good": a uterus diagram rebuilt as 36 named shapes. Every lesson from that redraw is built into the steps below (see `<skill_dir>/references/case_study_uterus.md`).

**Quality comes first.** There is no tool-call budget. Expect several mask iterations and one round of user feedback. A lost part, a leak between parts or a visible seam is always worth another iteration.

Paths below use `<skill_dir>` for the folder that contains this file. All coordinates are in source pixels.

## Choose the route

| Figure | Route |
|---|---|
| Up to ~40 nameable parts: diagrams, anatomy plates, line art, icons | **Redraw** (this workflow) |
| Dense, textured figures (organelles, BioRender scenes) | **Redraw** the structure, and mark textured parts `"draw": "trace"` so the engine traces their texture inside clean outlines |
| Hundreds of tiny items, or the user asks only for a quick trace | **Quick trace**: `vectorize.py` (see the end of this file) |

## Setup

- Python: `pip install -r <skill_dir>/scripts/requirements.txt` (numpy, scipy, scikit-image, pillow, resvg-py).
- **VectorCraft (required).** The drawing is built in VectorCraft, so the result is clean and easy to edit later. `redraw.py` drives `vectorcraft-cli` through its MCP server. VectorCraft simplifies each part, draws every primitive as a live shape (circles as ellipses, leaders as lines, arrows as lines with arrowheads), groups and stacks them, and saves the `.vectorcraft` document.
  - **If it is missing**, `redraw.py` stops with exit code 3 and the message `VectorCraft is required`. Stop and ask the user to install it, pointing to `<skill_dir>/references/vectorcraft.md`. Do not switch to another route on your own.
  - **The only exception** is an image VectorCraft cannot handle after you tried: build with `--geometry python` (a pure-Python SVG, no `.vectorcraft`), and tell the user why.
  - `--masks-only` does not need VectorCraft.

## Workflow

### 1. Look and name the parts

```
python <skill_dir>/scripts/inspect_figure.py <input.png> <work_dir> [--zoom x0,y0,x1,y1]... [--probe x,y]...
```

View `grid.png` (the figure zoomed, with a labelled source-pixel grid) and `palette.png`. Then write down:
- **Parts**, the shapes a designer would draw: name, parent (a part drawn on top of and inside another), drawing order.
  - Name by meaning, not by colour. Similar pinks in different organs are different parts.
  - A colour that appears only inside a part (a lining between two layers) is usually just the parent showing through, not a part.
  - Do not split one shape where the source draws no line (the cervix and the vagina of one body). Each part gets its own outline and tone bands, so a split shows as a seam.
  - Sibling order: where two parts meet, the one whose edge stays crisp and unbroken is on top, so list it later.
- **Drops**: text and labels.
- **Primitives**: a backdrop circle, leader lines and dots, arrows. A simple geometric shape is drawn, not traced, but only when a fit to its pixels is near exact. A roundish organ is not a circle.
- **Line art**: ink outlines and thin coloured lines. These become stroke parts.
- **Shading**: nested flat tones (bands, cores, highlights) or smooth ramps.
- **Texture**: stipple, cristae, hatching. These become `trace` parts.

### 2. Place seeds by probing

Use `--probe x,y` to check that each seed lands on the part's own colour, not on an edge, an arrow or a texture dot.

- **Seed every distinct colour zone of a part.** A part with a gradient needs seeds in its light and dark zones.
- **Seed every visible piece.** Both sides of a symmetric figure, and each piece of a part split by another part.
- Unseeded areas are flooded from their neighbours. This was the cause of every leak found while building this skill.

### 3. Write `parts.json`

See [The part spec](#the-part-spec) below. Worked examples are in `<skill_dir>/examples/` (`uterus`: flat tones; `heart`: line art; `cell_animal`: dense hybrid; `nephron`: thin outlined tubes).

### 4. Check the masks (most errors are caught here)

```
python <skill_dir>/scripts/redraw.py <input.png> parts.json <out_dir> --masks-only [--zoom x0,y0,x1,y1]...
```

1. **Read the per-part summary** it prints:
   - a box far larger than the part means a leak;
   - `EMPTY` or a few px means a bad seed;
   - `adopted ... (check it)` means an unseeded patch was given to a part by colour.
2. **View `part_map.png`.** Each part's own region is tinted, outlined and labelled; dropped pixels are cyan. A tint where that part does not belong is a leak: add a seed for the part that owns that area. Small leaks are invisible at full-image scale, so add `--zoom` boxes for close-ups (`part_map_zoom_N.png`). `inspect_figure.py --zoom` also works on any output PNG.
3. **View `masks.png`**, the source next to the masks painted flat in drawing order.

Fix the spec and repeat until every part is right. Each run writes a new `<stem>_redraw_vN` folder.

### 5. Build

```
python <skill_dir>/scripts/redraw.py <input.png> parts.json <out_dir> [--zoom x0,y0,x1,y1]...
```

It prints a score line (objects, anchors, gradients, MAE, edge F1, seam px, lost px) and a `vectorcraft:` line. The latter counts what VectorCraft holds (paths, ellipses, lines, groups) and how many arrows are native or outlined. The folder holds:
- the deliverable: `<stem>_vN.vectorcraft` (the editable document), `<stem>_vN.svg` and `<stem>_vN.png` (exported from it);
- the review evidence: `review_1.png`, `review_2.png`, … (three source | vector pairs each, short enough to view at full size) and `score.json`.

### 6. Review zoomed, then iterate

View every `review_N.png`, source beside vector at 4×:
- the 4 places where most parts meet;
- the 2 worst tiles (dropped text excluded);
- every `--zoom` box you asked for.

Add `--zoom` boxes for the parts the user cares about. Every real defect in the gold redraw was invisible at full-image scale. Go through the [review checklist](#review-checklist). Treat `seam_px` and `lost_blobs` in `score.json` as alarms that point at boxes.

MAE and edge F1 are **alarms, not targets**. The gold redraw has more than twice the engine's MAE and looks far better. Never tune for them.

### 7. Show the user, take feedback

Show `<stem>_vN.png`, or a source | vector sheet of the key areas, and ask what to improve. The gold redraw needed one feedback round, about ovary colours and a gap. Fix it in the spec, rebuild (new version) and zoom on what they named. A fix the spec cannot express (the gold redrew one ovary by hand) can be made in the `.vectorcraft` document with the VectorCraft MCP tools (`<skill_dir>/references/vectorcraft.md`). Say so when you deliver, because a rebuild from `parts.json` does not repeat it.

**Keep what the verdict teaches.** This skill exists because one "very good" redraw was written down step by step. When you maintain the skill (the user asks for it, or the skill folder is in their project), do the same:
- **Approval:** save `parts.json` under `<skill_dir>/examples/<name>/` and the source | vector sheet in the project. Add the figure to [What to expect](#what-to-expect) as a reference that later changes must not make worse.
- **A critique:** after fixing it, add a symptom → cause → fix row to `<skill_dir>/references/pitfalls.md`. If the toolkit had to change, also note it in `method.md`.

### 8. Deliver

Report:
- the `.vectorcraft`, SVG and PNG paths with their version (if `--geometry python` was used, say why VectorCraft could not be);
- the object and anchor counts;
- what was dropped on purpose (text);
- known cosmetic limits (see [What to expect](#what-to-expect)).

Keep `parts.json` with the result: it reproduces and edits the redraw. Say that the result is a redraw that follows the template, not a pixel copy.

## The part spec

```json
{
  "scale": 4,
  "drop": {"grey_text": true, "boxes": [[67, 189, 118, 219]]},
  "background": {"seeds": [[5, 5], [100, 240]], "tolerance": 6},
  "tuck": 2,
  "primitives": [
    {"type": "circle", "name": "backdrop_circle", "fit_color": "#b49dcb", "z": "bottom"},
    {"type": "leaders"},
    {"type": "line", "x1": 0, "y1": 5, "x2": 90, "y2": 5, "stroke": "#333333", "stroke-width": 2}
  ],
  "parts": [
    {"name": "uterus", "seeds": [[172, 52], [150, 262], [195, 262]], "smooth": "organ"},
    {"name": "cavity", "parent": "uterus", "seeds": [[172, 110]]},
    {"name": "left_ovary", "seeds": [[60, 160]], "tones": 2, "stroke": "#efccca", "smooth": "detail"},
    {"name": "ink", "colors": ["#000000"], "tolerance": 35, "draw": "strokes", "fill_holes": false, "close": 0},
    {"name": "nucleus", "seeds": [[155, 80]], "draw": "trace"}
  ]
}
```

**Top level**

| Key | Meaning |
|---|---|
| `scale` | Output px per source px. Default 4 for inputs ≤ 900 px, else 1. |
| `drop.grey_text` | Remove grey or black text and leaders (saturation < 20, mean < 185). Dropped pixels are given to the nearest part, so text inside a part vanishes into it. |
| `drop.boxes` | Remove whole boxes. |
| `background` | Seeds of the page or backdrop (default: the 4 corners). Background-coloured areas that no seed reaches (cut off by a ring or a leader, or split off by the figure, ≥ 1% of the image) are added automatically. |
| `tuck` | Px each part extends under the parts drawn after it (default 2), so no seam can open. |

**Primitives**, drawn by VectorCraft as live shapes:

| Type | How it is made |
|---|---|
| `circle` with `fit_color` | RANSAC fit to that colour. `fill`, `stroke` and `stroke-width` default to `auto` (sampled). `z`: `bottom` or `top`. |
| `leaders` | Straight grey leader lines and their end dots, recovered from the dropped text mask. |
| `arrows` with `color` | Every straight arrow of that colour, measured: tail, tip, shaft width, head length, head width. Each is kept only if the drawn arrow overlaps its blob with IoU ≥ `min_iou` (0.6). Curved, merged or unmeasurable arrows are left to the parts. Optional `box`, `tolerance`. Drawing: a head about as long as it is wide (length/width 0.75–1.25) becomes a native VectorCraft arrow, one line with a Triangle head scaled to the measured width, edited by dragging its ends. Other heads are drawn as the exact 7-point outline. |
| `arrow` | One arrow given explicitly: `x1, y1` (tail), `x2, y2` (tip), `width`, `head_width`, `head_length`, `fill`. Use this when the source is too small to measure (arrows a few px wide). Read the numbers off the zoomed grid. |
| `circle`, `ellipse` (with `angle`), `rect`, `line`, `polyline`, `path` | Given explicitly in source px. |

**Parts**, listed parents before children; list order is drawing order:

| Key | Meaning |
|---|---|
| `name` | Unique; becomes the SVG id. |
| `seeds` | `[[x, y], ...]`. Each grows a marker over connected pixels within `tolerance` ΔE of the seed colour (default 8), but not through 1–2 px bridges. A marker watershed on colour edges assigns every pixel, so parts split by adjacency, not by coordinate cuts. Markers are eroded by 1 px, so a part only 1–3 px wide cannot be seeded: select it with `colors` (and a `box`). |
| `colors` | Instead of or besides seeds: take every unclaimed pixel of these hex colours (for ink and scattered white details). A patch touching a seeded region of similar colour is left to that region. |
| `parent` | Drawn on top of and inside the parent. A part's shape is its own pixels plus all its descendants', closed (`close`, default 1) and hole-filled (`fill_holes`, default true; background holes stay open). |
| `box` | Limit the seed markers to `[x0, y0, x1, y1]`. |
| `smooth` | `organ` (σ 0.8, simplify 1.25 px), `layer` (0.8, 1.0, the default), `detail` (0.8, 0.75), `fine` (0.6, 0.4: scalloped edges), `sharp` (0.5, 0.5: valve tips). `fine` and `sharp` keep pixel steps on long straight or gently curved edges, so use them only on small or truly scalloped parts. A kink at a junction often goes away with `organ`. |
| `tones` | An int: that many nested flat tone layers, found along the part's main colour axis and stacked from the edge colour toward the core colour (cores and highlights end on top). Or a list of hex colours: each takes the pixels nearest to it and within 6 ΔE, and the base colour must not be in the list. Parts with tones get a flat base: the median of the pixels that are neither tone nor outline. `tone_min_px` (default 10). The mask summary prints the layers found and warns when none were. |
| `paint` | `auto` (flat, linear or radial gradient, fitted; the default), `flat`, or a hex colour. |
| `stroke` | The outline. Omit it for no outline; `auto` guesses (unreliable). Two explicit forms:<br>- **A hex colour probed from the source** (e.g. `"#efccca"`): pixels within 2.5 px of the edge and within 10 ΔE of it are the outline. Its colour is their median, its width is their count ÷ edge length (clipped to 0.75–2.5 px), and those just outside the part are pulled into it.<br>- **`{"color": "#hex", "width": px}`**, used exactly as given. Use it for antialiased 1 px dark outlines, where the hex form comes out too thin and too light, and add the outline's colours to the part's `colors` so its region reaches the outline's outer edge. |
| `draw` | `fill` (the default), `strokes` (centreline strokes, width measured per chain: ink and thin coloured lines), or `trace` (a clean outline plus the engine's traced texture, clipped to it). |
| `tolerance`, `min_px` | Seed colour tolerance; the smallest piece kept. |

## Review checklist

- [ ] Every part is present; no two parts merged; no tint leaks in `part_map.png`.
- [ ] Outlines are smooth with no wobble or notches, and scalloped edges stay scalloped (`fine`).
- [ ] No white hairlines or seams at junctions (`seam_px` near 0; zoom on junctions).
- [ ] Shading is stacked edge → core like the source. Highlights and cores are present, and no tone is inverted.
- [ ] Outlines (rims, ink) are present where the source has them, at the right colour and width, and continuous.
- [ ] Circles, leader lines and dots are true primitives; text is dropped (or kept, if the user asked).
- [ ] The colours in the gaps beside each part are right. Zoom there and compare; the gold redraw's last bug was a wrong colour in such a gap.
- [ ] `lost_blobs` in `score.json` are explained: dropped on purpose, or fixed.

## What to expect

Measured on the reference figures. The example specs are in `examples/`:

| Figure | Style | Objects | Anchors | MAE / edge F1 | Notes |
|---|---|---|---|---|---|
| Uterus (353×296) | Flat tones, rims, primitives | 40 | 541 | 1.64 / 0.81 | Matches the gold redraw (35 objects, 526 anchors, MAE 3.09) by eye; the user rated it "great". A blind agent with only this skill reached the same level. VectorCraft holds 3 live ellipses (backdrop, dots) and 4 lines (leaders) |
| Heart (400×400) | Line art | 53 | ~740 | 3.87 / 0.90 | Ink as constant-width strokes fitted by VectorCraft (`detail`: smoother long lines than `fine`, sub-pixel shifts raise MAE); 17 arrows fitted and drawn as native VectorCraft arrows (one line each in the document; the SVG export splits each into shaft and head) |
| Cell (400×266) | Dense, textured | ~1060 | ~11800 | 3.12 / 0.82 | The `trace` hybrid; the engine alone gives 3.23 / 0.89 with 723 objects but ragged silhouettes |
| Nephron (237×400) | Thin tubes, texture | 73 | ~780 | 2.55 / 0.94 | Written by a blind agent; tubes 2–3 px wide; the user rated it "great". VectorCraft tilts the thinnest limb slightly after Simplify |

Runtime is 5–20 s per build. Known limits:
- Only straight arrows with filled triangular heads are fitted. Curved, barbed or outlined arrows, and arrows touching a same-coloured shape, stay traced unless given explicitly.
- Text is dropped, not recreated as `<text>`.
- Repeated objects are not yet turned into symbols.
- A stroke part has one width per centreline chain, not a tapering width.

## Quick trace (engine)

For a fast, fully automatic result, or for figures with hundreds of tiny items:

```
python <skill_dir>/scripts/vectorize.py <input.png> <out_dir> [--hints hints.json]
```

It writes `<stem>_vN.svg` and a `<stem>_vN_review/` folder (`crops.png`, `worst_tiles.png`, `metrics.json`). It traces regions rather than named parts, so expect wobbly edges and seams compared with a redraw. Its hints are listed in `<skill_dir>/references/method.md`.

## Python API

```python
import sys
sys.path.insert(0, "<skill_dir>/scripts")
from pathlib import Path
from redraw import redraw

stats = redraw(Path("figure.png"), Path("parts.json"), Path("out"))   # or pass the spec as a dict
```

## References

- `<skill_dir>/references/case_study_uterus.md`: the gold-standard redraw step by step, and how each of its lessons maps to the toolkit.
- `<skill_dir>/references/pitfalls.md`: symptom → cause → spec fix.
- `<skill_dir>/references/vectorcraft.md`: install, the headless MCP server, what the build does in VectorCraft, and its quirks.
- `<skill_dir>/references/method.md`: how the toolkit and the engine work, for maintainers.
