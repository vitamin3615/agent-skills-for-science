# Pitfalls: symptom → cause → fix

Find the symptom in `part_map.png`, `masks.png`, `review_N.png` or the per-part summary, then change the spec. All of these were met while building the skill on the uterus, heart and cell figures.

## Redraw (`redraw.py`)

| Symptom | Cause | Fix in `parts.json` |
|---|---|---|
| A part's tint covers an area of another part; its summary box is far too large | That area has no seed of its owner, so the watershed flooded it from a neighbour | Seed every colour zone and every visible piece of the owner (both sides of symmetric figures, the dark end of a gradient) |
| A part is `EMPTY` or a few px | Its seed sits on an edge, a texture dot or an arrow | Probe and move the seed into a flat area; raise its `tolerance` for striped or textured parts |
| A thin strip (a lining between two layers) gets a far-away part's colour | The strip connects to that part through a narrow channel and has no seed | Seed the strip with the part it belongs to (often the parent: the parent shows through) |
| `adopted ... (check it)` in the summary | An unseeded flat patch was given to the part whose colour it has | Usually right (a vessel seen in pieces). If not, seed the patch with its real owner |
| A seed makes another part shrink or vanish | The seed is on a colour that belongs to another part (two parts' markers cancel where they overlap) | Probe each seed; remove seeds whose colour is another part's |
| Two neighbouring parts of nearly the same colour flood each other (one wins everything) | Their markers overlap and cancel, then one floods the other | If the source draws no line between them, make them one part. Otherwise give each a `box` so the boxes do not overlap |
| A seam or edge band along a boundary the source does not show | One shape was split into two parts; each gets its own outline and tone bands | Merge them into one part |
| At a junction, the wrong part's edge is on top | Sibling order | List the part whose edge is crisp and unbroken at the junction later |
| A part's outline looks doubled or too thick | The rim colour leaked into the base colour (older versions) | Fixed: outline pixels are kept out of the base colour and tones. Set `"paint": "#hex"` to force the base |
| Tones requested but `none found` in the summary | The part's colours do not split along one axis, or the tone areas are tiny | List the tone colours explicitly (probe them) |
| Long edges look stair-stepped | `fine` or `sharp` smoothing on a large part | Use `detail` or `organ`; keep `fine` for small scalloped parts |
| A backdrop ring or a leader line takes a part's colour all the way round | A thin line was flooded by one label | Fit it as a primitive (`circle` with `fit_color`, `leaders`): primitive bands are kept out of the watershed |
| A pale backdrop pocket inside the figure turns into a part | No background seed reaches it | Usually automatic (pockets ≥ 1% of the image, or walled by drops). Otherwise add a `background` seed there |
| An outline (rim) is missing | Rims are off by default; an `auto` rim may pick a tone band | Probe the outline pixel and set `"stroke": "#hex"` |
| Tones look inverted (a core drawn as a dark ring) | No clear edge-to-core trend, so the minority tone went on top | Give `tones` as explicit hex colours in stacking order |
| Highlights or streaks missing | Too few tone levels: one level was spent on a darker zone | Raise `tones` by 1, or list the highlight colour |
| White specks along a part's edge | Antialias pixels classed as a tone | Already avoided (tones stay 1 px inside the part). Raise `tone_min_px` if specks remain |
| Ink lines blobby, broken or filled between double lines | Line art drawn as filled outlines | `"draw": "strokes"` with `"fill_holes": false, "close": 0`, selected by `colors` |
| Ink painted as a gradient or the wrong colour | Old behaviour for thin parts | Fixed: thin parts take their marker colour. Set `"paint": "#000000"` if needed |
| Arrows blobby or ragged | Arrows traced as shapes | Add `{"type": "arrows", "color": "#hex"}`: straight arrows are measured and drawn as clean primitives |
| An arrow points the wrong way, or its size is off | Too few pixels to measure (arrows a few px wide), or the tail touches another shape | Give it explicitly: `{"type": "arrow", "x1", "y1", "x2", "y2", "width", "head_width", "head_length", "fill"}`, read off the zoomed grid |
| An arrow stays traced | The fit failed the IoU check (curved, barbed, merged with a same-coloured shape) | Leave it traced, draw it explicitly, or separate it with a `box` |
| Valve tips and other sharp shapes rounded | Organ-level smoothing | `"smooth": "sharp"` |
| Scalloped edges (ovary lobes) smoothed away | Too strong a smoothing class | `"smooth": "fine"` |
| Texture (pores, cristae, stipple) lost | A part is one flat or gradient shape | `"draw": "trace"` on that part (texture traced inside its clean outline) |
| A thin rim is drawn too thick in places | A rim's width varies along it | Widths are measured per chain; split the rim into parts with `box` if needed |
| A gradient with a black or odd stop | Extrapolated where no samples are | Fixed: such gradients fall back to flat. Use `"paint": "flat"` to force it |
| Slits, prongs or a detached piece at the end of a thin straight tube (already in `draft.svg`) | Older versions: the spline overshot where a long straight run met a short end | Fixed: chords are cut to ≤ 1 px before the spline. If it reappears, compare `draft.svg` with the final SVG to see whether the draft or Simplify causes it |
| A thin straight tube (2–3 px) leans or tapers slightly; `lost_blobs` lie along it | VectorCraft's Simplify tolerance is large next to the tube's width | `"smooth": "detail"` on that part keeps it straight but follows small mask steps; choose by zoomed review |
| `redraw.py` stops: `VectorCraft is required` (exit code 3) | `vectorcraft-cli` is not installed, or its MCP server lacks a tool | Not a spec problem. Ask the user to install it (`vectorcraft.md`). Only for an image VectorCraft cannot handle, build with `--geometry python` and say why |
| A 1 px antialiased outline drawn with `"draw": "strokes"` comes out dashed | The line is too faint and thin for the skeleton | Make it the part's outline instead: `stroke: {"color", "width"}`, with the outline colours in the part's `colors` |
| A part is missing, but there are 2–3 px vessels in the source | Seed markers are eroded by 1 px, so very thin parts cannot be seeded | Select them with `colors` and a `box` (keep the boxes of similar-coloured parts apart) |
| Small white gaps inside the figure are filled by a part | Background pockets under 1% of the image are not found automatically unless walled by drops | Add `background` seeds in those gaps |
| White hairline between two parts (`seam_px` > 0) | The lower part does not reach under the upper one | Raise `tuck` (global or per part); check that the parts are stacked parent → child |
| Text left inside a part | `grey_text` missed coloured or antialiased glyphs | Add a `drop.boxes` box over the label |

## Quick trace (`vectorize.py`)

| Symptom in the crops | Likely cause | Fix |
|---|---|---|
| Thin outlines or folds missing | Line too faint for the ridge test | Add a `keep_lines` box over the area (never over dense detail such as cells or beads; it erases their outlines) |
| Small dots or beads inside objects vanished | Dots smaller than ~3 working px | For small inputs run `mode: "shaded"` so the 4× upsampling applies |
| Distinct parts merged into one shape | Merge too permissive | Use the redraw workflow for those parts |
| Thin rim drawn as dashes or beads | A faint 1 px line segmented into pieces | Use the redraw workflow with a `strokes` part |
| Text traced as shapes | `annotations` off, or the figure has dark artwork | Add `remove` boxes |
| Edge F1 very low on a tiny input (< 200 px) | The 2 px tolerance is applied at 1600 px | Not a defect: judge the crops |

## Not fixable yet

- Text recreated as editable `<text>`: redraw labels by hand.
- Curved or barbed arrows as primitives (only straight, triangle-headed arrows are fitted).
- Repeated objects (cells, beads) as one symbol with instances.
- Photographs: use a raster.
