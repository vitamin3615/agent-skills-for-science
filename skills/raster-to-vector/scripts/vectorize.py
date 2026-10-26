"""Vectorize one raster illustration into a versioned, editable SVG with review evidence.

Usage:
    python vectorize.py <input.png> <out_dir> [--no-annotations] [--scale N] [--hints hints.json]

Writes <stem>_vN.svg, <stem>_vN.png and <stem>_vN_review/ (metrics.json, crops.png,
worst_tiles.png, error_heatmap.png) into out_dir. N is one more than the highest version
already there, so earlier results are never overwritten.
"""

import json
from pathlib import Path
import re
import sys
from time import perf_counter

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True

USAGE = __doc__.split("Writes")[0].strip()
IGNORED_HINTS = ("replace", "regions")


def parse_arguments(arguments):
    """Return (input, out_dir, options) from command-line arguments, or None when they are incomplete."""
    options = {"annotations": True, "scale": None, "hints": None}
    positional = []
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--no-annotations":
            options["annotations"] = False
        elif argument in ("--scale", "--hints") and index + 1 < len(arguments):
            options[argument[2:]] = arguments[index + 1]
            index += 1
        elif argument.startswith("--"):
            return None
        else:
            positional.append(argument)
        index += 1
    if len(positional) != 2:
        return None
    return Path(positional[0]), Path(positional[1]), options


def next_version(out_dir, stem):
    """Return one more than the highest <stem>_vN version already present in out_dir."""
    versions = [int(match.group(1)) for path in out_dir.glob(f"{stem}_v*")
                if (match := re.fullmatch(rf"{re.escape(stem)}_v(\d+)(?:\.svg|\.png|_review|_input\.png)", path.name))]
    return max(versions, default=0) + 1


def remove_boxes(png, boxes, out_png):
    """Fill source-pixel boxes in png from the nearest pixels outside them; save to out_png and return it."""
    from decompose import box_mask, load_rgb, restore_annotations

    rgb = load_rgb(png)
    mask = box_mask(boxes, rgb.shape[:2], 1.0)
    Image.fromarray(restore_annotations(rgb, mask).astype(np.uint8)).save(out_png)
    return out_png


def hint_shapes(primitives):
    """Turn hinted primitives (circle, ellipse, rect, line, path) into named SVG shapes for the result."""
    shapes = []
    for number, primitive in enumerate(primitives, 1):
        shape = dict(primitive)
        shape.setdefault("fill", "none")
        shape["name"] = shape.get("name", f"hint_{shape['type']}_{number:02d}")
        shape["group"] = "hint_primitives"
        shapes.append(shape)
    return shapes


def add_seam_underlay(svg, source_png, render_png):
    """Cover paper-white seams between traced shapes with patches in the source colour, placed under all shapes.

    svg: SVG path written by to_svg; source_png: the traced raster; render_png: a render of svg.
    A seam is a near-white render blob where the source has colour and the blob is mostly surrounded by shapes,
    so dropped lines on a white background are not restored. Up to 4 patch colours, one path each.
    Returns the number of seam pixels covered; 0 leaves the SVG unchanged.
    """
    from scipy import ndimage as ndi
    from scipy.cluster.vq import kmeans2
    from skimage import measure, morphology

    source = np.asarray(Image.open(source_png).convert("RGB"))
    render = np.asarray(Image.open(render_png).convert("RGB").resize(source.shape[1::-1], Image.BOX))
    figure = morphology.erosion(ndi.binary_fill_holes(source.min(2) < 245), morphology.disk(2))
    seams = morphology.remove_small_objects(figure & (render.min(2) > 240) & (source.min(2) < 235), max_size=3)
    labels, count = ndi.label(seams)
    if not count:
        return 0
    grown = ndi.grey_dilation(labels, size=7)
    ring = np.where((grown > 0) & (labels == 0), grown, 0)
    surrounded = ndi.mean(render.min(2) < 240, labels=ring, index=np.arange(1, count + 1)) >= 0.5
    seams = surrounded[np.maximum(labels - 1, 0)] & (labels > 0)
    if not seams.any():
        return 0
    colours = source[seams].astype(float)
    centres, groups = kmeans2(colours, min(4, len(colours)), seed=0, minit="++")
    group_image = np.full(seams.shape, -1)
    group_image[seams] = groups
    paths = []
    for group in np.unique(groups):
        mask = np.pad(morphology.dilation(group_image == group, morphology.disk(3)), 1)
        rings = [measure.approximate_polygon(contour, 0.7) for contour in measure.find_contours(mask.astype(float), 0.5)]
        d = " ".join("M " + " L ".join(f"{x - 1:.1f} {y - 1:.1f}" for y, x in r) + " Z" for r in rings if len(r) > 2)
        colour = "#%02x%02x%02x" % tuple(int(v) for v in np.median(colours[groups == group], 0))
        paths.append(f'<path id="seam_underlay_{group + 1}" fill="{colour}" fill-rule="evenodd" d="{d}"/>')
    text = svg.read_text(encoding="utf-8")
    paper = re.search(r'<rect id="paper"[^>]*/>', text).group(0)
    svg.write_text(text.replace(paper, paper + '<g id="seam_underlay">' + "".join(paths) + "</g>", 1), encoding="utf-8")
    return int(seams.sum())


def vectorize(png, out_dir, annotations=True, scale=None, hints=None):
    """Vectorize png into out_dir with optional hints dict; return the metrics dictionary of this version."""
    from decompose import decompose, render_svg, to_svg
    from evaluate import evaluate_raster

    hints = hints or {}
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = png.stem
    version = next_version(out_dir, stem)
    name = f"{stem}_v{version}"
    for key in IGNORED_HINTS:
        if hints.get(key):
            print(f"note: hint '{key}' is not implemented in this version and was ignored")
    source = png
    if hints.get("remove"):
        source = remove_boxes(png, hints["remove"], out_dir / f"{name}_input.png")
    annotations = hints.get("annotations", annotations)
    started = perf_counter()
    result = decompose(source, annotations=annotations, mode=hints.get("mode"),
                       keep_lines=hints.get("keep_lines", ()))
    if hints.get("primitives"):
        result.setdefault("shapes", []).extend(hint_shapes(hints["primitives"]))
    width, height = result["size"]
    scale = float(scale) if scale else (1 if max(width, height) > 900 else 4)
    svg = to_svg(result, out_dir / f"{name}.svg", scale=scale)
    runtime = round(perf_counter() - started, 3)
    render_svg(svg, out_dir / f"{name}.png")
    # Removed annotations render white on purpose, so seams are only filled when nothing was removed.
    annotation_pixels = int(result["metadata"].get("annotation_pixels", 0))
    seam_pixels = 0 if annotation_pixels else add_seam_underlay(svg, source, out_dir / f"{name}.png")
    if seam_pixels:
        render_svg(svg, out_dir / f"{name}.png")
    stats = evaluate_raster(svg, source, out_dir / f"{name}_review")
    stats.update(input=str(png), version=version, mode=result["metadata"].get("mode", "flat"),
                 annotation_pixels=annotation_pixels, seam_pixels=seam_pixels,
                 hints=hints, runtime_s=runtime)
    (out_dir / f"{name}_review" / "metrics.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return stats


def main(arguments):
    """Run vectorize from command-line arguments; print usage and return 2 when they are incomplete."""
    parsed = parse_arguments(arguments)
    if parsed is None:
        print(USAGE)
        return 2
    png, out_dir, options = parsed
    if not png.is_file():
        print(f"input not found: {png}")
        return 2
    hints = json.loads(Path(options["hints"]).read_text(encoding="utf-8")) if options["hints"] else {}
    stats = vectorize(png, out_dir, options["annotations"], options["scale"], hints)
    name = f"{png.stem}_v{stats['version']}"
    print(f"{name}: mode {stats['mode']}, MAE {stats['mae']:.2f}, edge F1 {stats['edge_f1']:.3f}, "
          f"{stats['object_count']} objects, {stats['gradient_count']} gradients, "
          f"{stats['svg_bytes'] / 1024:.0f} KB, {stats['runtime_s']:.1f} s")
    print(f"view: {out_dir / (name + '_review') / 'crops.png'} and worst_tiles.png")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
