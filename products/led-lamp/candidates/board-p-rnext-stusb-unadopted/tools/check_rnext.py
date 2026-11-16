"""Desk checks for the r-next spec: block parity with zudo-pd r3 and window arithmetic.

Usage: python3 candidates/board-p-rnext-stusb-unadopted/tools/check_rnext.py > .../checks/rnext-check.json
"""
import importlib.util
import json
import os
import runpy
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAND = os.path.dirname(HERE)
r3 = runpy.run_path(os.path.join(HERE, 'inputs', 'board_p_r3_spec-3ac13d4.py.txt'))
rn = runpy.run_path(os.path.join(HERE, 'board_p_rnext_spec.py'))
s = importlib.util.spec_from_file_location(
    'fw', os.path.join(CAND, 'board-p-v196-unadopted', 'analysis', 'failoff_window.py'))
fw = importlib.util.module_from_spec(s)
s.loader.exec_module(fw)

WINDOW_REFS = {'U4', 'U5', 'C40', 'C41', 'C42', '#FLG01', '#FLG02'} | {f'R{n}' for n in range(30, 40)}
ALLOWED_COMPONENT_DIFF = {'JOUT1': 'footprint nickname zudo-led-lamp (LED part, same name)',
                          'U3': 'manufacturer DBV0006A land', 'D5': 'manufacturer DRV0006A land',
                          'D8': 'manufacturer SOD123 land'}
# LED per-product population: footprint and value label may differ, symbol/LCSC/nets may not.
ALLOWED_VALUE_AND_FOOTPRINT_DIFF = {'J3': '2 x 4 1.5 mm debug test-pad array replaces the 1 x 8 2.54 mm pogo row'}
errors = []
for ref, comp in r3['COMPONENTS'].items():
    if ref not in rn['COMPONENTS']:
        errors.append(f'{ref}: dropped from block')
    elif ref in ALLOWED_VALUE_AND_FOOTPRINT_DIFF:
        a, b = rn['COMPONENTS'][ref], comp
        if (a[0], a[2]) + a[4:] != (b[0], b[2]) + b[4:]:
            errors.append(f'{ref}: changed beyond its value/footprint fields')
    elif ref in ALLOWED_COMPONENT_DIFF:
        a, b = rn['COMPONENTS'][ref], comp
        if a[:3] + a[4:] != b[:3] + b[4:]:
            errors.append(f'{ref}: changed beyond its footprint field')
    elif rn['COMPONENTS'][ref] != comp:
        errors.append(f'{ref}: changed from r3')
extra = set(rn['COMPONENTS']) - set(r3['COMPONENTS'])
if extra - WINDOW_REFS:
    errors.append(f'unexpected new refs {sorted(extra - WINDOW_REFS)}')
moved = {'JOUT1.1', 'JOUT1.2'}
for net, nodes in r3['NETS'].items():
    got = set(rn['NETS'].get(net, []))
    lost = set(nodes) - got
    if net == 'VBUS_OUT':
        lost -= moved
    if lost:
        errors.append(f'{net}: lost {sorted(lost)}')
    added = got - set(nodes)
    if any(n.split('.')[0] not in WINDOW_REFS for n in added):
        errors.append(f'{net}: non-window node added {sorted(added)}')
if set(rn['NETS']['LED_OUT']) & moved != moved:
    errors.append('JOUT1.1/.2 not on LED_OUT')
if set(r3['NO_CONNECT']) - set(rn['NO_CONNECT']):
    errors.append('block NC changed')


def ohms(ref):
    v = rn['COMPONENTS'][ref][1].split()[0]
    return float(v.rstrip('kM')) * {'k': 1e3, 'M': 1e6}.get(v[-1], 1)


U5_OUTA_LEAK_MAX_A = 300e-9
cases = {}
for name, e in fw.LEVELS.items():
    cases[name] = {
        'monitor_INA': fw.monitor(ohms('R35') + ohms('R36'), ohms('R37'), e),
        'efuse_UV_no_QINH': fw.efuse(ohms('R31'), ohms('R32'), fw.EFUSE_UV_RISE, fw.EFUSE_UV_FALL, e),
        # U5 OUTA is open-drain on the EN/UVLO node; TPS3701 datasheet ID(leak) max 300 nA
        # (fact-tps3701-out-leak) flows into the same node when OUTA is released.
        'efuse_UV_with_U5_OUTA_leak': fw.efuse(ohms('R31'), ohms('R32'), fw.EFUSE_UV_RISE, fw.EFUSE_UV_FALL, e,
                                               U5_OUTA_LEAK_MAX_A),
        'efuse_OV': fw.efuse(ohms('R33'), ohms('R34'), fw.EFUSE_OV_RISE, fw.EFUSE_OV_FALL, e),
    }
l2 = cases['L2_plus_endurance_0p5pct']
out = {
    'block_parity_errors': errors,
    'option': rn['OPTION'], 'nvm_image': rn['NVM_IMAGE'],
    'options': {k: {'nvm_i_snk_pdo2': v['nvm_i_snk_pdo2'], 'RILM': v['RILM'][1]} for k, v in rn['OPTIONS'].items()},
    'cases': cases,
    'summary_L2': {
        'off_guaranteed_at_or_below_v': round(l2['monitor_INA']['fall'][0], 3),
        'reject_12v6_margin_v': round(l2['monitor_INA']['reject_margin_v'], 3),
        'on_needs_vbus_out_at_least_v': round(l2['monitor_INA']['rise'][1], 3),
        'efuse_uv_rise_band_v': [round(x, 3) for x in l2['efuse_UV_no_QINH']['rise']],
        'efuse_uv_rise_band_with_u5_leak_v': [round(x, 3) for x in l2['efuse_UV_with_U5_OUTA_leak']['rise']],
        'efuse_uv_fall_band_with_u5_leak_v': [round(x, 3) for x in l2['efuse_UV_with_U5_OUTA_leak']['fall']],
        'ov_rise_band_v': [round(x, 3) for x in l2['efuse_OV']['rise']],
        'ov_fall_min_v': round(l2['efuse_OV']['fall'][0], 3),
    },
}
json.dump(out, sys.stdout, indent=1)
print()
sys.exit(1 if errors else 0)
