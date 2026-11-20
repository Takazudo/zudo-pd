"""Structural check and worst-case window arithmetic for window_spec.py.

Arithmetic only; reuses the V196 tolerance model (failoff_window.py) unchanged.
Usage: python3 check_window.py > window_check.json
"""
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import window_spec as ws  # noqa: E402

spec = importlib.util.spec_from_file_location(
    'failoff_window', HERE.parent / 'board-p-v196-unadopted/analysis/failoff_window.py')
fw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fw)


def structural():
    errors = []
    seen = {}
    for net, nodes in ws.NETS.items():
        if len(nodes) < 2 and net not in ws.INTERFACE:
            errors.append(f'{net}: single-node net')
        for node in nodes:
            ref, pin = node.split('.')
            if ref not in ws.COMPONENTS:
                errors.append(f'{node}: unknown ref')
            if ref in ws.PINS and int(pin) not in ws.PINS[ref]:
                errors.append(f'{node}: pin not in pin table')
            if node in seen:
                errors.append(f'{node}: on {seen[node]} and {net}')
            seen[node] = net
    for nc in ws.NO_CONNECT:
        if nc in seen:
            errors.append(f'{nc}: marked NC but connected')
        seen[nc] = 'NC'
    for ref in ws.COMPONENTS:
        pins = ws.PINS.get(ref, {1: '', 2: ''})
        for p in pins:
            if f'{ref}.{p}' not in seen:
                errors.append(f'{ref}.{p}: unconnected and not NC')
    return errors


def ohms(ref):
    v = ws.COMPONENTS[ref][1].split()[0]
    mult = {'k': 1e3, 'M': 1e6}.get(v[-1], 1)
    return float(v.rstrip('kM')) * mult


def main():
    errors = structural()
    rmon = ohms('RMH1') + ohms('RMH2')
    out = {'structural_errors': errors, 'reject_max_v': fw.REJECT_MAX_V, 'levels': fw.LEVELS, 'cases': {}}
    for name, e in fw.LEVELS.items():
        out['cases'][name] = {
            'monitor_INA': fw.monitor(rmon, ohms('RML'), e),
            'efuse_UV_with_QINH_1uA_assumed': fw.efuse(ohms('RUVH'), ohms('RUVL'), fw.EFUSE_UV_RISE,
                                                       fw.EFUSE_UV_FALL, e, fw.QINH_LKG_ASSUMED),
            'efuse_OV': fw.efuse(ohms('ROVH'), ohms('ROVL'), fw.EFUSE_OV_RISE, fw.EFUSE_OV_FALL, e),
        }
    l2 = out['cases']['L2_plus_endurance_0p5pct']
    out['summary_L2'] = {
        'off_guaranteed_at_or_below_v': round(l2['monitor_INA']['fall'][0], 3),
        'reject_12v6_margin_v': round(l2['monitor_INA']['reject_margin_v'], 3),
        'on_needs_raw_at_least_v': round(l2['monitor_INA']['rise'][1], 3),
        'ov_rise_band_v': [round(x, 3) for x in l2['efuse_OV']['rise']],
        'ov_fall_min_v': round(l2['efuse_OV']['fall'][0], 3),
    }
    json.dump(out, sys.stdout, indent=1)
    print()
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
