# Visual fragment contract (chapter illustrators)

A fragment is one self-contained file `build/visuals/chN-<slug>.html` (e.g. `ch3-rope-dial.html`). The build inlines it verbatim where the Markdown has `<!-- VISUAL-ID: ch3-rope-dial -->` on its own line (blank lines around it). A missing file fails the build.

## Structure
- Root: `<figure class="fig fig--wide" id="viz-<slug>">` (wide band up to 1100px, scrolls horizontally inside itself).
- Content: inline `<svg viewBox=... role="img" aria-label="what it shows">` and/or `<canvas>`; give SVG `style="width:100%;min-width:480px;height:auto"`.
- Controls in `<div class="viz-controls">` (native `input[type=range]`, `button`, `label`); numbers in `<span class="viz-readout" aria-live="polite">`.
- `<figcaption><span class="cap-label">Figure n.m</span> takeaway sentence.</figcaption>` states the takeaway, not just the content.
- At most one `<script>`, an IIFE, querying only inside its own figure (`document.getElementById("viz-<slug>")`). No libraries, no fetch, no external assets.
- Reference: `build/visuals/example-receptive-field.html`.

## Colors and theme
- Use CSS variables, never literals: `--paper --panel --ink --muted --rule --accent --mark`, subject tokens such as nucleotides `--nt-A/C/G/T` (SUBJECT-SPECIFIC), fonts `--f-display --f-mono --f-body`.
- In SVG set them through style: `el.style.fill = "var(--mark)"` (they follow the theme automatically).
- Canvas needs resolved values: `getComputedStyle(fig).getPropertyValue("--accent").trim()`, and redraw on `document.addEventListener("ag-theme", draw)` (fired on toggle and on system change).
- Nucleotide colors only for real bases. Color is never the only cue: add labels, shape or position.

## Motion, size, accessibility
- Check `matchMedia("(prefers-reduced-motion: reduce)").matches`: no autoplay or tweening; user-driven sliders still work.
- Must work at 400px wide (min-width scroll is fine) and fit 1100px; keep text at least 11px after scaling.
- `role="img"` + `aria-label` on the SVG, labeled controls, keyboard-operable, visible focus (inherited). No emoji. localStorage only in try/catch.

## In the Markdown
`<!-- VISUAL-ID: ch3-rope-dial -->` places a fragment. An idea without a fragment stays `<!-- VISUAL: description -->` (invisible).

## Rebuild and screenshot (run from book/)
```
python build/build_html.py                                      # all pages (or name .md files as arguments)
python build/shot.py ch3_transformer_and_pairs.html /tmp/qa/ch3   # needs playwright; writes /tmp/qa/ch3_{light,dark}_{1280,400}.png
```
`shot.py` waits for MathJax/mermaid, prints console errors and horizontal overflow (must be 0). Read the PNGs; fix before handing over. `build/test_components.md` builds to `build/test_components.html` and shows every component.
