"""Views and measurements that help name a figure's parts and place their seeds.

Usage:
    python inspect_figure.py <input.png> <out_dir> [--probe x,y]... [--zoom x0,y0,x1,y1]...

Writes grid.png (the figure zoomed with a labelled coordinate grid in source px) and
palette.png (its main colours with hex codes and area shares) into out_dir. --zoom adds
zoom_<n>.png, a gridded close-up of a box. --probe prints the colour at a point.
"""

from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy.cluster.vq import kmeans2

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.dont_write_bytecode = True

from decompose import hex_color, load_rgb

USAGE = __doc__.split("Writes")[0].strip()


def grid_view(rgb, box, out_path, target=1500):
    """Save the source box [x0, y0, x1, y1] zoomed (nearest) with grid lines and source-px labels."""
    x0, y0, x1, y1 = box
    crop = rgb[y0:y1, x0:x1].astype(np.uint8)
    k = max(1, min(16, target // max(crop.shape[:2])))
    image = Image.fromarray(np.repeat(np.repeat(crop, k, 0), k, 1))
    draw = ImageDraw.Draw(image)
    span = max(x1 - x0, y1 - y0)
    step = next(s for s in (5, 10, 20, 25, 50, 100, 200, 250, 500, 1000) if span / s <= 16)
    for x in range((x0 // step + 1) * step, x1, step):
        draw.line([((x - x0) * k, 0), ((x - x0) * k, image.height)], fill=(0, 160, 255), width=1)
        draw.text(((x - x0) * k + 2, 2), str(x), fill=(0, 90, 200))
    for y in range((y0 // step + 1) * step, y1, step):
        draw.line([(0, (y - y0) * k), (image.width, (y - y0) * k)], fill=(0, 160, 255), width=1)
        draw.text((2, (y - y0) * k + 2), str(y), fill=(0, 90, 200))
    image.save(out_path)
    return out_path


def palette_sheet(rgb, out_path, colors=16):
    """Save the main colours (k-means on a sample) as swatches with hex codes and area shares; return them."""
    pixels = rgb.reshape(-1, 3)
    sample = pixels[np.random.default_rng(0).choice(len(pixels), min(len(pixels), 60000), replace=False)]
    centres, _ = kmeans2(sample, colors, seed=0, minit="++")
    labels = np.argmin(((pixels[:, None, :] - centres[None]) ** 2).sum(-1), axis=1)
    shares = np.bincount(labels, minlength=colors) / len(labels)
    order = np.argsort(shares)[::-1]
    sheet = Image.new("RGB", (360, 24 * colors + 8), "white")
    draw = ImageDraw.Draw(sheet)
    found = []
    for row, index in enumerate(order):
        value = hex_color(np.median(pixels[labels == index], axis=0)) if shares[index] else hex_color(centres[index])
        draw.rectangle([4, 4 + 24 * row, 64, 24 + 24 * row], fill=value, outline="black")
        draw.text((72, 9 + 24 * row), f"{value}  {shares[index] * 100:5.1f}%", fill="black")
        found.append((value, float(shares[index])))
    sheet.save(out_path)
    return found


def main(arguments):
    """Command-line entry point; returns the process exit code."""
    positional, probes, zooms = [], [], []
    index = 0
    while index < len(arguments):
        if arguments[index] in ("--probe", "--zoom") and index + 1 < len(arguments):
            values = [int(float(v)) for v in arguments[index + 1].split(",")]
            (probes if arguments[index] == "--probe" else zooms).append(values)
            index += 2
        elif arguments[index].startswith("--"):
            print(USAGE)
            return 2
        else:
            positional.append(arguments[index])
            index += 1
    if len(positional) != 2:
        print(USAGE)
        return 2
    rgb = load_rgb(positional[0])
    out_dir = Path(positional[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    h, w = rgb.shape[:2]
    grid_view(rgb, (0, 0, w, h), out_dir / "grid.png")
    for number, box in enumerate(zooms, 1):
        grid_view(rgb, box, out_dir / f"zoom_{number}.png")
    found = palette_sheet(rgb, out_dir / "palette.png")
    print(f"size {w}x{h}; wrote grid.png, palette.png" + (f", {len(zooms)} zoom(s)" if zooms else ""))
    print("main colours: " + ", ".join(f"{v} {s * 100:.1f}%" for v, s in found[:10]))
    for x, y in probes:
        patch = rgb[max(0, y - 1):y + 2, max(0, x - 1):x + 2].reshape(-1, 3)
        print(f"probe ({x},{y}): {hex_color(rgb[y, x])} (3x3 median {hex_color(np.median(patch, axis=0))})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
