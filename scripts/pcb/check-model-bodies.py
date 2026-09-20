#!/usr/bin/env python3
"""Sanity-screen fitted WRL bodies against their local PCB pad regions.

Unlike the separate path checker, this evaluates opaque mesh geometry after the
model-node transform. It is not manufacturer dimensional certification, a native
render pixel test, a collision proof, or a substitute for physical inspection.
"""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts/schgen'))
from sexp import atom, find_all, load

NUMBER = r'[-+]?(?:\d*\.\d+|\d+)(?:[Ee][+-]?\d+)?'


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bounds(points):
    require(points, 'No mesh vertices')
    return [[min(v[i] for v in points) for i in range(3)],
            [max(v[i] for v in points) for i in range(3)]]


def shapes(text):
    require(not re.search(r'\bTransform\s*\{', text), 'Nested WRL transforms need separate review')
    result = []
    for block in re.split(r'\bShape\s*\{', text)[1:]:
        coords = re.search(r'\bpoint\s*\[([^]]+)\]', block)
        indices = re.search(r'\bcoordIndex\s*\[([^]]+)\]', block)
        if not coords or not indices:
            continue
        numbers = [float(v)*2.54 for v in re.findall(NUMBER, coords[1])]
        require(len(numbers) % 3 == 0, 'Malformed WRL coordinates')
        points = [numbers[i:i+3] for i in range(0, len(numbers), 3)]
        face_indices = [int(v) for v in re.findall(r'-?\d+', indices[1])]
        require(any(v >= 0 for v in face_indices), 'No WRL faces')
        require(all(v == -1 or 0 <= v < len(points) for v in face_indices), 'WRL face index out of range')
        # Signed triangle volume distinguishes a real bulk body from a single
        # mesh containing two separated metal ends with an oversized bbox.
        volume, polygon = 0.0, []
        for index in face_indices:
            if index == -1:
                for i in range(1, len(polygon)-1):
                    a, b, c = [points[j] for j in (polygon[0], polygon[i], polygon[i+1])]
                    volume += (a[0]*(b[1]*c[2]-b[2]*c[1]) +
                               a[1]*(b[2]*c[0]-b[0]*c[2]) +
                               a[2]*(b[0]*c[1]-b[1]*c[0]))/6
                polygon = []
            else:
                polygon.append(index)
        used = sorted({v for v in face_indices if v >= 0})
        points = [points[v] for v in used]
        alpha = re.search(r'\btransparency\s+('+NUMBER+r')', block)
        transparency = float(alpha[1]) if alpha else 0.0
        require(math.isfinite(transparency) and 0 <= transparency <= 1, 'Invalid WRL transparency')
        result.append({'points': points, 'transparency': transparency, 'mesh_volume_mm3': abs(volume)})
    require(result, 'No supported WRL mesh shapes')
    return result


def vector(model, name, default):
    found = find_all(model, name)
    if not found:
        return list(default)
    coords = find_all(found[0], 'xyz')
    require(len(coords) == 1, 'Malformed model '+name)
    result = [float(atom(v)) for v in coords[0][1:]]
    require(len(result) == 3 and all(math.isfinite(v) for v in result), 'Invalid model '+name)
    return result


def transformed(points, model):
    scale = vector(model, 'scale', [1, 1, 1])
    require(all(v > 0 for v in scale), 'Model scale must be positive')
    rx, ry, rz = [math.radians(v) for v in vector(model, 'rotate', [0, 0, 0])]
    offset = vector(model, 'offset', [0, 0, 0])
    result = []
    for raw in points:
        x, y, z = [a*b for a, b in zip(raw, scale)]
        y, z = y*math.cos(rx)-z*math.sin(rx), y*math.sin(rx)+z*math.cos(rx)
        x, z = x*math.cos(ry)+z*math.sin(ry), -x*math.sin(ry)+z*math.cos(ry)
        x, y = x*math.cos(rz)-y*math.sin(rz), x*math.sin(rz)+y*math.cos(rz)
        result.append([a+b for a, b in zip((x, y, z), offset)])
    return result


def pad_region(fp):
    # Local CAD coordinates: KiCad footprint Y points down, model Y points up.
    # Pad bounding boxes are conservative envelopes, not exact copper polygons.
    points = []
    for pad in find_all(fp, 'pad'):
        if atom(pad[2]) == 'np_thru_hole':
            continue
        at = find_all(pad, 'at')[0]
        x, y = [float(atom(v)) for v in at[1:3]]
        sx, sy = [float(atom(v)) for v in find_all(pad, 'size')[0][1:3]]
        # Serialized pad angle includes the footprint's board rotation; subtract
        # it before constructing the local bounding box.
        board_angle = find_all(fp, 'at')
        board_angle = float(atom(board_angle[0][3])) if board_angle and len(board_angle[0]) > 3 else 0
        angle = math.radians((float(atom(at[3])) if len(at) > 3 else 0)-board_angle)
        hx = (abs(sx*math.cos(angle))+abs(sy*math.sin(angle)))/2
        hy = (abs(sx*math.sin(angle))+abs(sy*math.cos(angle)))/2
        points.extend([[x-hx, -y-hy, 0], [x+hx, -y+hy, 0]])
    require(points, 'Fitted footprint has no copper-pad region')
    return bounds(points)


def screen_model(model, text, pads):
    require(not any((isinstance(n, list) and atom(n[0]) == 'hide' and (len(n) == 1 or atom(n[1]) in ('yes', 'true', '1')))
                    or (not isinstance(n, list) and atom(n) == 'hide') for n in model[2:]), 'Model is hidden')
    meshes = shapes(text)
    opaque = [mesh for mesh in meshes if mesh['transparency'] < .99]
    require(opaque, 'Model has no opaque body geometry')
    transformed_shapes = [transformed(mesh['points'], model) for mesh in meshes]
    volumes = []
    for points in transformed_shapes:
        bb = bounds(points)
        volumes.append(math.prod(max(0., bb[1][i]-bb[0][i]) for i in range(3)))
    largest = max(range(len(meshes)), key=lambda i: meshes[i]['mesh_volume_mm3'])
    require(volumes[largest] > 1e-6, 'Model has no volumetric body envelope')
    require(meshes[largest]['transparency'] < .99, 'Largest body envelope is transparent; visible metal alone is insufficient')
    body_bounds = bounds(transformed_shapes[largest])
    require(body_bounds[1][2] > .05, 'Model body is below the mounting plane')
    visible = [pt for mesh, points in zip(meshes, transformed_shapes) if mesh['transparency'] < .99 for pt in points]
    bb = bounds(visible)
    overlap = [min(bb[1][i], pads[1][i])-max(bb[0][i], pads[0][i]) for i in (0, 1)]
    require(all(v > .001 for v in overlap), 'Model body/terminal geometry is displaced from the pad region')
    return {'status': 'PASS', 'opaque_vertices': len(visible), 'mesh_shapes': len(meshes),
            'opaque_bounds_local_CAD_mm': bb, 'largest_body_bounds_local_CAD_mm': body_bounds,
            'pad_region_overlap_xy_mm': overlap, 'offset_mm': vector(model, 'offset', [0, 0, 0])}


def check(pcb, project_dir=None):
    project = (project_dir or pcb.parent).resolve()
    variables = {**os.environ, 'KIPRJMOD': str(project)}
    result = {'status': 'PASS', 'scope': 'Opaque-body placement sanity screen only; not exact manufacturer geometry, collision/occlusion certification, native pixel coverage or physical fit.',
              'pcb_sha256': digest(pcb), 'checker_sha256': digest(__file__), 'fitted_components': 0,
              'screened_components': 0, 'footprints': [], 'errors': []}
    for fp in find_all(load(pcb), 'footprint'):
        props = {atom(n[1]): atom(n[2]) for n in find_all(fp, 'property')}
        attrs = {atom(v) for n in find_all(fp, 'attr') for v in n[1:]}
        if 'dnp' in attrs or {'exclude_from_bom', 'exclude_from_pos_files'} <= attrs:
            continue
        ref = props.get('Reference', '(missing)')
        result['fitted_components'] += 1
        item = {'reference': ref, 'models': []}
        try:
            pads = pad_region(fp)
            models = find_all(fp, 'model')
            require(models, 'No model attached')
            for model in models:
                raw = atom(model[1])
                expanded = re.sub(r'\$\{([^}]+)\}', lambda m: variables.get(m[1], m[0]), raw)
                path = Path(expanded)
                if not path.is_absolute():
                    path = project/path
                path = path.resolve()
                require(path.is_file(), 'Missing model '+raw)
                require(path.suffix.lower() == '.wrl', 'Non-WRL body needs separate review: '+raw)
                screen = screen_model(model, path.read_text(), pads)
                item['models'].append({'file': path.name, 'sha256': digest(path), **screen})
            result['screened_components'] += 1
        except (ValueError, IndexError, OSError) as error:
            item['error'] = str(error)
            result['errors'].append(ref+': '+str(error))
        result['footprints'].append(item)
    if result['errors']:
        result['status'] = 'FAIL'
    return result


def self_test(pcb, project_dir=None):
    result = check(pcb, project_dir)
    require(result['status'] == 'PASS', 'Baseline body screen fails: '+str(result['errors']))
    # Use canonical exact F1210 geometry, independent of board placement changes.
    fp = load(ROOT/'footprints/kicad/zudo-power.pretty/F1210.kicad_mod')
    model = find_all(fp, 'model')[0]
    text = (ROOT/'footprints/kicad/zudo-pd.3dshapes/F1210_L3.2-W2.6-H0.6.wrl').read_text()
    pads = pad_region(fp)
    screen_model(model, text, pads)
    rejected = []

    def reject(name, changed, changed_text, expected):
        try:
            screen_model(changed, changed_text, pads)
        except ValueError as error:
            require(expected in str(error), name+': wrong failure '+str(error))
            rejected.append(name)
        else:
            raise ValueError('Negative control accepted: '+name)

    def offset(values):
        changed = copy.deepcopy(model)
        find_all(find_all(changed, 'offset')[0], 'xyz')[0][1:] = [('atom', str(v)) for v in values]
        return changed

    reject('original stale PTC1 XY offset', offset([-4.39, 14.35, 0]), text, 'displaced')
    reject('original stale PTC2 XY offset', offset([-12.94, 11.05, 0]), text, 'displaced')
    reject('body below PCB', offset([0, 0, -10]), text, 'below')
    transparent = re.sub(r'transparency\s+'+NUMBER, 'transparency 1.0', text)
    reject('all transparent geometry', model, transparent, 'no opaque')
    pieces = re.split(r'(?=\bShape\s*\{)', text)
    # Exact downloaded F1210 bulk substrate is its third Shape. Its metal
    # end meshes remain visible in this deliberate body-opacity regression.
    pieces[3] = re.sub(r'transparency\s+'+NUMBER, 'transparency 1.0', pieces[3], count=1)
    body_transparent = ''.join(pieces)
    reject('transparent body with visible metal', model, body_transparent, 'Largest body')
    require(digest(pcb) == result['pcb_sha256'], 'PCB changed during body self-test')
    return {'status': 'PASS', 'pcb_sha256': result['pcb_sha256'], 'positive_board_components': result['screened_components'],
            'negative_controls': rejected, 'source_files_not_written': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pcb', type=Path)
    parser.add_argument('--project-dir', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    result = self_test(args.pcb.resolve(), args.project_dir) if args.self_test else check(args.pcb.resolve(), args.project_dir)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'footprints'}, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
