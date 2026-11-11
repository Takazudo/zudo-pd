#!/usr/bin/env python3
"""Bind a native Board P r3 DRC report to the exact PCB, schematic and project bytes it checked.

usage: write-board-p-drc-receipt.py REPORT.json RECEIPT.json --command JSON --execution-revision SHA --toolchain JSON

The receipt has the fields native_receipt.py reads (pcb/schematic/project SHA-256, report file and hash,
the exact command). It refuses a report that is not from KiCad 10.0.6, lacks schematic parity or all
severities, or has DRC errors or unconnected items. Warnings stay in the report for review; this script
does not disposition them.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOARD = ROOT / 'boards/board-p'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def summary(report):
    severities = collections.Counter(v['severity'] for v in report['violations'])
    types = collections.Counter(f"{v['severity']}:{v['type']}" for v in report['violations'])
    return {'violations_by_severity': dict(sorted(severities.items())),
            'violations_by_type': dict(sorted(types.items())),
            'schematic_parity_items': len(report.get('schematic_parity', [])),
            'unconnected_items': len(report.get('unconnected_items', []))}


def build(report_path, command, revision, toolchain):
    report = json.loads(Path(report_path).read_text())
    if report.get('kicad_version') != '10.0.6':
        raise SystemExit(f"DRC report is from KiCad {report.get('kicad_version')}, not 10.0.6")
    if '--schematic-parity' not in command or '--severity-all' not in command:
        raise SystemExit('DRC command lacks --schematic-parity or --severity-all')
    counts = summary(report)
    if counts['violations_by_severity'].get('error') or counts['unconnected_items']:
        raise SystemExit(f'DRC has errors or unconnected items: {json.dumps(counts)}')
    return {'pcb_sha256': sha(BOARD / 'board-p.kicad_pcb'),
            'schematic_sha256': sha(BOARD / 'board-p.kicad_sch'),
            'project_sha256': sha(BOARD / 'board-p.kicad_pro'),
            'report_file': Path(report_path).name,
            'report_sha256': sha(report_path),
            'command': command,
            'execution_revision': revision,
            'adoption_revision': None,
            'toolchain': toolchain,
            'summary': counts,
            'scope': ('Native CAD and geometry only. Warnings and schematic-parity items are listed for review and '
                      'are not dispositioned here; supplier process, electrical/interface and measured thermal gates '
                      'remain separate.')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('receipt', type=Path)
    parser.add_argument('--command', required=True, help='JSON list of the exact DRC command')
    parser.add_argument('--execution-revision', required=True)
    parser.add_argument('--toolchain', required=True, help='JSON object describing image and runner')
    args = parser.parse_args()
    receipt = build(args.report, json.loads(args.command), args.execution_revision, json.loads(args.toolchain))
    args.receipt.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt['summary'], indent=1))


if __name__ == '__main__':
    main()
