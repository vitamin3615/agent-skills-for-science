# Case study: the uterus redraw rated "very good"

This is the reference result the skill is built to reproduce. The source is a 353×296 flat-shaded uterus diagram with grey labels and leader lines. The result is 36 VectorCraft objects (29 paths, 3 ellipses, 2 lines and 1 rectangle) drawn at 4×, in a 27 KB SVG.

## What was done

1. **Auto-trace first, then rejected.** VTracer gave 833 KB of jigsaw patches, stair-stepped edges and banded colour. Even with a fitted circle, text removal and Simplify, it was still patches, not shapes.
2. **The user's idea:** extract the critical coordinates from the image, then let VectorCraft draw a similar figure.
3. **Look first.** On a 3× view, the parts were named by eye: tubes, pale fans, uterus body, purple myometrium and dome, lining, red cavity, two ovaries, backdrop circle, leaders and dots. Colour clusters alone mixed similar pinks across organs. In the skill, the lining is not a part: it has the body's colour, so stacking body → myometrium → cavity lets the body show through as the lining. Its strips only need body seeds.
4. **One mask per named part** (`extract.py`), built from colour plus geometry plus adjacency. Lower shapes were tucked 4 px under upper ones, and the shading was copied as 3–4 nested flat tones per organ.
5. **Masks checked by eye**, painted flat at 3× beside the source. This found 3 errors:
   - grey-text filtering ate lavender ovary pixels;
   - the purple dome was missing;
   - a leader dot notched an ovary.
6. **Masks to curves:** blur the mask, take the contour, thin the points, then a Catmull-Rom Bézier.
7. **VectorCraft built the drawing:**
   - a real circle, leader lines and dots;
   - 2-stop gradients only where the colour ramps;
   - ovary outlines as strokes;
   - Simplify per class, with tolerance 5 for organs, 4 for inner layers, 3 for ovary tones and 1.5 for scalloped lobes.
8. **Zoomed side-by-side checks** found a white hairline at the tube–uterus junction, fixed by the 4 px tuck.
9. **User feedback:** "the purple ovary is not as good; check the colour between the pink and yellow, and the pink and purple." Sampling the gaps showed the uterus/tube split sat too low. It was fixed in the masks, and the ovary got 4 tones, 6 lobes and 6 highlights.

The cost was about 90 tool calls, 26 image views and one feedback round. The judgement (naming parts, choosing thresholds, spotting errors, deciding what to drop) was done by eye.

## How each lesson is built into the skill

| Lesson | Where it lives now |
|---|---|
| Name the parts before drawing; colour clusters mix organs | `parts.json`: named parts with seeds. The marker watershed separates same-coloured organs by their edges. |
| Split by adjacency, not hard position cuts ("x ≥ 88 is uterus" leaked) | Seeds plus a watershed on colour edges. Markers do not cross 1–2 px bridges. |
| Stack shapes; tuck lower ones under upper ones | `parent` stacking (a shape includes its children) plus `tuck` (default 2 px under everything drawn later). |
| Nested flat tones, not gradients, where the source uses them | `tones`: nested superlevel sets stacked edge → core, with a flat base. Gradients are fitted only where a part ramps. |
| True primitives for the circle, lines and dots | `primitives`: a RANSAC circle with sampled fill, stroke and width, and `leaders` from the dropped text. Their bands are kept out of the watershed, so no part can run along the ring. VectorCraft draws them as live shapes (`draw_shape`), as the gold build did. |
| VectorCraft builds the drawing (open the shapes, Simplify, primitives, paints, save) | VectorCraft is required. `redraw.py` drives its MCP server through the same steps, and stops and asks for it when it is missing. |
| Smooth each part separately: strong for organs, light for scallops | `smooth` classes with the gold tolerances (5/4/3/1.5 output px at 4× equal 1.25/1.0/0.75/0.4 source px). VectorCraft Simplify runs per class. |
| Outlines belong to the object (the ovary's pink rim) | `stroke: "#hex"`. Its width is measured, and outline pixels outside the mask are pulled into the part. |
| Text inside a part disappears into it; leader dots must not notch parts | Dropped pixels go to the nearest part; leaders are redrawn as primitives. |
| Check masks by eye before drawing | `--masks-only`: `part_map.png` (tinted regions, seeds), `masks.png`, and the per-part summary that flags leaks. |
| Zoomed side-by-side checks; every real bug was invisible at full scale | `review_N.png`: junction zooms, worst tiles and `--zoom` boxes, three pairs per sheet. `score.json` reports seam and lost-part alarms. |
| Drop what does not matter | `drop`, a small `tone_min_px`, and specks below `min_px` removed. |

## Reproduction with the skill

`examples/uterus/parts.json` (10 parts, no code) gives 40 objects, 547 anchors, MAE 1.67 and edge F1 0.82 in about 5 s. The gold redraw has 35 objects, 526 anchors and MAE 3.09. Side by side, the two match in the ovaries (rims, tones, lobes and highlights), the tubes and fans, the myometrium and the leaders. The skill's version follows the cervix's wavy canal more closely.

The spec took four mask iterations. Each found a real problem that the part map or summary showed:
1. the backdrop ring was flooded by a tube (fixed in the toolkit: primitive bands are kept out of the watershed);
2. the right half of the backdrop had no seed (fixed in the toolkit: large background-coloured areas are added automatically);
3. the right fan leaked into the uterus wall (fixed in the spec: seeds on both sides of the uterus);
4. the tubes flooded the lining strips (fixed in the spec: seeds in the strips).

## Blind test (2026-10-26)

A fresh agent got only the skill (with this example removed) and the source image. It wrote a 9-part spec from views and probes. It needed 5 mask runs and 5 builds (98 tool calls, 43 image views) and reached 52 objects, 768 anchors and MAE 1.46. By eye the result is on par with the gold redraw: the ovaries have rims, tones and lobes, and the cervix and vaginal walls are richer.

Its feedback led to these changes:
- shorter review sheets;
- close-ups of the part map;
- outline pixels kept out of the base colour;
- a warning when tones come out empty;
- the pitfalls rows for same-coloured neighbours, split shapes and sibling order.

## The skill's own output, rated by the user (2026-10-26)

After VectorCraft was made mandatory and set to draw the primitives, the user compared the skill's builds with the source:
- **Uterus:** source | gold | skill (`examples/uterus/parts.json`: 40 objects, 541 anchors, MAE 1.64).
- **Nephron:** source | a blind agent's Python-only build | skill (`examples/nephron/parts.json`, written by a blind agent: 73 objects, MAE 2.55).

The verdict was "They look great". The loop is closed: the method behind the gold redraw, rebuilt as this skill, produced output the same user approves. Both specs and their sheets (`redraw_check/*_source_*_vectorcraft.png`) are the user-approved references. Treat a change that makes either look worse in a zoomed review as a regression.
