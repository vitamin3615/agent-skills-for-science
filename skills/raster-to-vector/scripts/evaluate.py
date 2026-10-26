"""Score a vector against its source raster and write visual evidence for review."""

import io
import json
from pathlib import Path
from time import perf_counter
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw
import resvg_py
from scipy import ndimage as ndi
from skimage.feature import canny

SHAPE_TAGS = {"path", "rect", "circle", "ellipse", "line", "polyline", "polygon"}


def raster_rgb(path):
    """Load path as an RGB Pillow image with transparency composited on white."""
    image = Image.open(path).convert("RGBA")
    return Image.alpha_composite(Image.new("RGBA", image.size, "white"), image).convert("RGB")


def render_at(svg, size):
    """Render the SVG file svg at exact (width, height) size on white; return an RGB Pillow image."""
    root = ET.parse(svg).getroot()
    if root.get("viewBox") is None:
        root.set("viewBox", f'0 0 {root.get("width")} {root.get("height")}')
    root.set("width", str(size[0]))
    root.set("height", str(size[1]))
    data = resvg_py.svg_to_bytes(svg_string=ET.tostring(root, encoding="unicode"), background="#ffffff")
    return Image.open(io.BytesIO(data)).convert("RGB")


def edge_maps(candidate, source, edge_long=1600):
    """Return Canny edge maps of candidate and source resized so the long side is edge_long."""
    target = tuple(round(n * edge_long / max(source.size)) for n in source.size)
    arrays = [np.asarray(im.resize(target, Image.Resampling.LANCZOS)) for im in (candidate, source)]
    return [np.any([canny(a[..., channel] / 255, sigma=2) for channel in range(3)], axis=0) for a in arrays]


def compare_images(candidate, source, edge_long=1600):
    """Compare RGB Pillow candidate and source; return metrics, the error plane and the missed-edge map.

    MAE uses the native size; edges use a long side of edge_long with a 2 px tolerance.
    """
    error = np.abs(np.asarray(source, np.int16) - np.asarray(candidate, np.int16)).mean(axis=2).astype(np.float32)
    candidate_edges, source_edges = edge_maps(candidate, source, edge_long)
    near_source = ndi.distance_transform_edt(~source_edges) <= 2
    near_candidate = ndi.distance_transform_edt(~candidate_edges) <= 2
    precision = float(near_source[candidate_edges].mean()) if candidate_edges.any() else 0.0
    recall = float(near_candidate[source_edges].mean()) if source_edges.any() else 0.0
    stats = {"mae": float(error.mean()), "p95_err": float(np.percentile(error, 95)),
             "edge_precision": precision, "edge_recall": recall,
             "edge_f1": 2 * precision * recall / max(precision + recall, 1e-12),
             "size_px": list(source.size), "edge_size_px": list(source_edges.shape[::-1]), "edge_tolerance_px": 2}
    return stats, error, source_edges & ~near_candidate


def svg_counts(svg):
    """Return object, gradient and embedded-image counts plus byte size for the SVG file svg."""
    kinds = [node.tag.rsplit("}", 1)[-1] for node in ET.parse(svg).getroot().iter()]
    return {"object_count": sum(kind in SHAPE_TAGS for kind in kinds),
            "gradient_count": sum(kind in {"linearGradient", "radialGradient"} for kind in kinds),
            "embedded_images": kinds.count("image"), "svg_bytes": Path(svg).stat().st_size}


def detail_boxes(source, count=4):
    """Pick count non-overlapping square boxes (source pixels) where source has the densest edges."""
    long = max(source.size)
    side = max(32, long // 6)
    small = source.resize(tuple(max(1, round(n * 400 / long)) for n in source.size), Image.Resampling.LANCZOS)
    edges = np.any([canny(np.asarray(small)[..., c] / 255, sigma=1.5) for c in range(3)], axis=0)
    scale = long / max(small.size)
    window = max(4, round(side / scale))
    density = ndi.uniform_filter(edges.astype(float), window)
    boxes = []
    for _ in range(count):
        y, x = np.unravel_index(np.argmax(density), density.shape)
        if density[y, x] <= 0:
            break
        x0 = int(np.clip(x * scale - side / 2, 0, source.width - side))
        y0 = int(np.clip(y * scale - side / 2, 0, source.height - side))
        boxes.append((x0, y0, x0 + min(side, source.width), y0 + min(side, source.height)))
        density[max(0, y - window):y + window + 1, max(0, x - window):x + window + 1] = 0
    return boxes


def worst_boxes(error, missed, source_size, count=6):
    """Pick count non-overlapping tiles (source pixels) with the highest local error plus missed-edge share."""
    width, height = source_size
    side = max(32, max(source_size) // 8)
    columns, rows = max(1, width // side), max(1, height // side)
    edge_y, edge_x = np.nonzero(missed)
    sx, sy = width / missed.shape[1], height / missed.shape[0]
    lost = np.zeros((rows, columns))
    np.add.at(lost, (np.minimum((edge_y * sy // side).astype(int), rows - 1),
                     np.minimum((edge_x * sx // side).astype(int), columns - 1)), 1)
    scores = np.zeros((rows, columns))
    for row in range(rows):
        for column in range(columns):
            tile = error[row * side:(row + 1) * side, column * side:(column + 1) * side]
            scores[row, column] = tile.mean() + 255 * lost[row, column] / (side / sx * 4)
    order = np.argsort(scores.ravel())[::-1][:count]
    return [(int(c * side), int(r * side), int(min(width, (c + 1) * side)), int(min(height, (r + 1) * side)))
            for r, c in zip(*np.unravel_index(order, scores.shape)) if scores[r, c] > 0]


def write_crops(source, candidate, boxes, out_path, title="source", side=640, first=1):
    """Save source/candidate pairs for source-pixel boxes as one labelled sheet at out_path; return the Path.

    side is the width of each zoomed crop; first is the number of the first box in the labels.
    """
    sx, sy = candidate.width / source.width, candidate.height / source.height
    rows = []
    for number, box in enumerate(boxes, first):
        left = source.crop(box)
        right = candidate.crop(tuple(round(value * (sx if i % 2 == 0 else sy)) for i, value in enumerate(box)))
        size = (side, round(left.height * side / left.width))
        row = Image.new("RGB", (2 * side + 16, size[1] + 28), "#eeeeee")
        draw = ImageDraw.Draw(row)
        draw.text((4, 7), f"{number}: {title} box {box}", fill="black")
        draw.text((side + 20, 7), "vector", fill="black")
        row.paste(left.resize(size, Image.Resampling.LANCZOS), (0, 28))
        row.paste(right.resize(size, Image.Resampling.LANCZOS), (side + 16, 28))
        rows.append(row)
    sheet = Image.new("RGB", (2 * side + 16, max(1, sum(row.height for row in rows) + 12 * (len(rows) - 1))), "#dddddd")
    y = 0
    for row in rows:
        sheet.paste(row, (0, y))
        y += row.height + 12
    out_path = Path(out_path)
    sheet.save(out_path)
    return out_path


def evaluate_raster(svg, png, out_dir, boxes=None):
    """Render svg against the source png and write metrics.json, crops.png and worst_tiles.png into out_dir.

    boxes optionally fixes the crop-sheet boxes in source pixels; by default the four
    most detailed areas are used. Returns the metrics dictionary.
    """
    started = perf_counter()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    source = raster_rgb(png)
    candidate = render_at(svg, source.size)
    stats, error, missed = compare_images(candidate, source)
    stats.update(svg_counts(svg))
    boxes = boxes or detail_boxes(source)
    worst = worst_boxes(error, missed, source.size)
    write_crops(source, candidate, boxes, out_dir / "crops.png")
    write_crops(source, candidate, worst, out_dir / "worst_tiles.png", "worst tile")
    heat = Image.fromarray(np.clip(error * 4, 0, 255).astype(np.uint8))
    heat.thumbnail((1600, 1600))
    heat.save(out_dir / "error_heatmap.png")
    stats.update(crop_boxes=[list(b) for b in boxes], worst_boxes=[list(b) for b in worst],
                 evaluation_runtime_s=round(perf_counter() - started, 3))
    (out_dir / "metrics.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return stats
