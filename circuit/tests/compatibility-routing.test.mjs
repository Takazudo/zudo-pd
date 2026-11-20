import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {join} from 'node:path';
import {root, packageRoot} from './compatibility-helpers.mjs';

test('installed and project bundle resolvers agree on exact PESD order codes', () => {
  const program = String.raw`
import importlib.util, json, sys
from pathlib import Path
root, package = map(Path, sys.argv[1:])
sys.path.insert(0, str(package / 'python'))
from circuit_evidence.routing import resolve_bundle_route as installed, resolve, RoutingPolicy
spec = importlib.util.spec_from_file_location('project_validate', root / '.claude/skills/component-spec-audit/scripts/validate.py')
local = importlib.util.module_from_spec(spec); spec.loader.exec_module(local)
routes = json.loads((root / '.claude/skills/component-pesd24vs1ub-c85382/routing.json').read_text())['routes']
policy = RoutingPolicy(board_names=frozenset({'board-p'}))
positive = [
    'PESD24VS1UB', 'PESD24VS1UB,115', 'PESD24VS1UB, 115',
    'nexperia pesd24vs1ub,115 C85382', 'board-p Nexperia PESD24VS1UB,115',
    'PESD24VS1UB, please check pinout', 'C85382',
    'PESD24VS1UB, 115 from Nexperia', 'PESD24VS1UB, 115 by Nexperia',
]
negative = [
    'PESD24VS1UB,125', 'PESD24VS1UB,125 C85382',
    'PESD24VS1UB,115 and PESD24VS1UB,125', 'PESD24VS1UB,1150',
    '  nexperia  pesd24vs1ub, 125  C85382  ',
    'PESD24VS1UB, 115 from OtherVendor', 'PESD24VS1UB, 115 by OtherVendor',
    'PESD24VS1UB,115 from OtherVendor', 'PESD24VS1UB,115 by OtherVendor',
]
for query, expected in [(q, ['rec-pesd24vs1ub-c85382']) for q in positive] + [(q, []) for q in negative]:
    assert installed(query, routes, policy) == expected, ('installed', query)
    assert local.resolve_bundle_route(query, routes) == expected, ('project', query)
shared = [
    {'record_id': name, 'aliases': {'mpn': ['SHARED'], 'manufacturer': [maker], 'lcsc': [lcsc], 'function': ['test part']}}
    for name, maker, lcsc in [('a', 'Acme', 'C100'), ('b', 'Bravo', 'C200')]
]
for query, expected in [('SHARED', []), ('Acme SHARED', ['a']), ('Bravo SHARED', ['b']),
                        ('board-p Acme SHARED', ['a']), ('Bravo SHARED C100', [])]:
    assert installed(query, shared, policy) == expected, ('shared MPN', query)
empty_lcsc = [{'record_id': 'e', 'aliases': {'mpn': ['EMPTY'], 'manufacturer': ['Acme'], 'lcsc': [], 'function': ['test part']}}]
assert installed('EMPTY', empty_lcsc) == ['e']
assert resolve('PESD24VS1UB', [{'line_id': 'line-pesd', 'mpn': 'PESD24VS1UB', 'lcsc': 'C85382',
                                'manufacturer': 'Nexperia', 'function': 'ESD protection'}]) == ['line-pesd']
`;
  const run = spawnSync('python3', ['-c', program, root, packageRoot], {encoding: 'utf8', timeout: 30000});
  assert.equal(run.status, 0, run.stderr || run.stdout);
});

test('installed package CLI validates the exact routed evidence bundle', () => {
  const run = spawnSync(process.execPath, [join(packageRoot, 'bin/zudo-circuit-doc.js'), 'validate', '--config', join(root, 'circuit.config.ts')],
    {cwd: root, encoding: 'utf8', timeout: 90000});
  assert.equal(run.status, 0, run.stderr || run.stdout);
});
