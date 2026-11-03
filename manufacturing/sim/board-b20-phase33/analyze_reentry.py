"""Phase 11/12 re-entry analysis: usage python3 analyze_reentry.py <dir with *.dat and *.cir>.

Reads the disable (TD) and re-enable request (TR) times from each deck's VDIS PWL; with the phase-12
interlock the effective re-enable (TE) is the first time after TR at which v(enn) falls below 2.5 V. It evaluates the contract §5
start rows after the effective re-enable (TE to the end) and over the whole off/re-entry interval (TD to the end).
Slope limits are the contract rows (+12 / +5 / -12: 1.23 / 0.51 / 1.22 V/ms), over 50-100 us windows.
"""
import glob, json, re, sys

SLOPE = {'+12': 1.23, '+5': 0.51, '-12': 1.22}
BAND = {'+12': 12.00, '+5': 5.05, '-12': 12.00}
COL = {'+12': (1, 1), '+5': (2, 1), '-12': (3, -1)}


def load(f):
    rows = []
    for line in open(f):
        p = line.split()
        if len(p) < 20:
            continue
        v = [float(x) for x in p]
        rows.append((v[0], v[1], v[3], v[5], v[7], v[9], v[11], v[13], v[21] if len(v) > 21 else 0.0))
    return rows


def max_slope(w, idx):
    s, j = 0.0, 0
    for i in range(len(w)):
        while w[i][0] - w[j][0] > 1e-4:
            j += 1
        if w[i][0] - w[j][0] > 5e-5:
            s = max(s, abs(w[i][idx] - w[j][idx]) / (w[i][0] - w[j][0]) / 1e3)
    return s


def forms(w):
    return {
        'p12_max_while_absm12_lt_0v1': round(max((x[1] for x in w if -x[3] < 0.1), default=0), 4),
        'absm12_max_while_p12_le_0v5': round(max((-x[3] for x in w if x[1] <= 0.5), default=0), 4),
        'absm12_max_while_p12_lt_5v2': round(max((-x[3] for x in w if x[1] < 5.2), default=0), 4),
        'p12_minus_absm12_v': [round(min(x[1] + x[3] for x in w), 4), round(max(x[1] + x[3] for x in w), 4)],
        'p5_max_while_min_analog_lt_1v45': round(max((x[2] for x in w if min(x[1], -x[3]) < 1.45), default=0), 4),
    }


out = {}
for f in sorted(glob.glob(sys.argv[1] + '/*.dat')):
    name = f.split('/')[-1][:-4]
    pwl = re.search(r'^VDIS dis 0 PWL\(0 0 (\S+) 0 \S+ 5 (\S+) 5', open(f[:-4] + '.cir').read(), re.M)
    TD, TR = float(pwl.group(1)), float(pwl.group(2))
    r = load(f)
    at = lambda t: min(r, key=lambda x: abs(x[0] - t))
    TE = next((x[0] for x in r if x[0] >= TR and x[8] < 2.5), TR) if len(r[0]) > 8 and any(x[8] for x in r) else TR
    off = [x for x in r if TD <= x[0] < TE]
    re_on = [x for x in r if x[0] >= TE]
    whole = [x for x in r if x[0] >= TD]
    res = {'t_end_ms': round(r[-1][0] * 1e3, 3), 'disable_ms': round(TD * 1e3, 3), 'reenable_request_after_disable_ms': round((TR - TD) * 1e3, 3),
           'effective_reenable_after_disable_ms': round((TE - TD) * 1e3, 3),
           'at_disable': {k: round(at(TD)[i] * s, 4) for k, (i, s) in COL.items()} | {'ramp': round(at(TD)[4], 4)},
           'at_reenable': {k: round(at(TE)[i] * s, 4) for k, (i, s) in COL.items()} | {'ramp': round(at(TE)[4], 4)},
           'ramp_min_while_off_v': round(min(x[4] for x in off), 4)}
    be = {}
    for k, (i, s) in COL.items():
        t = next((x[0] for x in re_on if s * x[i] >= BAND[k]), None)
        be[k] = round((t - TE) * 1e3, 3) if t else None
    res['band_entry_after_reenable_ms'] = be
    res['band_entry_skew_ms'] = round(max(be.values()) - min(be.values()), 3) if None not in be.values() else None
    res['p5_last'] = None not in be.values() and be['+5'] >= max(be['+12'], be['-12'])
    res['max_slope_v_per_ms_after_reenable'] = {k: round(max_slope(re_on, i), 3) for k, (i, s) in COL.items()}
    res['max_slope_v_per_ms_while_off'] = {k: round(max_slope(off, i), 3) for k, (i, s) in COL.items()}
    res['slope_rows_after_reenable'] = {k: res['max_slope_v_per_ms_after_reenable'][k] <= SLOPE[k] for k in SLOPE}
    res['forms_after_reenable'] = forms(re_on)
    res['forms_disable_to_end'] = forms(whole)
    res['at_end'] = {k: round(r[-1][i] * s, 4) for k, (i, s) in COL.items()}
    res['peak_source_a_after_reenable'] = {'+12': round(max(-x[5] for x in re_on), 3), '+5': round(max(-x[6] for x in re_on), 3),
                                           '-12': round(max(x[7] for x in re_on), 3)}
    out[name] = res
print(json.dumps(out, indent=1))
