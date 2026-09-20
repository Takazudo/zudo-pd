#!/usr/bin/env python3
"""Check repository-local PCB model references and fitted-part model coverage.

This verifies availability and nonzero transforms, not exact manufacturer geometry.
Bare copper/mechanical exclusions and DNP parts need no visible model; every model
reference that is present must still resolve, including on DNP footprints.
"""
import argparse
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


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(pcb, project_directory=None):
    project_directory = (project_directory or pcb.parent).resolve()
    variables = dict(os.environ)
    variables['KIPRJMOD'] = str(project_directory)
    result = {'pcb': pcb.name, 'pcb_sha256': digest(pcb), 'status': 'PASS',
              'fitted_components': 0, 'fitted_components_with_visible_models': 0,
              'model_references': 0, 'footprints': [], 'errors': [],
              'scope': 'Model paths, file availability, visible fitted-part coverage and finite/nonzero transforms only. Models are visualization assets; physical dimensions, polarity, assembly fit and exact-part provenance require separate review.'}
    seen = set()
    for fp in find_all(load(pcb), 'footprint'):
        props = {atom(item[1]): atom(item[2]) for item in find_all(fp, 'property')}
        ref = props.get('Reference', '')
        if not ref or ref in seen:
            result['errors'].append('Missing or duplicate footprint reference: ' + ref)
        seen.add(ref)
        attrs = {atom(value) for attr in find_all(fp, 'attr') for value in attr[1:]}
        dnp = 'dnp' in attrs
        excluded = {'exclude_from_bom', 'exclude_from_pos_files'} <= attrs
        fitted = not dnp and not excluded
        result['fitted_components'] += int(fitted)
        item = {'reference': ref, 'fitted': fitted, 'dnp': dnp, 'assembly_excluded': excluded, 'models': []}
        visible = 0
        for model in find_all(fp, 'model'):
            result['model_references'] += 1
            raw = atom(model[1])
            unresolved = []

            def expand(match):
                name = match.group(1)
                if name not in variables:
                    unresolved.append(name)
                    return match.group(0)
                return variables[name]

            expanded = re.sub(r'\$\{([^}]+)\}', expand, raw)
            path = Path(expanded)
            if not path.is_absolute():
                path = project_directory/path
            path = path.resolve()
            local = path.is_relative_to(ROOT)
            hidden = any(atom(node[1]) in ('yes', 'true', '1') for node in find_all(model, 'hide') if len(node) > 1)
            hidden = hidden or any(not isinstance(node, list) and atom(node) == 'hide' for node in model[2:])
            transforms = {}
            for name, default in [('offset', [0, 0, 0]), ('rotate', [0, 0, 0]), ('scale', [1, 1, 1])]:
                entries = find_all(model, name)
                values = list(default)
                if entries:
                    coords = find_all(entries[0], 'xyz')
                    try:
                        values = [float(atom(value)) for value in coords[0][1:]]
                    except (IndexError, TypeError, ValueError):
                        values = []
                if len(values) != 3 or not all(math.isfinite(value) for value in values):
                    result['errors'].append(f'{ref}: invalid model {name} transform')
                elif name == 'scale' and not all(value > 0 for value in values):
                    result['errors'].append(f'{ref}: model scale must be positive/nonzero')
                transforms[name] = values
            found = not unresolved and local and path.is_file()
            entry = {'reference': raw, 'resolved_file': str(path.relative_to(ROOT)) if local else 'OUTSIDE REPOSITORY',
                     'exists': found, 'hidden': hidden, 'transforms': transforms}
            if unresolved:
                result['errors'].append(f'{ref}: unresolved model variables {unresolved}')
            elif not local:
                result['errors'].append(f'{ref}: model reference escapes this repository: {raw}')
            elif not path.is_file():
                result['errors'].append(f'{ref}: model file missing: {raw}')
            if found:
                entry['sha256'] = digest(path)
                if path.suffix.lower() == '.wrl':
                    companion = path.with_suffix('.step')
                    entry['step_companion_exists'] = companion.is_file()
                    if not companion.is_file():
                        result['errors'].append(f'{ref}: WRL has no matching STEP companion: {path.name}')
                    else:
                        entry['step_companion_sha256'] = digest(companion)
                visible += int(not hidden)
            item['models'].append(entry)
        if fitted:
            if not visible:
                result['errors'].append(f'{ref}: fitted component has no available visible model')
            else:
                result['fitted_components_with_visible_models'] += 1
        result['footprints'].append(item)
    if result['errors']:
        result['status'] = 'FAIL'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pcb', type=Path)
    parser.add_argument('--project-directory', type=Path, help='Override KIPRJMOD when inspecting a copied board')
    parser.add_argument('--output', type=Path, help='Write a detailed JSON report')
    args = parser.parse_args()
    result = check(args.pcb.resolve(), args.project_directory)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'footprints'}, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
