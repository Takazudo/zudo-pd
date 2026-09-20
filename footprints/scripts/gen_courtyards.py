#!/usr/bin/env python3
"""Generate IPC-style F.CrtYd outlines for the project's KiCad footprints.

Most of this library came from easyeda2kicad, which either omits the courtyard
entirely or draws it around the component *body only* -- so it does not enclose
the part's own pads, and KiCad's courtyard DRC either cannot run at all or runs
against a keepout smaller than the copper it is meant to protect. This tool
replaces whatever is on F.CrtYd with a rectangle enclosing every pad and every
body graphic, plus an IPC clearance.

The courtyard is deliberately a plain rectangle rather than a chamfered outline:
it is a DRC keepout, not artwork, and a rectangle cannot accidentally cut inside
the pads the way a body-shaped outline does. Silkscreen and fab artwork -- the
chamfer that marks electrolytic polarity included -- are left untouched.

Checks compare closed rectangle geometry and stroke width, not serialization.
An explicitly reviewed nominal project rectangle may differ from the generic
silkscreen-derived result. It must still enclose pads and nominal Fab
geometry with the normal clearance, and every silkscreen graphic itself. A
changed physical envelope invalidates that review rather than silently growing
or accepting its courtyard. These artwork-based checks do not establish maximum
manufacturer tolerances or physical assembly clearance.

Parsing goes through scripts/schgen/sexp.py rather than regexes so both the
legacy easyeda2kicad `(module ...)` layout and the modern multi-line KiCad
`(footprint ...)` layout are handled identically.

Usage:
    python3 footprints/scripts/gen_courtyards.py --check    # report drift, write nothing
    python3 footprints/scripts/gen_courtyards.py            # rewrite in place

Both the master `footprints/kicad/*.kicad_mod` and the KiCad resolution copies in
`footprints/kicad/zudo-power.pretty/` are kept in sync, per the dual-location rule
in footprints/CLAUDE.md.
"""

from __future__ import annotations

import argparse
import math
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "schgen"))

from sexp import atom, parse, tokenize  # noqa: E402

# IPC-7351 density-B ("nominal") courtyard excess, and the KiCad official-library
# default for non-fine-pitch parts.
CLEARANCE_MM = 0.25
LINE_WIDTH_MM = 0.05

MASTER_DIR = ROOT / "footprints" / "kicad"
PRETTY_DIR = MASTER_DIR / "zudo-power.pretty"

BODY_LAYERS = {"F.Fab", "B.Fab", "F.SilkS", "B.SilkS"}
GRAPHIC_NODES = {"fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly"}

# Exact reviewed NOMINAL project geometry, not permission for arbitrary boxes
# and NOT a manufacturer maximum-tolerance envelope. C8465's nominal body and
# interlock are represented by its Fab artwork. These frozen project bounds
# enclose that artwork and all pads with >=0.25mm clearance, and enclose silk.
# The generic silk-based result differs by0.02mm on three edges and0.10mm at
# the interlock edge. The real body's tolerance relative to the pin row is
# not resolved by these nominal graphics; maximum-envelope/physical-fit review
# remains open. Never describe this exception as covering those tolerances.
# Evidence: component-kangnex-wj500v-5-08-2p-c8465/facts.json,
# fact-c8465-dimensions and references/project-contract.json.
REVIEWED_RECTANGLES = {
    "WJ500V-5.08-2P_C8465": (-6.03, -5.85, 5.43, 4.85),
}
GEOMETRY_TOLERANCE_MM = 1e-6


def node_name(node):
    return atom(node[0]) if isinstance(node, list) and node else None


def child(node, name):
    for item in node[1:] if isinstance(node, list) else []:
        if isinstance(item, list) and node_name(item) == name:
            return item
    return None


def numbers(node):
    out = []
    for item in node[1:]:
        if not isinstance(item, list):
            try:
                out.append(float(atom(item)))
            except (TypeError, ValueError):
                pass
    return out


def layers_of(node):
    found = set()
    for name in ("layer", "layers"):
        holder = child(node, name)
        if holder:
            found |= {atom(x) for x in holder[1:] if not isinstance(x, list)}
    return found


def pad_box(pad):
    at, size = child(pad, "at"), child(pad, "size")
    if not at or not size:
        return None
    coords, dims = numbers(at), numbers(size)
    if len(coords) < 2 or len(dims) < 2:
        return None
    x, y = coords[0], coords[1]
    rot = coords[2] if len(coords) > 2 else 0.0
    w, h = dims[0], dims[1]
    # Only right angles occur in this library; anything else is bounded by its
    # circumscribed box so the courtyard can never come out too small.
    if abs(math.sin(math.radians(rot))) > 0.999:
        w, h = h, w
    elif abs(math.cos(math.radians(rot))) < 0.999:
        w = h = math.hypot(w, h)
    return (x - w / 2, y - h / 2, x + w / 2, y + h / 2)


def graphic_box(node, body_layers=BODY_LAYERS):
    """Bounding box of one body graphic, or None if it is not body artwork."""
    if not layers_of(node) & body_layers:
        return None
    name = node_name(node)
    points = []
    if name == "fp_circle":
        centre, edge = child(node, "center"), child(node, "end")
        if centre and edge:
            (cx, cy), (ex, ey) = numbers(centre)[:2], numbers(edge)[:2]
            r = math.dist((cx, cy), (ex, ey))
            points = [(cx - r, cy - r), (cx + r, cy + r)]
    elif name == "fp_poly":
        pts = child(node, "pts")
        for xy in (pts[1:] if pts else []):
            if isinstance(xy, list) and node_name(xy) == "xy":
                coords = numbers(xy)
                if len(coords) >= 2:
                    points.append((coords[0], coords[1]))
    else:
        for key in ("start", "mid", "end", "center"):
            part = child(node, key)
            if part:
                coords = numbers(part)
                if len(coords) >= 2:
                    points.append((coords[0], coords[1]))
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def walk(node):
    if isinstance(node, list):
        yield node
        for item in node:
            yield from walk(item)


def envelope(tree, body_layers=BODY_LAYERS, clearance=CLEARANCE_MM, rounded=True):
    boxes, pads = [], 0
    for node in walk(tree):
        name = node_name(node)
        if name == "pad":
            pads += 1
            box = pad_box(node)
            if box is None:
                raise ValueError("a pad has no parseable at/size")
            boxes.append(box)
        elif name in GRAPHIC_NODES:
            box = graphic_box(node, body_layers)
            if box:
                boxes.append(box)
    if not pads:
        raise ValueError("no pads found")
    box = (
        min(b[0] for b in boxes) - clearance,
        min(b[1] for b in boxes) - clearance,
        max(b[2] for b in boxes) + clearance,
        max(b[3] for b in boxes) + clearance,
    )
    return tuple(round(v, 2) for v in box) if rounded else box


def contains_box(outer, inner):
    eps = GEOMETRY_TOLERANCE_MM
    return (outer[0] <= inner[0] + eps and outer[1] <= inner[1] + eps
            and outer[2] >= inner[2] - eps and outer[3] >= inner[3] - eps)


def compute_courtyard(text):
    tree = parse(tokenize(text))
    name = atom(tree[1]).split(":")[-1]
    if name not in REVIEWED_RECTANGLES:
        return envelope(tree)
    reviewed = REVIEWED_RECTANGLES[name]
    if not contains_box(reviewed, envelope(tree, {"F.Fab", "B.Fab"}, rounded=False)):
        raise ValueError("reviewed courtyard no longer encloses pads/Fab plus clearance")
    if not contains_box(reviewed, envelope(tree, clearance=0, rounded=False)):
        raise ValueError("reviewed courtyard no longer encloses body/silkscreen artwork")
    return reviewed


def courtyard_box(text):
    """Read one closed rectangle, rejecting gaps, duplicates and wrong strokes."""
    graphics = [node for node in walk(parse(tokenize(text)))
                if node_name(node) in GRAPHIC_NODES and "F.CrtYd" in layers_of(node)]
    for node in graphics:
        width = child(node, "width")
        stroke = child(node, "stroke")
        if stroke:
            width = child(stroke, "width")
            style = child(stroke, "type")
            if style and atom(style[1]) not in {"solid", "default"}:
                raise ValueError("courtyard stroke must be solid")
        if not width or len(numbers(width)) != 1 or not math.isclose(
                numbers(width)[0], LINE_WIDTH_MM, abs_tol=GEOMETRY_TOLERANCE_MM):
            raise ValueError("courtyard stroke width differs")
        fill = child(node, "fill")
        if fill and atom(fill[1]) != "none":
            raise ValueError("courtyard must be an unfilled outline")

    def point(node, key):
        value = child(node, key)
        result = numbers(value) if value else []
        if len(result) != 2 or not all(math.isfinite(v) for v in result):
            raise ValueError("invalid courtyard endpoint")
        return tuple(result)

    if len(graphics) == 1 and node_name(graphics[0]) == "fp_rect":
        a, b = point(graphics[0], "start"), point(graphics[0], "end")
        box = min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])
    elif len(graphics) == 4 and all(node_name(n) == "fp_line" for n in graphics):
        edges = [tuple(sorted((point(n, "start"), point(n, "end")))) for n in graphics]
        points = [p for edge in edges for p in edge]
        box = (min(p[0] for p in points), min(p[1] for p in points),
               max(p[0] for p in points), max(p[1] for p in points))
        x0, y0, x1, y1 = box
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        expected = {tuple(sorted((a, b))) for a, b in zip(corners, corners[1:])}
        if len(set(edges)) != 4 or set(edges) != expected:
            raise ValueError("courtyard lines do not form one closed rectangle")
    else:
        raise ValueError("courtyard must be one rectangle or four closed rectangle edges")
    if box[0] >= box[2] or box[1] >= box[3]:
        raise ValueError("courtyard rectangle has no area")
    return box


def courtyard_matches(text, expected):
    try:
        actual = courtyard_box(text)
    except (ValueError, IndexError):
        return False
    return all(math.isclose(a, b, abs_tol=GEOMETRY_TOLERANCE_MM) for a, b in zip(actual, expected))


def render(box, indent, quoted):
    x0, y0, x1, y1 = box
    layer = '"F.CrtYd"' if quoted else "F.CrtYd"
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    return "".join(
        f"{indent}(fp_line (start {a[0]:.2f} {a[1]:.2f}) (end {b[0]:.2f} {b[1]:.2f})"
        f" (layer {layer}) (width {LINE_WIDTH_MM}))\n"
        for a, b in zip(corners, corners[1:])
    )


def strip_courtyard(text):
    """Remove existing F.CrtYd graphics in either single-line or multi-line form."""
    out, i, n = [], 0, len(text)
    while i < n:
        match = re.compile(r"[ \t]*\((fp_line|fp_rect|fp_poly|fp_circle|fp_arc)\s").match(text, i)
        if not match:
            out.append(text[i])
            i += 1
            continue
        depth, j = 0, text.index("(", i)
        while j < n:
            if text[j] == "(":
                depth += 1
            elif text[j] == ")":
                depth -= 1
                if depth == 0:
                    j += 1
                    break
            j += 1
        block = text[i:j]
        trailing = j
        while trailing < n and text[trailing] in " \t":
            trailing += 1
        if trailing < n and text[trailing] == "\n":
            trailing += 1
        if re.search(r'\(layer\s+"?F\.CrtYd"?\s*\)', block):
            i = trailing
            continue
        out.append(text[i:trailing])
        i = trailing
    return "".join(out)


def rewrite(text):
    box = compute_courtyard(text)
    if courtyard_matches(text, box):
        return text
    stripped = strip_courtyard(text)
    quoted = '(layer "' in stripped
    body = re.search(r"^([ \t]+)\(pad", stripped, re.M)
    indent = body.group(1) if body else "\t"
    anchor = stripped.rfind(f"{indent}(model ")
    if anchor == -1:
        tail = stripped.rstrip()
        anchor = tail.rfind("\n)")
        anchor = anchor + 1 if anchor != -1 else len(stripped)
    return stripped[:anchor] + render(box, indent, quoted) + stripped[anchor:]


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="report drift without writing")
    args = parser.parse_args(argv)

    drift, skipped, mirror_drift = [], [], []
    for path in sorted(MASTER_DIR.glob("*.kicad_mod")):
        original = path.read_text(encoding="utf-8")
        try:
            updated = rewrite(original)
            box = compute_courtyard(original)
        except (ValueError, IndexError) as exc:
            skipped.append(f"{path.name}: {exc}")
            continue
        changed = updated != original
        if changed:
            drift.append(path.name)
            if not args.check:
                path.write_text(updated, encoding="utf-8", newline="")
        mirror = PRETTY_DIR / path.name
        expected_copy = original if args.check else updated
        if not mirror.exists() or mirror.read_bytes() != expected_copy.encode("utf-8"):
            mirror_drift.append(path.name)
            if args.check:
                print(f"SYNC  {path.name}: missing or byte-different library copy")
            else:
                mirror.parent.mkdir(parents=True, exist_ok=True)
                mirror.write_text(updated, encoding="utf-8", newline="")
        print(f"{'DRIFT' if changed else '  ok '} {path.name:48s} {box[2] - box[0]:6.2f} x {box[3] - box[1]:6.2f} mm")

    for note in skipped:
        print(f"SKIP  {note}")
    if skipped:
        print(f"\n{len(skipped)} footprint(s) could not be parsed — fix before relying on courtyard DRC")
        return 1
    if args.check and (drift or mirror_drift):
        print(f"\n{len(drift)} footprint(s) need a courtyard refresh; "
              f"{len(mirror_drift)} library copies need synchronization; run without --check")
        return 1
    print(f"\n{len(drift)} footprint(s) {'would be ' if args.check else ''}updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
