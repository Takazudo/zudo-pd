#!/usr/bin/env python3
"""Draft B20 power-budget and power-layout reports for the Board P r3 + board-b20-draft pair.

usage: python3 power-report.py

Pure Python: reads the saved filled zones of boards/board-b20-draft/board-b20-draft.kicad_pcb with
scripts/schgen/sexp.py, plus the phase 33 desk reports (routing, loop, current, thermal) beside it. Writes
manufacturing/power-layout-b20.json and manufacturing/power-budget-b20.json, the files the exporter's
verify_power_report_freshness() requires for this pair. Everything here is a desk screen of an unvalidated draft:
nothing is measured, no field solver or thermal simulation runs, and no value establishes a rating.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/schgen'))
import sexp  # noqa: E402

BOARD_P, BOARD_B = 'board-p', 'board-b20-draft'
BOARD_DIR = ROOT / 'boards' / BOARD_B
PCB = BOARD_DIR / (BOARD_B + '.kicad_pcb')
P_PCB = ROOT / 'boards' / BOARD_P / (BOARD_P + '.kicad_pcb')
SPECS = {'board_p_spec_sha256': ROOT / 'scripts/schgen/board_p_spec.py',
         'board_b20_draft_spec_sha256': ROOT / 'scripts/schgen/board_b20_spec.py'}
SOURCES = {name: BOARD_DIR / (name + '.json') for name in ('routing-report', 'loop-check', 'current-check', 'thermal-check')}
GROUND_NET = 'GND'
NEGATIVE_NETS = {'M12_RAW': 'U3', 'M12_PRE': 'U3'}
DRAFT = ('DRAFT desk screen of an unvalidated draft board. Nothing is measured; values come from routed geometry and '
         'datasheet-maximum desk models and do not establish ratings, temperatures or qualification.')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rel(path):
    return str(Path(path).relative_to(ROOT))


def children(node, name):
    return [c for c in node[1:] if isinstance(c, list) and c and sexp.atom(c[0]) == name]


def shoelace(points):
    total = 0.
    for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
        total += x1 * y2 - x2 * y1
    return abs(total) / 2


def filled_areas():
    """Filled-polygon area per (net, layer). KiCad stores each fill as one fractured outline, so shoelace is exact."""
    tree = sexp.load(PCB)
    areas = {}
    for zone in children(tree, 'zone'):
        nets = [sexp.atom(c[1]) for c in children(zone, 'net')]
        if not nets:
            continue
        for polygon in children(zone, 'filled_polygon'):
            layer = sexp.atom(children(polygon, 'layer')[0][1])
            points = [(float(sexp.atom(p[1])), float(sexp.atom(p[2]))) for p in children(children(polygon, 'pts')[0], 'xy')]
            areas[(nets[0], layer)] = areas.get((nets[0], layer), 0.) + shoelace(points)
    return areas


def main():
    reports = {name: json.loads(path.read_text()) for name, path in SOURCES.items()}
    areas = filled_areas()
    pcb_sha = digest(PCB)
    ground = {layer: round(area, 3) for (net, layer), area in sorted(areas.items()) if net == GROUND_NET}
    negative = [{'regulator': NEGATIVE_NETS[net], 'layer': layer, 'net': net, 'filled_zone_area_mm2': round(area, 3),
                 'excluded_other_polygons_mm2': 0.0}
                for (net, layer), area in sorted(areas.items()) if net in NEGATIVE_NETS]

    routing, loops, current, thermal = (reports[k] for k in ('routing-report', 'loop-check', 'current-check', 'thermal-check'))
    hot_loops = {}
    for stage, data in loops['stages'].items():
        branches = {k: v for k, v in data.items() if k.endswith('_branch') or k.startswith('return_branch')}
        hot_loops[stage] = {
            'ic': data['ic'], 'input_cap': data['input_cap'], 'diode': data['diode'],
            'hot_loop_polygon_mm2': data['hot_loop_polygon_mm2'], 'hot_loop_perimeter_mm': data['hot_loop_perimeter_mm'],
            'branches_routed': all(b.get('routed') for b in branches.values()),
            'minimum_branch_width_mm': min(b['min_width_mm'] for b in branches.values()),
        }
    paths = current['paths'] + current['stage_cells']
    path_rows = [{'net': p['net'], 'from': p['from'], 'to': p['to'], 'narrowest_mm': p['narrowest_mm'],
                  'path_layers': p['path_layers'], 'rise_k': p['rise_k']} for p in paths]
    hottest = max(paths, key=lambda p: p['rise_k']['limiter_max'])

    checks = {
        'routing_complete': not routing['unrouted'],
        'switcher_hot_loop_branches_routed': all(h['branches_routed'] for h in hot_loops.values()),
        'high_current_paths_routed': all(p['narrowest_mm'] and p['path_layers'] for p in paths),
        'ground_pours_filled': bool(ground),
        'negative_pour_filled': bool(negative),
    }
    layout = {
        'board': BOARD_B,
        'board_p': BOARD_P,
        'draft': True,
        'status': 'PASS' if all(checks.values()) else 'FAIL',
        'status_scope': ('PASS means only that the listed geometry gates hold on the current saved PCB: routing is '
                         'complete, every hot-loop branch and high-current path is routed, and the pours are filled. '
                         'It is not a current-capacity, loop-inductance, EMI or thermal pass. ' + DRAFT),
        'pcb_sha256': pcb_sha,
        'source_generator': rel(__file__),
        'source_generator_sha256': digest(__file__),
        'source_reports_sha256': {rel(path): digest(path) for path in SOURCES.values()},
        'checks': checks,
        'switcher_hot_loops': hot_loops,
        'hot_loop_open': ('The inverter (stage C, U3/CCIN1/D3) loop is 44.4 mm2 on the SMC D3 land, against 29.6 mm2 for '
                          'stages A and B. Loop inductance, ringing and radiated pickup are OPEN: no field solver or '
                          'measurement was run.'),
        'high_current_paths': path_rows,
        'hottest_path_limiter_max': {'net': hottest['net'], 'from': hottest['from'], 'to': hottest['to'],
                                     'rise_k': hottest['rise_k']['limiter_max']},
        'path_rise_basis': ('Desk trace-rise estimate from routed width, length and copper thickness at the rated and '
                            'limiter-maximum currents (current-check.py). Not a measured temperature.'),
        'negative_filled_zone_areas': negative,
        'ground_filled_zone_areas_mm2': ground,
        'open': [
            'Inverter hot-loop inductance and pickup (OPEN, desk only).',
            'D3 local copper temperature (UNKNOWN).',
            'Ground polygon connectivity and stitch adequacy beyond DRC connectivity (NOT RUN for B20).',
            'Any measured temperature, ripple or efficiency (NOT RUN: no hardware).',
        ],
    }

    stages = {}
    for case in ('rated_typ_rds', 'rated_max_rds', 'limiter_max_typ_rds', 'limiter_max_max_rds'):
        row = thermal[case]
        stages[case] = {'board_loss_w': row['board_loss_w'], 'output_w': row['output_w'], 'efficiency': row['efficiency'],
                        'input_a_at_19v': row['input_a_at_19v'], 'mean_board_rise_k': row['mean_rise_k'],
                        'stage_loss_w': {k: v['stage_w'] for k, v in row['stages'].items()},
                        'stage_tj_std_board_c': {k: v['tj_std_board_c'] for k, v in row['stages'].items()}}
    budget = {
        'schema_version': 1,
        'draft': True,
        'status': 'DRAFT 20 V SWITCHER-DIRECT DESK BUDGET; ' + DRAFT,
        'board_p': BOARD_P,
        'board_b': BOARD_B,
        'rated_targets': {'plus12': {'voltage_v': 12, 'current_a': 1.2}, 'minus12': {'voltage_v': -12, 'current_a': 0.8},
                          'plus5': {'voltage_v': 5, 'current_a': 0.5}},
        'switcher_path': ('VIN (PD 20 V contract, 19 V desk input) feeds three switchers directly: +12 V buck U1, +5 V buck '
                          'U2 and the -12 V inverting stage U3. Each stage passes a post filter, a shunt (RSH1-RSH3) and '
                          'its rail FETs to J6/J7 and the J10/J11 bus headers.'),
        'desk_assumptions': thermal['assumptions'],
        'desk_loss_cases': stages,
        'board_loss_at_limiter_max_with_max_rdson_w': thermal['limiter_max_max_rds']['board_loss_w'],
        'loss_basis': ('thermal-check.py desk model: conduction, switching, gate and quiescent IC terms plus diode, '
                       'inductor, post-filter, shunt and rail-FET losses, with mean board rise from the board area and '
                       'an assumed convection coefficient range. Not a thermal simulation or measurement.'),
        'source_generator': rel(__file__),
        'source_generator_sha256': digest(__file__),
        'thermal_source': rel(SOURCES['thermal-check']),
        'thermal_source_sha256': digest(SOURCES['thermal-check']),
        **{key: digest(path) for key, path in SPECS.items()},
        'protection_pcb_source_sha256': {BOARD_P: digest(P_PCB), BOARD_B: pcb_sha},
        'actual_filled_copper': {'pcb_sha256': pcb_sha, 'negative_zones': negative, 'ground_zone_areas_mm2': ground},
        'open_qualification': [
            'Full-load, low-line, thermal and transient behavior (OPEN: no hardware).',
            'The -12 V stage carries the largest desk loss and junction estimate; its copper temperature is UNKNOWN.',
            'Input current against the PD contract during startup (OPEN).',
        ],
    }
    for name, data in (('power-layout-b20.json', layout), ('power-budget-b20.json', budget)):
        (ROOT / 'manufacturing' / name).write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps({'status': layout['status'], 'checks': checks, 'ground_mm2': ground, 'negative': negative,
                      'board_loss_w': budget['board_loss_at_limiter_max_with_max_rdson_w']}, indent=1))
    return 0 if layout['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
