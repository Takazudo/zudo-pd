"""D9 zener choice for the 15 V Board P VDD_LOC clamp (review F7): BZT52C18 kept or BZT52C20 adopted.

usage: python3 zener-choice.py [--write]  # print (and write) the JSON record
       python3 zener-choice.py --check    # fail if boards/board-p15/d9-zener-choice.json differs

Uses the guaranteed DS18004 rows and the bound helpers in scripts/pcb/calculate-input-ovp-20v.py. The p15 surge
row is the 28.6 V SMAJ16A hot estimate (TYP-based, input-clamp-fix.md), not the r3 TVS2200 row. Adoption rule set
by the coordinator: adopt BZT52C20 only if the VDD pin keeps >= 5 V margin to the 28 V absolute maximum.
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('ovp', ROOT / 'scripts/pcb/calculate-input-ovp-20v.py')
ovp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ovp)

SURGE_V = 28.6
INPUT_HIGH_V = 15.0 * 1.05
REQUIRED_MARGIN_V = 5.0
R29, R30 = 1000.0, 470.0
OUT = ROOT / 'boards/board-p15/d9-zener-choice.json'


def row(zener):
    z = ovp.ZENER[zener]
    pin = ovp.local_clamp_pin('VDD (U1.24)', zener, R29 + R30, SURGE_V, ovp.STUSB_VBUS_ABS_MAX_V)
    vz_cold_min = ovp._vz_bounds(z, ovp.T_RANGE[0])[0]
    vz_hot_max = ovp._vz_bounds(z, ovp.TA_OP_MAX)[1]
    i = (SURGE_V - vz_cold_min) / ((R29 + R30) * (1 - ovp.R1_TOL))
    return {
        'zener': zener,
        'vdd_pin_max_v_at_surge': pin['pin_max_v'],
        'margin_to_28v_v': pin['margin_v'],
        'meets_5v_margin': pin['margin_v'] >= REQUIRED_MARGIN_V,
        'vz_max_at_105c_v': round(vz_hot_max, 3),
        'vdd_operating_max_v': ovp.STUSB_VDD_OPERATING_MAX_V,
        'within_22v_operating_row_at_105c': vz_hot_max <= ovp.STUSB_VDD_OPERATING_MAX_V,
        'vz_min_at_minus40c_v': round(vz_cold_min, 3),
        'window_above_15v75_v': round(vz_cold_min - INPUT_HIGH_V, 3),
        'feed_current_ma_at_surge_minus40c': round(i * 1e3, 3),
        'beyond_izt_ma': round(max(0.0, i - z['izt']) * 1e3, 3),
        'r29_mw': round(i * i * R29 * (1 - ovp.R1_TOL) * 1e3, 1),
        'r30_mw': round(i * i * R30 * (1 - ovp.R1_TOL) * 1e3, 1),
        'zener_mw_bound': round(i * pin['pin_max_v'] * 1e3, 1),
        'rows': pin['rows'],
    }


def build():
    rows = [row('BZT52C18'), row('BZT52C20')]
    c20 = rows[1]
    adopt = c20['meets_5v_margin']
    return {
        'purpose': 'board-p15 D9 VDD_LOC clamp choice (review F7); desk arithmetic, nothing measured',
        'surge_row_v': SURGE_V, 'input_high_v': INPUT_HIGH_V, 'required_margin_v': REQUIRED_MARGIN_V,
        'feed_ohm': R29 + R30, 'resistor_tolerance': ovp.R1_TOL,
        'basis': 'VZ and TC rows from DS18004 (G); ZZT max used as a linear slope above IZT (PA); '
                 'resistor rating 0.1 W at <= 70 C only (derating above 70 C UNKNOWN); zener 370 mW at 25 C on FR-4',
        'candidates': rows,
        'choice': 'BZT52C20' if adopt else 'BZT52C18',
        'reason': ('BZT52C20 keeps >= 5 V margin to 28 V' if adopt else
                   f"BZT52C20 leaves {c20['margin_to_28v_v']} V to 28 V at {SURGE_V} V / 125 C (< {REQUIRED_MARGIN_V} V) "
                   f"and its 105 C VZ max {c20['vz_max_at_105c_v']} V exceeds the 22 V VDD operating row; "
                   'BZT52C18 stays, with a +0.01 V guaranteed cold window at 15.75 V'),
    }


def main():
    data = json.dumps(build(), indent=2) + '\n'
    if '--check' in sys.argv:
        if OUT.read_text() != data:
            raise SystemExit(f'{OUT} is stale; rerun without --check')
        print('d9-zener-choice: current')
        return
    if '--write' in sys.argv:
        OUT.write_text(data)
    print(data, end='')


if __name__ == '__main__':
    main()
