#!/usr/bin/env python3
"""Reproduce renewal electrical screening; no simulation or bench qualification."""
import argparse
import hashlib
import json
import math
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts/schgen'))
from sexp import atom, find_all, load


def require_pcb_part(board, reference, expected_lcsc):
    path = ROOT/'boards'/board/(board+'.kicad_pcb')
    found = []
    for footprint in find_all(load(path), 'footprint'):
        properties = {atom(item[1]): atom(item[2]) for item in find_all(footprint, 'property')}
        if properties.get('Reference') == reference:
            found.append(properties.get('LCSC'))
    if found != [expected_lcsc]:
        raise ValueError(f'{board}/{reference}: current PCB must contain {expected_lcsc} before calculating')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def divider(top, bottom, tolerance):
    return {
        'minimum_v': 1.18 * (1 + top * (1 - tolerance) / (bottom * (1 + tolerance))),
        'nominal_v': 1.23 * (1 + top / bottom),
        'maximum_v': 1.28 * (1 + top * (1 + tolerance) / (bottom * (1 - tolerance))),
    }


def inverter(vin, vout, iout, vf):
    # Approximate CCM volt-second/charge balance including 25C winding DCR.
    # z=1-D: (A+B)*z^2-A*z+Iout*R=0, A=Vin-Vsat, B=|Vout|+Vf.
    vsat, inductance, frequency, dcr = 1.5, 80e-6, 117000, 0.185
    a, b = vin - vsat, vout + vf
    discriminant = a*a - 4*(a+b)*iout*dcr
    if a <= 0 or discriminant <= 0:
        raise ValueError('No feasible low-current CCM solution in this screen')
    off_fraction = (a + math.sqrt(discriminant)) / (2*(a+b))
    duty = 1 - off_fraction
    average = iout / off_fraction
    ripple = (a - average*dcr) * duty / (inductance * frequency)
    rms = math.sqrt(average**2 + ripple**2 / 12)
    copper_loss = rms**2 * dcr
    switch_loss, diode_loss = vsat * average * duty, vf * iout
    modeled_input_power = vout*iout + copper_loss + switch_loss + diode_loss
    return {
        'vin_v': vin, 'vout_magnitude_v': vout, 'output_current_a': iout,
        'duty_cycle': duty, 'inductor_average_a': average,
        'inductor_ripple_pp_a': ripple, 'inductor_peak_a': average + ripple / 2,
        'inductor_rms_a': rms, 'inductor_copper_loss_w_at_25c_max_dcr': copper_loss,
        'switch_conduction_loss_w': switch_loss,
        'diode_conduction_loss_w': diode_loss,
        'input_current_charge_balance_a': duty * average,
        'input_current_including_ripple_copper_loss_a': modeled_input_power/vin,
        'modeled_input_power_w': modeled_input_power,
        'modeled_conduction_efficiency': vout*iout/modeled_input_power,
        'model_limits': '25C DCR and diode maximum at 5A/25C are screening assumptions at this waveform, not a full-temperature guarantee. Switching/core/quiescent/hot-copper/reverse-leakage losses and parasitic overshoot are omitted; predicted input current is not an upper bound.',
        'minimum_switch_current_limit_margin_a': 3.4 - average - ripple / 2,
        'inductor_heat_rating_margin_a': 4.5 - rms,
        'inductor_saturation_rating_margin_a': 8.5 - average - ripple / 2,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'manufacturing/power-budget.json')
    args = parser.parse_args()
    protection_path = ROOT/'.claude/skills/component-renewal-input-protection/facts.json'
    protection_facts = {fact['fact_id']: fact for fact in json.loads(protection_path.read_text())['facts']}
    vf_fact = protection_facts['fact-c3024223-vf-max-5a-25c']
    vf = vf_fact['value']
    clamp = protection_facts['fact-c74561-clamp']['value']
    diode_reverse = protection_facts['fact-c3024223-vrrm']['value']
    standoff = protection_facts['fact-c74561-standoff']['value']
    ldo_facts = {fact['fact_id']: fact for fact in json.loads((ROOT/'.claude/skills/component-renewal-ldos/facts.json').read_text())['facts']}
    negative_reference = ldo_facts['fact-c666306-reference-band']['value']
    negative_bias_a = ldo_facts['fact-c666306-adj-bias-max']['value']['max'] * 1e-9
    negative_dropout = ldo_facts['fact-c666306-dropout-max-1a5']['value']
    negative_top, negative_bottom, negative_resistor_hot_tolerance = 8200 + 680, 1000, .0035
    # Adjustable LT3015: |VOUT| = |VADJ| * (1 + Rtop/Rbottom) +/- IADJ * Rtop; the bias limit is a 25 C-only figure.
    out_negative = {
        'minimum_magnitude_v': -negative_reference['max'] * (1 + negative_top * (1 - negative_resistor_hot_tolerance) / (negative_bottom * (1 + negative_resistor_hot_tolerance))) - negative_bias_a * negative_top * (1 + negative_resistor_hot_tolerance),
        'nominal_magnitude_v': 1.22 * (1 + negative_top / negative_bottom),
        'maximum_magnitude_v': -negative_reference['min'] * (1 + negative_top * (1 + negative_resistor_hot_tolerance) / (negative_bottom * (1 - negative_resistor_hot_tolerance))) + negative_bias_a * negative_top * (1 + negative_resistor_hot_tolerance),
        'divider': {'top_refs': ['R26', 'R27'], 'top_ohm': negative_top, 'bottom_ref': 'R28', 'bottom_ohm': negative_bottom, 'tolerance_plus_tcr_fraction': negative_resistor_hot_tolerance},
        'conditions': 'Full-temperature ADJ reference band with opposed 0.35% resistor tolerance/TCR and the 25°C-only 200 nA ADJ-bias limit; not a guaranteed full-temperature output band.',
    }
    scenarios = []
    for top, tolerance in [(10600, .01), (10500, .001), (10600, .001), (10500, .0035)]:
        bounds = divider(top, 1000, tolerance)
        high = bounds['maximum_v']
        pass_loss = (high - out_negative['minimum_magnitude_v']) * .8
        # 70 mA is a published 1.5 A/dropout test maximum, not an interpolated
        # guaranteed 0.8 A normal-operation value. Both cases stay explicitly open.
        ground_loss_screen = high * .07
        thermal_screen = pass_loss + ground_loss_screen
        scenarios.append({
            'divider_top_ohm': top, 'divider_bottom_ohm': 1000,
            'resistor_tolerance_fraction': tolerance, 'bounds': bounds,
            'resistor_temperature_note': '0.35% combines initial 0.1% and 25 ppm/°C over 100 °C; other rows use initial tolerance only' if tolerance == .0035 else 'Initial tolerance only; see combined TCR case for hot-operation screening',
            'formula': 'Vref * (1 + Rtop/Rbottom); reference 1.18/1.23/1.28 V, resistor extrema opposed',
            'reference_conditions': 'UMW LM2596S-ADJ full-temperature limits; reference test at VOUT=3V, 0.2..3A load; application regulation/ripple still requires verification',
            'headroom_to_max_programmed_output_plus_dropout_v': bounds['minimum_v'] - out_negative['maximum_magnitude_v'] - negative_dropout,
            'negative_ldo_pass_loss_w': pass_loss,
            'negative_ldo_ground_loss_screen_w': ground_loss_screen,
            'negative_ldo_total_thermal_screen_w': thermal_screen,
            'maximum_effective_theta_ja_at40c_ambient_c_per_w': (125 - 40) / thermal_screen,
            'thermal_status': 'SCREENING ONLY: 70 mA is the 1.5 A/dropout test-point bound, not a guaranteed interpolated 0.8 A normal-operation value; copper/coupling/ambient validation open',
            'inductor_screen_load_only': inverter(14, high, .8, vf),
            'inductor_screen_with_ground_current_bracket': inverter(14, high, .8 + .07 + .00013 + high/(top + 1000), vf),
            'normal_high_line_effective_voltage_v': 15.75 + high,
            'normal_high_line_u4_operating_margin_v': 40 - (15.75 + high),
            'normal_high_line_d3_vrrm_margin_v': diode_reverse - (15.75 + high),
            'tvs_table_point_effective_voltage_v': clamp + high,
            'tvs_table_point_u4_absmax_margin_v': 45 - (clamp + high),
            'tvs_table_point_d3_vrrm_margin_v': diode_reverse - (clamp + high),
            'tvs_table_point_c9_50v_margin_v': 50 - (clamp + high),
            'nominal_output_capacitor_energy_j': .5 * 1410e-6 * bounds['nominal_v']**2,
        })
    spec = runpy.run_path(str(ROOT / 'scripts/schgen/board_b_spec.py'))
    pd_spec = runpy.run_path(str(ROOT / 'scripts/schgen/board_p_spec.py'))
    if spec['COMPONENTS']['D3'][2] != 'C3024223' or pd_spec['COMPONENTS']['D5'][2] != 'C74561':
        raise ValueError('Protection screen requires the selected D3/D5 identities in both current specs')
    protected_pcbs = {'board-b': require_pcb_part('board-b','D3','C3024223'),
                      'board-p': require_pcb_part('board-p','D5','C74561')}
    selected_negative = {
        'top': {'ref': 'R5', 'mpn': 'RT0603BRD0710K5L', 'lcsc': 'C861077', 'resistance_ohm': 10500, 'tolerance_fraction': .001},
        'bottom': {'ref': 'R6', 'mpn': 'RT0603BRD071KL', 'lcsc': 'C110776', 'resistance_ohm': 1000, 'tolerance_fraction': .001},
        'initial_tolerance_scenario_index': 1,
        'temperature_screen_scenario_index': 3,
        'tcr_assumption_ppm_per_c': 25,
        'maximum_delta_from25c': 100,
        'spec_identity_matches': spec['COMPONENTS']['R5'][2] == 'C861077' and spec['COMPONENTS']['R6'][2] == 'C110776',
    }
    five_pre = divider(4300, 1000, .01)
    positive_pre = {'minimum_v': .792 * (1 + 15.8 * (1 - .00425) / (1 + .002625)), 'nominal_v': .8 * 16.8, 'maximum_v': .808 * (1 + 15.8 * (1 + .00425) / (1 - .002625))}
    # Wider rail/load cases include fitted indicator and feedback overhead.
    resistor_hot_tolerance = .0035
    def adjusted_output(top):
        low = 1.174 * (1 + top * (1 - resistor_hot_tolerance) / (1000 * (1 + resistor_hot_tolerance)))
        high = 1.246 * (1 + top * (1 + resistor_hot_tolerance) / (1000 * (1 - resistor_hot_tolerance))) + 10e-6 * top * (1 + resistor_hot_tolerance)
        return {'minimum_v': low, 'maximum_v': high, 'conditions': 'Full-temperature reference and resistor/TCR screen combined with a 25°C-only 10µA ADJ-bias ceiling and assumed nonnegative bias; not a guaranteed full-temperature output band.'}
    out12, out5 = adjusted_output(8200 + 680), adjusted_output(3090 + 33)
    pre5_hot = divider(4300, 1000, .02)
    pre_negative_hot = scenarios[3]['bounds']
    led12, led5, led_negative = out12['maximum_v']/980, out5['maximum_v']/980, out_negative['maximum_magnitude_v']/980
    load12 = 1.2 + led12 + 1.246 / (1000 * (1 - resistor_hot_tolerance))
    load5 = .5 + led5 + 1.246 / (1000 * (1 - resistor_hot_tolerance))
    load_negative = .8 + led_negative + out_negative['maximum_magnitude_v'] / (negative_top + negative_bottom)
    input12 = load12 + .12 + positive_pre['maximum_v']/(168000 * .997375)
    input5 = load5 + .12 + pre5_hot['maximum_v']/(5300 * .98)  # conservative 1.5 A table bracket; fitted load exceeds 0.5 A
    input_negative = load_negative + .07 + .00013 + pre_negative_hot['maximum_v']/(11500 * .9965)
    stage_power12 = positive_pre['maximum_v'] * input12
    stage_power5 = pre5_hot['maximum_v'] * input5
    stage_power_negative = pre_negative_hot['maximum_v'] * input_negative
    stage_total = stage_power12 + stage_power5 + stage_power_negative
    thermal12 = (positive_pre['maximum_v'] - out12['minimum_v']) * load12 + positive_pre['maximum_v'] * .12
    thermal5 = (pre5_hot['maximum_v'] - out5['minimum_v']) * load5 + pre5_hot['maximum_v'] * .12
    thermal_negative = (pre_negative_hot['maximum_v'] - out_negative['minimum_magnitude_v']) * load_negative + pre_negative_hot['maximum_v'] * .07
    negative_screens = [inverter(vin,pre_negative_hot['maximum_v'],input_negative,vf) for vin in (14,14.25,15,15.75)]
    for screen in negative_screens:
        remaining = screen['vin_v']*3 - screen['modeled_input_power_w']
        screen['remaining_positive_converter_input_budget_w'] = remaining
        screen['minimum_positive_weighted_efficiency_for_3a_screen'] = (stage_power12+stage_power5)/remaining
    data = {
        'schema_version': 1,
        'status': '15V-ONLY RENEWAL PROTOTYPE SCREEN; selected parts and conditioned margins are not full-chain qualification',
        'selected_negative_divider': selected_negative,
        'positive_pre_regulator_screen': {'selected_converter':'AP63201', 'selected_lcsc':'C2071044', 'top_ohm':158000, 'bottom_ohm':10000, 'top_tolerance_plus_tcr_fraction':.00425, 'bottom_tolerance_plus_tcr_fraction':.002625, 'temperature_delta_c':65, 'reference_bounds_v':[.792,.808], 'bounds':positive_pre, 'screening_vin_after_front_end_v':14, 'minimum_high_duty_drop_allowance_v':14-positive_pre['maximum_v'], 'status':'Reference/resistor/TCR screen only; real high-duty operation, switch+inductor voltage drop, capacitor DC-bias derating, ripple and low-line behavior require exact-part evidence and qualification'},
        'five_volt_pre_regulator_screen': {'selected_r3_lcsc':'C23159', 'r3_ohm':4300, 'r4_ohm':1000, 'tolerance_fraction':.01, 'bounds':five_pre, 'spec_identity_matches':spec['COMPONENTS']['R3'][2] == 'C23159', 'maximum_ldo_pass_loss_w_assuming_output_min4v8':(five_pre['maximum_v'] - 4.8) * .5, 'status':'Initial-tolerance upstream screen; the whole-chain section includes wider TCR and conditional LT1963A reference/divider/bias output bounds. Actual ripple and full-temperature behavior remain open.'},
        'rated_targets': {'plus12': {'voltage_v':12,'current_a':1.2}, 'minus12': {'voltage_v':-12,'current_a':.8}, 'plus5': {'voltage_v':5,'current_a':.5}},
        'nominal_output_power_w': 26.5,
        'whole_chain_current_thermal_screen': {
            'plus12_output_band_conditional':out12, 'plus5_output_band_conditional':out5, 'minus12_output_band_conditional':out_negative,
            'plus5_pre_hot_tolerance_bounds':pre5_hot,
            'led_current_upper_bounds_a':{'plus12':led12,'plus5':led5,'minus12':led_negative},
            'led_assumption':'Zero LED forward drop and 1 kΩ resistor at 980 Ω deliberately overestimate indicator current; includes initial 1% plus 100 ppm/°C over 100°C.',
            'ldo_output_loads_including_indicators_feedback_a':{'plus12':load12,'plus5':load5,'minus12':load_negative},
            'converter_output_loads_with_ground_current_brackets_a':{'plus12':input12,'plus5':input5,'minus12':input_negative},
            'pre_regulator_power_w':{'plus12':stage_power12,'plus5':stage_power5,'minus12':stage_power_negative,'total':stage_total},
            'minimum_weighted_converter_efficiency_at14v_3a':stage_total/(14*3),
            'ldo_dissipation_screen_w':{'plus12':thermal12,'plus5':thermal5,'minus12':thermal_negative},
            'maximum_effective_theta_ja_at40c_ambient_c_per_w':{'plus12':85/thermal12,'plus5':85/thermal5,'minus12':85/thermal_negative},
            'negative_inductor_screen_with_all_overhead':inverter(14,pre_negative_hot['maximum_v'],input_negative,vf),
            'negative_input_screens': negative_screens,
            'status':'Conservative screening cases, not simultaneous guaranteed worst cases. Positive IADJ only bounded at 25°C; higher-load ground-current brackets are not exact target-load maxima. Converter switching/core/hot-resistance losses and actual source/board minimum voltage still require validation.'},
        'pd_contract': {'nominal_v':15,'current_a':3,'nominal_power_w':45,'minus5pct_source_power_w':42.75,'normal_source_range_v':[14.25,15.75],'scope':'Prototype permits 15V ±5% normal source input only; the 14V B-input loss screen is separate. 20V is unsupported, including accidental factory-NVM negotiation.','first_power':'Mandatory current-limited 5V-only source with B disconnected; resolve programming-jig voltage/pull-up load, program and read back the 15V-only NVM policy before using any 15V-capable PD source.'},
        'negative_stage_scenarios': scenarios,
        'inductor_screen_assumptions': {'vin_after_front_end_v':14,'minimum_l_h':80e-6,'minimum_frequency_hz':117000,'switch_saturation_v':1.5,'diode_forward_v':vf,'diode_forward_fact':vf_fact,'max_dcr_25c_ohm':.185,'heat_rating_a':4.5,'saturation_rating_a':8.5,'notes':'Approximate CCM including average winding DCR in duty balance and ripple copper loss in input power. Hot DCR, magnetic bias, switching/core/quiescent losses, PCB parasitics, component test-point conditions, and actual input minima remain open.'},
        'thermal_layout_requirement': {'historical_proposal_u8_copper_mm2_each_side':1280,'historical_expansion_goal_mm2':2500,'status':'Use current source-locked filled areas below; historical proposals are not achieved-area claims. Effective theta-JA is not inferred from area alone.','lt3015_ddpak_published_test_conditions':{'top2500_back2500_mm2_theta_ja':14,'top1000_back2500_mm2_theta_ja':16,'top225_back2500_mm2_theta_ja':19,'board_area_mm2':2500}},
        'capacitor_requirements': {'lt3015_output':{'minimum_effective_uf':10,'maximum_esr_ohm':.5},'lt1963a_output':{'minimum_effective_uf':10,'maximum_esr_ohm':3},'status':'Selected polymer parts have component evidence; installed effective capacitance/ESR over temperature and load-step stability remain qualification requirements.'},
        'open_qualification': [
            'AP63201 full high-duty low-line behavior, actual path voltage drop and final whole-chain input-current budget.',
            'Negative LM2596 startup may reach about 4.5 A for at least 2 ms versus 3 A PD contract; steady-state margins do not prove startup.',
            'SMAJ16A 26V is a 15.4A,10/1000us,25C table point, not a universal hot or installed-surge ceiling. Source/rail/switch/gate waveforms, clamp current and temperature remain unqualified; VBR temperature coefficient is not a VC correction formula.',
            'Mandatory 5V-only first power/programming with B disconnected, then verified 15V-only NVM image/readback/reload before a PD-capable source; 20V unsupported. Resolve VREG_2V7 programming pull-up loading.',
            'Actual thermal copper, heatsinking, ambient, coupled regulator losses, and full-load temperatures.',
            'Converter reference tolerance, ripple, inductor current waveform, and LDO output-capacitor ESR/stability.',
            'New D3 hot reverse leakage: maximum0.5mA at60V/25C and typical50mA at60V/125C do not provide a guaranteed leakage bound at the installed hot reverse waveform. Reverse-leakage heating is not included in the conduction model.',
            'PTC hot hold-current, output rail drop and fault trip/recovery tests.',
        ],
        'evidence': [
            {'owner':'component-lm2596s-adj-c347423','fact_ids':['fact-lm2596-fb-vref-min-full-temp','fact-lm2596-fb-vref-max-full-temp','fact-lm2596-current-limit','fact-lm2596-vsat-max','fact-lm2596-oscillator-frequency','fact-lm2596-inverting-startup-current']},
            {'owner':'component-cya1265-100uh-c19268674','fact_ids':['fact-cya1265-inductance','fact-cya1265-isat','fact-cya1265-idc-heat-rating','fact-cya1265-rdc-max']},
            {'owner':'component-ss34-c8678','scope':'Retained B D2 and retired old D3 comparison only','fact_ids':['fact-ss34-vrrm','fact-ss34-vf']},
            {'owner':'component-renewal-input-protection','fact_ids':['fact-c74561-standoff','fact-c74561-clamp','fact-c74561-vbr-tempco-typ','fact-c3024223-vrrm','fact-c3024223-vf-max-5a-25c','fact-c3024223-vf-max-5a-125c','fact-c3024223-leakage-max-25c','fact-c3024223-leakage-typ-125c']},
            {'url':'https://www.analog.com/media/en/technical-documentation/data-sheets/3015fb.pdf','locator':'printed pages 5, 16, 19: output guarantee/dropout/GND current, COUT ESR, DD-Pak thermal test boards','retrieved':'2026-09-20'},
            {'url':'https://www.analog.com/media/en/technical-documentation/data-sheets/1963aff.pdf','locator':'printed pages 14-15: output capacitor minimum and ESR; high-output-voltage minimum ESR','retrieved':'2026-09-20'},
        ],
        'source_generator': 'scripts/pcb/calculate-power-budget.py',
        'board_b_spec_sha256': hashlib.sha256((ROOT/'scripts/schgen/board_b_spec.py').read_bytes()).hexdigest(),
        'board_p_spec_sha256': hashlib.sha256((ROOT/'scripts/schgen/board_p_spec.py').read_bytes()).hexdigest(),
        'protection_pcb_source_sha256': protected_pcbs,
    }
    negative_high = pre_negative_hot['maximum_v']
    effective = clamp + negative_high
    data['input_protection_screen'] = {
        'selected_p_tvs': {'mpn':'SMAJ16A','lcsc':'C74561','standoff_v':standoff,'conditioned_clamp_v':clamp,'conditions':protection_facts['fact-c74561-clamp']['conditions']},
        'selected_b_d3': {'mpn':'SDT5A60SA-13','lcsc':'C3024223','reverse_rating_v':diode_reverse,'vf_screen_v':vf,'vf_conditions':vf_fact['conditions']},
        'normal_input_high_v':15.75, 'standoff_margin_over_normal_high_v':standoff-15.75,
        'negative_rail_hot_tcr_max_v':negative_high, 'conditioned_effective_u4_d3_c9_v':effective,
        'conditioned_margins_v':{'stusb_28v_abs':28-clamp,'q1_30v_vds_magnitude':30-clamp,'u4_45v_abs':45-effective,'u4_40v_operating':40-effective,'d3_60v_reverse':diode_reverse-effective,'c9_50v_bridge':50-effective,'35v_input_capacitors':35-clamp,'50v_input_capacitors':50-clamp},
        'ideal_q1_gate_vgs_v':-clamp*100000/(100000+150000),
        'q1_comparison_conditions':'VDS comparison assumes off-state output near0V; VGS assumes asserted VBEN near0V and the ideal100k/150k steady divider. Neither is a measured transient gate/drain/source waveform.',
        'status':'Conditioned arithmetic clears the listed absolute/rated limits. U4 operating range is not maintained at this table point; regulation and survival of a real transient are not certified. STUSB limit retains its mirror-source trust limitation.',
        'diode_hot_reverse_leakage_note':'0.5mA is a maximum at60V/25C;50mA at60V/125C is typical only. Neither is an established installed hot leakage limit, and the forward-conduction model excludes reverse-leakage heating.',
        'retired_comparison':{'status':'RETIRED: old P SMAJ20A and B SS34 comparison, not the fitted protection pair','clamp_v':32.4,'old_d3_reverse_v':40,'effective_nominal_negative_v':32.4+14.145,'u4_abs_margin_at_nominal_v':45-32.4-14.145,'old_d3_margin_at_nominal_v':40-32.4-14.145},
    }
    layout_path = ROOT/'manufacturing/power-layout.json'
    if not layout_path.is_file():
        raise ValueError('A current power-layout.json is required before writing the power-budget report')
    if layout_path.is_file():
        layout = json.loads(layout_path.read_text())
        board_hash = hashlib.sha256((ROOT/'boards/board-b/board-b.kicad_pcb').read_bytes()).hexdigest()
        if layout.get('status') != 'PASS' or layout.get('pcb_sha256') != board_hash:
            raise ValueError('Re-run verify-power-layout.py on the final filled Board B before calculating')
        data['actual_filled_copper'] = {
            'pcb_sha256': board_hash,
            'negative_zones': layout['negative_filled_zone_areas'],
            'ground_zone_areas_mm2': layout['ground_filled_zone_areas_mm2'],
            'report': 'power-layout.json',
            'limitation': 'Filled area and connected vias are geometry evidence, not measured thermal resistance or current capacity.',
        }
    out = args.output;out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,indent=2)+'\n')
    print(out)


if __name__ == '__main__':
    main()
