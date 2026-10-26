# Method

Two tools share the engine modules:
- `redraw.py` is the main path: a redraw from a part spec.
- `vectorize.py` is the quick trace.

## A. Redraw (`parts.py`, `redraw.py`, `review.py`)

1. **Drops and primitives.**
   - `drop.grey_text` takes pixels with saturation < 20 and mean < 185, grown by 1 px; `drop.boxes` adds whole boxes.
   - Primitive circles are fitted by RANSAC: 2000 three-point circles with inliers within 1.5 px, then a least-squares refit.
   - The circle's stroke width is its antialias coverage over the visible arc. Its band of matching pixels is **unknown**, like dropped pixels.
   - `arrows`: each blob of the colour is profiled along its main axis by line coverage. The head side is the half holding the widest point. It is an arrow when it is straight (shaft offset ≤ half its width), length ≥ 3 shafts, and head ≥ 1.6× shaft. The drawn 7-point arrow must overlap the blob with IoU ≥ 0.6. Accepted arrow pixels are unknown in the watershed, so the part beneath fills under them.
2. **Markers.**
   - Each seed grows a magic-wand marker: connected pixels within `tolerance` ΔE (CIE76, Lab) of the 3×3 median at the seed. Connectivity is taken on the region eroded by 1 px, so a marker cannot cross a 1–2 px bridge.
   - Where markers of different parts overlap, they cancel.
   - `colors` parts take every unclaimed pixel of their colours, except patches touching a seeded region of a similar colour (within 2× tolerance).
   - Background pockets become background markers. These are unmarked background-coloured patches of 20+ px whose border is ≥ 35% unknown, or that cover ≥ 1% of the image.
3. **Watershed.**
   - The watershed runs on Lab Sobel strength (σ 0.5), with unknown pixels masked out so no label can run along a thin line.
   - Orphan adoption: an unmarked flat patch (strength < 6, 20+ px) far from its assigned part's colour (> 15 ΔE) but within 8 ΔE of another part's marker colour becomes that part's marker, and the watershed reruns.
   - Unknown pixels then take the label of the nearest labelled pixel.
4. **Shapes.**
   - A part's shape is its own pixels plus its descendants'. It is closed (`close`) and hole-filled, but holes that are mostly background stay open.
   - Rims: with `stroke: "#hex"`, pixels within 10 ΔE of that colour within 2.5 px of the edge are the rim. Width = rim pixels ÷ edge length. Rim pixels outside the shape are added to it.
   - Tuck: each shape grows `tuck` px into the shapes drawn after it (not its descendants).
5. **Tones.**
   - Lab values of the part's own pixels (eroded 1 px) are projected on their main axis; multi-Otsu gives the thresholds.
   - The orientation puts the deepest colour (distance-transform depth) on top; if depth does not separate the tones, the minority goes on top.
   - Tone layers are nested superlevel sets, closed, hole-filled and kept 1 px inside the part; pieces are at least `tone_min_px`.
6. **Paint.**
   - `fit_paint` (flat, linear or elliptical radial, piecewise-linear stops) runs on own pixels eroded 1 px, without tones.
   - A gradient with a stop outside the sampled colour range ± 12 falls back to flat. Parts with tones are flat.
   - Thin parts without tones (lines) take the median of their marker pixels.
7. **Geometry.**
   - Outline: the signed distance field of the shape, blurred by σ (smoothing class), contoured at 0 (or at the rim inset w/2).
   - Python route: cubic Béziers fitted at the class tolerance.
   - VectorCraft route: points thinned to 0.35 px (Douglas-Peucker keeps corners and the ends of straight runs), every chord cut into pieces ≤ 1 px, a Catmull-Rom through them, then Simplify per class (see `vectorcraft.md`). Without the cut, a long chord next to a 1 px one gives a handle that loops across thin tubes. Clip paths of `trace` parts get the Python fit, because Simplify does not reach them.
   - `strokes` parts: skeleton at 2×, branches joined through junctions (`join_branches`), each chain smoothed (σ 1.5), then passed to VectorCraft as dense points for Simplify (Python route: fitted with cubic Béziers). Width per chain = line coverage nearest the chain ÷ chain length, in 0.25 px bins. Coverage is 1 at the line colour and falls to 0 at the colour beside it within 7 px.
   - `trace` parts: the part's bounding box is cropped, pixels outside its own region are set to its base colour, the crop is upsampled 4× and traced by `decompose_shaded`. Shapes of the base colour are dropped, and the rest go in a group clipped by the part's outline.
8. **SVG and VectorCraft.**
   - `draft.svg` holds the parts only. VectorCraft simplifies them, draws the paper and every primitive as live shapes, groups and stacks them, saves the `.vectorcraft` and exports the SVG (see `vectorcraft.md`). `--geometry python` writes everything into the SVG instead.
   - Drawing order: `paper` rect, then `backdrop` primitives.
   - Then one `<name>_group` per top-level part, holding the part, its tones, its children (recursively) and any traced texture.
   - Then the `annotations` primitives.
   - Geometry is in output px (source px × `scale`).
9. **Review.**
   - `part_map.png`: tinted own regions, outlines, seeds and names; dropped pixels in cyan.
   - `masks.png`: flat preview of the shapes.
   - `review_N.png` (three pairs per sheet): 4 junction boxes (densest boundaries between different parts) plus 2 worst tiles (dropped pixels excluded) plus `--zoom` boxes, at 4×.
   - `score.json` holds the following measures:
     - `seam_px`: render shows paper inside a part where the source does not;
     - `lost_blobs`: inside a part, render and source differ by > 60 RGB over 12+ px;
     - anchors, objects, MAE and edge F1.

## B. Quick trace (engine)

All engine geometry is emitted in source-pixel coordinates; segmentation may run at a working resolution.

### 1. Load and route (`decompose.decompose`)

Transparency is composited onto white, then the image is routed to one of four paths:

| Input | Route | Why |
|---|---|---|
| Long side > 900 px, < 85 % flat foreground | **Shaded** at `WORKING_LONG` = 2400 px | BioRender-style gradients |
| Small, pale circular backdrop, `annotations=True` | **Pale parts** (`flat_regions.pale_parts`) | Labelled anatomy plates: tone groups, rim strokes, leaders |
| Small, > 12 palette modes, < 50 % flat foreground | **Shaded small**: bicubic 4× to 1600 px, then the shaded path | Gradient art at low resolution |
| Otherwise | **Flat** at native resolution | Few exact colours |

The `mode` hint overrides the auto-detection.

### 2. Shaded path (`shaded_regions.py`)

1. **Seeds.**
   - Edge strength is the per-channel Sobel maximum of a σ = 0.55 blur.
   - Fill seeds are pixels with strength < 3.2.
   - Line seeds (`line_ridges`): Sato valley response > 5 at σ 1–3, darker than a σ = 4 blur by 2, and strength < 8. This keeps the flat core of each line and cuts it where two touching lines change colour. They are joined (∪) with local-minimum ridges, which catch one-pixel coloured lines.
   - Dot seeds (`detail_dots`): black/white top-hat (disk r = 4) > 14; compact components ≤ 2r².
   - The `keep_lines` hint adds every pixel darker than its blur by 1 inside the boxes.
2. **Watershed** on edge strength.
3. **Agglomeration**, from the most similar pair upward:
   - Merge when Lab difference ≤ 14 and the boundary is soft (median strength ≤ 3.2), or difference ≤ 4.
   - A thin region (≤ 8 px) darker than its neighbour by 4 L* is an outline and never merges.
   - Groups grown from line or dot seeds never merge into paint more than 4 L* lighter. This blocks chains of antialias slivers.
   - Two ridge pieces of one colour meeting end to end (contact ≤ 3 × width) merge while both are still marks.
   - Whole-group colour gap ≤ `GROUP_GAP` (8).
4. **`split_structured`.** A region whose colours form two Lab clusters ≥ 20 apart, divided by a sharp edge (mean strength ≥ 6), is split. This prevents gradients smearing across a boundary.
5. **`join_line_fragments`.** Thin same-colour fragments close across gaps of about 2 px.
6. **Paint (`fit_paint`).** Least-squares flat vs linear vs elliptical radial (9 centres), 2–4 stops, piecewise-linear so it matches SVG interpolation exactly. The choice is penalized by stop count (+0.4 each) and radial (+0.6).
7. **Geometry (`region_geometry`)**, smallest regions first:
   - straight constant-width bar → one segment, butt caps;
   - near-constant-width line (σ of local width < 0.3 × median) → stroke, round caps, ends trimmed by 0.75 width;
   - tapered line → filled outline;
   - two concentric ellipse contours → ring stroke;
   - occupancy > 98.5 % → `rect`;
   - ellipse residual < 0.32 px → `ellipse` or `circle`;
   - otherwise σ-smoothed contours fitted with cubic Béziers (tolerance 0.8 working px).
   
   Each region tucks 2 px under later (smaller) regions, and fully under neighbours that became strokes.

### 3. Flat path (`decompose.py`)

- Palette of exact colours, with antialias mixtures rejected by non-negative unmixing.
- Ink selection for thin dark or saturated modes.
- Coverage unmixing; skeleton at 2×; branches joined through junctions; spurs < 2 widths dropped; widths integrated across the normal.
- Fills stacked largest first with 1 px tuck-under and subpixel edges.
- Repeated tiny ellipses become primitives; light enclosed shapes are painted last.

### 4. Pale-parts path (`flat_regions.py`)

- Labelling on a supersampled grid (~2400 px).
- Antialias tones (reach < 1.2 px) are dropped.
- Islands < 25 px² are reassigned.
- Hue families find enclosed parts, each with a rim stroke inset by half its width.
- Spatial groups: left, centre, right.
- Leaders become `<line>` plus `<circle>` dots.

### 5. Seam underlay (`vectorize.add_seam_underlay`)

- After the first render, a seam is a near-white render blob (> 3 px) where the source has colour, inside the figure, and at least half surrounded by shapes. Dropped lines on a white background therefore stay dropped.
- Seam colours are grouped into at most 4 clusters. Each cluster becomes one path (seams dilated by 3 px) in its median source colour, inserted right after the paper so every shape covers it.
- It is skipped when annotations were removed, because removed text renders white on purpose.
- On brain_vessel it removed 83% of the white slivers inside the lens with MAE unchanged.

### Tunable parameters (engine)

| Parameter | Where | Default | Change when |
|---|---|---|---|
| `WORKING_LONG` | decompose.py | 2400 | Dots or fine lines fuse (raise, up to ~3200; time grows ~quadratically); memory is tight (lower) |
| `response` / `contrast` | `line_ridges` | 5 / 2 | Faint lines are lost (lower) or texture becomes lines (raise); prefer `keep_lines` boxes |
| `radius` / `contrast` | `detail_dots` | 4 / 14 | Small dots are lost (lower `contrast`) or noise becomes dots (raise) |
| `GROUP_GAP` | shaded_regions.py | 8 | Gradients break into bands (raise to 10) or distinct parts merge (lower to 6) |
| `separation` / `sharp` | `split_structured` | 20 / 6 | Colour still smears across a boundary (lower `sharp`) |
| `tolerance` | `join_line_fragments` | 10 | Dashed rims (raise to 14) |
| Penalties | `fit_paint` | 0.4 / 0.6 | Too many or too few gradients |
