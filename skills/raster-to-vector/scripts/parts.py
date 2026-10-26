"""Turn a part spec (parts.json) into named masks, paints, tones and primitives for a redraw.

The spec names the parts a designer would draw. Every figure pixel is assigned to the deepest
visible part by a marker watershed on colour edges, so parts are split by adjacency rather than
by hard coordinate cuts. A part's drawn shape is its own pixels plus those of its children,
tucked under the parts drawn above it, so no seam can open between stacked shapes.
"""

import math

import numpy as np
from scipy import ndimage as ndi
from skimage import color, draw, filters, measure, morphology, segmentation

from decompose import box_mask, hex_color
from flat_regions import leaders_from_mask
from shaded_regions import fit_paint

# (contour sigma in source px, simplify tolerance in source px) per smoothing class.
SMOOTH = {"organ": (0.8, 1.25), "layer": (0.8, 1.0), "detail": (0.8, 0.75), "fine": (0.6, 0.4),
          "sharp": (0.5, 0.5)}


def parse_hex(value):
    """Return the RGB float array for an SVG hex colour '#rrggbb'."""
    return np.array([int(value[i:i + 2], 16) for i in (1, 3, 5)], float)


def lab_of(rgb):
    """Return CIELAB for a float RGB array in 0–255."""
    return color.rgb2lab(np.clip(rgb, 0, 255) / 255)


def delta_e(lab, reference):
    """Return the CIE76 colour difference between every pixel of lab and one Lab reference."""
    return np.linalg.norm(lab - reference, axis=-1)


def edge_strength(lab):
    """Return the per-pixel colour edge strength (Sobel on Lab, in ΔE units per pixel)."""
    smooth = np.stack([ndi.gaussian_filter(lab[..., c], 0.5) for c in range(3)], -1)
    return np.sqrt(sum(filters.sobel(smooth[..., c]) ** 2 for c in range(3))) * 4


def drop_mask(rgb, spec):
    """Return the pixels to leave out of every part (labels, text), from spec['drop'].

    drop.grey_text finds grey or black text and leaders (saturation < 20, mean < 185, grown by 1 px);
    drop.boxes drops whole [x0, y0, x1, y1] boxes. Dropped pixels are later given to the nearest
    part, so text inside a part vanishes into it and text on the page becomes page.
    """
    drop = spec.get("drop", {})
    mask = np.zeros(rgb.shape[:2], bool)
    if drop.get("grey_text"):
        mask = ndi.binary_dilation((np.ptp(rgb, axis=2) < 20) & (rgb.mean(axis=2) < 185))
    if drop.get("boxes"):
        mask |= box_mask(drop["boxes"], rgb.shape[:2], 1)
    return mask


def seed_marker(lab, seed, tolerance, blocked):
    """Return the magic-wand region around seed (x, y): connected pixels within tolerance ΔE of its colour.

    Connectivity is taken on the region eroded by 1 px, so the marker cannot travel through a
    1–2 px bridge into a neighbouring part of similar colour, and it stays off antialiased rims;
    the watershed places the actual boundary.
    """
    x, y = int(seed[0]), int(seed[1])
    reference = np.median(lab[max(0, y - 1):y + 2, max(0, x - 1):x + 2].reshape(-1, 3), axis=0)
    candidate = (delta_e(lab, reference) < tolerance) & ~blocked
    core = ndi.binary_erosion(candidate)
    labels, _ = ndi.label(core)
    if labels[y, x] == 0:
        labels, _ = ndi.label(candidate)
        marker = np.zeros(candidate.shape, bool)
        marker[y, x] = True
        return labels == labels[y, x] if labels[y, x] else marker
    return labels == labels[y, x]


def part_tree(spec):
    """Return parts in drawing order (parents before children, list order otherwise) and a children map."""
    parts = spec["parts"]
    names = [p["name"] for p in parts]
    if len(set(names)) != len(names) or "background" in names:
        raise ValueError("part names must be unique and must not be 'background'")
    children = {name: [p["name"] for p in parts if p.get("parent") == name] for name in names}
    order = []

    def visit(name):
        order.append(name)
        for child in children[name]:
            visit(child)

    for part in parts:
        if part.get("parent") is None:
            visit(part["name"])
        elif part["parent"] not in children:
            raise ValueError(f"part {part['name']}: unknown parent {part['parent']}")
    return order, children


def background_pockets(lab, seeds, tolerance, unknown, markers):
    """Return background-coloured areas that no seed reached, to be marked as background.

    Candidates are unmarked connected patches of 20+ px within tolerance of a background seed
    colour. One is kept when its border is at least 35% unknown pixels (a pocket cut off by a
    leader or a backdrop ring) or when it covers 1% of the image (a backdrop area split off by
    the figure). Without this, the watershed would flood it from the nearest part.
    """
    references = [np.median(lab[max(0, y - 1):y + 2, max(0, x - 1):x + 2].reshape(-1, 3), axis=0)
                  for x, y in ((int(a), int(b)) for a, b in seeds)]
    near = np.min([delta_e(lab, ref) for ref in references], axis=0) < tolerance
    patches, count = ndi.label(near & ~unknown & (markers == 0))
    pockets = np.zeros(near.shape, bool)
    for index, region in enumerate(ndi.find_objects(patches), 1):
        if region is None:
            continue
        grown = tuple(slice(max(0, s.start - 1), s.stop + 1) for s in region)
        patch = patches[grown] == index
        if patch.sum() < 20:
            continue
        border = ndi.binary_dilation(patch) & ~patch
        if unknown[grown][border].mean() >= 0.35 or patch.sum() >= 0.01 * near.size:
            pockets[grown] |= patch
    return pockets


def label_figure(rgb, lab, spec, unknown):
    """Assign every pixel to background (0) or to one part (1..n, spec order) by marker watershed.

    unknown pixels (dropped text, primitive bands) take no part in the watershed, so no label can
    run along a thin line; each gets the label of its nearest labelled pixel afterwards.
    Returns (labels, markers, strength).
    """
    strength = edge_strength(lab)
    markers = np.zeros(rgb.shape[:2], int)
    conflict = np.zeros(rgb.shape[:2], bool)
    colour_markers = []
    background = spec.get("background", {})
    h, w = rgb.shape[:2]
    entries = [(0, background.get("seeds", [[1, 1], [w - 2, 1], [1, h - 2], [w - 2, h - 2]]),
                background.get("tolerance", 6), None)]
    entries += [(index, part.get("seeds", []), part.get("tolerance", 8), part.get("box"))
                for index, part in enumerate(spec["parts"], 1)]
    for index, part in enumerate(spec["parts"], 1):
        if part.get("colors"):
            # Colour-selected parts (ink lines, scattered white details) take every unclaimed pixel of
            # their colours, without erosion, so lines 1–2 px wide keep their markers.
            references = [lab_of(parse_hex(value)[None, None])[0, 0] for value in part["colors"]]
            chosen = np.min([delta_e(lab, ref) for ref in references], axis=0) < part.get("tolerance", 8)
            chosen &= ~unknown
            if part.get("box"):
                chosen &= box_mask([part["box"]], chosen.shape, 1)
            colour_markers.append((index, chosen, part.get("tolerance", 8)))
    for index, seeds, tolerance, box in entries:
        for seed in seeds:
            marker = seed_marker(lab, seed, tolerance, unknown)
            if box is not None:
                marker &= box_mask([box], marker.shape, 1)
            # Markers of different parts that touch the same pixels cancel there: the watershed decides.
            claimed = marker & (markers > 0) & (markers != index + 1)
            conflict |= claimed
            markers[marker & (markers == 0)] = index + 1
    markers[conflict] = 0
    for index, chosen, tolerance in colour_markers:
        # A colour patch touching a seeded region of a similar colour (the page around white details)
        # is a continuation of that region, not part of this one.
        colour = np.median(lab[chosen], axis=0) if chosen.any() else None
        similar = np.zeros(markers.shape, bool)
        for other in np.unique(markers[markers > 0]):
            if other != index + 1 and colour is not None:
                if np.linalg.norm(np.median(lab[markers == other], axis=0) - colour) < 2 * tolerance:
                    similar |= markers == other
        patches, count = ndi.label(chosen & (markers == 0))
        touching = np.unique(patches[ndi.binary_dilation(similar) & (patches > 0)])
        markers[(patches > 0) & ~np.isin(patches, touching)] = index + 1
    markers[background_pockets(lab, entries[0][1], entries[0][2], unknown, markers)] = 1
    labels = segmentation.watershed(strength, markers, mask=~unknown) - 1
    adopted = adopt_orphans(lab, strength, labels, markers, unknown)
    if adopted:
        labels = segmentation.watershed(strength, markers, mask=~unknown) - 1
    if unknown.any():
        nearest = ndi.distance_transform_edt(unknown, return_distances=False, return_indices=True)
        labels = labels[tuple(nearest)]
    return labels, markers, strength, adopted


def adopt_orphans(lab, strength, labels, markers, unknown):
    """Give unseeded flat patches to the part whose colour they have, when the watershed gave them away.

    A part seen in pieces (a vessel passing behind another) has fragments without seeds; the
    watershed floods them from whatever touches them. A flat patch (20+ px) without markers whose
    colour is over 15 ΔE from its assigned part's marker colour but within 8 ΔE of another part's
    marker colour becomes a marker of that part (markers is updated in place).
    Returns [(label, px, box)] of adopted patches.
    """
    present = [v for v in np.unique(markers) if v > 0]
    colours = {v: np.median(lab[markers == v], axis=0) for v in present}
    patches, count = ndi.label((strength < 6) & ~unknown & (markers == 0))
    adopted = []
    for index, region in enumerate(ndi.find_objects(patches), 1):
        if region is None:
            continue
        patch = patches[region] == index
        if patch.sum() < 20:
            continue
        colour = np.median(lab[region][patch], axis=0)
        assigned = int(np.bincount(labels[region][patch]).argmax()) + 1
        if assigned not in colours or np.linalg.norm(colour - colours[assigned]) <= 15:
            continue
        best = min(colours, key=lambda v: np.linalg.norm(colour - colours[v]))
        if np.linalg.norm(colour - colours[best]) < 8:
            markers[region][patch] = best
            ys, xs = np.nonzero(patch)
            adopted.append((best - 1, int(patch.sum()), [int(xs.min() + region[1].start), int(ys.min() + region[0].start),
                                                         int(xs.max() + region[1].start + 1), int(ys.max() + region[0].start + 1)]))
    return adopted


def fill_part_holes(mask, labels):
    """Fill holes in mask except those that are mostly background (a real hole in the shape)."""
    holes, count = ndi.label(ndi.binary_fill_holes(mask) & ~mask)
    if count == 0:
        return mask
    background_share = ndi.mean(labels == 0, holes, np.arange(1, count + 1))
    keep = np.r_[False, background_share < 0.5]
    return mask | keep[holes]


def full_masks(spec, labels, order, children):
    """Return each part's drawn shape: own pixels plus all descendants, closed and hole-filled."""
    index = {p["name"]: i for i, p in enumerate(spec["parts"], 1)}
    config = {p["name"]: p for p in spec["parts"]}
    full = {}
    for name in reversed(order):
        mask = labels == index[name]
        for child in children[name]:
            mask = mask | full[child]
        close = config[name].get("close", 1)
        if close:
            mask = mask | ndi.binary_closing(np.pad(mask, close + 1), iterations=close)[close + 1:-close - 1, close + 1:-close - 1]
        if config[name].get("fill_holes", True):
            mask = fill_part_holes(mask, labels)
        minimum = config[name].get("min_px", 6)
        components, count = ndi.label(mask)
        if count > 1:
            sizes = np.bincount(components.ravel())
            mask = np.isin(components, [i for i in range(1, count + 1) if sizes[i] >= minimum])
        full[name] = mask
    return full


def tuck(full, order, children, spec):
    """Extend each part under the parts drawn after it (not its descendants) by its tuck width in px."""
    config = {p["name"]: p for p in spec["parts"]}
    position = {name: i for i, name in enumerate(order)}

    def descendants(name):
        found = set(children[name])
        for child in children[name]:
            found |= descendants(child)
        return found

    tucked = {}
    for name in order:
        width = config[name].get("tuck", spec.get("tuck", 2))
        above = [other for other in order if position[other] > position[name] and other not in descendants(name)]
        if not width or not above:
            tucked[name] = full[name]
            continue
        cover = np.any([full[other] for other in above], axis=0)
        grown = ndi.distance_transform_edt(~full[name]) <= width
        tucked[name] = full[name] | (grown & cover)
    return tucked


def tone_masks(rgb, lab, own, full, setting):
    """Return nested tone layers inside one part as a list of (mask, hex colour).

    setting: an int (number of tone levels, found by multi-Otsu along the main colour axis) or a
    list of hex colours (each tone is the pixels nearest that colour). Lighter or rarer tones are
    drawn on top of the part, like a designer's flat shading.
    """
    region = ndi.binary_erosion(own) & own
    if region.sum() < 30:
        return []
    values = lab[region]
    tones = []
    if isinstance(setting, int):
        centred = values - values.mean(axis=0)
        axis = np.linalg.svd(centred, full_matrices=False)[2][0]
        t_all = (lab - values.mean(axis=0)) @ axis
        t = t_all[region]
        if np.ptp(t) < 4:
            return []
        thresholds = filters.threshold_multiotsu(t, classes=setting + 1)
        # Stack from the edge colour toward the core colour, as a designer shades: the colour found
        # deepest inside goes on top. When depth does not separate them, the minority goes on top.
        depth = ndi.distance_transform_edt(own)[region]
        deep, shallow = t[depth >= 0.6 * depth.max()].mean(), t[depth <= 2].mean()
        if abs(deep - shallow) > 0.25 * np.ptp(t):
            flip = deep < shallow
        else:
            flip = (t > thresholds[-1]).mean() > (t < thresholds[0]).mean()
        if flip:
            t_all, t, thresholds = -t_all, -t, -thresholds[::-1]
        for level, threshold in enumerate(thresholds):
            mask = (t_all > threshold) & ndi.binary_dilation(own) & ndi.binary_erosion(full)
            mask = ndi.binary_fill_holes(ndi.binary_closing(mask))
            band = region & (t_all > threshold)
            if level + 1 < len(thresholds):
                band &= t_all <= thresholds[level + 1]
            if band.sum() < 10 or mask.sum() < 10:
                continue
            tones.append((mask, hex_color(np.median(rgb[band], axis=0))))
    else:
        references = [lab_of(parse_hex(value)[None, None])[0, 0] for value in setting]
        base = np.median(values, axis=0)
        distances = np.stack([delta_e(lab, ref) for ref in [base] + references])
        nearest = np.argmin(distances, axis=0)
        for k, value in enumerate(setting, 1):
            mask = (nearest == k) & (distances[k] < 6) & ndi.binary_dilation(own) & ndi.binary_erosion(full)
            mask = ndi.binary_fill_holes(ndi.binary_closing(mask))
            if mask.sum() >= 10:
                tones.append((mask, value))
    return tones


def line_coverage(lab, own, value):
    """Return per-pixel line coverage (0–1) near a line part: 1 at its pure colour, 0 at the paint beside it."""
    distance = delta_e(lab, lab_of(parse_hex(value)[None, None])[0, 0])
    far = ndi.maximum_filter(distance, 7)
    return np.clip(1 - distance / np.maximum(far, 1e-6), 0, 1) * ndi.binary_dilation(own, iterations=2)


def split_components(mask, minimum):
    """Return the connected components of mask with at least minimum pixels."""
    labels, count = ndi.label(mask)
    sizes = np.bincount(labels.ravel())
    return [labels == i for i in range(1, count + 1) if sizes[i] >= minimum]


def part_paint(rgb, own, exclude, setting, scale, marker):
    """Fit flat or gradient paint to the part's own pixels; return {'fill': hex, 'gradient': spec?}.

    Thin parts without tones (lines), whose interior vanishes when eroded, take the flat median of
    their marker pixels, which are pure samples of their colour rather than antialiased edges.
    """
    if isinstance(setting, str) and setting.startswith("#"):
        return {"fill": setting}
    if isinstance(setting, dict):
        return {"fill": setting["stops"][0][1], "gradient": setting}
    region = ndi.binary_erosion(own) & ~exclude
    if not exclude.any() and region.sum() < 0.25 * own.sum() and marker.any():
        return {"fill": hex_color(np.median(rgb[marker], axis=0))}
    if region.sum() < 12:
        region = own
    y, x = np.nonzero(region)
    stride = max(1, len(x) // 6000)
    xy = np.c_[x[::stride] + 0.5, y[::stride] + 0.5] * scale
    values = rgb[region][::stride]
    if setting == "flat" or len(values) < 12:
        return {"fill": hex_color(np.median(values, axis=0))}
    bounds = (x.min() * scale, y.min() * scale, (x.max() + 1) * scale, (y.max() + 1) * scale)
    paint = fit_paint(xy, values, bounds)
    result = {"fill": hex_color(np.median(values, axis=0))}
    if "gradient" in paint:
        # A stop outside the sampled colours was extrapolated where no pixels are; keep the flat fill.
        stops = np.array([parse_hex(value) for _, value in paint["gradient"]["stops"]])
        low, high = np.percentile(values, 1, axis=0) - 12, np.percentile(values, 99, axis=0) + 12
        if np.all((stops >= low) & (stops <= high)):
            result["gradient"] = paint["gradient"]
    return result


def detect_rim(rgb, lab, full, own, setting):
    """Find a distinct outline along a part's edge; return (rim or None, rim pixels outside the part, all rim pixels).

    setting: None (no rim, the default), a hex colour (the outline colour, probed by the agent),
    {'color', 'width'} (used as given) or 'auto'. With 'auto' the two pixel bands on each side of
    the edge are compared with the part's interior and the colour 3–4 px outside; the band least
    explained as a mix of those two is taken when it is clearly off that mix (6+ ΔE). Rim pixels
    just outside the part are returned so the caller can add them to it: an outline belongs to
    the object it outlines.
    """
    empty = np.zeros(full.shape, bool)
    if isinstance(setting, dict):
        return setting, empty, empty
    if setting in (None, False, "none"):
        return None, empty, empty
    inside_d = ndi.distance_transform_edt(full)
    outside_d = ndi.distance_transform_edt(~full)
    bands = [(inside_d > 1.5) & (inside_d <= 2.5), (inside_d > 0) & (inside_d <= 1.5),
             (outside_d > 0) & (outside_d <= 1.5), (outside_d > 1.5) & (outside_d <= 2.5)]
    interior = own & (inside_d > 3)
    exterior = (outside_d > 2.5) & (outside_d <= 4.5)
    if interior.sum() < 20 or exterior.sum() < 20 or min(b.sum() for b in bands) < 20:
        return None, empty, empty
    if isinstance(setting, str) and setting.startswith("#"):
        rim_c = lab_of(parse_hex(setting)[None, None])[0, 0]
    else:
        interior_c, exterior_c = np.median(lab[interior], axis=0), np.median(lab[exterior], axis=0)
        segment = exterior_c - interior_c
        best = None
        for band in bands:
            c = np.median(lab[band], axis=0)
            t = np.clip(np.dot(c - interior_c, segment) / max(np.dot(segment, segment), 1e-9), 0, 1)
            off = float(np.linalg.norm(c - (interior_c + t * segment)))
            if best is None or off > best[0]:
                best = off, c
        off, rim_c = best
        if off < 6 or np.linalg.norm(rim_c - interior_c) < 6:
            return None, empty, empty
    near_edge = (inside_d > 0) & (inside_d <= 2.5) | (outside_d > 0) & (outside_d <= 2.5)
    rim_pixels = near_edge & (delta_e(lab, rim_c) < 10)
    if rim_pixels.sum() < 10:
        return None, empty, empty
    # Width from the edge stretches that face the page or a clearly different colour, where rim pixels are countable.
    edge = (inside_d > 0) & (inside_d <= 1.5)
    width = float(np.clip(rim_pixels.sum() / max(edge.sum(), 1), 0.75, 2.5))
    rim = {"color": hex_color(np.median(rgb[rim_pixels], axis=0)), "width": width}
    return rim, rim_pixels & (outside_d > 0) & (outside_d <= 2.5), rim_pixels


def fit_circle(rgb, lab, primitive):
    """Fit a circle to pixels of primitive['fit_color'] by RANSAC; return (shape, band of matching pixels).

    stroke and stroke-width may be 'auto' (sampled from the ring); fill 'auto' is resolved later by
    resolve_fills, once the background is known.
    """
    reference = lab_of(parse_hex(primitive["fit_color"])[None, None])[0, 0]
    candidate = delta_e(lab, reference) < primitive.get("tolerance", 12)
    if primitive.get("box"):
        candidate &= box_mask([primitive["box"]], candidate.shape, 1)
    y, x = np.nonzero(candidate)
    if len(x) < 20:
        raise ValueError(f"primitive {primitive.get('name')}: too few pixels of {primitive['fit_color']}")
    xy = np.c_[x + 0.5, y + 0.5]
    rng = np.random.default_rng(0)
    best = None
    for _ in range(2000):
        points = xy[rng.choice(len(xy), 3, replace=False)]
        try:
            cx, cy, c = np.linalg.solve(np.c_[2 * points, np.ones(3)], (points ** 2).sum(axis=1))
        except np.linalg.LinAlgError:
            continue
        radius = math.sqrt(max(0.0, c + cx * cx + cy * cy))
        inliers = np.abs(np.hypot(xy[:, 0] - cx, xy[:, 1] - cy) - radius) < 1.5
        if best is None or inliers.sum() > best.sum():
            best = inliers
    points = xy[best]
    cx, cy, c = np.linalg.lstsq(np.c_[2 * points, np.ones(len(points))], (points ** 2).sum(axis=1), rcond=None)[0]
    radius = math.sqrt(max(0.0, c + cx * cx + cy * cy))
    yy, xx = np.indices(candidate.shape)
    rr = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
    band = candidate & (np.abs(rr - radius) < 3)
    shape = {"type": "circle", "name": primitive.get("name", "circle"), "cx": cx, "cy": cy, "r": radius,
             "z": primitive.get("z", "bottom"), "fill": primitive.get("fill", "auto")}
    stroke = primitive.get("stroke", "auto")
    if stroke == "auto":
        stroke = hex_color(np.median(rgb[candidate & (np.abs(rr - radius) < 1.5)], axis=0))
    width = primitive.get("stroke-width", "auto")
    if width == "auto":
        # Coverage counts antialiased pixels fractionally; only the visible arc is measured.
        near = np.abs(rr - radius) < 3
        backdrop = np.median(lab[(rr > radius - 7) & (rr < radius - 4)], axis=0)
        reach = max(float(np.linalg.norm(backdrop - reference)), 1.0)
        coverage = np.clip(1 - delta_e(lab, reference) / reach, 0, 1) * near
        angles = np.degrees(np.arctan2(yy + 0.5 - cy, xx + 0.5 - cx)).astype(int) + 180
        visible = np.zeros(361, bool)
        visible[angles[band]] = True
        seen = visible[angles] & near
        width = float(np.clip(coverage[seen].sum() / (2 * math.pi * radius * visible.mean()), 0.75, 6))
    shape.update(stroke=stroke, width=width)
    return shape, band


def resolve_fills(rgb, shapes, labels):
    """Replace fill 'auto' on fitted circles with the median background colour inside them."""
    yy, xx = np.indices(labels.shape)
    for shape in shapes:
        if shape.get("fill") == "auto":
            inside = (np.hypot(xx + 0.5 - shape["cx"], yy + 0.5 - shape["cy"]) < shape["r"] - 3) & (labels == 0)
            shape["fill"] = hex_color(np.median(rgb[inside], axis=0)) if inside.sum() > 20 else "none"
    return shapes


def fit_arrows(rgb, lab, primitive, drop):
    """Measure every straight arrow drawn in primitive['color']; return (arrow shapes, their pixels).

    Each connected blob of that colour (within 'tolerance' ΔE, inside 'box' if given) is measured
    along its main axis: a line coverage profile gives the width at each step. A blob is an arrow
    when it is straight, at least 3 shaft widths long, and its widest point (the head base) is at
    least 1.6x the shaft width and lies in one half. The drawn arrow must then overlap the blob
    (IoU >= min_iou, default 0.6), or the blob is left to the parts. The arrow is tail, tip, shaft width, head length and head width; anything else
    (curved leaflets, the page) is left to the parts.
    """
    reference = lab_of(parse_hex(primitive["color"])[None, None])[0, 0]
    candidate = (delta_e(lab, reference) < primitive.get("tolerance", 12)) & ~drop
    if primitive.get("box"):
        candidate &= box_mask([primitive["box"]], candidate.shape, 1)
    blobs, count = ndi.label(candidate)
    shapes, pixels = [], np.zeros(candidate.shape, bool)
    for index, region in enumerate(ndi.find_objects(blobs), 1):
        if region is None:
            continue
        grown = tuple(slice(max(0, s.start - 3), s.stop + 3) for s in region)
        blob = blobs[grown] == index
        if not 12 <= blob.sum() <= 0.02 * candidate.size:
            continue
        coverage = line_coverage(lab[grown], blob, primitive["color"])
        ys, xs = np.nonzero(coverage > 0.05)
        weights = coverage[ys, xs]
        points = np.c_[xs + 0.5 + grown[1].start, ys + 0.5 + grown[0].start]
        centre = np.average(points, axis=0, weights=weights)
        axis = np.linalg.svd((points - centre) * np.sqrt(weights)[:, None], full_matrices=False)[2][0]
        for _ in range(2):
            # Profile along the axis; if the wide end (the head) comes first, turn the axis round once.
            across = np.array([-axis[1], axis[0]])
            along, side = (points - centre) @ axis, (points - centre) @ across
            steps = np.floor(along - along.min()).astype(int)
            width = np.bincount(steps, weights=weights)
            offset = np.bincount(steps, weights=weights * side) / np.maximum(width, 1e-9)
            # The head's widest point (its base) lies in the head half, even though the tip tapers.
            if np.argmax(ndi.uniform_filter1d(width, 3)) >= len(width) / 2:
                break
            axis = -axis
        if len(width) < 6:
            continue
        shaft = float(np.median(width[:len(width) // 2]))
        head = float(width.max())
        straight = np.abs(offset[:len(width) // 2] - np.median(offset[:len(width) // 2])).max() <= max(1.0, shaft / 2)
        if shaft < 0.5 or len(width) < 3 * shaft or head < 1.6 * shaft or not straight:
            continue
        head_steps = np.nonzero(width > (shaft + head) / 2)[0]
        head_length = float(len(width) - head_steps.min()) if len(head_steps) else head
        middle = float(np.median(offset[:len(width) // 2]))
        tail = centre + axis * along.min() + across * middle
        tip = centre + axis * along.max() + across * middle
        name = primitive.get("name", "arrow")
        shape = {"type": "arrow", "name": f"{name}_{len(shapes):02d}", "x1": float(tail[0]), "y1": float(tail[1]),
                 "x2": float(tip[0]), "y2": float(tip[1]), "width": round(shaft, 2), "head_width": round(head, 2),
                 "head_length": round(min(head_length, 0.6 * len(width)), 2),
                 "fill": hex_color(np.median(rgb[grown][blob], axis=0)), "z": primitive.get("z", "top")}
        # Verify before replacing: the drawn arrow must cover the blob it replaces (IoU >= min_iou).
        drawn = arrow_mask(shape, candidate.shape)[grown]
        source = coverage > 0.5
        iou = (drawn & source).sum() / max((drawn | source).sum(), 1)
        if iou < primitive.get("min_iou", 0.6):
            continue
        shape["iou"] = round(float(iou), 2)
        shapes.append(shape)
        pixels[grown] |= ndi.binary_dilation(blob, iterations=1)
    return shapes, pixels


def arrow_corners(shape, scale=1.0):
    """Return the 7 corners (tail side, head base, tip) of an arrow shape, in source px times scale."""
    tail, tip = np.array([shape["x1"], shape["y1"]]) * scale, np.array([shape["x2"], shape["y2"]]) * scale
    axis = (tip - tail) / max(np.linalg.norm(tip - tail), 1e-9)
    across = np.array([-axis[1], axis[0]])
    half = shape["width"] * scale / 2
    head_half = shape.get("head_width", shape["width"] * 2.5) * scale / 2
    base = tip - axis * shape.get("head_length", shape["width"] * 2.5) * scale
    return [tail + across * half, base + across * half, base + across * head_half, tip,
            base - across * head_half, base - across * half, tail - across * half]


def arrow_mask(shape, size):
    """Rasterize an arrow shape into a boolean mask of size (h, w), sampled at pixel centres."""
    corners = np.array(arrow_corners(shape)) - 0.5
    rows, cols = draw.polygon(corners[:, 1], corners[:, 0], size)
    mask = np.zeros(size, bool)
    mask[rows, cols] = True
    return mask


def primitives(rgb, lab, spec, drop):
    """Return (shapes, band) for spec['primitives'] in source px; each shape has z 'bottom' or 'top'.

    band holds the pixels the fitted primitives cover, which the watershed treats as unknown.
    """
    shapes = []
    band = np.zeros(rgb.shape[:2], bool)
    for primitive in spec.get("primitives", []):
        kind = primitive["type"]
        if kind == "leaders":
            for shape in leaders_from_mask(rgb, drop):
                shapes.append(dict(shape, z="top"))
        elif kind == "circle" and "fit_color" in primitive:
            shape, pixels = fit_circle(rgb, lab, primitive)
            shapes.append(shape)
            band |= pixels
        elif kind == "arrows":
            arrows, pixels = fit_arrows(rgb, lab, primitive, drop)
            shapes += arrows
            band |= pixels
        else:
            shape = {k: v for k, v in primitive.items()}
            shape.setdefault("name", f"{kind}_{len(shapes):02d}")
            shape.setdefault("z", "top")
            shape.setdefault("fill", "#000000" if kind == "arrow" else "none")
            if "stroke-width" in shape and kind != "rect":  # a rect's width is its size
                shape["width"] = shape.pop("stroke-width")
            shapes.append(shape)
    return shapes, band


def build_parts(rgb, spec, scale):
    """Run the whole spec on rgb; return a dict with labels, ordered layers and primitives.

    Each layer is {'name', 'mask', 'paint', 'rim', 'smooth', 'group'} in drawing order (source px masks).
    """
    lab = lab_of(rgb)
    drop = drop_mask(rgb, spec)
    shapes, band = primitives(rgb, lab, spec, drop)
    labels, markers, strength, adopted = label_figure(rgb, lab, spec, drop | band)
    resolve_fills(rgb, shapes, labels)
    order, children = part_tree(spec)
    config = {p["name"]: p for p in spec["parts"]}
    index = {p["name"]: i for i, p in enumerate(spec["parts"], 1)}
    full = full_masks(spec, labels, order, children)
    rims, rim_pixels = {}, {}
    for name in order:
        rims[name], outside, rim_pixels[name] = detect_rim(rgb, lab, full[name], labels == index[name],
                                                           config[name].get("stroke"))
        full[name] |= outside
    drawn = tuck(full, order, children, spec)

    def top_level(name):
        while config[name].get("parent"):
            name = config[name]["parent"]
        return name

    layers, tone_counts = [], {}
    for name in order:
        part = config[name]
        own = labels == index[name]
        smooth = part.get("smooth", "layer")
        # The outline is drawn by the stroke, so its pixels take no part in the tones or the base colour.
        inner = own & ~drop & ~rim_pixels[name]
        tones = tone_masks(rgb, lab, inner, full[name], part["tones"]) if part.get("tones") else []
        tone_counts[name] = (bool(part.get("tones")), len(tones))
        tone_pixels = np.any([m for m, _ in tones], axis=0) if tones else np.zeros(own.shape, bool)
        # With tones the shading is carried by nested flat layers, so the base stays flat.
        paint = part_paint(rgb, inner & ~band, tone_pixels, part.get("paint", "flat" if tones else "auto"), scale,
                           markers == index[name] + 1)
        rim = rims[name]
        layers.append({"name": name, "mask": drawn[name], "full": full[name], "own": own, "paint": paint,
                       "rim": rim, "smooth": smooth, "group": top_level(name), "draw": part.get("draw", "fill"),
                       "coverage": line_coverage(lab, own, paint["fill"]) if part.get("draw") == "strokes" else None})
        tone_smooth = part.get("tone_smooth", "fine" if smooth == "fine" else "detail")
        for level, (mask, value) in enumerate(tones, 1):
            for k, piece in enumerate(split_components(mask, part.get("tone_min_px", 10))):
                layers.append({"name": f"{name}_tone{level}_{k}", "mask": piece, "full": piece, "own": piece,
                               "paint": {"fill": value}, "rim": None, "smooth": tone_smooth,
                               "group": top_level(name)})
    return {"labels": labels, "markers": markers, "drop": drop | band, "layers": layers, "order": order,
            "primitives": shapes, "strength": strength, "adopted": adopted, "tone_counts": tone_counts}
