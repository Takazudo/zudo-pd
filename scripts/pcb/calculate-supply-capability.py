#!/usr/bin/env python3
"""Screen the current Board P + Board B supply capability per rail and at arbitrary load points.

This is evidence-classified arithmetic, not simulation or measurement. It reuses the
source-locked bands in manufacturing/power-budget.json and the exact-part facts in the
component owner bundles. Every limit carries an evidence class:

  GUARANTEED          manufacturer min/max limit from the retained primary source
  GUARANTEED_UNSOURCED manufacturer min/max limit retained only from a mirror (repo marks UNSOURCED)
  DESIGN_POINT        manufacturer nominal/continuous design value that is not a tested limit
  TYPICAL             manufacturer typical value
  PROJECT_ASSUMPTION  project screening assumption, never a guarantee
  UNAVAILABLE         no retained number; the check is NOT RUN

External loads are the currents drawn from the J10/J11/J6/J7 rail pins. Indicator,
feedback-divider and regulator ground currents are added by the screen.
"""
import argparse
import hashlib
import json
import math
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT/'.claude/skills'
TARGETS = {'plus12': 1.2, 'minus12': .8, 'plus5': .5}
SCREEN_VIN = (14.0, 14.25, 15.0)
PD_CURRENT_A = 3.0
AMBIENT_C, TJ_SCREEN_C = 40, 125
RIPPLE_ALLOWANCE_V = .05


def fact(owner, fact_id, cls):
    path = SKILLS/f'component-{owner}'/'facts.json'
    found = [f for f in json.loads(path.read_text())['facts'] if f['fact_id'] == fact_id]
    if len(found) != 1:
        raise ValueError(f'{owner}: expected exactly one {fact_id}')
    return {'value': found[0]['value'], 'class': cls, 'source': f'{path.relative_to(ROOT)}#{fact_id}',
            'conditions': found[0].get('conditions', '')}


def assumption(value, note):
    return {'value': value, 'class': 'PROJECT_ASSUMPTION', 'source': 'scripts/pcb/calculate-supply-capability.py', 'conditions': note}


def load_evidence():
    G, GU, D, T = 'GUARANTEED', 'GUARANTEED_UNSOURCED', 'DESIGN_POINT', 'TYPICAL'
    return {
        'u2_continuous_a': fact('ap63201-power-stage', 'fact-ap63201wu-7-current', D),
        'u2_peak_limit_min_a': fact('ap63201-power-stage', 'fact-ap63201wu-7-peak-limit-min', G),
        'u2_rds_on_ohm': fact('ap63201-power-stage', 'fact-ap63201wu-7-rds-on', T),
        'l1_inductance_uh': fact('ap63201-power-stage', 'fact-aspi-0630lr-100m-t15-inductance', D),
        'l1_tolerance': fact('ap63201-power-stage', 'fact-aspi-0630lr-100m-t15-tolerance', G),
        'l1_dcr_max_ohm': fact('ap63201-power-stage', 'fact-aspi-0630lr-100m-t15-dcr-max', G),
        'l1_irms_a': fact('ap63201-power-stage', 'fact-aspi-0630lr-100m-t15-irms', T),
        'l1_isat_a': fact('ap63201-power-stage', 'fact-aspi-0630lr-100m-t15-isat', T),
        'u2_frequency_khz': fact('ap63201-power-stage', 'fact-ap63201wu-7-frequency', T),
        'lm2596_switch_limit_min_a': assumption(3.4, 'Full-temperature minimum switch-current limit used by calculate-power-budget.py (fact-lm2596-current-limit records the 4.5 A typical); see the LM2596 owner bundle'),
        'lm2596_vsat_screen_v': assumption(1.5, 'Full-temperature Vsat maximum used by calculate-power-budget.py; fact-lm2596-vsat-max is 1.4 V at 25 C'),
        'lm2596_frequency_min_hz': assumption(117000, 'Minimum oscillator frequency used by calculate-power-budget.py'),
        'l23_inductance_min_h': assumption(80e-6, 'CYA1265-100UH minimum inductance screen used by calculate-power-budget.py'),
        'l23_idc_a': fact('cya1265-100uh-c19268674', 'fact-cya1265-idc-heat-rating', D),
        'l23_isat_a': fact('cya1265-100uh-c19268674', 'fact-cya1265-isat', D),
        'l23_dcr_max_mohm': fact('cya1265-100uh-c19268674', 'fact-cya1265-rdc-max', G),
        'd2_if_avg_a': fact('ss34-c8678', 'fact-ss34-if-avg', G),
        'd2_vf_max_v': fact('ss34-c8678', 'fact-ss34-vf', G),
        'd3_if_avg_a': fact('renewal-input-protection', 'fact-c3024223-average-current', G),
        'd3_vf_max_v': fact('renewal-input-protection', 'fact-c3024223-vf-max-5a-25c', G),
        'lt1963a_dropout_0a5_v': fact('renewal-ldos', 'fact-c459702-dropout-max-0a5', GU),
        'lt1963a_dropout_1a5_v': fact('renewal-ldos', 'fact-c459702-dropout-max-1a5', GU),
        'lt1963a_ground_1a5_a': fact('renewal-ldos', 'fact-c459702-ground-current-max-1a5', GU),
        'lt3015_dropout_1a5_v': fact('renewal-ldos', 'fact-c666306-dropout-max-1a5', GU),
        'lt3015_ground_1a5_a': fact('renewal-ldos', 'fact-c666306-ground-current-max-1a5', GU),
        'ldo_characterized_max_a': assumption(1.5, 'Highest load at which the retained LT1963A/LT3015 dropout and ground-current maxima exist; no retained number above it'),
        'ldo_theta_ja': {'value': None, 'class': 'UNAVAILABLE', 'source': 'renewal-ldos', 'conditions': 'LT1963A theta-JA unavailable; LT3015 14 C/W requires 2500 mm2 per side, versus about 293/253 mm2 fitted'},
        'tj_screen_c': assumption(TJ_SCREEN_C, 'Junction ceiling used by calculate-power-budget.py; not a retained LT1963A/LT3015 fact'),
        'ptc1_hold_25c_a': fact('ptc-smd1210p200tf-c20808', 'fact-ptc1b-ihold', G),
        'ptc2_hold_25c_a': fact('ptc-msmd110-33v-c70119', 'fact-ptc2-ihold', G),
        'ptc3_hold_25c_a': fact('ptc-bsmd1206-150-16v-c883133', 'fact-ptc3-ihold', G),
        'ptc3_hold_85c_a': fact('ptc-bsmd1206-150-16v-c883133', 'fact-ptc3-hold-85c', G),
        'ptc2_r1max_ohm': fact('ptc-msmd110-33v-c70119', 'fact-ptc2-r1max', G),
        'ptc3_r1max_ohm': fact('ptc-bsmd1206-150-16v-c883133', 'fact-ptc3-r1max', G),
        'j10_j11_contact_a': fact('dealon-dw254p-2x8-l0-c4749189', 'fact-dw254p-current', GU),
        'j5_contact_a': fact('xfcn-board-headers', 'fact-c2832269-current', G),
        'q1_rds_on_4v5_max': fact('umw-ao3401a-c347476', 'fact-umw-ao3401a-rdson', G),
    }


def v(ev, key):
    return ev[key]['value']


def bisect_max(ok, low=0.0, high=8.0, steps=60):
    if not ok(low):
        return 0.0
    if ok(high):
        return high
    for _ in range(steps):
        mid = (low + high) / 2
        low, high = (mid, high) if ok(mid) else (low, mid)
    return low


class Screen:
    def __init__(self):
        budget_path = ROOT/'manufacturing/power-budget.json'
        self.budget = json.loads(budget_path.read_text())
        spec_hash = hashlib.sha256((ROOT/'scripts/schgen/board_b_spec.py').read_bytes()).hexdigest()
        if self.budget['board_b_spec_sha256'] != spec_hash:
            raise ValueError('power-budget.json is stale against board_b_spec.py; regenerate it first')
        self.inverter = runpy.run_path(str(ROOT/'scripts/pcb/calculate-power-budget.py'))['inverter']
        self.ev = load_evidence()
        w = self.budget['whole_chain_current_thermal_screen']
        self.bands = {
            'plus12': {'pre': self.budget['positive_pre_regulator_screen']['bounds'], 'out_min': w['plus12_output_band_conditional']['minimum_v'], 'out_max': w['plus12_output_band_conditional']['maximum_v']},
            'plus5': {'pre': w['plus5_pre_hot_tolerance_bounds'], 'out_min': w['plus5_output_band_conditional']['minimum_v'], 'out_max': w['plus5_output_band_conditional']['maximum_v']},
            'minus12': {'pre': self.budget['negative_stage_scenarios'][3]['bounds'], 'out_min': w['minus12_output_band_conditional']['minimum_magnitude_v'], 'out_max': w['minus12_output_band_conditional']['maximum_magnitude_v']},
        }
        loads = w['ldo_output_loads_including_indicators_feedback_a']
        converter = w['converter_output_loads_with_ground_current_brackets_a']
        self.overhead = {rail: loads[rail] - TARGETS[rail] for rail in TARGETS}
        ground_bracket = {'plus12': .12, 'plus5': .12, 'minus12': .07 + .00013}
        self.divider = {rail: converter[rail] - loads[rail] - ground_bracket[rail] for rail in TARGETS}

    def ground(self, rail, ldo_out):
        # Same conservative 1.5 A-table brackets as power-budget.json; none exists above 1.5 A.
        if ldo_out > v(self.ev, 'ldo_characterized_max_a'):
            return None
        if rail == 'minus12':
            return v(self.ev, 'lt3015_ground_1a5_a') + .00013
        return v(self.ev, 'lt1963a_ground_1a5_a')

    def dropout(self, rail, ldo_out):
        if ldo_out > v(self.ev, 'ldo_characterized_max_a'):
            return None
        if rail == 'minus12':
            return v(self.ev, 'lt3015_dropout_1a5_v')
        return v(self.ev, 'lt1963a_dropout_0a5_v') if ldo_out <= .5 else v(self.ev, 'lt1963a_dropout_1a5_v')

    def buck_peak(self, vin, vout, iout, inductance, frequency, vsat, vf):
        duty = (vout + vf) / (vin - vsat + vf)
        ripple = (vin - vsat - vout) * duty / (inductance * frequency)
        return duty, ripple, iout + ripple / 2

    def rail(self, rail, external):
        ev, band = self.ev, self.bands[rail]
        ldo_out = external + self.overhead[rail]
        ground = self.ground(rail, ldo_out)
        dropout = self.dropout(rail, ldo_out)
        r = {'external_load_a': external, 'ldo_output_a': ldo_out, 'checks': {}}
        c = r['checks']
        c['ldo_characterized_current'] = {'limit_a': v(ev, 'ldo_characterized_max_a'), 'value_a': ldo_out,
                                          'status': 'PASS' if ground is not None else 'EXCEEDS_EVIDENCE',
                                          'class': 'GUARANTEED_UNSOURCED'}
        hold_key = {'plus12': 'ptc1_hold_25c_a', 'plus5': 'ptc2_hold_25c_a', 'minus12': 'ptc3_hold_25c_a'}[rail]
        c['ptc_hold_25c'] = {'limit_a': v(ev, hold_key), 'value_a': external, 'status': 'PASS' if external <= v(ev, hold_key) else 'FAIL', 'class': 'GUARANTEED'}
        if rail == 'minus12':
            hot = v(ev, 'ptc3_hold_85c_a')
            c['ptc_hold_85c'] = {'limit_a': hot, 'value_a': external, 'status': 'PASS' if external <= hot else 'FAIL', 'class': 'GUARANTEED'}
        else:
            c['ptc_hold_85c'] = {'status': 'NOT RUN', 'reason': '85 C hold current unavailable for this fitted PTC'}
        per_contact = external / 2  # worst case: one header carries the whole rail on its two pins
        c['j10_or_j11_single_header_contact'] = {'limit_a': v(ev, 'j10_j11_contact_a'), 'value_a': per_contact,
                                                 'status': 'PASS' if per_contact <= v(ev, 'j10_j11_contact_a') else 'FAIL', 'class': 'GUARANTEED_UNSOURCED'}
        if ground is None:
            r['status'] = 'EXCEEDS_EVIDENCE'
            r['note'] = 'LDO load above the highest retained characterization point; dropout, ground current and pre-regulator load cannot be screened'
            return r
        headroom = band['pre']['minimum_v'] - RIPPLE_ALLOWANCE_V - band['out_max']
        c['ldo_dropout'] = {'available_v': headroom, 'required_v': dropout, 'margin_v': headroom - dropout,
                            'status': 'PASS' if headroom >= dropout else 'FAIL', 'class': 'GUARANTEED_UNSOURCED',
                            'conditions': f'Conditional pre-rail minimum minus {RIPPLE_ALLOWANCE_V} V ripple allowance and maximum output band; wiring loss excluded'}
        dissipation = (band['pre']['maximum_v'] - band['out_min']) * ldo_out + band['pre']['maximum_v'] * ground
        c['ldo_thermal'] = {'dissipation_screen_w': dissipation,
                            'required_effective_theta_ja_c_per_w': (TJ_SCREEN_C - AMBIENT_C) / dissipation,
                            'status': 'NOT RUN', 'reason': 'Installed theta-JA unavailable; the value is the requirement at 40 C ambient and the 125 C project ceiling'}
        conv = ldo_out + ground + self.divider[rail]
        r['converter_output_a'] = conv
        r['pre_rail_power_w'] = band['pre']['maximum_v'] * conv
        if rail == 'plus12':
            c['u2_continuous'] = {'limit_a': v(ev, 'u2_continuous_a'), 'value_a': conv, 'status': 'PASS' if conv <= v(ev, 'u2_continuous_a') else 'FAIL', 'class': 'DESIGN_POINT'}
            lmin = v(ev, 'l1_inductance_uh') * (1 - v(ev, 'l1_tolerance')) * 1e-6
            vin = SCREEN_VIN[0]
            duty = min(band['pre']['maximum_v'] / vin, 1.0)
            ripple = (vin - band['pre']['maximum_v']) * duty / (lmin * v(ev, 'u2_frequency_khz') * 1e3)
            peak = conv + ripple / 2
            c['u2_peak_current_limit'] = {'limit_a': v(ev, 'u2_peak_limit_min_a'), 'value_a': peak, 'status': 'PASS' if peak <= v(ev, 'u2_peak_limit_min_a') else 'FAIL', 'class': 'GUARANTEED',
                                          'conditions': '14 V input, minimum inductance, typical 500 kHz; ripple is small near 100% duty'}
            drop = conv * (v(ev, 'u2_rds_on_ohm') + v(ev, 'l1_dcr_max_ohm'))
            c['u2_low_line_headroom_14v'] = {'available_v': vin - band['pre']['maximum_v'], 'typical_path_drop_v': drop,
                                             'margin_v': vin - band['pre']['maximum_v'] - drop,
                                             'status': 'PASS' if vin - band['pre']['maximum_v'] >= drop else 'FAIL', 'class': 'TYPICAL',
                                             'conditions': 'Typical high-side RDS(on) plus maximum L1 DCR; no guaranteed AP63201 dropout exists'}
        elif rail == 'plus5':
            duty, ripple, peak = self.buck_peak(SCREEN_VIN[0], band['pre']['maximum_v'], conv, v(ev, 'l23_inductance_min_h'),
                                                v(ev, 'lm2596_frequency_min_hz'), v(ev, 'lm2596_vsat_screen_v'), v(ev, 'd2_vf_max_v'))
            limit = v(ev, 'lm2596_switch_limit_min_a')
            c['u3_switch_current_limit'] = {'limit_a': limit, 'value_a': peak, 'status': 'PASS' if peak <= limit else 'FAIL', 'class': 'PROJECT_ASSUMPTION'}
            diode = conv * (1 - duty)
            c['d2_average_current'] = {'limit_a': v(ev, 'd2_if_avg_a'), 'value_a': diode, 'status': 'PASS' if diode <= v(ev, 'd2_if_avg_a') else 'FAIL', 'class': 'GUARANTEED'}
            r['converter_model'] = {'duty': duty, 'ripple_pp_a': ripple, 'peak_a': peak}
        else:
            model = self.inverter(SCREEN_VIN[0], band['pre']['maximum_v'], conv, v(ev, 'd3_vf_max_v'))
            peak = model['inductor_peak_a']
            limit = v(ev, 'lm2596_switch_limit_min_a')
            c['u4_switch_current_limit'] = {'limit_a': limit, 'value_a': peak, 'status': 'PASS' if peak <= limit else 'FAIL', 'class': 'PROJECT_ASSUMPTION'}
            c['l3_heat_rating'] = {'limit_a': v(ev, 'l23_idc_a'), 'value_a': model['inductor_rms_a'], 'status': 'PASS' if model['inductor_rms_a'] <= v(ev, 'l23_idc_a') else 'FAIL', 'class': 'DESIGN_POINT'}
            c['d3_average_current'] = {'limit_a': v(ev, 'd3_if_avg_a'), 'value_a': conv, 'status': 'PASS' if conv <= v(ev, 'd3_if_avg_a') else 'FAIL', 'class': 'GUARANTEED'}
            r['converter_model'] = {k: model[k] for k in ('duty_cycle', 'inductor_average_a', 'inductor_peak_a', 'inductor_rms_a', 'modeled_conduction_efficiency')}
        statuses = {x.get('status') for x in c.values()}
        r['status'] = 'FAIL' if 'FAIL' in statuses else 'PASS_SCREEN'
        return r

    def evaluate(self, loads):
        rails = {rail: self.rail(rail, loads[rail]) for rail in TARGETS}
        result = {'external_loads_a': loads, 'output_power_w': 12*loads['plus12'] + 12*loads['minus12'] + 5*loads['plus5'], 'rails': rails}
        # Optimistic floor: external load only at the minimum pre-rail voltage, with no indicator,
        # divider or ground current. Any real chain needs at least this converter output power.
        floor = sum(self.bands[rail]['pre']['minimum_v'] * loads[rail] for rail in TARGETS)
        floor_required = {f'{vin:g}V': floor / (vin * PD_CURRENT_A) for vin in SCREEN_VIN}
        result['pre_rail_power_floor'] = {'power_w': floor, 'required_weighted_converter_efficiency_at_3a': floor_required,
                                          'status': 'INFEASIBLE' if floor_required['15V'] > 1 else 'NOT RUN'}
        if any('pre_rail_power_w' not in r for r in rails.values()):
            result['input'] = {'status': 'NOT RUN', 'reason': 'At least one LDO exceeds its retained characterization; only the optimistic pre-rail floor is available'}
            result['status'] = 'EXCEEDS_EVIDENCE'
            return result
        total = sum(r['pre_rail_power_w'] for r in rails.values())
        required = {f'{vin:g}V': total / (vin * PD_CURRENT_A) for vin in SCREEN_VIN}
        result['input'] = {
            'pre_rail_power_w': total,
            'required_weighted_converter_efficiency_at_3a': required,
            'status': 'INFEASIBLE' if required['15V'] > 1 else 'NOT RUN',
            'reason': 'Converter efficiencies are unavailable; feasibility needs the listed efficiency at the PD 3 A contract. Above 1.0 no converter efficiency can close it.',
        }
        statuses = {r['status'] for r in rails.values()}
        result['status'] = 'INFEASIBLE' if result['input']['status'] == 'INFEASIBLE' else ('FAIL' if 'FAIL' in statuses else 'PASS_SCREEN_EFFICIENCY_OPEN')
        return result

    def rail_limits(self):
        """Largest external current per rail, other rails at their PD targets, under each separate limit."""
        out = {}
        for rail in TARGETS:
            def under(check):
                def ok(current):
                    loads = dict(TARGETS, **{rail: current})
                    item = self.evaluate(loads)['rails'][rail]['checks'].get(check)
                    return item is not None and item.get('status') == 'PASS'
                return ok
            checks = self.evaluate(dict(TARGETS))['rails'][rail]['checks']
            ceiling = round(bisect_max(under('ldo_characterized_current')), 4)
            out[rail] = {}
            for name, item in checks.items():
                if item.get('status') not in ('PASS', 'FAIL'):
                    continue
                limit = round(bisect_max(under(name)), 4)
                # Checks downstream of the LDO cannot be evaluated above its retained characterization.
                masked = name != 'ldo_characterized_current' and limit >= ceiling and 'ptc' not in name and 'header' not in name
                out[rail][name] = f'>={ceiling} (not evaluable above LDO evidence)' if masked else limit
            for efficiency in (1.0, .85):
                def ok(current, efficiency=efficiency):
                    result = self.evaluate(dict(TARGETS, **{rail: current}))
                    return 'pre_rail_power_w' in result['input'] and result['input']['required_weighted_converter_efficiency_at_3a']['14V'] <= efficiency
                limit = round(bisect_max(ok), 4)
                key = f'input_42w_at_14v_3a_with_weighted_efficiency_{efficiency:g}'
                out[rail][key] = f'>={ceiling} (not evaluable above LDO evidence)' if limit >= ceiling else limit
        return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--output', type=Path, default=ROOT/'manufacturing/supply-capability.json')
    parser.add_argument('--load', action='append', default=[], metavar='NAME=I12,IM12,I5',
                        help='Evaluate an extra external load point (A) and print it; not written to --output')
    args = parser.parse_args()
    screen = Screen()
    if args.load:
        for item in args.load:
            name, values = item.split('=')
            i12, im12, i5 = (float(x) for x in values.split(','))
            print(json.dumps({'name': name, **screen.evaluate({'plus12': i12, 'minus12': im12, 'plus5': i5})}, indent=2))
        return
    data = {
        'schema_version': 1,
        'status': 'SCREENING ARITHMETIC ONLY: no simulation, bench, thermal or startup measurement exists for the renewal boards',
        'input_contract': {'pdo_v': 15, 'pdo_a': PD_CURRENT_A, 'power_w': 45, 'screen_board_input_v': list(SCREEN_VIN), '20v': 'unsupported'},
        'pd_target_evaluation': screen.evaluate(dict(TARGETS)),
        'per_rail_limits_other_rails_at_targets_a': screen.rail_limits(),
        'evidence': screen.ev,
        'open_items': [
            'Converter efficiencies (U2/U3/U4) are unavailable; the input budget is a required-efficiency statement, not a pass.',
            'LT1963A/LT3015 current limit, theta-JA (as fitted), thermal shutdown and Tj maximum are unavailable; thermal checks are NOT RUN.',
            'LDO loads above 1.5 A have no retained dropout or ground-current data and are reported as EXCEEDS_EVIDENCE.',
            'LM2596 inverting startup can draw about 4.5 A for at least 2 ms against the 3 A PD contract (rules.json inverting-startup-vs-pd-source).',
            'PTC1/PTC2 hold current above 25 C is unavailable; PTC3 holds 0.77 A at 85 C.',
            'Single-header contact screen assumes one J10/J11 header carries a whole rail; harness distribution is not modeled.',
        ],
        'source_generator': 'scripts/pcb/calculate-supply-capability.py',
        'power_budget_sha256': hashlib.sha256((ROOT/'manufacturing/power-budget.json').read_bytes()).hexdigest(),
        'board_b_spec_sha256': screen.budget['board_b_spec_sha256'],
    }
    args.output.write_text(json.dumps(data, indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
