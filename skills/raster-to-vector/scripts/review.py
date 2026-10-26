"""Review sheets and scores for a part-based redraw: part map, mask preview, junction zooms, seams, lost parts."""

import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from skimage import segmentation

from evaluate import compare_images, render_at, svg_counts, worst_boxes, write_crops

MARK_COLORS = [(230, 25, 75), (60, 180, 75), (0, 130, 200), (245, 130, 48), (145, 30, 180), (70, 240, 240),
               (240, 50, 230), (128, 128, 0), (0, 0, 128), (170, 110, 40)]


def zoom_factor(shape, target=1500):
    """Return the integer zoom that brings the long side of shape near target (1 to 4)."""
    return int(np.clip(target // max(shape[:2]), 1, 4))


def zoom_sheets(image_path, shape, boxes, out_dir, prefix):
    """Save zoomed crops (nearest, about 1200 px) of an output image for source-px boxes; return their paths."""
    image = Image.open(image_path)
    k = image.width / shape[1]
    paths = []
    for number, (x0, y0, x1, y1) in enumerate(boxes, 1):
        crop = image.crop(tuple(round(v * k) for v in (x0, y0, x1, y1)))
        factor = max(1, 1200 // max(crop.size))
        path = Path(out_dir) / f"{prefix}_zoom_{number}.png"
        crop.resize((crop.width * factor, crop.height * factor), Image.Resampling.NEAREST).save(path)
        paths.append(str(path))
    return paths


def part_map(rgb, result, spec, out_path):
    """Save the source zoomed with every part's own region tinted and outlined, its name and its seeds.

    Dropped pixels and primitive bands are cyan. A tint where a part should not be is a leak:
    add a seed for the part that owns that area.
    """
    k = zoom_factor(rgb.shape)
    labels = result["labels"]
    big = np.repeat(np.repeat(rgb.astype(float), k, 0), k, 1)
    big_labels = np.repeat(np.repeat(labels, k, 0), k, 1)
    for index in range(1, labels.max() + 1):
        inside = big_labels == index
        big[inside] = big[inside] * 0.6 + np.array(MARK_COLORS[(index - 1) % len(MARK_COLORS)]) * 0.4
    big = big.astype(np.uint8)
    big[np.repeat(np.repeat(result["drop"], k, 0), k, 1)] = (0, 220, 255)
    for index in range(1, labels.max() + 1):
        edge = segmentation.find_boundaries(big_labels == index, mode="inner")
        big[edge] = MARK_COLORS[(index - 1) % len(MARK_COLORS)]
    image = Image.fromarray(big)
    draw = ImageDraw.Draw(image)
    for index, part in enumerate(spec["parts"], 1):
        mark = MARK_COLORS[(index - 1) % len(MARK_COLORS)]
        for x, y in part.get("seeds", []):
            draw.line([(x * k - 6, y * k), (x * k + 6, y * k)], fill=mark, width=2)
            draw.line([(x * k, y * k - 6), (x * k, y * k + 6)], fill=mark, width=2)
        if part.get("seeds"):
            x, y = part["seeds"][0]
        elif (labels == index).any():
            ys, xs = np.nonzero(labels == index)
            x, y = int(xs[0]), int(ys[0])
        else:
            continue
        draw.rectangle([x * k + 6, y * k - 14, x * k + 8 + 6 * len(part["name"]), y * k - 2], fill="white", outline=mark)
        draw.text((x * k + 7, y * k - 14), part["name"], fill=mark)
    image.save(out_path)
    return out_path


def mask_preview(rgb, result, out_path):
    """Save source | flat-painted masks in drawing order, side by side and zoomed, to compare segmentation."""
    k = zoom_factor(rgb.shape, 900)
    preview = np.full(rgb.shape, 255, np.uint8)
    for shape in [s for s in result["primitives"] if s.get("z") == "bottom" and s["type"] == "circle"]:
        yy, xx = np.indices(rgb.shape[:2])
        inside = np.hypot(xx + 0.5 - shape["cx"], yy + 0.5 - shape["cy"]) < shape["r"]
        if shape["fill"] != "none":
            preview[inside] = [int(shape["fill"][i:i + 2], 16) for i in (1, 3, 5)]
    for layer in result["layers"]:
        fill = layer["paint"]["fill"]
        preview[layer["mask"]] = [int(fill[i:i + 2], 16) for i in (1, 3, 5)]
    pair = np.concatenate([rgb.astype(np.uint8), np.full((rgb.shape[0], 6, 3), 200, np.uint8), preview], 1)
    Image.fromarray(np.repeat(np.repeat(pair, k, 0), k, 1)).save(out_path)
    return out_path


def junction_boxes(labels, count=6):
    """Pick count non-overlapping square boxes (source px) centred where different parts meet most."""
    h, w = labels.shape
    side = max(24, max(h, w) // 6)
    meet = np.zeros(labels.shape, float)
    for axis in (0, 1):
        a = labels
        b = np.roll(labels, 1, axis)
        between = (a != b) & (a > 0) & (b > 0)
        meet += between
    density = ndi.uniform_filter(meet, side)
    boxes = []
    for _ in range(count):
        y, x = np.unravel_index(np.argmax(density), density.shape)
        if density[y, x] <= 0:
            break
        x0 = int(np.clip(x - side // 2, 0, max(0, w - side)))
        y0 = int(np.clip(y - side // 2, 0, max(0, h - side)))
        boxes.append((x0, y0, min(w, x0 + side), min(h, y0 + side)))
        density[max(0, y - side):y + side, max(0, x - side):x + side] = 0
    return boxes


def score(rgb, candidate, result, paper):
    """Return seam and lost-part statistics of the rendered candidate (same size as rgb) against the source.

    seams: inside a part, the render shows paper while the source does not.
    lost: inside a part (not dropped), the render differs from the source by more than 60 RGB in a blob of 12+ px.
    """
    render = np.asarray(candidate, float)
    inside = ndi.binary_erosion(result["labels"] > 0, iterations=1) & ~ndi.binary_dilation(result["drop"], iterations=2)
    paper_rgb = np.array([int(paper[i:i + 2], 16) for i in (1, 3, 5)], float)
    seam = inside & (np.abs(render - paper_rgb).max(axis=2) < 10) & (np.abs(rgb - paper_rgb).max(axis=2) > 25)
    wrong = inside & (np.abs(render - rgb).max(axis=2) > 60)
    blobs, count = ndi.label(wrong)
    sizes = np.bincount(blobs.ravel())[1:]
    lost = []
    for index in np.nonzero(sizes >= 12)[0]:
        y, x = np.nonzero(blobs == index + 1)
        lost.append({"px": int(sizes[index]), "box": [int(x.min()), int(y.min()), int(x.max()) + 1, int(y.max()) + 1]})
    return {"seam_px": int(seam.sum()), "lost_blobs": sorted(lost, key=lambda b: -b["px"])[:10],
            "lost_px": int(sum(b["px"] for b in lost))}


def anchor_count(svg):
    """Count path anchors (segment end points of M, L, C, Q, A, H, V commands) in the SVG file svg."""
    text = Path(svg).read_text(encoding="utf-8")
    return sum(len(re.findall(r"[MLCQAHVmlcqahv]", d)) for d in re.findall(r'\sd="([^"]*)"', text))


def review(rgb, svg, result, paper, out_dir, zoom_boxes=()):
    """Render svg, write review_N.png sheets (junctions, worst tiles, requested zooms) and score.json; return the score."""
    out_dir = Path(out_dir)
    source = Image.fromarray(rgb.astype(np.uint8))
    candidate = render_at(svg, source.size)
    stats, error, missed = compare_images(candidate, source)
    stats.update(svg_counts(svg))
    stats["anchors"] = anchor_count(svg)
    stats.update(score(rgb, candidate, result, paper))
    # Dropped text is meant to differ from the source; leave it out of the worst tiles.
    dropped = ndi.binary_dilation(result["drop"], iterations=2)
    error = np.where(dropped, 0, error)
    missed = missed & ~np.asarray(Image.fromarray(dropped).resize(missed.shape[::-1]))
    boxes = list(zoom_boxes) + junction_boxes(result["labels"], 4) + worst_boxes(error, missed, source.size, 2)
    # Three pairs per sheet keep each image short enough to be viewed at full size.
    big = render_at(svg, (source.width * 4, source.height * 4))
    sheets = []
    for start in range(0, len(boxes), 3):
        sheets.append(str(write_crops(source, big, boxes[start:start + 3], out_dir / f"review_{start // 3 + 1}.png",
                                      side=480, first=start + 1)))
    stats["review_boxes"] = [list(b) for b in boxes]
    stats["review_sheets"] = sheets
    (out_dir / "score.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return stats


def part_summary(spec, result):
    """Return one line per part: own pixels, marker pixels and own-region box, to spot leaks and starved parts."""
    labels, markers = result["labels"], result["markers"]
    lines = []
    for index, part in enumerate(spec["parts"], 1):
        own = labels == index
        if not own.any():
            lines.append(f"{part['name']}: EMPTY (check its seeds)")
            continue
        y, x = np.nonzero(own)
        lines.append(f"{part['name']}: {int(own.sum())} px, marker {int((markers == index + 1).sum())} px, "
                     f"box [{x.min()}, {y.min()}, {x.max() + 1}, {y.max() + 1}]")
    for name, (wanted, found) in result.get("tone_counts", {}).items():
        if wanted and not found:
            lines.append(f"{name}: tones requested but none found (list the tone colours explicitly)")
        elif wanted:
            lines.append(f"{name}: {found} tone layer(s)")
    names = ["background"] + [part["name"] for part in spec["parts"]]
    for label, size, box in result.get("adopted", []):
        lines.append(f"adopted an unseeded {size} px patch at {box} into {names[label]} by colour (check it)")
    return lines
