"""Read revision-bound native evidence without treating routing as a DRC result."""
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_native_receipt(directory, pcb, schematic, project):
    directory = Path(directory)
    path = directory / 'native-drc-receipt.json'
    if not path.exists():
        return {'status': 'NOT RUN', 'reason': 'No native DRC receipt for this source.'}
    receipt = json.loads(path.read_text())
    for name, source in [('pcb', pcb), ('schematic', schematic), ('project', project)]:
        if receipt.get(name+'_sha256') != sha(source):
            return {'status': 'NOT RUN', 'reason': f'Existing native receipt is stale for {name}.'}
    report_path = directory / receipt['report_file']
    if receipt['report_sha256'] != sha(report_path):
        raise ValueError('Native report hash does not match its receipt')
    report = json.loads(report_path.read_text())
    command = receipt['command']
    if report['kicad_version'] != '10.0.6' or '--schematic-parity' not in command or '--severity-all' not in command:
        raise ValueError('Native receipt lacks pinned tool or complete parity/severity scope')
    violations = report['violations']
    return {'status': 'EXECUTED; inspect errors, opens, parity and warning dispositions',
            'receipt': str(path), 'report_sha256': receipt['report_sha256'],
            'pcb_sha256': receipt['pcb_sha256'], 'kicad_version': report['kicad_version'],
            'date': report['date'],
            'errors': sum(v['severity'] == 'error' for v in violations),
            'unconnected_items': len(report['unconnected_items']),
            'schematic_parity': report['schematic_parity'],
            'warning_counts': {kind: sum(v['type'] == kind and v['severity'] == 'warning' for v in violations)
                               for kind in sorted({v['type'] for v in violations if v['severity'] == 'warning'})},
            'ignored_checks': report['ignored_checks'],
            'scope': 'Native CAD evidence only; no electrical, thermal, supplier or physical acceptance is implied.'}
