"""Clean connected tone regions, rims, and leaders in pale flat artwork."""

from collections import defaultdict

import numpy as np
from scipy import ndimage as ndi
from skimage import measure


def leaders_from_mask(rgb, removed):
    """Recover long straight leaders and endpoint dots from neutral pixels in removed; return SVG primitives."""
    from decompose import hex_color

    ink = (np.ptp(rgb, axis=2) < 35) & (rgb.mean(axis=2) < 185)
    ink = ndi.binary_closing(ink, structure=np.ones((3, 1)))
    shapes = []
    covered = np.zeros(ink.shape, bool)
    # Axis-aligned runs distinguish leaders from glyph stems without OCR.
    for vertical in (True, False):
        source = ink if vertical else ink.T
        opened = ndi.binary_opening(source, structure=np.ones((15, 1)))
        labels, _ = ndi.label(opened)
        for index, slices in enumerate(ndi.find_objects(labels), 1):
            if slices is None:
                continue
            y, x = np.nonzero(labels == index)
            if len(y) < 15:
                continue
            center = float(np.mean(x) + 0.5)
            first, last = float(y.min() + 0.5), float(y.max() + 0.5)
            points = [(center, first), (center, last)] if vertical else [(first, center), (last, center)]
            color = hex_color(np.median((rgb if vertical else rgb.transpose(1, 0, 2))[y, x], axis=0))
            name = f"leader_{len(shapes):02d}"
            shapes.append({"type": "line", "name": name, "group": "leaders", "x1": points[0][0],
                           "y1": points[0][1], "x2": points[1][0], "y2": points[1][1],
                           "stroke": color, "width": max(0.8, len(y) / (last - first + 1))})
            if vertical:
                covered[y, x] = True
            else:
                covered[x, y] = True
    # Close collinear interruptions where a colored ring crossed a gray leader.
    for first in shapes:
        for second in shapes:
            if first is second or second.get("drop"):
                continue
            if abs(first["y1"] - first["y2"]) < .1 and abs(second["y1"] - second["y2"]) < .1:
                if abs(first["y1"] - second["y1"]) < 1 and 0 <= second["x1"] - first["x2"] <= 6:
                    first["x2"] = second["x2"]
                    second["drop"] = True
    shapes = [s for s in shapes if not s.get("drop")]
    endpoints = np.array([(s[kx], s[ky]) for s in shapes for kx, ky in (("x1", "y1"), ("x2", "y2"))])
    dots, _ = ndi.label(ndi.binary_opening(ink & (rgb.mean(axis=2) < 130)))
    for component, slices in enumerate(ndi.find_objects(dots), 1):
        if slices is None:
            continue
        y, x = np.nonzero(dots == component)
        if not 5 <= len(x) <= 30 or max(np.ptp(x), np.ptp(y)) > 7:
            continue
        center = np.array([x.mean() + .5, y.mean() + .5])
        if len(endpoints) and np.linalg.norm(endpoints - center, axis=1).min() < 10:
            shapes.append({"type": "circle", "name": f"leader_dot_{component:02d}", "group": "leaders",
                           "cx": float(center[0]), "cy": float(center[1]), "r": 1.65,
                           "fill": hex_color(np.median(rgb[y, x], axis=0))})
    return shapes


def pale_parts(rgb, clean, removed, backdrop, S=None):
    """Build spatial tone groups from RGB/clean annotation mask removed and fitted backdrop; return decomposition.

    S is the supersampling factor: tones are labeled on an S-times bicubic grid so
    boundaries fall at antialias midpoints rather than on source pixel edges. By
    default S makes the grid about 2400 px on the long side (at most 8x), which is
    finer than the 1600 px at which edges are judged.
    """
    from PIL import Image
    from decompose import find_palette, nearest_labels, mask_path, hex_color

    palette = find_palette(clean)
    # Near-identical modes in a downsampled source describe antialiasing, not
    # independent tone layers. Keep the more frequent representative.
    retained = []
    for paint in palette:
        comparators = np.asarray(retained)
        if len(comparators) and np.ptp(paint) > 5:
            comparators = comparators[np.ptp(comparators, axis=1) > 5]
        if not len(comparators) or np.linalg.norm(comparators - paint, axis=1).min() >= 11:
            retained.append(paint)
    palette = np.asarray(retained)
    h, w = clean.shape[:2]
    S = S or int(np.clip(round(2400 / max(h, w)), 1, 8))
    up = np.asarray(Image.fromarray(np.clip(clean, 0, 255).astype(np.uint8)).resize(
        (w * S, h * S), Image.Resampling.BICUBIC), dtype=float)
    labels = nearest_labels(up, palette)
    # A tone that never gets wider than ~2.4 native px is an antialias mixture of its
    # neighbors; dropping it lets those pixels fall to the nearer real neighbor.
    reach = np.array([ndi.distance_transform_edt(labels == i).max() / S if (labels == i).any() else 0
                      for i in range(len(palette))])
    reach[0] = np.inf
    palette = palette[reach >= 1.2]
    labels = nearest_labels(up, palette)
    # Radii in native pixels: widths below ~1.6 px are antialias rims, not tones.
    OPEN, SIG = 3, 0.3 * S
    yy, xx = np.indices(labels.shape)
    ring = np.abs(np.hypot((xx + .5) / S - backdrop["cx"], (yy + .5) / S - backdrop["cy"]) - backdrop["r"]) < 3
    bg = np.array([int(backdrop["fill"][i:i + 2], 16) for i in (1, 3, 5)])
    artwork = (np.linalg.norm(palette[labels] - bg, axis=2) > 12) & (palette[labels].min(axis=2) < 245)
    core = ndi.binary_dilation(ndi.binary_opening(artwork, iterations=2 * S), iterations=2 * S)
    labels[ring & ~core] = 0
    background = (np.linalg.norm(palette - bg, axis=1) < 12) | (palette.min(axis=1) > 245)
    labels[background[labels]] = 0
    # Remove low-area islands and narrow antialias rims. Opening (not erosion)
    # keeps wide regions at full extent, so boundaries do not drift toward the
    # backdrop; only sub-1.5 px slivers are handed to the nearest stable tone.
    stable = np.zeros(labels.shape, bool)
    for i in np.unique(labels):
        components, _ = ndi.label(labels == i)
        sizes = np.bincount(components.ravel())
        region = (labels == i) & (sizes[components] >= 25 * S * S)
        stable |= ndi.binary_opening(region, iterations=OPEN)
    indices = ndi.distance_transform_edt(~stable, return_distances=False, return_indices=True)
    labels = labels[tuple(indices)]
    lightness = up.mean(axis=2)
    shapes, parts, rims = [], {}, {}
    # Hue families identify the two enclosed ovaries independently of position.
    for family in ("yellow", "lavender"):
        paints = ((palette[:, 0] > 235) & (palette[:, 1] > 225) & (palette[:, 2] < palette[:, 0] - 5)) if family == "yellow" else (
            (palette[:, 2] - palette[:, 0] > 10) & (palette[:, 0] - palette[:, 1] > 4)
            & (palette[:, 0] < 225))
        mask = paints[labels] & (~ring | core)
        mask = ndi.binary_closing(mask, iterations=S)
        connected, _ = ndi.label(mask)
        sizes = np.bincount(connected.ravel())
        for component in np.argsort(sizes[1:])[::-1] + 1:
            if sizes[component] < 600 * S * S:
                continue
            mask = ndi.binary_fill_holes(connected == component)
            name = "left_ovary" if family == "yellow" else "right_ovary"
            parts[name] = mask
            # The rim is the darker paint just inside the part boundary.
            band = mask & ~ndi.binary_erosion(mask, iterations=S)
            rims[name] = np.median(up[band & (lightness <= np.percentile(lightness[band], 30))], axis=0)
            break
    foreground = labels != 0
    # A pale body undercoat prevents seams without filling external openings.
    values, counts = np.unique(labels[foreground], return_counts=True)
    shapes.append({"type": "path", "name": "anatomy_undercoat", "group": "uterus_layers",
                   "d": mask_path(foreground, SIG, 0.25, S), "fill": hex_color(palette[values[np.argmax(counts)]])})
    painted = np.zeros(labels.shape, bool)
    for name, part in parts.items():
        values, counts = np.unique(labels[part], return_counts=True)
        dominant = values[np.argmax(counts)]
        rim = rims[name]
        # Inset the outline by half its width so the stroke stays inside the part.
        shapes.append({"type": "path", "name": name + "_base", "group": name,
                       "d": mask_path(ndi.binary_erosion(part, iterations=round(0.5 * S)), SIG, 0.2, S),
                       "fill": hex_color(palette[dominant]), "stroke": hex_color(rim), "stroke-width": 1.1})
        for index in values[np.argsort(counts)[::-1]]:
            if index == dominant or index == 0:
                continue
            local = (labels == index) & part
            components, _ = ndi.label(local)
            sizes = np.bincount(components.ravel())
            local &= sizes[components] >= 25 * S * S
            if local.sum() < 25 * S * S:
                continue
            # Tones matching the rim color belong in the boundary stroke.
            if np.linalg.norm(palette[index] - rim) < 12:
                continue
            local &= ndi.distance_transform_edt(part) > 0.8 * S
            shapes.append({"type": "path", "name": f"{name}_tone_{index}", "group": name,
                           "d": mask_path(local, 1.3 * SIG, 0.3, S), "fill": hex_color(palette[index])})
        painted |= part
    order = sorted((i for i in np.unique(labels) if i), key=lambda i: -(labels == i).sum())
    rank = np.full(len(palette), -1)
    rank[order] = np.arange(len(order))
    group_names = ["uterus_layers", "left_tube", "right_tube"]
    group_map = np.full(labels.shape, -1)
    pieces = []
    for index in order:
        mask = (labels == index) & ~painted
        components, _ = ndi.label(mask)
        sizes = np.bincount(components.ravel())
        # Separate spatial parts; collect the small fan rays inside their parent
        # structure rather than emitting dozens of antialias islands.
        buckets = defaultdict(lambda: np.zeros(labels.shape, bool))
        for component, slices in enumerate(ndi.find_objects(components), 1):
            if slices is None or sizes[component] < 25 * S * S:
                continue
            ys, xs = slices
            center_x = (xs.start + xs.stop) / 2
            group = 1 if center_x < labels.shape[1] * .31 else (2 if center_x > labels.shape[1] * .70 else 0)
            buckets[group] |= components == component
        for group, mask in buckets.items():
            group_map[mask] = group
            pieces.append((index, group, mask))
    for index, group, mask in pieces:
        # Seal seams by tucking each tone under tones painted after it in the same
        # group only; growing into earlier paint would move its visible boundary.
        expanded = mask | (ndi.binary_dilation(mask, iterations=S) & (group_map == group)
                           & (rank[labels] > rank[index]))
        shapes.append({"type": "path", "name": f"{group_names[group]}_tone_{index}", "group": group_names[group],
                       "d": mask_path(expanded, SIG, 0.25, S), "fill": hex_color(palette[index])})
    return {"size": (rgb.shape[1], rgb.shape[0]), "layers": [], "strokes": [],
            "primitives": [backdrop] + leaders_from_mask(rgb, removed), "shapes": shapes, "gradients": {},
            "annotations": {"removed": removed}, "metadata": {"mode": "pale_flat", "annotation_pixels": int(removed.sum()),
                "palette": [hex_color(p) for p in palette], "fill_components": {s["name"]: s["d"].count("M") for s in shapes}}}
