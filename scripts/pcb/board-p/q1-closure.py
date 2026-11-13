#!/usr/bin/env python3
"""Board P r3 Q1 closure screen: C36 Miller soft start at a 20 V contract.

The Q1 drain slews at the R12 gate current divided by the incremental C36 capacitance
(dec-p-20v-q1-soft-start). C36 sits between VBUS_OUT and Q1_MX, which is held near
VBUS_P - V_plateau + V_f(Q5), so its DC bias starts near VBUS_P and falls as VBUS_OUT rises.

Every input is cited in q1-closure-inputs.json. Capacitance curves are manufacturer typical
small-signal data, so the result is CALCULATED and SCREEN-only: no case ever returns an
acceptance verdict. Missing guaranteed curve, temperature or linear-mode SOA data stays OPEN:
those labels are fixed (fail-closed), and a missing or inconsistent cited input is refused with InputError
rather than evaluated. Comparisons against the adopted ranges carry a TYPICAL_ prefix because both sides
rest on typical or PA values.

Usage: q1-closure.py [--json] [--inputs PATH]
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
INPUTS = Path(__file__).with_name('q1-closure-inputs.json')
STEPS = 4000

OPEN_ITEMS = [
    'C(V) is manufacturer typical 25 C small-signal data; no guaranteed minimum over tolerance, temperature and aging (OPEN)',
    'Large-signal dQ/dV of a class II dielectric is not characterised; the small-signal curve is used as incremental capacitance',
    'Q1 SOA is a graph read at VGS 10 V, TA 25 C, single pulse; linear-mode operation at the plateau VGS and elevated ambient are UNSOURCED',
    'Q1 transconductance, Crss and the downstream load are ignored',
    'Bench T3 (slew, inrush, Q1 temperature) is NOT RUN',
]


class InputError(ValueError):
    pass


def canonical_sha256(series: dict) -> str:
    payload = {'partsName': series['partsName'], 'graphType': series['graphType'], 'degC': series['degC'],
               'dsDcFre': series['dsDcFre'], 'points': series['points']}
    return hashlib.sha256(json.dumps(payload, separators=(',', ':')).encode()).hexdigest()


def _bundle_items(owner: str, kind: str) -> dict:
    data = json.loads((ROOT / '.claude' / 'skills' / owner / f'{kind}.json').read_text())
    key = next(k for k, v in data.items() if isinstance(v, list))
    id_key = 'source_id' if kind == 'sources' else 'fact_id'
    return {item[id_key]: item for item in data[key]}


def _fact(owner: str, fact_id: str) -> dict:
    fact = _bundle_items(owner, 'facts').get(fact_id)
    if fact is None:
        raise InputError(f"fact {fact_id} missing from {owner}")
    return fact


def _first_number(value) -> float:
    return float(value) if isinstance(value, (int, float)) else float(str(value).split('/')[0].split()[0])


def verify_inputs(inp: dict, root: Path = ROOT) -> None:
    for key in ('adopted', 'circuit', 'u2_iol_min_a', 'q1_soa', 'capacitors'):
        if key not in inp:
            raise InputError(f"cited input '{key}' is missing; nothing is evaluated (UNSOURCED)")
    adopted = inp['adopted']
    decisions = json.loads((root / adopted['decision_file']).read_text())['decisions']
    decision = next((d for d in decisions if d['id'] == adopted['decision_id']), None)
    if decision is None:
        raise InputError(f"adopted decision {adopted['decision_id']} not found")
    for phrase in adopted['rationale_phrases']:
        if phrase not in decision['rationale']:
            raise InputError(f"adopted value '{phrase}' not in the {adopted['decision_id']} rationale")
    r12 = inp['circuit']['r12_ohm']
    if _first_number(_fact(r12['owner'], r12['fact_id'])['value']) != r12['value']:
        raise InputError('R12 value does not match its resistance fact')
    if _first_number(_fact(r12['owner'], r12['tolerance_fact_id'])['value']) / 100 != r12['tolerance']:
        raise InputError('R12 tolerance does not match its fact')
    tol = inp['circuit']['c_nominal_tolerance']
    cap_tol = _first_number(_fact(tol['owner'], tol['fact_id'])['value']) / 100
    if sorted(tol['values']) != sorted([1.0, round(1 - cap_tol, 6)]):
        raise InputError('capacitor tolerance corners do not match the cited tolerance fact')
    iol = inp['u2_iol_min_a']
    if _first_number(_fact(iol['owner'], iol['fact_id'])['value']) != iol['value']:
        raise InputError('U2 I(OL) minimum does not match its fact')
    soa = inp['q1_soa']
    src = _bundle_items(soa['owner'], 'sources').get(soa['source_id'])
    if src is None or src['availability'] != 'AVAILABLE' or src['sha256'] != soa['sha256']:
        raise InputError(f"SOA source {soa['source_id']} missing, unavailable or hash-mismatched")
    pws = [p['pw_s'] for p in soa['points']]
    if pws != sorted(pws) or len(pws) < 2:
        raise InputError('SOA points must be sorted by pulse width')
    for cap in inp['capacitors']:
        if canonical_sha256(cap['series']) != cap['canonical_sha256']:
            raise InputError(f"{cap['id']}: curve points do not match the cited canonical series hash")
        if cap['status'] in ('FITTED', 'SUPERSEDED'):
            source = _bundle_items(cap['owner'], 'sources').get(cap['source_id'])
            if source is None or source['availability'] != 'AVAILABLE':
                raise InputError(f"{cap['id']}: cited source {cap['source_id']} missing or unavailable")
            if cap['canonical_sha256'] not in source['evidence_extract']:
                raise InputError(f"{cap['id']}: owner source does not cite the canonical series hash")
        elif cap['status'] == 'PROPOSED':
            if not (cap.get('url', '').startswith('https://') and cap.get('page_sha256')):
                raise InputError(f"{cap['id']}: PROPOSED candidate lacks its manufacturer URL or page hash")
        else:
            raise InputError(f"{cap['id']}: status must be FITTED, SUPERSEDED or PROPOSED")
    if [cap['status'] for cap in inp['capacitors']].count('FITTED') != 1:
        raise InputError('exactly one capacitor must be FITTED')


def curve(series: dict):
    pts = [(float(x), float(y)) for x, y in series['points']]
    xs = [p[0] for p in pts]

    def delta_pct(v: float) -> float:
        v = abs(v)  # published for positive bias only
        if v > xs[-1]:
            raise InputError(f"bias {v:.2f} V beyond the published curve")
        i = max(1, min(len(xs) - 1, bisect.bisect_left(xs, v)))
        (x0, y0), (x1, y1) = pts[i - 1], pts[i]
        return y0 + (y1 - y0) * (v - x0) / (x1 - x0)
    return delta_pct


def soa_allowed_w(soa: dict, pw_s: float) -> float:
    pts = [(math.log10(p['pw_s']), math.log10(p['id_a'] * soa['vds_v'])) for p in soa['points']]
    lx = math.log10(pw_s)
    if lx <= pts[0][0]:
        return 10 ** pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if lx <= x1:
            return 10 ** (y0 + (y1 - y0) * (lx - x0) / (x1 - x0))
    return 10 ** pts[-1][1]


def closure(cap: dict, inp: dict, vbus: float, vpl: float, ctol: float) -> dict:
    c = inp['circuit']
    delta = curve(cap['series'])
    i_gate = (vbus - vpl) / c['r12_ohm']['value']
    v_mx = vbus - vpl + c['v_f_q5_v']['value']
    cnom = cap['nominal_uf'] * 1e-6 * ctol
    dv = vbus / STEPS
    t = 0.0
    energy = {b: 0.0 for b in c['bank_uf']['values']}
    peak_p = {b: 0.0 for b in c['bank_uf']['values']}
    peak_slew, t_floor, profile = 0.0, None, []
    floor = inp['adopted']['c36_effective_uf'][0] * 1e-6
    for k in range(STEPS):
        vout = (k + 0.5) * dv
        c_eff = cnom * (1 + delta(v_mx - vout) / 100)
        slew = i_gate / c_eff
        if k == 0:
            peak_slew = i_gate / (cnom * (1 + delta(v_mx) / 100))
        peak_slew = max(peak_slew, slew)
        if t_floor is None and c_eff >= floor:
            t_floor = (t, vout)
        dt = dv / slew
        for b in energy:
            p = b * 1e-6 * slew * (vbus - vout)
            peak_p[b] = max(peak_p[b], p)
            energy[b] += p * dt
        if k % (STEPS // 8) == 0:
            profile.append({'t_ms': round(t * 1e3, 3), 'vout_v': round(vout, 2), 'slew_v_per_ms': round(slew / 1e3, 2)})
        t += dt
    ramp = t
    iol = inp['u2_iol_min_a']['value']
    adopted = inp['adopted']
    banks = {}
    for b in energy:
        i_pk = b * 1e-6 * peak_slew
        allowed = soa_allowed_w(inp['q1_soa'], ramp)
        banks[f'{b:g}uF'] = {
            'peak_inrush_a': round(i_pk, 3),
            'inrush_vs_u2_iol_min': 'TYPICAL_EXCEEDS' if i_pk > iol else 'TYPICAL_BELOW',
            'inrush_vs_adopted_max': 'TYPICAL_EXCEEDS' if i_pk > adopted['max_inrush_a'] else 'TYPICAL_WITHIN',
            'q1_energy_mj': round(energy[b] * 1e3, 2),
            'q1_peak_power_w': round(peak_p[b], 1),
            'soa_allowed_w_at_ramp': round(allowed, 1),
            'soa_ratio_peak_rectangular': round(allowed / peak_p[b], 2),
            'soa_ratio_energy_equivalent': round(allowed / (energy[b] / ramp), 2),
            'soa_status': 'OPEN (graph-read screen; linear-mode and temperature UNSOURCED)',
        }
    return {
        'vbus_p_v': vbus, 'v_plateau_v': vpl, 'c_tolerance_factor': ctol,
        'gate_current_ma': round(i_gate * 1e3, 3),
        'c36_bias_at_start_v': round(v_mx, 2),
        'c36_at_start_uf': round(cnom * (1 + delta(v_mx) / 100) * 1e6, 3),
        'peak_slew_v_per_ms': round(peak_slew / 1e3, 2),
        'average_slew_v_per_ms': round(vbus / ramp / 1e3, 2),
        'ramp_to_vbus_ms': round(ramp * 1e3, 3),
        'c36_reaches_adopted_floor': None if t_floor is None else {'t_ms': round(t_floor[0] * 1e3, 3), 'vout_v': round(t_floor[1], 2)},
        'peak_slew_vs_adopted': 'TYPICAL_EXCEEDS' if peak_slew / 1e3 > adopted['slew_v_per_ms'][1] else
                                ('TYPICAL_BELOW' if peak_slew / 1e3 < adopted['slew_v_per_ms'][0] else 'TYPICAL_WITHIN'),
        'banks': banks,
        'profile': profile,
    }


def evaluate(inp: dict, root: Path = ROOT) -> dict:
    verify_inputs(inp, root)
    c = inp['circuit']
    out = {'class': 'CALCULATED', 'data_class': 'TYPICAL', 'verdict': 'SCREEN ONLY - NOT AN ACCEPTANCE',
           'open_items': OPEN_ITEMS, 'adopted': inp['adopted'], 'u2_iol_min_a': inp['u2_iol_min_a']['value'], 'capacitors': []}
    for cap in inp['capacitors']:
        cases = [closure(cap, inp, vbus, vpl, ctol)
                 for vbus in c['vbus_p_v']['values'] for vpl in c['v_plateau_v']['values']
                 for ctol in c['c_nominal_tolerance']['values']]
        out['capacitors'].append({'id': cap['id'], 'label': cap['label'], 'status': cap['status'], 'cases': cases})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--inputs', type=Path, default=INPUTS)
    args = ap.parse_args()
    res = evaluate(json.loads(args.inputs.read_text()))
    if args.json:
        print(json.dumps(res, indent=2))
        return 0
    print(res['verdict'])
    for cap in res['capacitors']:
        print(f"\n{cap['label']} [{cap['status']}]")
        for k in cap['cases']:
            b = k['banks']
            print(f"  VBUS_P {k['vbus_p_v']:g} V, plateau {k['v_plateau_v']:g} V, C x{k['c_tolerance_factor']:g}: "
                  f"C36 {k['c36_at_start_uf']} uF, peak {k['peak_slew_v_per_ms']} V/ms ({k['peak_slew_vs_adopted']}), "
                  f"avg {k['average_slew_v_per_ms']} V/ms, ramp {k['ramp_to_vbus_ms']} ms; "
                  + '; '.join(f"{n}: {v['peak_inrush_a']} A {v['inrush_vs_u2_iol_min']} I(OL) min, "
                             f"{v['q1_peak_power_w']} W peak, {v['q1_energy_mj']} mJ, SOA x{v['soa_ratio_peak_rectangular']}"
                             for n, v in b.items()) + ' (typical data; SOA OPEN; not an acceptance)')
    print('\nOPEN: ' + '\n      '.join(res['open_items']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
