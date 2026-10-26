# VectorCraft

VectorCraft is an open-source vector editor written in Rust (https://github.com/storytold/vectorcraft). Agents drive it through an MCP server or a command line. **The skill requires it.** The redraw is built in VectorCraft so the result is clean and easy to edit: named groups, live shapes and native arrows in a `.vectorcraft` document. When `vectorcraft-cli` is missing or its MCP server lacks a needed tool, `redraw.py` stops with exit code 3. The agent then asks the user to install it with the steps below.

`--geometry python` builds without VectorCraft. It is only for an image VectorCraft cannot handle, and the user must be told why. It writes no `.vectorcraft`, draws primitives as plain SVG, and leaves more anchors (669 vs 541 on the uterus).

## Install

| Platform | Steps |
|---|---|
| Linux or a cloud session (source build, ~10 min on 4 cores, Rust 1.95+) | `git clone --depth 1 https://github.com/storytold/vectorcraft && cd vectorcraft && cargo install --path apps/vectorcraft-cli --locked` |
| Windows | The release MSI installs `C:\Program Files\VectorCraft\vectorcraft-cli.exe` (not on `PATH`) |
| Linux packages | deb or rpm install `/usr/bin/vectorcraft-cli` |

Register the MCP server for interactive editing (the tools appear in the next agent session):

```
claude mcp add vectorcraft -- vectorcraft-cli mcp --headless          # headless engine
claude mcp add vectorcraft -- vectorcraft-cli mcp                     # live app if running with --control 7979
```

Other MCP clients use `{"command": "vectorcraft-cli", "args": ["mcp"]}`.

`redraw.py` does not need the MCP registration. It starts the same server (`vectorcraft-cli mcp --headless`) itself through `scripts/vc_client.py` and sends it the commands below, so a build is repeatable and costs one tool call. Register the server for the agent's own calls: checking a result and hand fixes the spec cannot express.

## What the build does

It follows the gold uterus build: the part outlines come in as a file, and VectorCraft simplifies them and draws everything else.

1. `open_file` loads `draft.svg`, which holds only the parts (one `figure` group, so they open as one layer). Part ids become object names, and `inspect_document` returns their numeric ids.
2. One `command_batch` per step, each atomic:
   - **Simplify**, per smoothing class: `select.set` with the class's ids, then `object.path.simplify` with `tolerance` (class tolerance × scale) and `cornerAngle: 100`. A fill part is the object named after it, and a `strokes` part is one object per line width, `<name>_w<k>`. Both reach VectorCraft as dense points: closed outlines for fills, smoothed centrelines for strokes. VectorCraft fits every curve.
   - **Draw primitives and paper**:
     - `draw_shape` `rectangle` for the paper, `ellipse` for circles and ellipses, `line` for leaders;
     - `draw_path` for polylines, `path` primitives and arrows with non-square heads (the exact 7-point outline);
     - an arrow whose head is about as long as wide (0.75–1.25) is a `line` with `stroke.set {endArrow: "Triangle", arrowAlign: "tip"}` and `stroke.setAdvanced {arrowScale: [100, head_width ÷ (4 × width) × 100]}`.
   - **Group and stack**: `object.group` for the `backdrop` (z `bottom`) and `annotations` primitives, `object.setProps {name}`, `object.arrange.sendToBack` for the backdrop and then the paper.
   - A rotated ellipse gets `transform {rotate: -angle, origin}` (VectorCraft turns counter-clockwise for a positive angle; SVG turns clockwise).
3. `save_file <stem>_vN.vectorcraft`, then `export` to SVG. The PNG is rendered from that SVG. `score.json` → `vectorcraft` lists the object kinds in the document and the native and outlined arrow counts.

Tested on 2026-10-25 with VectorCraft 0.17.0 (commit `3f8d7a0`):
- Replaying the gold uterus build reproduced its PNG with a mean difference of 0.017/255.
- Names, groups, gradients (linear and radial, `userSpaceOnUse`), strokes, evenodd holes, z-order and `clipPath` groups (used by `trace` parts) all survive import and export.
- Earlier, a 5056×3392 engine SVG with 372 objects round-tripped with identical MAE and edge F1.
- Native drawing (2026-10-26) gave the same renders as the earlier SVG-imported primitives:

  | Figure | MAE | What VectorCraft holds |
  |---|---|---|
  | Uterus | 1.64 | 3 `Ellipse`, 4 `Line` |
  | Heart | 3.40 (was 3.42) | 17 native arrows |
  | Cell | 3.12 | no primitives |
  | Nephron | 2.55 | 1 native and 2 outlined arrows |

## Quirks

- **Simplify overshoots on sparse polygons.** A 7-point polygon with a corner bulged 13 px outside after tolerance 5. Only run it on dense, smoothed contours, as `redraw.py` does.
- **Simplify can tilt a thin straight part.** Its tolerance (1 source px for `layer`) is large next to a 2–3 px tube, so a long straight side may lean within it. `detail` smoothing keeps it straight, but it also follows small steps in the mask. On the nephron, lost px fell from 126 to 0 while a bump and a few kinks appeared. Choose by zoomed review.
- **Top-level SVG groups open as separate layers**, and new art goes into the current (top) layer, where `sendToBack` cannot reach below the others. `redraw.py` wraps the parts in one `figure` group for this reason.
- **Native arrowheads are square.** Every style (`Triangle`, `Arrow`, `Barbed`, …) is 4 stroke widths long and wide at 100 %, and `arrowScale` scales both. A head with another ratio is drawn as an outline instead.
- **Live shapes export as paths.** `draw_shape` ellipses stay `Ellipse` objects in the `.vectorcraft` document but export to SVG as 4-anchor Bézier paths. A native arrow exports as a group of shaft and head.
- **Deleting objects:** use `edit.clear` after `select.set`, not `layer.delete`.
- On large files, call `inspect_document` with `depth` and `childLimit`.
- Paths inside `run_command` and `command_batch` are resolved by the app, so use absolute paths.

## Editing a redraw by hand or by agent

Open `<stem>_vN.vectorcraft` (app or MCP `open_file`). Useful commands, all of which the gold redraw used:

| Command | Purpose |
|---|---|
| `paint.setFill` with `{ids, gradient: {kind: "linear", angle, stops}}` or `{kind: "radial", stops}` | Replace a fill with a gradient |
| `set_paint` with `{ids, stroke, strokeWidth}` | Add or change an outline |
| `draw_shape` (`ellipse`, `rectangle`, `line`) and `draw_path` (`points` or `d`, plus `fill`/`stroke`/`name`) | Add true primitives |
| `object.arrange.sendToBack` / `bringToFront` | Z-order |
| `object.path.simplify` (`tolerance`, `cornerAngle`) | Smooth selected paths |

Other available commands: `object.path.offsetPath`, the `object.pathfinder.*` set (unite, minusFront, …), the `symbol.*` set (repeated objects) and `object.mesh.*` (gradient mesh).

Export a new version (`<stem>_vN_edited.svg` and `.png`) and score it against the source:

```python
import sys; sys.path.insert(0, "<skill_dir>/scripts")
from evaluate import evaluate_raster
evaluate_raster("<stem>_vN_edited.svg", "<input.png>", "<out_dir>/<stem>_vN_edited_review")
```
