"""Model-free decomposition of small scientific illustrations into editable SVGs.

Only raster pixels drive decomposition. Coordinates use source pixels; masks use
the source grid. Compound paths keep related disconnected details together.
"""

from collections import defaultdict
from html import escape
from pathlib import Path
import io
import math

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.optimize import nnls
from scipy.spatial import cKDTree
from skimage import color, measure, morphology

# Long side of the working raster for large shaded inputs, in pixels.
WORKING_LONG = 2400


def load_rgb(path):
    """Load path as float RGB, compositing any transparency onto white."""
    image = Image.open(path).convert("RGBA")
    image = Image.alpha_composite(Image.new("RGBA", image.size, "white"), image)
    return np.asarray(image.convert("RGB"), dtype=float)


def hex_color(rgb):
    """Return an SVG hexadecimal color for the three-channel RGB value rgb."""
    return "#%02x%02x%02x" % tuple(np.clip(np.rint(rgb), 0, 255).astype(int))


def annotation_mask(rgb):
    """Find neutral text/leaders in rgb when its illustration has no dark ink."""
    neutral = (np.ptp(rgb, axis=2) < 12) & (rgb.mean(axis=2) < 190)
    dark_chromatic = (rgb.min(axis=2) < 100) & (np.ptp(rgb, axis=2) > 25)
    labels, count = ndi.label(neutral)
    mask = np.zeros(neutral.shape, bool)
    # Dark chromatic artwork is evidence against treating neutral ink as labels.
    if dark_chromatic.sum() > 0.003 * neutral.size:
        return mask
    for region in ndi.find_objects(labels):
        if region is None:
            continue
        local = neutral[region]
        if local.sum() >= 2:
            mask[region] |= local
    return ndi.binary_dilation(mask, iterations=1)


def restore_annotations(rgb, removed):
    """Replace removed pixels in rgb using neighboring illustration colors."""
    if not removed.any():
        return rgb.copy()
    indices = ndi.distance_transform_edt(removed, return_distances=False, return_indices=True)
    clean = rgb[tuple(indices)].copy()
    # Nearest colors preserve narrow anatomical boundaries better than a blur.
    return clean


def find_palette(rgb, max_colors=36):
    """Find color modes in rgb; max_colors bounds representative paint colors."""
    pixels = rgb.reshape(-1, 3).astype(np.uint8)
    centers, counts = np.unique(pixels, axis=0, return_counts=True)
    centers = centers.astype(float)
    local_range = ndi.maximum_filter(rgb, size=(3, 3, 1)) - ndi.minimum_filter(rgb, size=(3, 3, 1))
    flat = np.max(local_range, axis=2) < 0.5
    flat_colors, flat_counts = np.unique(rgb[flat].astype(np.uint8), axis=0, return_counts=True)
    flat_support = {tuple(c): int(n) for c, n in zip(flat_colors, flat_counts)}
    selected = [np.array([255., 255., 255.])]
    # Reject colors explained as anti-alias mixtures of established paint modes.
    order = np.argsort(counts)[::-1]
    for index in order:
        if counts[index] < max(12, pixels.shape[0] * 0.0001):
            break
        paint = centers[index]
        current = np.asarray(selected)
        stable = flat_support.get(tuple(paint), 0) >= 8
        if np.linalg.norm(current - paint, axis=1).min() < (4 if stable else 12):
            continue
        mixed = False
        for i in range(len(current)):
            direction = current[i + 1:] - current[i]
            if not len(direction):
                continue
            t = np.clip(((paint - current[i]) * direction).sum(axis=1)
                        / np.maximum((direction * direction).sum(axis=1), 1), 0, 1)
            distance = np.linalg.norm(paint - current[i] - t[:, None] * direction, axis=1)
            if (distance < 11).any():
                mixed = True
                break
        if stable or not mixed:
            selected.append(paint)
        if len(selected) >= max_colors:
            break
    palette = np.asarray(selected)
    labels = nearest_labels(rgb, palette)
    retained = np.ones(len(palette), bool)
    for index in range(1, len(palette)):
        if flat_support.get(tuple(palette[index]), 0) >= 8:
            continue
        mask = labels == index
        distances = ndi.distance_transform_edt(mask)
        if mask.any() and (distances[mask] > 1.5).mean() > 0.08:
            continue
        others = np.delete(palette, index, axis=0)
        weights, _ = nnls(np.vstack([others.T / 255, np.ones(len(others)) * 4]),
                          np.r_[palette[index] / 255, 4], maxiter=300)
        if weights.sum() and np.linalg.norm(weights @ others / weights.sum() - palette[index]) < 9:
            retained[index] = False
    palette = palette[retained]
    # Smooth gradients have few repeated exact colors. Add their interior modes,
    # while excluding high-contrast antialias edges from the histogram.
    distance = cKDTree(palette).query(rgb.reshape(-1, 3))[0].reshape(rgb.shape[:2])
    smooth = (np.max(local_range, axis=2) < 18) & (distance > 22)
    samples = rgb[smooth]
    if len(samples):
        bins, inverse, frequencies = np.unique((samples // 12).astype(int), axis=0,
                                                return_inverse=True, return_counts=True)
        added = 0
        for index in np.argsort(frequencies)[::-1]:
            if frequencies[index] < 30 or len(palette) >= max_colors or added >= 8:
                break
            paint = np.median(samples[inverse == index], axis=0)
            lab_paint = color.rgb2lab((paint / 255)[None, None])[0, 0]
            lab_palette = color.rgb2lab((palette / 255)[None])[0]
            if np.linalg.norm(lab_palette - lab_paint, axis=1).min() > 6:
                palette = np.vstack([palette, paint])
                added += 1
    return palette


def nearest_labels(rgb, palette):
    """Assign pixels in rgb to nearest Lab color in palette; return label map."""
    labs = color.rgb2lab(rgb / 255)
    paint_lab = color.rgb2lab((palette / 255)[None])[0]
    return cKDTree(paint_lab).query(labs.reshape(-1, 3))[1].reshape(rgb.shape[:2])


def pick_inks(rgb, palette, labels):
    """Select thin dark or saturated paint modes from rgb, palette, and labels."""
    inks = []
    lab = color.rgb2lab((palette / 255)[None])[0]
    for i, paint in enumerate(palette):
        mask = labels == i
        if mask.sum() < 24 or lab[i, 0] > 62:
            continue
        distances = ndi.distance_transform_edt(mask)
        core_fraction = (distances[mask] > 2).mean()
        exact_count = np.all(rgb == paint, axis=2).sum()
        bulk = ndi.binary_dilation(ndi.binary_opening(mask, iterations=2), iterations=3)
        thin = mask & ~bulk
        components, _ = ndi.label(thin)
        sizes = np.bincount(components.ravel())
        red_family = paint[0] > 1.35 * paint[1] and paint[0] > 1.3 * paint[2]
        colored_network = (red_family and np.ptp(paint) > 60 and thin.sum() >= 60
                           and len(sizes) > 1 and sizes[1:].max() >= 18)
        if (core_fraction < 0.14 or colored_network) and exact_count >= 12:
            inks.append(i)
    # Neutral outlines can be too subpixel to form a palette mode.
    neutral = (np.ptp(rgb, axis=2) < 15) & (rgb.mean(axis=2) < 75)
    if neutral.sum() > 50 and not any(np.max(palette[i]) < 85 for i in inks):
        palette = np.vstack([palette, np.median(rgb[neutral], axis=0)])
        inks.append(len(palette) - 1)
    return palette, inks


def ink_coverage(rgb, ink, palette, labels):
    """Unmix ink RGB from nearby palette paint in rgb, using labels for locality."""
    alpha = np.zeros(rgb.shape[:2])
    best = np.full(rgb.shape[:2], 1e9)
    ink_lightness = color.rgb2lab((ink / 255)[None, None])[0, 0, 0]
    for i, background in enumerate(palette):
        direction = background - ink
        denominator = np.dot(direction, direction)
        if denominator < 900:
            continue
        if background.mean() < ink.mean() + 10 and ink_lightness < 65:
            continue
        local = ndi.maximum_filter((labels == i).astype(np.uint8), size=7) > 0
        a = np.clip(np.sum((background - rgb) * direction, axis=2) / denominator, 0, 1)
        error = np.linalg.norm(rgb - (background - a[..., None] * direction), axis=2)
        take = local & (error < best) & (a > 0.12)
        best[take], alpha[take] = error[take], a[take]
    if np.ptp(ink) > 60:
        background = ndi.median_filter(rgb, size=(7, 7, 1))
        direction = background - ink
        denominator = np.sum(direction * direction, axis=2)
        a = np.clip(np.sum((background - rgb) * direction, axis=2) / np.maximum(denominator, 1), 0, 1)
        error = np.linalg.norm(rgb - background + a[..., None] * direction, axis=2)
        take = (denominator > 900) & (error < best) & (a > 0.12)
        best[take], alpha[take] = error[take], a[take]
        # Chroma survives neutral dark edging around very small colored tubes.
        # Recover their colored centerline without turning the edging into black ink.
        if len(palette) <= 6 and (labels == 0).mean() > 0.60:
            for background in palette:
                direction = ink - background
                chroma = direction - direction.mean()
                denominator = np.dot(chroma, chroma)
                if denominator < 2000:
                    continue
                delta = rgb - background
                delta_chroma = delta - delta.mean(axis=2, keepdims=True)
                a = np.clip(np.sum(delta_chroma * chroma, axis=2) / denominator, 0, 1)
                error = np.linalg.norm(delta_chroma - a[..., None] * chroma, axis=2)
                take = (error < 10) & (a > 0.15) & (a > alpha)
                alpha[take] = a[take]
                best[take] = np.minimum(best[take], error[take])
    near_fill = np.full(rgb.shape[:2], 1e9)
    for paint in palette:
        if np.linalg.norm(paint - ink) > 12:
            near_fill = np.minimum(near_fill, np.linalg.norm(rgb - paint, axis=2))
    limit = 45 if len(palette) <= 6 and np.ptp(ink) < 25 else 25
    alpha[(best > limit) | (near_fill < 5)] = 0
    sensitive = len(palette) <= 6 and np.ptp(ink) < 25
    support = alpha > (0.10 if sensitive else 0.16)
    seed = alpha > (0.26 if sensitive else 0.42)
    support = ndi.binary_propagation(seed, mask=support)
    return alpha * support


def trace_skeleton(skeleton):
    """Return ordered XY polylines for the boolean skeleton, including cycles."""
    ys, xs = np.nonzero(skeleton)
    points = list(zip(ys.tolist(), xs.tolist()))
    point_set = set(points)
    adjacent = {}
    for y, x in points:
        neighbors = []
        for dy, dx in ((-1, -1), (-1, 0), (-1, 1), (0, -1),
                       (0, 1), (1, -1), (1, 0), (1, 1)):
            q = y + dy, x + dx
            if q not in point_set:
                continue
            if dy and dx and ((y + dy, x) in point_set or (y, x + dx) in point_set):
                continue
            neighbors.append(q)
        adjacent[(y, x)] = neighbors
    visited = set()
    paths = []
    starts = [p for p in points if len(adjacent[p]) != 2] + points
    for start in starts:
        for neighbor in adjacent[start]:
            edge = tuple(sorted((start, neighbor)))
            if edge in visited:
                continue
            visited.add(edge)
            chain = [start, neighbor]
            previous, current = start, neighbor
            while len(adjacent[current]) == 2:
                next_point = next(q for q in adjacent[current] if q != previous)
                edge = tuple(sorted((current, next_point)))
                if edge in visited:
                    break
                visited.add(edge)
                chain.append(next_point)
                previous, current = current, next_point
            if len(chain) >= 2:
                paths.append(np.asarray(chain, float)[:, ::-1])
    return paths


def join_branches(paths, width):
    """Join skeleton paths through junctions and absorb leaf spurs shorter than twice width; return XY chains."""
    if not paths:
        return []
    endpoints = np.array([p[end] for p in paths for end in (0, -1)])
    parent = np.arange(len(endpoints))
    for a, b in cKDTree(endpoints).query_pairs(1.45):
        while parent[a] != a:
            a = parent[a]
        while parent[b] != b:
            b = parent[b]
        parent[max(a, b)] = min(a, b)
    for i in range(len(parent)):
        while parent[i] != parent[parent[i]]:
            parent[i] = parent[parent[i]]
    nodes = defaultdict(list)
    for i, node in enumerate(parent):
        nodes[int(node)].append((i // 2, i % 2))
    dropped = set()
    for i, p in enumerate(paths):
        length = np.linalg.norm(np.diff(p, axis=0), axis=1).sum()
        if length < 2 * width and any(len(nodes[int(parent[2 * i + end])]) == 1 for end in (0, 1)):
            if any(len(nodes[int(parent[2 * i + end])]) >= 3 for end in (0, 1)):
                dropped.add(i)
    pairs = {}
    for members in nodes.values():
        members = [(i, end) for i, end in members if i not in dropped]
        while len(members) >= 2:
            directions = []
            for i, end in members:
                p = paths[i] if end == 0 else paths[i][::-1]
                direction = p[min(6, len(p) - 1)] - p[0]
                directions.append(direction / max(np.linalg.norm(direction), 1e-9))
            costs = np.asarray(directions) @ np.asarray(directions).T
            np.fill_diagonal(costs, 2)
            a, b = np.unravel_index(np.argmin(costs), costs.shape)
            if costs[a, b] > -0.25:
                break
            first, second = members[a], members[b]
            pairs[first], pairs[second] = second, first
            members = [member for k, member in enumerate(members) if k not in (a, b)]
    used, joined = set(dropped), []
    starts = [(i, end) for i in range(len(paths)) for end in (0, 1) if (i, end) not in pairs]
    starts += [(i, 0) for i in range(len(paths))]
    for i, end in starts:
        if i in used:
            continue
        chain = []
        while i not in used:
            used.add(i)
            p = paths[i] if end == 0 else paths[i][::-1]
            chain.extend(p)
            next_end = pairs.get((i, 1 - end))
            if next_end is None:
                break
            i, end = next_end
        joined.append(np.asarray(chain))
    return joined


def bezier_segments(points, left, right, tolerance):
    """Fit points recursively using endpoint tangents left/right and pixel tolerance; return cubic control arrays."""
    if len(points) == 2:
        length = np.linalg.norm(points[1] - points[0]) / 3
        return [np.array([points[0], points[0] + left * length, points[-1] + right * length, points[-1]])]
    distances = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    t = distances / max(distances[-1], 1e-9)
    b = np.c_[(1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3]
    a1, a2 = b[:, 1, None] * left, b[:, 2, None] * right
    rhs = points - (b[:, 0] + b[:, 1])[:, None] * points[0] - (b[:, 2] + b[:, 3])[:, None] * points[-1]
    normal = np.array([[np.sum(a1 * a1), np.sum(a1 * a2)], [np.sum(a1 * a2), np.sum(a2 * a2)]])
    target = np.array([np.sum(a1 * rhs), np.sum(a2 * rhs)])
    alpha = np.linalg.lstsq(normal, target, rcond=None)[0]
    chord = np.linalg.norm(points[-1] - points[0])
    if np.min(alpha) < 1e-6 or np.max(alpha) > max(chord, distances[-1]) * 2:
        alpha[:] = distances[-1] / 3
    controls = np.array([points[0], points[0] + left * alpha[0], points[-1] + right * alpha[1], points[-1]])
    errors = np.linalg.norm(b @ controls - points, axis=1)
    split = int(np.argmax(errors))
    if errors[split] <= tolerance:
        return [controls]
    split = min(max(split, 1), len(points) - 2)
    tangent = points[split - 1] - points[split + 1]
    tangent /= max(np.linalg.norm(tangent), 1e-9)
    return (bezier_segments(points[:split + 1], left, tangent, tolerance)
            + bezier_segments(points[split:], -tangent, right, tolerance))


def cubic_path(points, closed=False, tolerance=0.30):
    """Fit compact cubic Beziers to XY points; closed joins endpoints; tolerance uses pixels."""
    points = np.asarray(points, float)
    if len(points) < 2:
        return ""
    if closed and np.linalg.norm(points[0] - points[-1]) > 0.01:
        points = np.vstack([points, points[0]])
    points = points[np.r_[True, np.linalg.norm(np.diff(points, axis=0), axis=1) > 1e-6]]
    if len(points) < 2:
        return ""
    left = points[1] - (points[-2] if closed else points[0])
    right = (points[1] if closed else points[-2]) - points[-1]
    left /= max(np.linalg.norm(left), 1e-9)
    right /= max(np.linalg.norm(right), 1e-9)
    segments = bezier_segments(points, left, right, tolerance)
    d = [f"M{points[0, 0]:.2f},{points[0, 1]:.2f}"]
    for segment in segments:
        c1, c2, end = segment[1:]
        d.append(f"C{c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f} {end[0]:.2f},{end[1]:.2f}")
    return " ".join(d) + (" Z" if closed else "")


def mask_path(mask, sigma=0.5, tolerance=0.32, scale=1):
    """Return evenodd compound Beziers for mask, preserving holes.

    sigma uses mask pixels; tolerance uses output pixels; scale is mask pixels per
    output pixel (supersampled masks use scale > 1).
    """
    field = ndi.gaussian_filter(np.pad(mask.astype(float), 2), sigma)
    paths = []
    for contour in measure.find_contours(field, 0.5):
        points = (contour[:, ::-1] - 2 + 0.5) / scale
        if len(points) < 5:
            continue
        area = abs(np.sum(points[:-1, 0] * points[1:, 1] - points[1:, 0] * points[:-1, 1])) / 2
        if area >= 0.65:
            paths.append(cubic_path(points, True, tolerance))
    return " ".join(paths)


def extract_strokes(rgb, palette, inks):
    """Extract stroked centerlines from rgb for palette inks; return strokes and covered mask."""
    strokes = []
    primitives = []
    covered = np.zeros(rgb.shape[:2], bool)
    diagnostics = []
    labels = nearest_labels(rgb, palette)
    accepted_supports = []
    inks = sorted(inks, key=lambda i: float(np.mean(palette[i])))
    for index in inks:
        ink = palette[index]
        coverage = ink_coverage(rgb, ink, palette, labels)
        mode = labels == index
        mode_distance = ndi.distance_transform_edt(mode)
        if mode.any() and (mode_distance[mode] > 2).mean() >= 0.14:
            bulk = ndi.binary_dilation(ndi.binary_opening(mode, iterations=2), iterations=3)
            coverage[bulk] = 0
        sensitive = len(palette) <= 6 and np.ptp(ink) < 25
        threshold = 0.10 if sensitive else 0.18
        support = coverage > threshold
        if any((support & previous).sum() > 0.74 * max(1, support.sum())
               for previous in accepted_supports):
            continue
        accepted_supports.append(support.copy())
        distances = ndi.distance_transform_edt(support)
        thick = distances > 3.5
        # Keep solid arrowheads and other broad ink regions as fills.
        broad = ndi.binary_dilation(thick, iterations=1) if thick.any() else thick
        if np.ptp(ink) < 25:
            connected, count = ndi.label(support)
            for region in ndi.find_objects(connected):
                if region is None:
                    continue
                ys, xs = region
                local = support[region]
                solid_distance = ndi.distance_transform_edt(coverage[region] > 0.65)
                box_area = (ys.stop - ys.start) * (xs.stop - xs.start)
                if (local.sum() < 250 and max(ys.stop - ys.start, xs.stop - xs.start) < 45
                        and solid_distance.max() > 1.9 and local.sum() / box_area > 0.45):
                    broad[region] |= local
        support &= ~broad
        high = ndi.zoom(coverage * support, 2, order=1, grid_mode=True, mode="nearest")
        skeleton = morphology.skeletonize(high > (0.12 if sensitive else 0.22))
        typical_width = 2 * float(np.median(distances[support])) if support.any() else 1
        paths = join_branches(trace_skeleton(skeleton), typical_width * 2)
        structures, _ = ndi.label(support)
        bins = defaultdict(list)
        retained = np.zeros_like(skeleton)
        for points in paths:
            length = np.linalg.norm(np.diff(points, axis=0), axis=1).sum() / 2
            if length < 1.25:
                continue
            source = (points + 0.5) / 2
            xy = np.rint(points).astype(int)
            # Integrate anti-alias coverage across the local normal to recover width.
            tangent = ndi.gaussian_filter1d(source, 1.4, axis=0)
            derivative = np.gradient(tangent, axis=0)
            normals = np.c_[-derivative[:, 1], derivative[:, 0]]
            normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-9)
            offsets = np.arange(-2.5, 2.51, 0.25)
            sample = source[:, None, :] + normals[:, None, :] * offsets[None, :, None] - 0.5
            values = ndi.map_coordinates(coverage, [sample[..., 1], sample[..., 0]], order=1, mode="nearest")
            widths = values.sum(axis=1) * 0.25
            shift = (values * offsets).sum(axis=1) / np.maximum(values.sum(axis=1), 1e-9)
            shift[:2] = 0
            shift[-2:] = 0
            source += normals * shift[:, None]
            width = float(np.clip(np.median(widths), 0.33, 3.4))
            width = round(width / 0.20) * 0.20
            smooth = ndi.gaussian_filter1d(source, 2.0, axis=0, mode="nearest")
            smooth[0], smooth[-1] = source[0], source[-1]
            center = smooth.mean(axis=0)
            _, _, axes = np.linalg.svd(smooth - center, full_matrices=False)
            perpendicular = np.abs((smooth - center) @ axes[1])
            if length >= 6 and perpendicular.max() < 0.13:
                projected = (smooth[[0, -1]] - center) @ axes[0]
                endpoints = center + projected[:, None] * axes[0]
                primitives.append({"type": "line", "name": f"ink_{index}_line_{len(primitives)}",
                                   "group": "ink", "x1": float(endpoints[0, 0]), "y1": float(endpoints[0, 1]),
                                   "x2": float(endpoints[1, 0]), "y2": float(endpoints[1, 1]),
                                   "stroke": hex_color(ink), "width": width})
            else:
                px, py = np.clip(np.rint(source[len(source) // 2] - .5).astype(int), [0, 0],
                                 [support.shape[1] - 1, support.shape[0] - 1])
                structure = int(structures[py, px])
                bins[structure, width].append(cubic_path(smooth, False, max(0.18, width * 0.15)))
            retained[xy[:, 1], xy[:, 0]] = True
        for (structure, width), paths_d in sorted(bins.items()):
            strokes.append((f"ink_{index}_part{structure}_w{width:.2f}".replace(".", "_"),
                            " ".join(paths_d), hex_color(ink), width, f"ink_{index}_structure_{structure}"))
        local_covered = support & ndi.binary_dilation(ndi.zoom(retained.astype(float), 0.5, order=0,
                                                             grid_mode=True, mode="nearest") > 0, iterations=2)
        local_covered |= (labels == index) & ndi.binary_dilation(local_covered, iterations=1)
        covered |= local_covered
        diagnostics.append({"color": hex_color(ink), "pixels": int(support.sum()),
                            "branches": sum(len(v) for v in bins.values())})
    return strokes, covered, diagnostics, primitives


def clean_fill_labels(rgb, labels, palette):
    """Reassign anti-alias islands in labels to nearby confident palette paint in rgb."""
    confident = np.zeros(labels.shape, bool)
    for i, paint in enumerate(palette):
        mask = labels == i
        exact = np.linalg.norm(rgb - paint, axis=2) < 4
        confident |= ndi.binary_erosion(mask) | (mask & exact)
    indices = ndi.distance_transform_edt(~confident, return_distances=False, return_indices=True)
    return labels[tuple(indices)]


def subpixel_mask(mask, rgb, paint, labels, palette, excluded):
    """Recover fractional mask edges from rgb mixed between paint and neighboring labels/palette; skip excluded ink."""
    field = mask.astype(float)
    distance, indices = ndi.distance_transform_edt(mask, return_indices=True)
    background = palette[labels[tuple(indices)]]
    direction = paint - background
    denominator = np.sum(direction * direction, axis=2)
    alpha = np.clip(np.sum((rgb - background) * direction, axis=2) / np.maximum(denominator, 1), 0, 1)
    residual = np.linalg.norm(rgb - background - alpha[..., None] * direction, axis=2)
    band = ndi.binary_dilation(mask) & (distance <= 1.5) & ~excluded
    take = band & (denominator > 30) & (residual < 12)
    field[take] = alpha[take]
    return field


def merge_soft_colors(rgb, labels, palette):
    """Merge adjacent palette bins across smooth shading in rgb; return relabeled map."""
    count = len(palette)
    parent = np.arange(count)
    lab = color.rgb2lab((palette / 255)[None])[0]
    exact = [np.all(rgb[labels == i] == paint, axis=1).mean() if (labels == i).any() else 0
             for i, paint in enumerate(palette)]
    contacts = defaultdict(list)
    for axis in (0, 1):
        a = labels[:-1, :] if axis == 0 else labels[:, :-1]
        b = labels[1:, :] if axis == 0 else labels[:, 1:]
        ca = rgb[:-1, :] if axis == 0 else rgb[:, :-1]
        cb = rgb[1:, :] if axis == 0 else rgb[:, 1:]
        changes = (a != b) & (a != 0) & (b != 0)
        pairs = np.sort(np.c_[a[changes], b[changes]], axis=1)
        differences = np.linalg.norm(ca[changes] - cb[changes], axis=1)
        for key in np.unique(pairs[:, 0] * count + pairs[:, 1]):
            i, j = divmod(int(key), count)
            contacts[i, j].extend(differences[(pairs[:, 0] == i) & (pairs[:, 1] == j)].tolist())
    for (i, j), differences in contacts.items():
        if len(differences) < 8 or np.linalg.norm(lab[i] - lab[j]) > 22:
            continue
        if np.median(differences) > 6.0:
            continue
        if exact[i] > 0.4 and exact[j] > 0.4:
            continue
        while parent[i] != i:
            i = parent[i]
        while parent[j] != j:
            j = parent[j]
        parent[max(i, j)] = min(i, j)
    for i in range(count):
        while parent[i] != parent[parent[i]]:
            parent[i] = parent[parent[i]]
    merged = parent[labels]
    for representative in np.unique(parent):
        children = np.flatnonzero(parent == representative)
        if len(children) > 1:
            mask = merged == representative
            if fit_gradient(rgb, mask) is None:
                merged[mask] = labels[mask]
    return merged


def ellipse_primitive(mask, paint, name, group):
    """Fit a small true ellipse to mask; paint/name/group label it; return spec or None."""
    if not 6 <= mask.sum() <= 800 or not np.array_equal(ndi.binary_fill_holes(mask), mask):
        return None
    contours = measure.find_contours(np.pad(mask.astype(float), 1), 0.5)
    if len(contours) != 1:
        return None
    points = contours[0][:, ::-1] - 1 + 0.5
    y, x = np.nonzero(mask)
    center = np.array([x.mean() + 0.5, y.mean() + 0.5])
    covariance = np.cov(np.c_[x, y].T, bias=True) + np.eye(2) / 12
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    a, b = 2 * np.sqrt(eigenvalues)
    angle = np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0])
    cx, cy = center
    if min(a, b) < 0.8 or max(a, b) / min(a, b) > 7:
        return None
    transformed = (points - center) @ eigenvectors
    residual = (np.linalg.norm(transformed / [a, b], axis=1) - 1) * min(a, b)
    if np.sqrt(np.mean(residual ** 2)) > 0.28:
        return None
    return {"type": "ellipse", "name": name, "group": group, "cx": float(cx), "cy": float(cy),
            "rx": float(a), "ry": float(b), "angle": float(np.degrees(angle)), "fill": paint}


def microdots(rgb, labels, palette, stroke_mask):
    """Recover unresolved small dark dots in rgb, excluding palette paint and stroke_mask; return circles."""
    background = ndi.median_filter(rgb, size=(5, 5, 1))
    contrast = (background - rgb) @ np.array([0.213, 0.715, 0.072])
    interior = ndi.distance_transform_edt(labels != 0) > 3
    unresolved = np.linalg.norm(rgb - palette[labels], axis=2) > 35
    spots = ((contrast > 35) & interior & unresolved
             & ~ndi.binary_dilation(stroke_mask, iterations=2))
    connected, count = ndi.label(spots)
    circles = []
    for index, region in enumerate(ndi.find_objects(connected), 1):
        if region is None:
            continue
        ys, xs = region
        mask = connected[region] == index
        if mask.sum() > 6 or max(ys.stop - ys.start, xs.stop - xs.start) > 4:
            continue
        local_y, local_x = np.nonzero(mask)
        weights = contrast[region][mask]
        cx = float(np.average(local_x + xs.start + 0.5, weights=weights))
        cy = float(np.average(local_y + ys.start + 0.5, weights=weights))
        py0, py1 = max(0, round(cy) - 5), min(rgb.shape[0], round(cy) + 5)
        px0, px1 = max(0, round(cx) - 5), min(rgb.shape[1], round(cx) + 5)
        patch = contrast[py0:py1, px0:px1]
        near_y, near_x = np.nonzero(patch > max(10, weights.max() * 0.3))
        if len(near_x) >= 3:
            covariance = np.cov(np.c_[near_x, near_y].T, aweights=patch[near_y, near_x], bias=True)
            eigenvalues = np.linalg.eigvalsh(covariance)
            if eigenvalues[1] > 5 * max(eigenvalues[0], 0.2):
                continue
        paint = np.average((2 * rgb - background)[region][mask], axis=0, weights=weights)
        area = 0.5 * weights.sum() / weights.max()
        circles.append({"type": "circle", "name": f"microdot_{len(circles)}", "group": "microdetails",
                        "cx": cx, "cy": cy, "r": float(np.sqrt(area / np.pi)), "fill": hex_color(paint)})
    return circles


def fit_gradient(rgb, mask):
    """Fit linear/radial paint to rgb inside mask; return SVG gradient spec or None."""
    interior = ndi.binary_erosion(mask, iterations=1)
    y, x = np.nonzero(interior)
    if len(x) < 80:
        return None
    stride = max(1, len(x) // 4000)
    x, y = x[::stride] + 0.5, y[::stride] + 0.5
    values = rgb[interior][::stride]
    centered = values - np.median(values, axis=0)
    constant_squared = np.mean(centered ** 2, axis=1)
    constant_error = np.mean(np.sort(constant_squared)[:max(1, int(len(values) * 0.8))])
    if constant_error < 12:
        return None
    xmin, xmax, ymin, ymax = x.min(), x.max(), y.min(), y.max()
    sx, sy = max(xmax - xmin, 1), max(ymax - ymin, 1)
    design = np.c_[(x - xmin) / sx, (y - ymin) / sy, np.ones(len(x))]
    coefficients = robust_plane(design, values)
    u, singular, _ = np.linalg.svd(coefficients[:2], full_matrices=False)
    direction = u[:, 0]
    coordinate = design[:, :2] @ direction
    lo, hi = np.percentile(coordinate, [0, 100])
    t = (coordinate - lo) / max(hi - lo, 1e-9)
    linear_design = np.c_[np.ones(len(t)), t, t * t]
    coeff = robust_plane(linear_design, values)
    squared = np.mean((values - linear_design @ coeff) ** 2, axis=1)
    best_error = np.mean(np.sort(squared)[:max(1, int(len(squared) * 0.8))])
    norm = float(np.dot(direction / [sx, sy], direction / [sx, sy]))
    g = direction / [sx, sy]
    origin = np.array([xmin, ymin]) + g * lo / norm
    end = origin + g * (hi - lo) / norm
    result = {"type": "linear", "x1": origin[0], "y1": origin[1],
              "x2": end[0], "y2": end[1], "coefficients": coeff}
    for fx, fy in ((0.5, 0.5), (0.25, 0.25), (0.75, 0.25), (0.5, 0.1), (0.5, 0.9)):
        cx, cy = xmin + sx * fx, ymin + sy * fy
        r = np.hypot((x - cx) / sx, (y - cy) / sy)
        radius = max(r.max(), 0.1)
        t = r / radius
        radial_design = np.c_[np.ones(len(t)), t, t * t]
        radial_coeff = robust_plane(radial_design, values)
        squared = np.mean((values - radial_design @ radial_coeff) ** 2, axis=1)
        error = np.mean(np.sort(squared)[:max(1, int(len(squared) * 0.8))])
        if error < best_error * 0.8:
            best_error = error
            result = {"type": "radial", "cx": cx, "cy": cy,
                      "rx": sx * radius, "ry": sy * radius, "coefficients": radial_coeff}
    if best_error > min(70, constant_error * 0.45):
        return None
    coeff = result.pop("coefficients")
    result["stops"] = [(float(t), hex_color(np.array([1, t, t * t]) @ coeff))
                       for t in np.linspace(0, 1, 5)]
    result["rmse"] = float(np.sqrt(best_error))
    return result


def robust_plane(design, values):
    """Fit design to RGB values with four robust least-squares passes; return coefficients."""
    coefficients = np.linalg.lstsq(design, values, rcond=None)[0]
    for _ in range(4):
        error = np.linalg.norm(values - design @ coefficients, axis=1)
        weights = 1 / np.maximum(error / max(3, np.median(error) * 1.5), 1)
        coefficients = np.linalg.lstsq(design * weights[:, None], values * weights[:, None], rcond=None)[0]
    return coefficients


def circle_backdrop(rgb):
    """Detect a large, mostly visible pale circular backdrop in rgb; return primitive and mask."""
    # Require a pale violet thin ring, avoiding anatomical circles and filled disks.
    candidate = ((rgb[..., 2] - rgb[..., 0] > 10) & (rgb[..., 0] - rgb[..., 1] > 4)
                 & (rgb.mean(axis=2) > 150) & (rgb.mean(axis=2) < 216))
    y, x = np.nonzero(candidate)
    if len(x) < 160:
        return None, np.zeros(rgb.shape[:2], bool)
    rng = np.random.default_rng(0)
    best = None
    xy = np.c_[x + 0.5, y + 0.5]
    for _ in range(450):
        points = xy[rng.choice(len(xy), 3, replace=False)]
        try:
            cx, cy, c = np.linalg.solve(np.c_[2 * points, np.ones(3)], (points * points).sum(axis=1))
        except np.linalg.LinAlgError:
            continue
        radius = math.sqrt(max(0, c + cx * cx + cy * cy))
        if not min(rgb.shape[:2]) * 0.32 < radius < max(rgb.shape[:2]) * 0.6:
            continue
        residual = np.abs(np.hypot(xy[:, 0] - cx, xy[:, 1] - cy) - radius)
        inliers = residual < 1.1
        if best is None or inliers.sum() > best[0]:
            best = int(inliers.sum()), cx, cy, radius, inliers
    if best is None or best[0] < 0.55 * 2 * np.pi * best[3]:
        return None, np.zeros(rgb.shape[:2], bool)
    points = xy[best[4]]
    cx, cy, c = np.linalg.lstsq(np.c_[2 * points, np.ones(len(points))],
                               (points * points).sum(axis=1), rcond=None)[0]
    radius = math.sqrt(max(0, c + cx * cx + cy * cy))
    yy, xx = np.indices(rgb.shape[:2])
    rr = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
    band = np.abs(rr - radius) < 1.8
    ring_color = np.median(rgb[candidate & band], axis=0)
    inside = rr < radius - 3
    values, counts = np.unique(rgb[inside].astype(np.uint8), axis=0, return_counts=True)
    fill = values[np.argmax(counts)]
    primitive = {"type": "circle", "name": "backdrop_circle", "cx": float(cx), "cy": float(cy),
                 "r": float(radius), "fill": hex_color(fill), "stroke": hex_color(ring_color),
                 "width": 1.55, "group": "backdrop"}
    return primitive, band & candidate


def box_mask(boxes, shape, scale):
    """Return a boolean mask of shape covering source-pixel boxes [x0, y0, x1, y1] scaled by scale."""
    mask = np.zeros(shape, bool)
    for x0, y0, x1, y1 in boxes:
        mask[max(0, int(y0 * scale)):int(math.ceil(y1 * scale)), max(0, int(x0 * scale)):int(math.ceil(x1 * scale))] = True
    return mask


def decompose(png_path, annotations=True, mode=None, keep_lines=()):
    """Decompose png_path into ordered layers, strokes, primitives, and annotation masks.

    annotations enables conservative neutral-text removal. mode forces "flat" or
    "shaded" instead of auto-detection. keep_lines lists source-pixel boxes where
    faint thin lines must survive (shaded mode). Returns a dict whose masks and path
    coordinates use source pixels, with metadata and gradient specs.
    """
    source = Image.open(png_path).convert("RGBA")
    source_size = source.size
    if max(source_size) > 900 and mode != "flat":
        source.thumbnail((WORKING_LONG, WORKING_LONG), Image.Resampling.LANCZOS)
        working = Image.alpha_composite(Image.new("RGBA", source.size, "white"), source).convert("RGB")
        sampled = np.asarray(working, dtype=np.float32)
        local_range = ndi.maximum_filter(sampled, size=(3, 3, 1)) - ndi.minimum_filter(sampled, size=(3, 3, 1))
        foreground = sampled.min(axis=2) < 245
        flat_fraction = float((np.max(local_range, axis=2)[foreground] < 0.5).mean()) if foreground.any() else 1.0
        if flat_fraction < 0.85 or mode == "shaded":
            from shaded_regions import decompose_shaded
            keep = box_mask(keep_lines, sampled.shape[:2], sampled.shape[1] / source_size[0])
            result = decompose_shaded(sampled, source_size, keep)
            result["metadata"]["flat_fraction"] = flat_fraction
            return result
    rgb = load_rgb(png_path)
    removed = annotation_mask(rgb) if annotations else np.zeros(rgb.shape[:2], bool)
    clean = restore_annotations(rgb, removed)
    backdrop, ring_mask = circle_backdrop(clean)
    if backdrop and annotations and mode != "shaded":
        from flat_regions import pale_parts
        removed |= ndi.binary_dilation((np.ptp(rgb, axis=2) < 35) & (rgb.mean(axis=2) < 130))
        clean = restore_annotations(rgb, removed)
        return pale_parts(rgb, clean, removed, backdrop)
    palette = find_palette(clean)
    local_range = ndi.maximum_filter(clean, size=(3, 3, 1)) - ndi.minimum_filter(clean, size=(3, 3, 1))
    foreground = clean.min(axis=2) < 245
    flat_fraction = float((local_range.max(axis=2)[foreground] < .5).mean()) if foreground.any() else 1.0
    if mode == "shaded" or (mode is None and len(palette) > 12 and flat_fraction < .5):
        from shaded_regions import decompose_shaded
        size = (round(rgb.shape[1] * 1600 / max(rgb.shape[:2])), round(rgb.shape[0] * 1600 / max(rgb.shape[:2])))
        sampled = np.asarray(Image.fromarray(clean.astype(np.uint8)).resize(size, Image.Resampling.BICUBIC), dtype=np.float32)
        keep = box_mask(keep_lines, sampled.shape[:2], size[0] / rgb.shape[1])
        result = decompose_shaded(sampled, (rgb.shape[1], rgb.shape[0]), keep)
        result["metadata"]["flat_fraction"] = flat_fraction
        result["metadata"]["mode"] = "shaded_small"
        result["annotations"]["removed"] = removed
        return result
    labels = nearest_labels(clean, palette)
    palette, inks = pick_inks(clean, palette, labels)
    if backdrop:
        inks = []
    strokes, stroke_mask, ink_info, stroke_primitives = extract_strokes(clean, palette, inks)
    hidden = stroke_mask | ring_mask
    filled_rgb = restore_annotations(clean, hidden)
    fill_labels = nearest_labels(filled_rgb, palette)
    # Restore solid ink shapes; only extracted thin lines disappear from fills.
    for index in inks:
        fill_labels[(labels == index) & ~hidden] = index
    fill_labels = clean_fill_labels(filled_rgb, fill_labels, palette)
    fill_labels = merge_soft_colors(filled_rgb, fill_labels, palette)
    light_components, _ = ndi.label(labels == 0)
    for component, region in enumerate(ndi.find_objects(light_components), 1):
        if region is None:
            continue
        ys, xs = region
        if ys.start == 0 or xs.start == 0 or ys.stop == rgb.shape[0] or xs.stop == rgb.shape[1]:
            continue
        light_mask = light_components == component
        if not 5 <= light_mask.sum() <= 900:
            continue
        ring = ndi.binary_dilation(light_mask, iterations=2) & ~ndi.binary_dilation(light_mask)
        counts_local = np.bincount(labels[ring], minlength=len(palette))
        counts_local[0] = 0
        if not counts_local.any():
            continue
        background_index = int(np.argmax(counts_local))
        background = palette[background_index]
        direction = 255 - background
        denominator = np.dot(direction, direction)
        alpha = np.clip(np.sum((clean - background) * direction, axis=2) / max(denominator, 1), 0, 1)
        residual = np.linalg.norm(clean - background - alpha[..., None] * direction, axis=2)
        band = ndi.binary_dilation(light_mask) & ~light_mask & ~hidden
        fill_labels[band & (residual < 15) & (alpha > 0.12)] = background_index
    if backdrop:
        yy, xx = np.indices(rgb.shape[:2])
        inside = np.hypot(xx + 0.5 - backdrop["cx"], yy + 0.5 - backdrop["cy"]) < backdrop["r"] + 1.5
        pale = np.linalg.norm(filled_rgb - np.array([int(backdrop["fill"][i:i + 2], 16)
                                                  for i in (1, 3, 5)]), axis=2) < 9
        fill_labels[inside & pale] = 0
        ring = np.abs(np.hypot(xx + 0.5 - backdrop["cx"], yy + 0.5 - backdrop["cy"]) - backdrop["r"]) < 2.8
        background_rgb = np.array([int(backdrop["fill"][i:i + 2], 16) for i in (1, 3, 5)])
        core = ((np.linalg.norm(clean - background_rgb, axis=2) > 8)
                & (np.linalg.norm(clean - 255, axis=2) > 6))
        protected = ndi.binary_dilation(ndi.binary_opening(core, iterations=2), iterations=2)
        fill_labels[ring & ~protected] = 0
        small = np.zeros(fill_labels.shape, bool)
        for index in np.unique(fill_labels):
            if index == 0:
                continue
            components, number = ndi.label(fill_labels == index)
            sizes = np.bincount(components.ravel())
            small |= (components > 0) & (sizes[components] < 8)
        if small.any():
            indices = ndi.distance_transform_edt(small, return_distances=False, return_indices=True)
            fill_labels[small] = fill_labels[tuple(indices)][small]
    counts = np.bincount(fill_labels.ravel(), minlength=len(palette))
    order = [int(i) for i in np.argsort(counts)[::-1] if i != 0 and counts[i] >= 4]
    ranks = np.full(len(palette), -1, int)
    ranks[order] = np.arange(len(order))
    layers, primitives, gradients = [], list(stroke_primitives), {}
    if backdrop:
        primitives.append(backdrop)
    elif len(palette) > 10:
        primitives.extend(microdots(clean, labels, palette, stroke_mask))
    part_counts = {}
    foreground = fill_labels != 0
    for rank, index in enumerate(order):
        visible = fill_labels == index
        connected, number = ndi.label(visible)
        sizes = np.bincount(connected.ravel())
        minimum = 8 if palette[index].mean() > 140 else 3
        visible &= sizes[connected] >= minimum
        if not visible.any():
            continue
        mask = foreground.copy() if rank == 0 else visible.copy()
        holes = ndi.binary_fill_holes(mask) & ~mask
        mask |= holes & (ranks[fill_labels] > rank)
        mask |= ndi.binary_dilation(mask) & (ranks[fill_labels] > rank)
        if backdrop:
            mask = ndi.binary_closing(mask)
        paint = hex_color(palette[index])
        name = f"paint_{index:02d}_{paint[1:]}"
        group = "artwork"
        gradient = fit_gradient(filled_rgb, visible)
        if gradient:
            gradients[name] = gradient
        # Fit repeated tiny ellipses before contour tracing, keeping organelle dots editable.
        if index not in inks and len(palette) <= 6:
            candidates, fitted = [], []
            for component in range(1, number + 1):
                component_mask = connected == component
                if not 6 <= sizes[component] <= 800:
                    continue
                candidates.append(component)
                primitive = ellipse_primitive(component_mask, paint, f"{name}_ellipse_{component}", "details")
                if primitive:
                    fitted.append((component, primitive))
            # Repeated shape evidence prevents incidental brain highlights becoming ellipses.
            if len(candidates) >= 2 and len(fitted) >= 0.75 * len(candidates):
                for component, primitive in fitted:
                    primitives.append(primitive)
                    mask[connected == component] = False
        if mask.any():
            field = subpixel_mask(mask, clean, palette[index], fill_labels, palette, hidden)
            layers.append((name, field, paint, 0.85 if backdrop else 0.60, group))
        if not gradient and number > 1:
            for component in range(1, number + 1):
                if sizes[component] < 150:
                    continue
                component_mask = connected == component
                local_gradient = fit_gradient(filled_rgb, component_mask)
                if local_gradient:
                    local_name = f"{name}_shading_{component}"
                    gradients[local_name] = local_gradient
                    component_mask |= ndi.binary_dilation(component_mask) & (ranks[fill_labels] > rank)
                    layers.append((local_name, component_mask, paint, 0.60, group))
        part_counts[name] = int((sizes[1:] >= 3).sum())
    # Enclosed light shapes have their own paint and sharp arrowheads. Painting
    # them last also covers antialias colors borrowed from a neighboring fill.
    light, count = ndi.label((labels == 0) & ~removed)
    for component, region in enumerate(ndi.find_objects(light), 1):
        if region is None:
            continue
        ys, xs = region
        if ys.start == 0 or xs.start == 0 or ys.stop == rgb.shape[0] or xs.stop == rgb.shape[1]:
            continue
        mask = light == component
        if not 5 <= mask.sum() <= 900:
            continue
        border = ndi.binary_dilation(mask) & ~mask
        if (rgb[border].mean(axis=1) < 80).mean() > 0.25:
            continue
        name = f"light_shape_{component:03d}"
        field = subpixel_mask(mask, clean, np.array([255., 255., 255.]), labels, palette, np.zeros_like(mask))
        layers.append((name, field, "#ffffff", 0.28, f"light_detail_{component:03d}"))
    layer_strokes = {}
    silhouette = ndi.binary_fill_holes(labels != 0)
    if len(palette) <= 6 and len(inks) == 1:
        index = inks[0]
        near_border = ndi.distance_transform_edt(silhouette) < 5
        if near_border[labels == index].mean() > 0.85:
            ink = hex_color(palette[index])
            rim_paths = [stroke for stroke in strokes if stroke[2] == ink]
            if rim_paths:
                width = max(rim_paths, key=lambda item: len(item[1]))[3]
                strokes = [stroke for stroke in strokes if stroke[2] != ink]
                primitives = [p for p in primitives if p.get("stroke") != ink]
                layers = [layer for layer in layers if layer[2] != ink]
                name, field, paint, sigma, group = layers[0]
                field = np.clip(ndi.distance_transform_edt(silhouette) - width / 2, 0, 1) - .15
                layers[0] = (name, field, paint, 1.4, group)
                layer_strokes[name] = (ink, width)
    return {"size": (rgb.shape[1], rgb.shape[0]), "layers": layers, "strokes": strokes,
            "primitives": primitives, "annotations": {"removed": removed}, "gradients": gradients,
            "layer_strokes": layer_strokes, "spatial_parts": True,
            "metadata": {"palette": [hex_color(c) for c in palette], "ink": ink_info,
                         "fill_components": part_counts, "annotation_pixels": int(removed.sum()),
                         "mask_coordinates": "source pixel centers at x+0.5,y+0.5"}}


def gradient_xml(name, spec):
    """Return SVG gradient definition for name and fitted gradient spec."""
    if spec["type"] == "linear":
        attributes = " ".join(f'{key}="{spec[key]:.4f}"' for key in ("x1", "y1", "x2", "y2"))
        tag = "linearGradient"
    else:
        attributes = (f'cx="0" cy="0" r="1" gradientTransform="translate({spec["cx"]:.4f},'
                      f'{spec["cy"]:.4f}) scale({spec["rx"]:.4f},{spec["ry"]:.4f})"')
        tag = "radialGradient"
    stops = "".join(f'<stop offset="{offset:.4f}" stop-color="{paint}"/>' for offset, paint in spec["stops"])
    return f'<{tag} id="gradient_{name}" gradientUnits="userSpaceOnUse" {attributes}>{stops}</{tag}>'


def shape_xml(shape, gradients):
    """Serialize named shape with gradients dictionary; return one editable SVG element."""
    name = shape["name"]
    paint = f"url(#gradient_{name})" if name in gradients else shape.get("fill", "none")
    attributes = {"id": name, "fill": paint, "fill-rule": "evenodd"}
    for key in ("d", "x", "y", "width", "height", "cx", "cy", "r", "rx", "ry", "x1", "y1", "x2", "y2",
                "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin"):
        if key in shape:
            value = shape[key]
            attributes[key] = f"{value:.4f}" if isinstance(value, (float, np.floating)) else str(value)
    if shape.get("angle"):
        attributes["transform"] = f'rotate({shape["angle"]:.4f} {shape["cx"]:.4f} {shape["cy"]:.4f})'
    text = " ".join(f'{key}="{escape(value)}"' for key, value in attributes.items())
    return f'<{shape["type"]} {text}/>'


def to_svg(result, out_svg, scale=4):
    """Write result to out_svg at scale times native dimensions; return written Path."""
    width, height = result["size"]
    groups = list(dict.fromkeys([p["group"] for p in result["primitives"] if p["group"] == "backdrop"]
                               + [shape["group"] for shape in result.get("shapes", [])]
                               + [layer[4] for layer in result["layers"]]
                               + [stroke[4] for stroke in result["strokes"]]
                               + [p["group"] for p in result["primitives"] if p["group"] != "backdrop"]))
    gradients = result.get("gradients", {})
    xml = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width * scale:g}" height="{height * scale:g}" '
           f'viewBox="0 0 {width} {height}">',
           '<title>Raster decomposition: editable fills and centerline strokes</title>',
           '<defs>' + "".join(gradient_xml(name, spec) for name, spec in gradients.items()) + '</defs>',
           f'<rect id="paper" width="{width}" height="{height}" fill="#ffffff"/>']
    for group in groups:
        xml.append(f'<g id="{escape(group)}">')
        for p in result["primitives"]:
            if p["group"] != group:
                continue
            if p["type"] == "circle":
                geometry = " ".join(f'{key}="{p[key]:.4f}"' for key in ("cx", "cy", "r"))
            elif p["type"] == "line":
                geometry = " ".join(f'{key}="{p[key]:.4f}"' for key in ("x1", "y1", "x2", "y2"))
            else:
                geometry = " ".join(f'{key}="{p[key]:.4f}"' for key in ("cx", "cy", "rx", "ry"))
                if p.get("angle"):
                    geometry += f' transform="rotate({p["angle"]:.4f} {p["cx"]:.4f} {p["cy"]:.4f})"'
            xml.append(f'<{p["type"]} id="{escape(p["name"])}" {geometry} fill="{p.get("fill", "none")}" '
                       f'stroke="{p.get("stroke", "none")}" stroke-width="{p.get("width", 0):.3f}"/>')
        xml.extend(shape_xml(shape, gradients) for shape in result.get("shapes", []) if shape["group"] == group)
        for name, mask, paint, sigma, layer_group in result["layers"]:
            if layer_group != group:
                continue
            fill = f"url(#gradient_{name})" if name in gradients else paint
            rim = result.get("layer_strokes", {}).get(name)
            stroke_attributes = f' stroke="{rim[0]}" stroke-width="{rim[1]:.3f}"' if rim else ""
            if result.get("spatial_parts"):
                connected, number = ndi.label(mask > .5)
                sizes = np.bincount(connected.ravel())
                pieces = []
                for component, region in enumerate(ndi.find_objects(connected), 1):
                    if region is None or sizes[component] < 3:
                        continue
                    ys, xs = region
                    ys = slice(max(0, ys.start - 2), min(mask.shape[0], ys.stop + 2))
                    xs = slice(max(0, xs.start - 2), min(mask.shape[1], xs.stop + 2))
                    local = np.where(ndi.binary_dilation(connected[ys, xs] == component), mask[ys, xs], 0)
                    d = mask_path(local, sigma)
                    part = f"{name}_part_{component:03d}"
                    pieces.append(f'<g id="{part}"><path id="{part}_fill" transform="translate({xs.start} {ys.start})" '
                                  f'd="{d}" fill="{fill}" fill-rule="evenodd"{stroke_attributes}/></g>')
                # Gradients use source coordinates, so their geometry must not
                # inherit a local-coordinate translation.
                if name in gradients:
                    d = mask_path(mask, sigma)
                    xml.append(f'<path id="{escape(name)}" d="{d}" fill="{fill}" fill-rule="evenodd"{stroke_attributes}/>')
                else:
                    xml.extend(pieces)
            else:
                d = mask_path(mask, sigma)
                xml.append(f'<path id="{escape(name)}" d="{d}" fill="{fill}" fill-rule="evenodd"{stroke_attributes}/>')
        for name, d, paint, stroke_width, stroke_group in result["strokes"]:
            if stroke_group == group:
                xml.append(f'<path id="{escape(name)}" d="{d}" fill="none" stroke="{paint}" '
                           f'stroke-width="{stroke_width:.3f}" stroke-linecap="butt" stroke-linejoin="round"/>')
        xml.append('</g>')
    xml.append('</svg>')
    path = Path(out_svg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(xml) + "\n", encoding="utf-8")
    return path


def render_svg(svg_path, png_path):
    """Render svg_path on white into png_path using resvg; return RGB PIL image."""
    import resvg_py
    image = Image.open(io.BytesIO(resvg_py.svg_to_bytes(svg_path=str(svg_path), background="#ffffff"))).convert("RGB")
    image.save(png_path)
    return image
