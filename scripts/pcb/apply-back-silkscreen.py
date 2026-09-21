#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["shapely==2.1.2", "svgpathtools==1.7.1"]
# ///
"""Apply the supplied vector art to Board B without rewriting electrical geometry.

Run with uv. KiCad's Python is used only for pad geometry and polygon fracture.
All SVG dimensions are uniformly scaled; holes use the SVG nonzero fill rule.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
from sexp import atom, find_all, load, parse, tokenize

KPY = '/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3'
ART = ROOT / 'boards/board-b/artwork'
GROUP = 'Board B back artwork'
NAMESPACE = uuid.UUID('2c5f7b75-42b9-40f7-8f84-1ab378622cab')
OLD_TITLE = 'zudo-pd B / rev1'
WIDTH = 110


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def serialize(node):
    if isinstance(node, list):
        return '(' + ' '.join(serialize(v) for v in node) + ')'
    return json.dumps(node[1], ensure_ascii=False) if node[0] == 'str' else node[1]


def native(mode, source, destination):
    """Native operations never save the source board."""
    import wx
    app = wx.App(False)
    import pcbnew as p
    if mode == 'obstacles':
        board = p.LoadBoard(str(source))
        rows = []
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if not pad.IsOnLayer(p.B_Mask):
                    continue
                bb = pad.GetBoundingBox()
                margin = max(0, p.ToMM(pad.GetSolderMaskExpansion(p.B_Mask)))
                rows.append({'ref': fp.GetReference(), 'pin': pad.GetNumber(),
                             'bounds': [p.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())],
                             'mask_expansion_mm': margin})
        Path(destination).write_text(json.dumps(rows))
    elif mode == 'fracture':
        result = []
        for rings in json.loads(Path(source).read_text()):
            shape = p.SHAPE_POLY_SET()
            shape.NewOutline()
            for x, y in rings[0]:
                shape.Append(p.FromMM(x), p.FromMM(y))
            for ring in rings[1:]:
                hole = shape.NewHole()
                for x, y in ring:
                    shape.Append(p.FromMM(x), p.FromMM(y), -1, hole)
            shape.Fracture(False)
            for i in range(shape.OutlineCount()):
                outline = shape.COutline(i)
                result.append([[p.ToMM(outline.CPoint(j).x), p.ToMM(outline.CPoint(j).y)]
                               for j in range(outline.PointCount())])
        Path(destination).write_text(json.dumps(result))


def flatten(segment, tolerance, a=0., b=1., depth=0):
    start, end = segment.point(a), segment.point(b)
    samples = [(fraction, segment.point(a+(b-a)*fraction)) for fraction in (.25, .5, .75)]
    error = max(abs(point - (start + (end-start)*fraction)) for fraction, point in samples)
    if error <= tolerance or depth >= 18:
        return [start, end]
    middle = (a+b)/2
    return flatten(segment, tolerance, a, middle, depth+1)[:-1] + flatten(segment, tolerance, middle, b, depth+1)


def svg_geometry(path, tolerance=.015):
    from shapely.geometry import LineString, Polygon, box
    from shapely.ops import polygonize, unary_union
    from shapely import make_valid, STRtree
    from svgpathtools import parse_path
    tree = ET.parse(path)
    shapes = []
    for item in tree.getroot().iter():
        if item.tag.split('}')[-1] != 'path':
            continue
        if item.get('transform') or item.get('fill-rule', 'nonzero') != 'nonzero':
            raise ValueError('Unreviewed SVG transform or fill rule')
        rings, signs, lines = [], [], []
        for sub in parse_path(item.attrib['d']).continuous_subpaths():
            points = []
            for segment in sub:
                points += flatten(segment, tolerance)[:-1]
            points += [sub[-1].end]
            coords = [(v.real, v.imag) for v in points]
            if coords[-1] != coords[0]:
                coords.append(coords[0])
            if len(set(coords)) < 3:
                continue
            signed = sum(x1*y2-x2*y1 for (x1,y1),(x2,y2) in zip(coords, coords[1:]))
            rings.append(make_valid(Polygon(coords)))
            signs.append(1 if signed > 0 else -1)
            lines.append(LineString(coords))
        index = STRtree(rings)
        faces = []
        for face in polygonize(unary_union(lines)):
            point = face.representative_point()
            winding = sum(signs[i] for i in index.query(point) if rings[i].covers(point))
            if winding:
                faces.append(face)
        shapes.append(unary_union(faces))
    x,y,w,h = map(float, tree.getroot().attrib['viewBox'].split())
    return unary_union(shapes).intersection(box(x,y,x+w,y+h))


def children(geom):
    if geom.geom_type == 'Polygon':
        return [geom]
    return [p for part in geom.geoms for p in children(part)] if hasattr(geom, 'geoms') else []


def top_spans(text):
    """Top-level source spans, preserving every byte outside edited artwork."""
    depth, quoted, escaped, start = 0, False, False, None
    for i, char in enumerate(text):
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == '(':
            depth += 1
            if depth == 2:
                start = i
        elif char == ')':
            if depth == 2:
                yield start, i+1
            depth -= 1


def art_ids(tree):
    ids = set()
    for group in find_all(tree, 'group'):
        if atom(group[1]) == GROUP:
            ids.update(atom(v) for v in find_all(group, 'members')[0][1:])
    return ids


def is_art(node, ids):
    name = atom(node[0])
    if name == 'group' and atom(node[1]) == GROUP:
        return True
    key = find_all(node, 'uuid')
    generated = bool(key and atom(key[0][1]) in ids)
    title = name == 'gr_text' and atom(node[1]) == OLD_TITLE
    if generated or title:
        if name not in ('gr_poly', 'gr_text') or atom(find_all(node, 'layer')[0][1]) != 'B.SilkS':
            raise ValueError('Artwork edit tried to remove a non-back-silkscreen item')
        return True
    return False


def immutable(tree, ids=None):
    ids = art_ids(tree) if ids is None else ids
    return [n for n in tree if not isinstance(n, list) or not is_art(n, ids)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pcb', type=Path, default=ROOT/'boards/board-b/board-b.kicad_pcb')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--kicad-python', default=KPY)
    parser.add_argument('--branding-only', action='store_true',
                        help='Preserve existing native pattern polygons, including manual edits')
    args = parser.parse_args()
    from shapely.geometry import box
    from shapely.ops import unary_union
    from shapely.affinity import affine_transform

    original = args.pcb.read_text()
    source_sha256 = digest(args.pcb)
    source = load(args.pcb)
    pattern = svg_geometry(ART/'pattern.svg')
    logo = svg_geometry(ART/'logo.svg', .004)
    # Coordinates below describe the normal back view. Native PCB X is mirrored.
    pattern_scale = 91.0 / 372.72
    pattern = affine_transform(pattern, [-pattern_scale, 0, 0, pattern_scale, 109.2, -4.5])
    pattern_area = box(18.2, .8, 109.2, 84.2)
    pattern = pattern.intersection(pattern_area)
    # In the user's portrait back view, horizontal U=PCB Y and vertical V=PCB X.
    # Rotate the pre-mirrored source so the emblem is left of readable branding.
    def place_logo(part, width, u_left, v_top):
        x0,y0,x1,y1 = part.bounds
        ratio = width/(x1-x0)
        return affine_transform(part, [0,ratio,-ratio,0,v_top-y0*ratio,u_left+x1*ratio])
    emblem = place_logo(logo.intersection(box(32,-1,52,20)), 11.5, 6.0, 6.0)
    brand = place_logo(logo.intersection(box(-1,-1,31,20)), 17.5, 19.0, 7.0)

    old_ids = art_ids(source)
    preserved_ids = set()
    if args.branding_only:
        for node in find_all(source, 'gr_poly'):
            key = atom(find_all(node, 'uuid')[0][1])
            if key not in old_ids:
                continue
            xs = [float(atom(point[1])) for point in find_all(find_all(node, 'pts')[0], 'xy')]
            if min(xs) >= 18.199:
                preserved_ids.add(key)
            elif max(xs) >= 18.199:
                raise ValueError('Artwork crosses branding/pattern boundary; review manual edits')
        if not preserved_ids:
            raise ValueError('--branding-only needs the existing native pattern')
    mutable_old_ids = old_ids - preserved_ids

    with tempfile.TemporaryDirectory(prefix='zudo-back-silk-') as temporary:
        temporary = Path(temporary)
        obstacles_path = temporary/'obstacles.json'
        subprocess.run([args.kicad_python, __file__, '--native', 'obstacles', str(args.pcb), str(obstacles_path)], check=True)
        obstacles = json.loads(obstacles_path.read_text())
        masks = []
        by_ref = {}
        for row in obstacles:
            pad = box(*row['bounds']).buffer(row['mask_expansion_mm']+.3, join_style=2)
            masks.append(pad)
            by_ref.setdefault(row['ref'], []).append(pad)
        # Clear whole solder rows so hand soldering and inspection stay legible.
        for ref in ('J5','J10','J11'):
            masks.append(box(*unary_union(by_ref[ref]).bounds).buffer(.3, join_style=2))
        keepouts = unary_union(masks)
        all_art = unary_union(([pattern] if not args.branding_only else []) + [emblem, brand]).difference(keepouts)
        # Drop sub-printable detached flecks created by boundary clipping.
        pieces = [p for p in children(all_art) if p.area >= .008 and max(p.bounds[2]-p.bounds[0], p.bounds[3]-p.bounds[1]) >= .12]
        all_art = unary_union(pieces)
        if all_art.intersection(keepouts).area > 1e-8:
            raise ValueError('Artwork intrudes on solder-mask clearances')
        polygons_path = temporary/'polygons.json'
        fractured_path = temporary/'fractured.json'
        polygons_path.write_text(json.dumps([[list(p.exterior.coords)[:-1], *[list(h.coords)[:-1] for h in p.interiors]] for p in pieces]))
        subprocess.run([args.kicad_python, __file__, '--native', 'fracture', str(polygons_path), str(fractured_path)], check=True)
        polygons = json.loads(fractured_path.read_text())

    ids, drawings = [], []
    def item_id(name):
        key = str(uuid.uuid5(NAMESPACE, name))
        ids.append(key)
        return key
    for i, points in enumerate(polygons):
        pts = ' '.join(f'(xy {x:.6f} {y:.6f})' for x,y in points)
        prefix = 'branding-polygon-' if args.branding_only else 'polygon-'
        drawings.append(f'(gr_poly (pts {pts}) (stroke (width 0) (type solid)) (fill solid) (layer "B.SilkS") (uuid "{item_id(prefix+str(i))}"))')
    title_lines = [('zudo-pd v1',68.8),('+12V : 1.2A',71.6),('-12V : 0.8A',74.4),('+5V : 0.5A',77.2)]
    for text,y in title_lines:
        drawings.append(f'(gr_text "{text}" (at 9.4 {y}) (layer "B.SilkS") (uuid "{item_id(text)}") (effects (font (size 1.4 1.4) (thickness 0.22)) (justify mirror)))')
    drawings.append(f'(group "{GROUP}" (uuid "{uuid.uuid5(NAMESPACE, GROUP)}") (members '+ ' '.join(f'"{v}"' for v in sorted(preserved_ids)+ids)+'))')
    removals = []
    for start,end in top_spans(original):
        node = parse(tokenize(original[start:end]))
        if is_art(node, mutable_old_ids):
            line_start = original.rfind('\n', 0, start)+1
            if not original[line_start:start].strip():
                start = line_start
            if original[end:end+1] == '\n':
                end += 1
            removals.append((start,end))
    result = original
    for start,end in reversed(removals):
        result = result[:start]+result[end:]
    end = result.rfind(')')
    result = result[:end]+'\n\t'+'\n\t'.join(drawings)+'\n'+result[end:]
    final = parse(tokenize(result))
    if immutable(source, mutable_old_ids) != immutable(final, set(ids)):
        raise ValueError('Non-artwork PCB data changed')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(result)
    report = {'status':'PASS','layer':'B.SilkS','source_pcb_sha256':source_sha256,
              'result_pcb_sha256':digest(args.output),
              'non_artwork_structure_sha256':hashlib.sha256(serialize(immutable(source, mutable_old_ids)).encode()).hexdigest(),
              'preserved':'Every original node except the replaced branding/title/group, including existing pattern polygons when branding-only, all copper, zones/fill, footprints, pads, models, holes, rail labels and front silk.',
              'branding_only':args.branding_only, 'preserved_pattern_uuids':sorted(preserved_ids),
              'sources':{str(p.relative_to(ROOT)):digest(p) for p in [ART/'logo.svg', ART/'pattern.svg', Path(__file__)]},
              'pattern_bounds_pcb_mm':list(pattern_area.bounds),'pattern_uniform_scale':pattern_scale,
              'mask_gap_mm':.3,'row_extra_gap_mm':.3,'edge_gap_mm':.8,
              'polygon_count':len(polygons),'filled_area_mm2':all_art.area,
              'board_title':{'lines':[text for text,y in title_lines],'centers_mm':[[9.4,y] for text,y in title_lines],'mirrored':True},
              'branding':{'portrait_back_view':'U=PCB Y, V=PCB X; emblem left, two-line brand name right',
                          'emblem_uv_mm':[6,6], 'emblem_width_mm':11.5, 'brand_uv_mm':[19,7], 'brand_width_mm':17.5},
              'limits':['Fine logo feather/fish details are retained vector artwork, not guaranteed printed detail.','Native DRC and final Gerber/render inspection are separate checks.']}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--native':
        native(*sys.argv[2:])
    else:
        main()
