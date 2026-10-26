"""Redraw one raster figure from a part spec as a clean, layered vector, then review it.

Usage:
    python redraw.py <input.png> <parts.json> <out_dir> [--geometry vectorcraft|python] [--masks-only]
                     [--zoom x0,y0,x1,y1]...

Writes <stem>_redraw_vN/ into out_dir with: part_map.png, masks.png, <stem>_vN.svg, <stem>_vN.png,
<stem>_vN.vectorcraft, review_1.png, review_2.png, ... and score.json.
With --masks-only, --zoom boxes write part_map_zoom_N.png close-ups of the part map instead. N is one more
than the highest version already there, so earlier results are never overwritten.

VectorCraft is required for a build (not for --masks-only): it is driven through its MCP server, and the run
stops with exit code 3 and set-up advice when it is missing. --geometry python builds without it, only for an
image VectorCraft cannot handle; the user must be told.
"""

import json
from pathlib import Path
import re
import shutil
import sys
from time import perf_counter

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import measure, morphology

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True

from decompose import cubic_path, gradient_xml, hex_color, join_branches, load_rgb, trace_skeleton
from parts import SMOOTH, arrow_corners, build_parts
from review import mask_preview, part_map, part_summary, review, zoom_sheets

USAGE = __doc__.split("Writes")[0].strip()


def parse_arguments(arguments):
    """Return (input, spec, out_dir, options) from command-line arguments, or None when they are incomplete."""
    options = {"geometry": "vectorcraft", "masks_only": False, "zoom": []}
    positional = []
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--masks-only":
            options["masks_only"] = True
        elif argument == "--geometry" and index + 1 < len(arguments) and arguments[index + 1] in ("vectorcraft", "python"):
            options["geometry"] = arguments[index + 1]
            index += 1
        elif argument == "--zoom" and index + 1 < len(arguments):
            options["zoom"].append(tuple(int(float(v)) for v in arguments[index + 1].split(",")))
            index += 1
        elif argument.startswith("--"):
            return None
        else:
            positional.append(argument)
        index += 1
    if len(positional) != 3:
        return None
    return Path(positional[0]), Path(positional[1]), Path(positional[2]), options


def next_version(out_dir, stem):
    """Return one more than the highest <stem>_redraw_vN folder already present in out_dir."""
    versions = [int(m.group(1)) for p in out_dir.glob(f"{stem}_redraw_v*")
                if (m := re.fullmatch(rf"{re.escape(stem)}_redraw_v(\d+)", p.name))]
    return max(versions, default=0) + 1


def outline_contours(mask, sigma, inset=0.0):
    """Return smoothed closed outlines of mask as XY arrays in source px (pixel edges at integers).

    The signed distance field is blurred by sigma, so edges are smooth but stay in place;
    inset > 0 moves the outline inward (for a centred rim stroke).
    """
    padded = np.pad(mask, 3)
    field = ndi.distance_transform_edt(padded) - ndi.distance_transform_edt(~padded)
    field = ndi.gaussian_filter(field, sigma)
    outlines = []
    for contour in measure.find_contours(field, inset):
        points = contour[:, ::-1] - 3 + 0.5
        area = abs(np.sum(points[:-1, 0] * points[1:, 1] - points[1:, 0] * points[:-1, 1])) / 2
        if len(points) >= 6 and area >= 2:
            outlines.append(points)
    return outlines


def catmull_rom(points, scale, step=1.0):
    """Return a closed cubic path through points thinned to 0.35 px, as in the uterus gold build (x scale).

    Thinning keeps the corners and the ends of straight runs, but leaves a long chord next to a 1 px one,
    and a Catmull-Rom handle there (a sixth of the long chord) loops across a thin tube. So every chord is
    cut into pieces of at most step px: the spline stays straight along a run and cannot overshoot at a
    corner. VectorCraft's Simplify then removes the redundant anchors.
    """
    corners = measure.approximate_polygon(points, 0.35)
    if len(corners) < 4:
        return ""
    pieces = [np.linspace(a, b, max(int(np.ceil(np.linalg.norm(b - a) / step)), 1), endpoint=False)
              for a, b in zip(corners[:-1], corners[1:])]
    p = np.vstack(pieces) * scale
    d = f"M{p[0][0]:.2f} {p[0][1]:.2f}"
    n = len(p)
    for i in range(n):
        p0, p1, p2, p3 = p[i - 1], p[i], p[(i + 1) % n], p[(i + 2) % n]
        c1, c2 = p1 + (p2 - p0) / 6, p2 - (p3 - p1) / 6
        d += f" C{c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {p2[0]:.2f} {p2[1]:.2f}"
    return d + " Z"


def stroke_paths(layer, scale, geometry="python"):
    """Return [(path data, width)] for a line part drawn as centreline strokes, in output px.

    The mask is skeletonized at 2x, branches are joined through junctions, and each centreline is
    smoothed, then fitted with cubic Beziers (python) or left as its dense points for VectorCraft's
    Simplify to fit. Each chain's width is the line coverage nearest to it divided by its length, so
    antialiased edges count fractionally and a rim that is thin in one place and thick in another
    keeps both; chains are grouped by width in 0.25 px steps.
    """
    from scipy.spatial import cKDTree

    high = ndi.zoom(layer["own"].astype(float), 2, order=1, grid_mode=True, mode="nearest") > 0.5
    skeleton = morphology.skeletonize(high)
    chains = [(c + 0.5) / 2 for c in join_branches(trace_skeleton(skeleton), 4)]
    chains = [c for c in chains if np.linalg.norm(np.diff(c, axis=0), axis=1).sum() >= 1]
    if not chains:
        return []
    points = np.vstack(chains)
    owner = np.concatenate([np.full(len(c), i) for i, c in enumerate(chains)])
    ys, xs = np.nonzero(layer["coverage"] > 0)
    _, nearest = cKDTree(points).query(np.c_[xs + 0.5, ys + 0.5])
    coverage = np.bincount(owner[nearest], weights=layer["coverage"][ys, xs], minlength=len(chains))
    groups = {}
    for i, chain in enumerate(chains):
        length = np.linalg.norm(np.diff(chain, axis=0), axis=1).sum()
        width = round(float(np.clip(coverage[i] / max(length, 1), 0.6, 6)) * 4) / 4
        if length < width:
            continue
        closed = len(chain) > 8 and np.linalg.norm(chain[0] - chain[-1]) < 1.5
        smooth = ndi.gaussian_filter1d(chain, 1.5, axis=0, mode="wrap" if closed else "nearest")
        if not closed:
            smooth[0], smooth[-1] = chain[0], chain[-1]
        if geometry == "vectorcraft":
            points = smooth * scale
            piece = "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in points) + (" Z" if closed else "")
        else:
            piece = cubic_path(smooth * scale, closed, SMOOTH[layer["smooth"]][1] * scale)
        groups.setdefault(width, []).append(piece)
    return [(" ".join(p for p in pieces if p), width) for width, pieces in sorted(groups.items())]


def layer_path(layer, scale, geometry):
    """Return SVG path data for one layer: fitted Beziers (python) or dense Catmull-Rom for VectorCraft to simplify."""
    sigma, tolerance = SMOOTH[layer["smooth"]]
    inset = layer["rim"]["width"] / 2 if layer["rim"] else 0.0
    pieces = []
    for points in outline_contours(layer["mask"], sigma, inset):
        if geometry == "python":
            pieces.append(cubic_path(points * scale, closed=True, tolerance=tolerance * scale))
        else:
            pieces.append(catmull_rom(points, scale))
    return " ".join(p for p in pieces if p)


def primitive_xml(shape, scale):
    """Serialize one primitive (source px) as an SVG element in output px."""
    s = scale
    stroke = shape.get("stroke", "none")
    width = shape.get("stroke-width", 1) if shape["type"] == "rect" else shape.get("width", 1)
    paint = f'fill="{shape.get("fill", "none")}" stroke="{stroke}"'
    if stroke != "none":
        paint += f' stroke-width="{width * s:.2f}"'
    name = shape["name"]
    if shape["type"] == "circle":
        return f'<circle id="{name}" cx="{shape["cx"] * s:.2f}" cy="{shape["cy"] * s:.2f}" r="{shape["r"] * s:.2f}" {paint}/>'
    if shape["type"] == "ellipse":
        angle = shape.get("angle", 0)
        return (f'<ellipse id="{name}" cx="{shape["cx"] * s:.2f}" cy="{shape["cy"] * s:.2f}" rx="{shape["rx"] * s:.2f}" '
                f'ry="{shape["ry"] * s:.2f}" transform="rotate({angle} {shape["cx"] * s:.2f} {shape["cy"] * s:.2f})" {paint}/>')
    if shape["type"] == "line":
        return (f'<line id="{name}" x1="{shape["x1"] * s:.2f}" y1="{shape["y1"] * s:.2f}" x2="{shape["x2"] * s:.2f}" '
                f'y2="{shape["y2"] * s:.2f}" {paint} stroke-linecap="{shape.get("stroke-linecap", "butt")}"/>')
    if shape["type"] == "polyline":
        points = " ".join(f"{x * s:.2f},{y * s:.2f}" for x, y in shape["points"])
        return f'<polyline id="{name}" points="{points}" {paint} stroke-linejoin="miter"/>'
    if shape["type"] == "rect":
        return (f'<rect id="{name}" x="{shape["x"] * s:.2f}" y="{shape["y"] * s:.2f}" width="{shape["width"] * s:.2f}" '
                f'height="{shape["height"] * s:.2f}" {paint}/>')
    if shape["type"] == "arrow":
        # Tail (x1, y1) to tip (x2, y2): a constant-width shaft and a triangular head, as one closed path.
        d = "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in arrow_corners(shape, s)) + " Z"
        return f'<path id="{name}" d="{d}" fill="{shape.get("fill", "#000000")}" stroke="none"/>'
    if shape["type"] == "path":
        return f'<path id="{name}" d="{shape["d"]}" transform="scale({s})" {paint.replace(f"{width * s:.2f}", f"{width:.2f}")}/>'
    raise ValueError(f"unknown primitive type {shape['type']}")


def trace_detail(rgb, layer, scale, outline):
    """Trace the texture inside one part with the engine; return (gradient defs, clipped SVG group).

    The source is cropped to the part; pixels outside the part's own region (including its children,
    which draw themselves) are set to the part's base colour; the crop is upsampled 4x and traced
    by decompose_shaded. Traced shapes of the base colour are dropped, and the rest are placed in
    a group clipped by the part's outline, so the clean silhouette stays and only texture is traced.
    """
    from decompose import shape_xml
    from shaded_regions import decompose_shaded

    ys, xs = np.nonzero(layer["full"])
    x0, y0 = max(0, xs.min() - 2), max(0, ys.min() - 2)
    x1, y1 = min(rgb.shape[1], xs.max() + 3), min(rgb.shape[0], ys.max() + 3)
    crop = rgb[y0:y1, x0:x1].copy()
    base = np.array([int(layer["paint"]["fill"][i:i + 2], 16) for i in (1, 3, 5)], float)
    own = ndi.binary_dilation(layer["own"], iterations=1)[y0:y1, x0:x1]
    crop[~own] = base
    size = ((x1 - x0) * 4, (y1 - y0) * 4)
    sampled = np.asarray(Image.fromarray(crop.astype(np.uint8)).resize(size, Image.Resampling.BICUBIC), dtype=np.float32)
    traced = decompose_shaded(sampled, ((x1 - x0) * scale, (y1 - y0) * scale))
    prefix = f'{layer["name"]}_trace'
    gradients, elements = {}, []
    for shape in traced["shapes"]:
        fill = shape.get("fill", "none")
        flat = shape["name"] not in traced["gradients"] and fill.startswith("#")
        if flat and np.abs(np.array([int(fill[i:i + 2], 16) for i in (1, 3, 5)]) - base).max() <= 3:
            continue
        old_name = shape["name"]
        shape["name"] = f"{prefix}_{old_name.split('_')[-1]}"
        if old_name in traced["gradients"]:
            gradients[shape["name"]] = traced["gradients"][old_name]
        elements.append(shape_xml(shape, gradients))
    defs = [gradient_xml(name, spec) for name, spec in gradients.items()]
    defs.append(f'<clipPath id="clip_{layer["name"]}"><path d="{outline}" clip-rule="evenodd"/></clipPath>')
    group = (f'<g id="{prefix}" clip-path="url(#clip_{layer["name"]})"><g transform="translate({x0 * scale},{y0 * scale})">'
             + "".join(elements) + "</g></g>")
    return defs, group


def paper_color(rgb, labels):
    """Return the hex colour of the background pixels on the image border (the page)."""
    border = np.zeros(labels.shape, bool)
    border[[0, -1], :] = border[:, [0, -1]] = True
    pixels = rgb[border & (labels == 0)]
    return hex_color(np.median(pixels, axis=0)) if len(pixels) else "#ffffff"


def write_svg(path, rgb, result, scale, geometry):
    """Write the redraw as a layered SVG in output px (source px x scale); return the paper colour.

    For VectorCraft the SVG holds only the parts: VectorCraft draws the paper and the primitives itself.
    """
    h, w = rgb.shape[:2]
    paper = paper_color(rgb, result["labels"])
    native = geometry == "vectorcraft"
    defs, body = [], [] if native else [f'<rect id="paper" x="0" y="0" width="{w * scale}" height="{h * scale}" fill="{paper}"/>']
    bottom = [primitive_xml(s, scale) for s in result["primitives"] if s.get("z") == "bottom" and not native]
    if bottom:
        body.append('<g id="backdrop">' + "".join(bottom) + "</g>")
    groups = {}
    for layer in result["layers"]:
        if layer.get("draw") == "strokes":
            for k, (d, width) in enumerate(stroke_paths(layer, scale, geometry)):
                groups.setdefault(layer["group"], []).append(
                    f'<path id="{layer["name"]}_w{k}" d="{d}" fill="none" stroke="{layer["paint"]["fill"]}" '
                    f'stroke-width="{width * scale:.2f}" stroke-linecap="round" stroke-linejoin="round"/>')
            continue
        d = layer_path(layer, scale, geometry)
        if not d:
            continue
        paint = layer["paint"]
        fill = paint["fill"]
        if "gradient" in paint:
            defs.append(gradient_xml(layer["name"], paint["gradient"]))
            fill = f"url(#gradient_{layer['name']})"
        attributes = f'id="{layer["name"]}" d="{d}" fill="{fill}" fill-rule="evenodd"'
        if layer["rim"]:
            attributes += (f' stroke="{layer["rim"]["color"]}" stroke-width="{layer["rim"]["width"] * scale:.2f}"'
                           ' stroke-linejoin="round"')
        groups.setdefault(layer["group"], []).append(f"<path {attributes}/>")
        if layer.get("draw") == "trace":
            # Simplify does not reach clip paths, so the clip gets the fitted outline, not the dense draft.
            extra_defs, group = trace_detail(rgb, layer, scale, layer_path(layer, scale, "python"))
            defs += extra_defs
            groups[layer["group"]].append(group)
    for group, elements in groups.items():
        body.append(f'<g id="{group}_group">' + "".join(elements) + "</g>")
    top = [primitive_xml(s, scale) for s in result["primitives"] if s.get("z") != "bottom" and not native]
    if top:
        body.append('<g id="annotations">' + "".join(top) + "</g>")
    if native:
        # VectorCraft opens top-level groups as layers; one wrapper makes one layer, so the paper and
        # backdrop it draws later can go behind every part.
        body = ['<g id="figure">'] + body + ["</g>"]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w * scale}" height="{h * scale}" '
           f'viewBox="0 0 {w * scale} {h * scale}">\n<defs>{"".join(defs)}</defs>\n' + "\n".join(body) + "\n</svg>\n")
    Path(path).write_text(svg, encoding="utf-8")
    return paper


VECTORCRAFT_TOOLS = {"open_file", "inspect_document", "command_batch", "transform", "save_file", "export"}
SETUP = ("VectorCraft is required: redraw.py draws the figure in VectorCraft through its MCP server "
         "(vectorcraft-cli mcp --headless). {problem}\nAsk the user to set it up (see references/vectorcraft.md), "
         "then rerun. Only if VectorCraft cannot handle this image, rerun with --geometry python and tell the user why.")
# VectorCraft arrowheads at 100 % are 4 stroke widths long and 4 wide; scaling keeps them square.
NATIVE_HEAD = 4.0


class VectorCraftMissing(RuntimeError):
    """VectorCraft is not installed, or its MCP server lacks a tool the build needs."""


def open_vectorcraft():
    """Start the VectorCraft MCP server and check its tools; raise VectorCraftMissing with set-up advice."""
    from vc_client import VectorCraft

    binary = shutil.which("vectorcraft-cli")
    if binary is None:
        raise VectorCraftMissing(SETUP.format(problem="vectorcraft-cli is not on PATH."))
    try:
        vc = VectorCraft(binary=binary)
        missing = VECTORCRAFT_TOOLS - set(vc.tools())
    except (OSError, RuntimeError, ValueError) as error:
        raise VectorCraftMissing(SETUP.format(problem=f"Its MCP server did not start ({error}).")) from error
    if missing:
        vc.close()
        raise VectorCraftMissing(SETUP.format(problem=f"Its MCP server lacks {', '.join(sorted(missing))}."))
    return vc


def batch(vc, steps, label):
    """Run steps as one atomic VectorCraft command batch; return the per-step results, raising if any failed."""
    reply = json.loads(vc.call("command_batch", steps=steps, atomic=True, label=label))
    if reply.get("failed"):
        failed = [r for r in reply["results"] if not r.get("ok")]
        raise RuntimeError(f"VectorCraft batch '{label}' failed: {failed[:3]}")
    return [r.get("result") for r in reply["results"]]


def scale_path(d, s):
    """Scale every number of SVG path data d by s (arcs are refused: their flags must not scale)."""
    if re.search(r"[Aa]", d):
        raise ValueError("path primitives with arcs are not supported; give them as cubic segments")
    return re.sub(r"-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?", lambda m: f"{float(m.group()) * s:.2f}", d)


def native_arrow(shape):
    """True when an arrow's head is close enough to square for VectorCraft's own Triangle arrowhead."""
    width = shape["width"]
    head_width, head_length = shape.get("head_width", width * 2.5), shape.get("head_length", width * 2.5)
    return 0.75 <= head_length / head_width <= 1.25


def draw_step(shape, s):
    """Return (VectorCraft draw step, finishing steps given the new id) for one primitive, in output px.

    Circles, ellipses and rectangles become live shapes and leaders live lines, so they stay editable
    as shapes. An arrow with a near-square head becomes one line with VectorCraft's Triangle arrowhead
    scaled to the measured head width (drag its ends to edit it); other arrows are drawn as their exact
    7-point outline.
    """
    paint = {"fill": shape.get("fill", "none"), "stroke": shape.get("stroke", "none"), "name": shape["name"]}
    if paint["stroke"] != "none":
        paint["strokeWidth"] = shape.get("width", 1) * s
    kind = shape["type"]
    if kind in ("circle", "ellipse"):
        rx, ry = (shape["r"], shape["r"]) if kind == "circle" else (shape["rx"], shape["ry"])
        params = {"shape": "ellipse", "x": (shape["cx"] - rx) * s, "y": (shape["cy"] - ry) * s,
                  "width": 2 * rx * s, "height": 2 * ry * s}
        return {"id": "draw_shape", "params": {**params, **paint}}, lambda i: []
    if kind == "rect":
        params = {"shape": "rectangle", "x": shape["x"] * s, "y": shape["y"] * s,
                  "width": shape["width"] * s, "height": shape["height"] * s}
        paint.pop("strokeWidth", None)
        if paint["stroke"] != "none":
            paint["strokeWidth"] = shape.get("stroke-width", 1) * s
        return {"id": "draw_shape", "params": {**params, **paint}}, lambda i: []
    if kind == "line":
        params = {"shape": "line", "x1": shape["x1"] * s, "y1": shape["y1"] * s, "x2": shape["x2"] * s,
                  "y2": shape["y2"] * s, "cap": shape.get("stroke-linecap", "butt")}
        return {"id": "draw_shape", "params": {**params, **paint, "fill": "none"}}, lambda i: []
    if kind == "polyline":
        params = {"points": [[x * s, y * s] for x, y in shape["points"]], "closed": False, "join": "miter"}
        return {"id": "draw_path", "params": {**params, **paint, "fill": "none"}}, lambda i: []
    if kind == "path":
        return {"id": "draw_path", "params": {"d": scale_path(shape["d"], s), **paint}}, lambda i: []
    if kind == "arrow":
        color = shape.get("fill", "#000000")
        if native_arrow(shape):
            width = shape["width"]
            head = shape.get("head_width", width * 2.5) / (NATIVE_HEAD * width) * 100
            params = {"shape": "line", "x1": shape["x1"] * s, "y1": shape["y1"] * s, "x2": shape["x2"] * s,
                      "y2": shape["y2"] * s, "cap": "butt", "fill": "none", "stroke": color,
                      "strokeWidth": width * s, "name": shape["name"]}
            return {"id": "draw_shape", "params": params}, lambda i: [
                {"id": "stroke.set", "params": {"ids": [i], "endArrow": "Triangle", "arrowAlign": "tip"}},
                {"id": "stroke.setAdvanced", "params": {"ids": [i], "arrowScale": [100, round(head, 1)]}}]
        points = [[float(x), float(y)] for x, y in arrow_corners(shape, s)]
        params = {"points": points, "closed": True, "fill": color, "stroke": "none", "name": shape["name"]}
        return {"id": "draw_path", "params": params}, lambda i: []
    raise ValueError(f"unknown primitive type {kind}")


def vectorcraft_build(vc, svg, result, scale, out_stem, paper, size):
    """Finish the redraw in VectorCraft; return what it drew.

    The part outlines come in from svg (as the gold build opened its shapes.svg) and are simplified
    per smoothing class. VectorCraft then draws every primitive itself, groups them as backdrop
    (behind the parts) and annotations (on top), draws the paper, and saves .vectorcraft, SVG and PNG.
    """
    vc.call("open_file", path=str(Path(svg).resolve()))
    tree = json.loads(vc.call("inspect_document", depth=8))
    # A fill part is one object named after it; a strokes part is one object per width, <name>_w<k>.
    smooth_of = {layer["name"]: layer["smooth"] for layer in result["layers"]}
    strokes = {layer["name"] for layer in result["layers"] if layer.get("draw") == "strokes"}
    classes = {}
    for node in walk_nodes(tree):
        name = node.get("name") or ""
        stem = re.sub(r"_w\d+$", "", name)
        if stem != name and stem in strokes:
            part = stem
        elif name in smooth_of and name not in strokes:
            part = name
        else:
            continue
        classes.setdefault(smooth_of[part], []).append(node["id"])
    steps = []
    for smooth, chosen in classes.items():
        if chosen:
            steps += [{"id": "select.set", "params": {"ids": chosen}},
                      {"id": "object.path.simplify", "params": {"tolerance": SMOOTH[smooth][1] * scale, "cornerAngle": 100}}]
    if steps:
        batch(vc, steps + [{"id": "select.set", "params": {"ids": []}}], "Simplify per smoothing class")

    shapes = sorted(result["primitives"], key=lambda p: p.get("z") != "bottom")
    drawn = [draw_step(shape, scale) for shape in shapes]
    paper_step = {"id": "draw_shape", "params": {"shape": "rectangle", "x": 0, "y": 0, "width": size[0], "height": size[1],
                                                 "fill": paper, "stroke": "none", "name": "paper"}}
    created = [r["id"] for r in batch(vc, [paper_step] + [step for step, _ in drawn], "Draw primitives and paper")]
    paper_id, shape_ids = created[0], created[1:]
    finish = [step for (_, then), i in zip(drawn, shape_ids) for step in then(i)]
    layers = {"backdrop": [i for shape, i in zip(shapes, shape_ids) if shape.get("z") == "bottom"],
              "annotations": [i for shape, i in zip(shapes, shape_ids) if shape.get("z") != "bottom"]}
    names = [name for name, members in layers.items() if members]
    finish += [{"id": "object.group", "params": {"ids": layers[name]}} for name in names]
    groups = batch(vc, finish, "Arrowheads and groups")[-len(names):] if names else []
    arrange = []
    for name, group in zip(names, groups):
        arrange.append({"id": "object.setProps", "params": {"id": group["id"], "name": name}})
        if name == "backdrop":
            arrange.append({"id": "object.arrange.sendToBack", "params": {"ids": [group["id"]]}})
    arrange += [{"id": "object.arrange.sendToBack", "params": {"ids": [paper_id]}},
                {"id": "select.set", "params": {"ids": []}}]
    batch(vc, arrange, "Name groups and stack paper")
    for shape, i in zip(shapes, shape_ids):
        if shape["type"] == "ellipse" and shape.get("angle"):
            vc.call("transform", ids=[i], rotate=-shape["angle"], origin=[shape["cx"] * scale, shape["cy"] * scale])

    vc.call("save_file", path=str(Path(f"{out_stem}.vectorcraft").resolve()))
    vc.call("export", path=str(Path(f"{out_stem}.svg").resolve()), format="svg")
    exported = Path(f"{out_stem}.svg")
    exported.write_text(exported.read_text(encoding="utf-8").replace(
        f"<title>{Path(svg).name}</title>", f"<title>{Path(out_stem).name}</title>"), encoding="utf-8")
    kinds = {}
    for node in walk_nodes(json.loads(vc.call("inspect_document", depth=8))):
        kinds[node["kind"]] = kinds.get(node["kind"], 0) + 1
    arrows = [s for s in shapes if s["type"] == "arrow"]
    return {"kinds": kinds, "native_arrows": sum(native_arrow(s) for s in arrows),
            "outlined_arrows": sum(not native_arrow(s) for s in arrows)}


def walk_nodes(node):
    """Yield every object below an inspect_document node (layers excluded)."""
    for child in node.get("children", []) + node.get("layers", []):
        if "kind" in child:
            yield child
        yield from walk_nodes(child)


def redraw(png, spec, out_dir, geometry="vectorcraft", masks_only=False, zoom=()):
    """Run the part spec on png and write a versioned redraw folder in out_dir; return the stats dict.

    The drawing is built in VectorCraft, which is opened first so a missing install stops the run
    before any work (VectorCraftMissing). geometry "python" builds without VectorCraft; use it only
    when VectorCraft cannot handle the image, and tell the user.
    """
    started = perf_counter()
    vc = open_vectorcraft() if geometry == "vectorcraft" and not masks_only else None
    try:
        return build_redraw(png, spec, out_dir, geometry, masks_only, zoom, vc, started)
    finally:
        if vc is not None:
            vc.close()


def build_redraw(png, spec, out_dir, geometry, masks_only, zoom, vc, started):
    """The body of redraw, with VectorCraft (vc) already open when it is used."""
    spec = json.loads(Path(spec).read_text(encoding="utf-8")) if not isinstance(spec, dict) else spec
    out_dir.mkdir(parents=True, exist_ok=True)
    version = next_version(out_dir, png.stem)
    folder = out_dir / f"{png.stem}_redraw_v{version}"
    folder.mkdir()
    (folder / "parts.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")
    rgb = load_rgb(png)
    scale = spec.get("scale", 4 if max(rgb.shape[:2]) <= 900 else 1)
    result = build_parts(rgb, spec, scale)
    part_map(rgb, result, spec, folder / "part_map.png")
    mask_preview(rgb, result, folder / "masks.png")
    stats = {"folder": str(folder), "parts": len(spec["parts"]), "layers": len(result["layers"]),
             "primitives": len(result["primitives"]), "part_summary": part_summary(spec, result)}
    if masks_only:
        stats["zooms"] = zoom_sheets(folder / "part_map.png", rgb.shape, zoom, folder, "part_map")
        return stats
    stem = folder / f"{png.stem}_v{version}"
    draft = folder / "draft.svg" if geometry == "vectorcraft" else Path(f"{stem}.svg")
    paper = write_svg(draft, rgb, result, scale, geometry)
    if geometry == "vectorcraft":
        size = (rgb.shape[1] * scale, rgb.shape[0] * scale)
        stats["vectorcraft"] = vectorcraft_build(vc, draft, result, scale, stem, paper, size)
    from evaluate import render_at
    render_at(f"{stem}.svg", (rgb.shape[1] * scale, rgb.shape[0] * scale)).save(f"{stem}.png")
    stats.update(review(rgb, f"{stem}.svg", result, paper, folder, zoom))
    stats.update(geometry=geometry, scale=scale, runtime_s=round(perf_counter() - started, 2))
    (folder / "score.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return stats


def main(arguments):
    """Command-line entry point; returns the process exit code."""
    parsed = parse_arguments(arguments)
    if parsed is None:
        print(USAGE)
        return 2
    png, spec, out_dir, options = parsed
    try:
        stats = redraw(png, spec, out_dir, options["geometry"], options["masks_only"], options["zoom"])
    except VectorCraftMissing as error:
        print(error, file=sys.stderr)
        return 3
    if options["masks_only"]:
        print(f"masks: {stats['folder']} parts {stats['parts']} layers {stats['layers']}")
        print("\n".join("  " + line for line in stats["part_summary"]))
        if stats["zooms"]:
            print("zooms: " + ", ".join(stats["zooms"]))
        return 0
    print(f"redraw: {stats['folder']} geometry {stats['geometry']} | objects {stats['object_count']} "
          f"anchors {stats['anchors']} gradients {stats['gradient_count']} | MAE {stats['mae']:.2f} "
          f"edge F1 {stats['edge_f1']:.3f} | seams {stats['seam_px']} px lost {stats['lost_px']} px | {stats['runtime_s']} s")
    if "vectorcraft" in stats:
        drawn = stats["vectorcraft"]
        kinds = ", ".join(f"{count} {kind}" for kind, count in sorted(drawn["kinds"].items()))
        print(f"vectorcraft: {kinds} | arrows {drawn['native_arrows']} native, {drawn['outlined_arrows']} outlined")
    else:
        print("WARNING: built without VectorCraft (--geometry python). Tell the user why VectorCraft could not be used.")
    print("review: " + ", ".join(stats["review_sheets"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
