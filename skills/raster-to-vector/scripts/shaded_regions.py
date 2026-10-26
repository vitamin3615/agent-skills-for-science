"""Edge-bounded regions and fitted SVG paint for shaded scientific artwork."""

from collections import defaultdict
import math

import numpy as np
from scipy import ndimage as ndi
from skimage import color, measure, morphology, segmentation
from skimage.filters import sato


GROUP_GAP = 8


def line_ridges(lightness, strength, sigmas=(1, 2, 3), response=5.0, contrast=2.0, flat=8.0):
    """Return the cores of thin lines in lightness that are darker than their surroundings, whatever their hue.

    A Sato valley filter at the stroke scales (sigmas in working pixels) finds line
    structure. Only pixels darker than their blurred neighbourhood by contrast, and
    with colour edge strength below flat, are kept: that is the flat core of each
    line, which also breaks the network wherever two touching lines change colour.
    """
    valleys = sato(lightness, sigmas=sigmas, black_ridges=True)
    ridges = ((valleys > response) & (lightness < ndi.gaussian_filter(lightness, 4) - contrast)
              & (strength < flat))
    # Local lightness minima keep one-pixel coloured lines whose core is never flat.
    # The window scales with the widest sigma; minima stop where a darker line meets.
    reach = 2 * round(max(sigmas)) + 1
    minima = ((lightness < ndi.minimum_filter(lightness, size=3) + 1.5)
              & (ndi.maximum_filter(lightness, size=reach + 4) - lightness > 8))
    ridges |= minima
    labels, _ = ndi.label(ridges)
    sizes = np.bincount(labels.ravel())
    return ridges & (sizes[labels] >= 6)


def detail_dots(lightness, radius=4, contrast=14):
    """Return small compact marks in lightness that differ from their surroundings, whatever their hue.

    A black or white top-hat at the dot scale (radius in working pixels) finds marks
    darker or lighter than the paint around them. Only isolated components no wider
    than the footprint count, so lines and broad highlights are left to the ridges and
    the gradient fits.
    """
    footprint = morphology.disk(radius)
    dots = np.zeros(lightness.shape, bool)
    for tophat in (morphology.black_tophat, morphology.white_tophat):
        marks = tophat(lightness, footprint) > contrast
        labels, _ = ndi.label(marks)
        for index, region in enumerate(ndi.find_objects(labels), 1):
            ys, xs = region
            mask = labels[region] == index
            if 3 <= mask.sum() <= 2 * radius * radius and max(ys.stop - ys.start, xs.stop - xs.start) <= 2 * radius:
                dots[region] |= mask
    return dots


def segment_regions(rgb, keep=None):
    """Segment working-resolution RGB by sharp boundaries; return connected labels and edge strength.

    keep optionally marks working pixels where any line darker than its surroundings
    by one lightness unit must survive, as requested by a hint.
    """
    smooth = ndi.gaussian_filter(rgb.astype(np.float32), (0.55, 0.55, 0))
    dx = ndi.sobel(smooth, axis=1) / 8
    dy = ndi.sobel(smooth, axis=0) / 8
    strength = np.sqrt(np.max(dx * dx + dy * dy, axis=2))
    lightness = smooth.mean(axis=2)
    unit = max(rgb.shape[:2]) / 1600
    ridges = line_ridges(lightness, strength)
    if keep is not None and keep.any():
        ridges |= keep & (lightness < ndi.gaussian_filter(lightness, 4) - 1)
    dots = detail_dots(lightness) & ~ridges
    seeds, _ = ndi.label((strength < 3.2) & ~ndi.binary_dilation(ridges | dots))
    sizes = np.bincount(seeds.ravel())
    seeds[sizes[seeds] < 6] = 0
    seeds, _, _ = segmentation.relabel_sequential(seeds)
    # Small dots seed their own regions, so the fill around them cannot absorb them.
    first_mark = int(seeds.max()) + 1
    for marks in (ridges, dots):
        mark_labels, _ = ndi.label(marks)
        seeds[marks] = mark_labels[marks] + seeds.max()
    labels = segmentation.watershed(strength, markers=seeds, connectivity=1)
    # A smooth color transition must not become a boundary merely because a
    # thin highlight or an antialiased corner briefly interrupted its seed.
    count = int(labels.max()) + 1
    parent = np.arange(count)
    lab = color.rgb2lab(rgb / 255).astype(np.float32)
    sizes = np.bincount(labels.ravel(), minlength=count)
    means = np.array([np.bincount(labels.ravel(), weights=lab[..., c].ravel(), minlength=count)
                      / np.maximum(sizes, 1) for c in range(3)]).T
    region_distance = ndi.distance_transform_edt(~segmentation.find_boundaries(labels, mode="inner"))
    widths = 2 * ndi.maximum(region_distance, labels, np.arange(count))
    contacts = defaultdict(list)
    for a, b, e in ((labels[:, :-1], labels[:, 1:], np.maximum(strength[:, :-1], strength[:, 1:])),
                    (labels[:-1], labels[1:], np.maximum(strength[:-1], strength[1:]))):
        change = a != b
        pairs = np.sort(np.c_[a[change], b[change]], axis=1)
        keys = pairs[:, 0].astype(np.int64) * count + pairs[:, 1]
        order = np.argsort(keys)
        keys, values = keys[order], e[change][order]
        starts = np.r_[0, np.flatnonzero(np.diff(keys)) + 1, len(keys)]
        for start, stop in zip(starts[:-1], starts[1:]):
            contacts[divmod(int(keys[start]), count)].extend(values[start:stop].tolist())
    # Greedy agglomeration from the most similar pair. A merge is judged on whole-group
    # mean colors as well as the pair, so a chain of small steps (outline, shadow
    # band, fill) cannot drift into one region.
    group_sum, group_size = means * sizes[:, None], sizes.astype(float)
    # Groups grown from a ridge or dot seed are drawn marks. A chain of antialias
    # slivers must not carry them into the lighter paint they are drawn on.
    group_mark = np.arange(count) >= first_mark
    ordered = sorted(contacts.items(), key=lambda item: np.linalg.norm(means[item[0][0]] - means[item[0][1]]))
    for (a, b), values in ordered:
        difference = np.linalg.norm(means[a] - means[b])
        chroma_a, chroma_b = means[a, 1:], means[b, 1:]
        same_hue = np.dot(chroma_a, chroma_b) / max(np.linalg.norm(chroma_a) * np.linalg.norm(chroma_b), 1)
        # A thin same-hue region is a highlight or antialias band to absorb, unless it
        # is darker than its neighbor: that is a drawn outline and stays separate.
        thin = a if widths[a] <= widths[b] else b
        other = b if thin == a else a
        # Two thin pieces of one colour that meet end to end, across a cut no longer
        # than the line is wide, are one line cut by its own antialiasing.
        line_pieces = (min(a, b) >= first_mark and widths[other] <= 8 * unit
                       and len(values) <= 3 * widths[other] and difference < 12 and same_hue > .9)
        dark_line = (not line_pieces and widths[thin] <= 8
                     and means[thin, 0] < means[other, 0] - 4)
        same_line = line_pieces or (max(widths[a], widths[b]) <= 5 and same_hue > .92 and not dark_line
                                    and abs(means[a, 0] - means[b, 0]) < 18 and difference < 26)
        if dark_line and difference < 60:
            continue
        if len(values) < 2 or (difference > 14 and not same_line):
            continue
        if np.median(values) > 3.2 and difference > 4.0 and not same_line:
            continue
        while parent[a] != a:
            a = parent[a]
        while parent[b] != b:
            b = parent[b]
        if a == b:
            continue
        # Line pieces join only while both sides are still marks, never two paint groups.
        if line_pieces and not (group_mark[a] and group_mark[b]):
            if (difference > 14 or (np.median(values) > 3.2 and difference > 4.0)
                    or (widths[thin] <= 8 and means[thin, 0] < means[other, 0] - 4)):
                continue
            same_line = False
        group_gap = np.linalg.norm(group_sum[a] / group_size[a] - group_sum[b] / group_size[b])
        if group_mark[a] != group_mark[b]:
            mark, paint = (a, b) if group_mark[a] else (b, a)
            if abs(group_sum[mark, 0] / group_size[mark] - group_sum[paint, 0] / group_size[paint]) > 4:
                continue
        # A thin absorbed band must not bridge two groups that differ clearly.
        if group_gap > (GROUP_GAP + 2 if same_line else GROUP_GAP):
            continue
        low, high = min(a, b), max(a, b)
        parent[high] = low
        group_sum[low] += group_sum[high]
        group_size[low] += group_size[high]
        # A mark absorbed into paint of its own lightness is paint from then on.
        group_mark[low] = group_mark[a] and group_mark[b]
    for i in range(count):
        while parent[i] != parent[parent[i]]:
            parent[i] = parent[parent[i]]
    return segmentation.relabel_sequential(parent[labels])[0], strength


def split_structured(labels, rgb, strength, separation=20.0, sharp=6.0):
    """Split regions of labels whose rgb colours form two clusters divided by an edge; return new labels.

    A gradient fit over such a region would smear one part's colour across the other.
    Clusters come from two-means in Lab; the split is kept only when cluster centres
    differ by separation and the mean edge strength on the cluster boundary inside the
    region exceeds sharp, so a smooth gradient is never cut.
    """
    labels = labels.copy()
    next_label = int(labels.max()) + 1
    sizes = np.bincount(labels.ravel())
    for index, region in enumerate(ndi.find_objects(labels), 1):
        if region is None or sizes[index] < 200:
            continue
        mask = labels[region] == index
        lab = color.rgb2lab(rgb[region][mask] / 255)
        centres = lab[[np.argmin(lab[:, 0]), np.argmax(lab[:, 0])]]
        for _ in range(8):
            assign = np.linalg.norm(lab[:, None] - centres[None], axis=2).argmin(axis=1)
            if assign.min() == assign.max():
                break
            centres = np.array([lab[assign == k].mean(axis=0) for k in (0, 1)])
        if assign.min() == assign.max() or np.linalg.norm(centres[0] - centres[1]) < separation:
            continue
        minority = np.bincount(assign, minlength=2).argmin()
        part = np.zeros(mask.shape, bool)
        part[mask] = assign == minority
        if part.sum() < max(20, 0.03 * mask.sum()):
            continue
        boundary = part & ndi.binary_dilation(mask & ~part)
        if not boundary.any() or strength[region][boundary].mean() < sharp:
            continue
        pieces, count = ndi.label(part)
        piece_sizes = np.bincount(pieces.ravel())
        for piece in range(1, count + 1):
            if piece_sizes[piece] >= 40:
                local = labels[region]
                local[pieces == piece] = next_label
                next_label += 1
    return labels


def join_line_fragments(labels, rgb, unit=1.0, tolerance=10.0):
    """Rejoin thin same-colour fragments in labels across short gaps; return new labels.

    A faint one-pixel outline often segments into a row of short pieces, which would
    render as a beaded line. Thin regions (at most 5 * unit working pixels wide) of
    similar Lab colour (within tolerance) are closed across gaps of about 2 * unit
    pixels; a gap pixel joins the line only if its colour is nearer the line's colour
    than its own region's mean.
    """
    lab = color.rgb2lab(rgb / 255).astype(np.float32)
    count = int(labels.max()) + 1
    sizes = np.bincount(labels.ravel(), minlength=count)
    means = np.array([np.bincount(labels.ravel(), weights=lab[..., c].ravel(), minlength=count)
                      / np.maximum(sizes, 1) for c in range(3)]).T
    thin = []
    for index, region in enumerate(ndi.find_objects(labels), 1):
        if region is None or sizes[index] < 4:
            continue
        mask = labels[region] == index
        if 2 * ndi.distance_transform_edt(np.pad(mask, 1)).max() <= 5 * unit and max(mask.shape) >= 4 * unit:
            thin.append(index)
    labels = labels.copy()
    remaining = list(thin)
    footprint = morphology.disk(max(1, round(2 * unit)))
    while remaining:
        seed = remaining.pop(0)
        family = [seed] + [i for i in remaining if np.linalg.norm(means[i] - means[seed]) < tolerance]
        remaining = [i for i in remaining if i not in family]
        if len(family) < 2:
            continue
        member = np.isin(labels, family)
        closed = ndi.binary_closing(member, structure=footprint) | member
        line = means[family].mean(axis=0)
        gap = closed & ~member
        nearer = np.linalg.norm(lab[gap] - line, axis=1) < np.linalg.norm(lab[gap] - means[labels[gap]], axis=1)
        joined = member.copy()
        joined[np.nonzero(gap)[0][nearer], np.nonzero(gap)[1][nearer]] = True
        pieces, number = ndi.label(joined, structure=np.ones((3, 3)))
        for piece in range(1, number + 1):
            area = pieces == piece
            inside = np.unique(labels[area & member])
            if len(inside) >= 2:
                labels[area] = inside.min()
    return labels


def fit_paint(xy, values, bounds):
    """Fit flat, linear, or elliptical radial paint to XY/RGB samples within bounds; return paint and error."""
    from decompose import hex_color

    x0, y0, x1, y1 = bounds
    span = np.maximum([x1 - x0, y1 - y0], 1)
    uv = (xy - [x0, y0]) / span
    flat = np.mean(values, axis=0)
    flat_error = float(np.mean((values - flat) ** 2))
    best = {"fill": hex_color(flat), "error": flat_error, "penalty": flat_error + 0.2}
    if len(values) < 12 or flat_error < 0.4:
        return best
    plane = np.linalg.lstsq(np.c_[np.ones(len(uv)), uv], values, rcond=None)[0]
    u, _, _ = np.linalg.svd(plane[1:], full_matrices=False)
    direction = u[:, 0]
    coordinates = uv @ direction
    lo, hi = float(coordinates.min()), float(coordinates.max())
    t = (coordinates - lo) / max(hi - lo, 1e-6)
    candidates = [("linear", t, direction, lo, hi)]
    if len(values) >= 80 and min(span) > 5:
        for cx, cy in ((0.5, 0.5), (0.2, 0.2), (0.8, 0.2), (0.2, 0.8), (0.8, 0.8),
                       (0.5, 0), (0, 0.5), (1, 0.5), (0.5, 1)):
            radius = np.linalg.norm(uv - [cx, cy], axis=1)
            extent = max(float(radius.max()), 0.1)
            candidates.append(("radial", radius / extent, [cx, cy], extent, None))
    for kind, t, location, lo, hi in candidates:
        # Piecewise linear least squares matches SVG interpolation exactly.
        for stop_count in (2, 3, 4):
            stops = np.linspace(0, 1, stop_count)
            design = np.maximum(1 - np.abs(t[:, None] - stops) * (stop_count - 1), 0)
            coefficients = np.linalg.lstsq(design, values, rcond=None)[0]
            coefficients = np.clip(coefficients, 0, 255)
            error = float(np.mean((values - design @ coefficients) ** 2))
            penalty = error + stop_count * 0.4 + (0.6 if kind == "radial" else 0)
            if penalty >= best["penalty"]:
                continue
            spec = {"type": kind, "stops": [(float(t), hex_color(c)) for t, c in zip(stops, coefficients)],
                    "rmse": math.sqrt(error)}
            if kind == "linear":
                g = location / span
                origin = np.array([x0, y0]) + g * lo / np.dot(g, g)
                end = origin + g * (hi - lo) / np.dot(g, g)
                spec.update(dict(zip(("x1", "y1", "x2", "y2"), [*origin, *end])))
            else:
                center = np.array([x0, y0]) + np.array(location) * span
                spec.update(cx=float(center[0]), cy=float(center[1]), rx=float(span[0] * lo), ry=float(span[1] * lo))
            best = {"fill": hex_color(flat), "gradient": spec, "error": error, "penalty": penalty}
    return best


def region_geometry(mask, origin, factor, core=None, unit=1.0):
    """Fit mask with a primitive, a stroke or closed Beziers; origin and factor map working pixels to source coordinates.

    core is the region before it was tucked under later paint; stroke centrelines and
    widths come from it, so the overlap does not widen the stroke. unit is working
    pixels per pixel of a 1600 px working raster, which the size limits assume.
    """
    from decompose import cubic_path, trace_skeleton, join_branches

    core = mask if core is None else core
    padded = np.pad(mask.astype(np.float32), 2)
    distance = ndi.distance_transform_edt(core)
    thickness = 2 * distance.max()
    if core.sum() > 40 * unit * unit and thickness < 9 * unit and max(core.shape) > 25 * unit:
        # A straight bar of constant width is one exact segment with butt ends.
        y, x = np.nonzero(core)
        points = np.c_[x, y] + 0.5
        center = points.mean(axis=0)
        _, _, axes = np.linalg.svd(points - center, full_matrices=False)
        along, across = (points - center) @ axes[0], (points - center) @ axes[1]
        span = np.ptp(along)
        width = len(points) / max(span, 1)
        if span > 8 * width and np.abs(across).max() < width / 2 + 1:
            ends = center + np.array([along.min(), along.max()])[:, None] * axes[0]
            ends = (ends + origin) * factor
            return {"type": "path", "d": f"M{ends[0, 0]:.2f},{ends[0, 1]:.2f} L{ends[1, 0]:.2f},{ends[1, 1]:.2f}",
                    "as_stroke": True, "stroke-width": width * factor, "stroke-linecap": "butt"}
        skeleton = morphology.skeletonize(core)
        # Tapered marks keep their filled outline; only constant-width lines become strokes.
        local = 2 * distance[skeleton]
        constant = len(local) > 0 and np.std(local) < 0.3 * np.median(local)
        chains = join_branches(trace_skeleton(skeleton), max(1, thickness / 2))
        length = sum(np.linalg.norm(np.diff(p, axis=0), axis=1).sum() for p in chains)
        width = core.sum() / max(length, 1)
        if constant and 0.7 * unit < width < 5.0 * unit and length > 25 * unit:
            paths = []
            for points in chains:
                if len(points) < 3:
                    continue
                closed = np.linalg.norm(points[0] - points[-1]) < max(4, width * 2)
                if not closed:
                    # Skeleton ends curl into the blunt tip; the round cap restores the length.
                    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
                    if arc[-1] > 4 * width:
                        points = points[(arc >= 0.75 * width) & (arc <= arc[-1] - 0.75 * width)]
                points = ndi.gaussian_filter1d(points, 2.0, axis=0, mode="wrap" if closed else "nearest")
                paths.append(cubic_path((points + origin + .5) * factor, closed, max(.6, width * .22) * factor))
            if paths:
                return {"type": "path", "d": " ".join(paths), "as_stroke": True,
                        "stroke-width": width * factor, "stroke-linecap": "round", "stroke-linejoin": "round"}
    sigma = min(0.85, max(0.48, thickness * 0.12))
    contours = measure.find_contours(ndi.gaussian_filter(padded, sigma), 0.5)
    contours = [p[:, ::-1] - 2 + 0.5 for p in contours if len(p) >= 5]
    if not contours:
        return None
    contour = max(contours, key=len)
    y, x = np.nonzero(mask)
    bounds = np.array([x.min(), y.min(), x.max() + 1, y.max() + 1], float)
    w, h = bounds[2:] - bounds[:2]
    occupancy = len(x) / (w * h)
    if len(contours) == 2 and min(w, h) > 12:
        try:
            rings = [measure.EllipseModel.from_estimate(p) for p in contours]
        except (ValueError, TypeError, np.linalg.LinAlgError):
            rings = [None]
        if all(ring is not None for ring in rings) and len(rings) == 2:
            first, second = [np.array(ring.params) for ring in rings]
            errors = [np.sqrt(np.mean(ring.residuals(p) ** 2)) for ring, p in zip(rings, contours)]
            if (max(errors) < .5 and np.linalg.norm(first[:2] - second[:2]) < .8
                    and abs(first[2] / first[3] - second[2] / second[3]) < .06):
                center = (first + second) / 2
                return {"type": "ellipse", "cx": (center[0] + origin[0]) * factor,
                        "cy": (center[1] + origin[1]) * factor, "rx": center[2] * factor, "ry": center[3] * factor,
                        "angle": float(np.degrees(center[4])), "as_stroke": True,
                        "stroke-width": float(np.mean(np.abs(first[2:4] - second[2:4])) * factor)}
    # Exact panel edges are preferable to dense curved contours.
    if len(contours) == 1 and min(w, h) >= 5 and occupancy > 0.985:
        return {"type": "rect", "x": (bounds[0] + origin[0]) * factor,
                "y": (bounds[1] + origin[1]) * factor, "width": w * factor, "height": h * factor}
    if len(contours) == 1 and len(x) >= 12 and min(w, h) >= 3:
        try:
            ellipse = measure.EllipseModel.from_estimate(contour)
        except (ValueError, TypeError, np.linalg.LinAlgError):
            ellipse = None
        if ellipse is not None:
            cx, cy, a, b, angle = ellipse.params
            residual = ellipse.residuals(contour)
            if min(a, b) > 1 and np.sqrt(np.mean(residual ** 2)) < 0.32 and max(a, b) / min(a, b) < 12:
                spec = {"type": "ellipse", "cx": (cx + origin[0]) * factor, "cy": (cy + origin[1]) * factor,
                        "rx": a * factor, "ry": b * factor, "angle": float(np.degrees(angle))}
                if abs(a - b) / max(a, b) < 0.035:
                    spec = {"type": "circle", "cx": spec["cx"], "cy": spec["cy"], "r": (a + b) * factor / 2}
                return spec
    paths = []
    for contour in contours:
        area = abs(np.sum(contour[:-1, 0] * contour[1:, 1] - contour[1:, 0] * contour[:-1, 1])) / 2
        if area >= 0.6:
            contour = ndi.gaussian_filter1d(contour, 2.0, axis=0, mode="wrap")
            paths.append(cubic_path((contour + origin) * factor, True, tolerance=0.80 * factor))
    return {"type": "path", "d": " ".join(paths)} if paths else None


def decompose_shaded(rgb, source_size, keep=None):
    """Build named, edge-bounded SVG shapes from working RGB; source_size defines full-resolution geometry.

    keep optionally marks working pixels where faint lines must survive.
    """
    from decompose import hex_color

    labels, strength = segment_regions(rgb, keep)
    labels = split_structured(labels, rgb, strength)
    labels = join_line_fragments(labels, rgb, max(rgb.shape) / 1600)
    factor = source_size[0] / rgb.shape[1]
    shapes, gradients, errors = [], {}, []
    objects = ndi.find_objects(labels)
    sizes = np.bincount(labels.ravel())
    order = sorted(range(1, len(objects) + 1), key=lambda i: -int(sizes[i]))
    # Region labels occupy disjoint pixels. A small paint-colored overlap seals
    # antialias seams; smaller, sharper details are drawn last. Regions are fitted
    # smallest first, so each fill knows which smaller neighbours became strokes and
    # tucks fully under them: a stroke never leaves its region's corners unpainted.
    rank = np.zeros(len(sizes), int)
    rank[order] = np.arange(len(order))
    unit = max(rgb.shape) / 1600
    stroked = np.zeros(len(sizes), bool)
    fitted = {}
    for index in order[::-1]:
        slices = objects[index - 1]
        if slices is None or sizes[index] < 3:
            continue
        ys, xs = slices
        pad = 2 + round(5 * unit)
        ys = slice(max(0, ys.start - pad), min(rgb.shape[0], ys.stop + pad))
        xs = slice(max(0, xs.start - pad), min(rgb.shape[1], xs.stop + pad))
        local_labels = labels[ys, xs]
        mask = local_labels == index
        distance = ndi.distance_transform_edt(mask)
        sample = mask & (distance > 1.3)
        if sample.sum() < max(8, mask.sum() * 0.1):
            sample = mask
        y, x = np.nonzero(sample)
        step = max(1, len(x) // 1200)
        x, y = x[::step], y[::step]
        values = rgb[ys, xs][y, x]
        if np.mean(np.abs(values - 255)) < 0.8:
            continue
        xy = (np.c_[x + xs.start + 0.5, y + ys.start + 0.5]) * factor
        bounds = np.array([xs.start, ys.start, xs.stop, ys.stop]) * factor
        paint = fit_paint(xy, values, bounds)
        later = rank[local_labels] > rank[index]
        expanded = mask | (ndi.binary_dilation(mask, iterations=2) & later)
        under = later & stroked[local_labels]
        if under.any():
            expanded |= ndi.binary_dilation(mask, iterations=round(5 * unit)) & under
        geometry = region_geometry(expanded, np.array([xs.start, ys.start]), factor, mask, unit)
        if geometry is None:
            continue
        stroked[index] = bool(geometry.get("as_stroke"))
        fitted[index] = geometry, paint
    for index in order:
        if index not in fitted:
            continue
        geometry, paint = fitted[index]
        name = f"region_{index:04d}"
        geometry.update(name=name, group=f"structure_{index:04d}", fill=paint["fill"])
        if geometry.pop("as_stroke", False):
            geometry["stroke"] = paint["fill"]
            geometry["fill"] = "none"
        elif "gradient" in paint:
            gradients[name] = paint["gradient"]
        shapes.append(geometry)
        errors.append({"name": name, "pixels": int(sizes[index]), "rmse": math.sqrt(paint["error"])})
    return {"size": tuple(source_size), "layers": [], "strokes": [], "primitives": [], "shapes": shapes,
            "gradients": gradients, "annotations": {"removed": np.zeros(rgb.shape[:2], bool)},
            "metadata": {"mode": "shaded", "working_size": [rgb.shape[1], rgb.shape[0]],
                         "coordinate_scale": factor, "regions": errors, "annotation_pixels": 0,
                         "fill_components": {s["name"]: 1 for s in shapes}}}
