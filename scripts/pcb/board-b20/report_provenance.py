"""Bind B20 desk calculations to native copper inputs; not electrical acceptance."""
import hashlib
import json
from pathlib import Path

OWNER = 'scripts/pcb/board-b20'
RECEIPT = 'boards/board-b20-draft/report-input-receipt.json'
BOARD = 'boards/board-b20-draft/board-b20-draft.kicad_pcb'
REPORT_NAMES = ('routing-report', 'current-check', 'loop-check', 'thermal-check')
DEPENDENCIES = (f'{OWNER}/load_cases.py', f'{OWNER}/report_provenance.py',
                'scripts/schgen/board_b20_spec.py', 'scripts/schgen/sexp.py')
OWNER_PATHS = (*DEPENDENCIES, *(f'{OWNER}/{name}.py' for name in
                ('read-routed-copper', 'dump-geom', 'current-check', 'loop-check', 'thermal-check')))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def owner_hashes(root):
    return {name: digest(Path(root)/name) for name in OWNER_PATHS}


def calculation_binding(producer, inputs, root=None, settings=None):
    producer = Path(producer)
    root = Path(root) if root is not None else producer.resolve().parents[3]
    source = f'{OWNER}/{producer.name}'
    return {'schema': 1, 'producer': source, 'producer_sha256': digest(root/source),
            'dependencies_sha256': {name: digest(root/name) for name in DEPENDENCIES},
            'inputs_sha256': inputs, 'settings': settings or {}}


def verify_native_report_inputs(root, reports=None):
    root = Path(root)
    receipt = json.loads((root/RECEIPT).read_text())
    pcb_hash = digest(root/BOARD)
    require(receipt['pcb_sha256'] == pcb_hash, 'B20 native report input PCB is stale')
    require(receipt['kicad_version'] == '10.0.6', 'B20 native input tool version differs from the pin')
    require(receipt['owner_sha256'] == owner_hashes(root), 'B20 native input owner/dependency changed')
    reports = reports if reports is not None else {
        name: json.loads((root/'boards/board-b20-draft'/f'{name}.json').read_text()) for name in REPORT_NAMES}
    for name in ('current-check', 'loop-check'):
        expected = calculation_binding(name+'.py',
            {'geom': receipt['geom_sha256'], 'routes': receipt['routes_sha256']}, root,
            settings={'plane_height_mm': 0.2175} if name == 'loop-check' else {})
        require(reports[name].get('input_binding') == expected,
                f'B20 {name} did not use the current native inputs/producer/dependencies')
    expected = calculation_binding('thermal-check.py', {'pcb': pcb_hash}, root)
    require(reports['thermal-check'].get('input_binding') == expected,
            'B20 thermal report did not use current PCB/producer/dependencies')
    routing = reports['routing-report']
    require(routing['tracks'] == receipt['native_track_count'] and routing['vias'] == receipt['native_via_count'],
            'B20 routing counts do not describe saved native copper')
    require(not routing['unrouted'], 'B20 routing is incomplete')
    return {'path': RECEIPT, 'sha256': digest(root/RECEIPT), 'pcb_sha256': pcb_hash,
            'scope': 'Native input and calculation freshness only; not current, thermal or electrical qualification'}
