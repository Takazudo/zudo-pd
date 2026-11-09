"""Fail closed if PD20 export refill changes approved manufacturing geometry.

Only UUIDs, generator labels, object serialization order, exact numeric spelling,
closed-ring start/direction and resolved model-path spelling are normalized.
There is no copper tolerance, area-only comparison or discarded unknown field.
"""
import argparse
import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'schgen'))
from sexp import atom, parse, tokenize


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def scalar(token):
    kind, value = token
    if kind == 'atom':
        try:
            number = Decimal(value)
            if number.is_finite():
                return ('number', number)
        except InvalidOperation:
            pass
    return kind, value


def ring(points):
    vertices = []
    for point in points[1:]:
        if not isinstance(point, list) or atom(point[0]) != 'xy' or len(point) != 3:
            raise ValueError('Unsupported filled/outline polygon vertex')
        xy = tuple(Decimal(atom(v)) for v in point[1:])
        if not all(v.is_finite() for v in xy):
            raise ValueError('Nonfinite polygon coordinate')
        vertices.append(xy)
    if len(vertices) > 1 and vertices[0] == vertices[-1]:
        vertices.pop()
    if len(vertices) < 3:
        raise ValueError('Incomplete polygon boundary')
    minimum = min(vertices)
    return min(tuple(sequence[i:] + sequence[:i])
               for sequence in (vertices, list(reversed(vertices)))
               for i, point in enumerate(sequence) if point == minimum)


def normalize(node, directory, parent=None):
    if not isinstance(node, list):
        return scalar(node)
    tag = atom(node[0])
    if tag == 'pts' and parent in ('filled_polygon', 'polygon'):
        return ('ring', ring(node))
    values = []
    for index, item in enumerate(node):
        if isinstance(item, list):
            child = atom(item[0])
            if child == 'uuid' or (tag == 'kicad_pcb' and child in ('generator', 'generator_version')):
                continue
        if tag == 'model' and index == 1:
            path = atom(item).replace('${KIPRJMOD}', str(directory))
            if '${' in path:
                raise ValueError(f'Unresolved model path: {path}')
            resolved = Path(path)
            if not resolved.is_absolute():
                resolved = directory / resolved
            values.append(('model_path', str(resolved.resolve())))
        else:
            values.append(normalize(item, directory, tag))
    # These are unordered collections of declared objects/attributes. Do not
    # reorder arbitrary children (notably stackup layers or coordinate lists).
    if tag in ('kicad_pcb', 'footprint', 'zone'):
        scalars, children = [], []
        for value in values:
            if isinstance(value, tuple) and value and value[0] in ('atom', 'str', 'number'):
                scalars.append(value)
            else:
                children.append(value)
        return tuple(scalars + sorted(children, key=repr))
    return tuple(values)


def compare(source, staged, expected_source_sha256=None):
    source, staged = Path(source), Path(staged)
    source_bytes, staged_bytes = source.read_bytes(), staged.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    if expected_source_sha256 is not None and source_hash != expected_source_sha256:
        raise ValueError('Approved source PCB changed after export staging')
    equal = (normalize(parse(tokenize(source_bytes.decode())), source.resolve().parent)
             == normalize(parse(tokenize(staged_bytes.decode())), staged.resolve().parent))
    if source.read_bytes()!=source_bytes or staged.read_bytes()!=staged_bytes:
        raise ValueError('PCB changed during staged geometry verification')
    result = {'source_sha256': source_hash, 'staged_sha256': hashlib.sha256(staged_bytes).hexdigest(),
              'manufacturing_geometry_equal': equal,
              'scope': 'Exact source-versus-staged geometry including filled copper boundaries; no physical tolerance.',
              'normalization': ['UUIDs', 'root generator labels', 'declared object order',
                                'exact numeric spelling', 'closed polygon start/direction', 'resolved model paths'],
              'helper_sha256': digest(__file__)}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('staged', type=Path)
    parser.add_argument('--expected-source-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = compare(args.source, args.staged, args.expected_source_sha256)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    if not result['manufacturing_geometry_equal']:
        raise SystemExit('PD20 staged refill changed approved manufacturing geometry; export blocked. Quantify and review separately.')
    print('PASS: exact approved source/staged manufacturing geometry, including filled copper')


if __name__ == '__main__':
    main()
