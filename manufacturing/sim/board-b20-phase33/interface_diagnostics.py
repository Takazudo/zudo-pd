"""PD20 interface diagnostics for the open D1-D3 pre-order questions (#235, #243).

Arithmetic and source-binding only. Nothing here runs a circuit simulation, qualifies an
installed board or relaxes a contract value. Every assumption is labelled; a quantity
without a retained bound is reported as OPEN/UNSOURCED instead of being invented.

usage: python3 interface_diagnostics.py [--output PATH] [--check PATH]
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCHEMATIC = ROOT / 'boards/board-b20-draft/board-b20-draft.kicad_sch'
DECK = HERE / 'tracking/nom.cir'
CALCULATOR = ROOT / 'scripts/pcb/calculate-board-b20-draft.py'
OPEN, UNSOURCED, SUPPORTED, REFUTED, UNRESOLVED = 'OPEN', 'UNSOURCED', 'SUPPORTED', 'REFUTED', 'UNRESOLVED'

# CONTRACT/CALCULATED voltage forms from the canonical interface (OSC 433c88b, pd-interface-20v.md §3/§5)
P12_WHILE_M12_ABSENT_MAX = 0.5    # +12 V alone (R-VEE, CALCULATED A1)
M12_WHILE_P12_ABSENT_MAX = 6.0    # |-12 V| alone (R-VEE, CALCULATED A1)
ADG_OTHER_RAIL_MIN = 8.0          # R-ADG: one analog rail absent, the other >= 8 V
P5_HOLD_MAX = 0.8                 # R-ADG: +5 V above 0.8 V is the hazard term
SCREEN_ANALOG_MIN = 1.5           # definition 1 sufficient screen: +5 <= 0.8 V until both |analog| > 1.5 V

REFINEMENT = HERE / 'startup-refinement-20261109.json'
EXECUTION = HERE / 'execution-20261110.json'
D1_REFERENCE = HERE / 'd1-reference-20261111.json'
FAILED_PEAKS = {'+5': 'nom', '-12': 'adv'}  # rail -> case holding the recorded failed condition
# Annotated schematic reference of each discharge resistor (builder name RXN is renumbered)
DISCHARGE_REFS = {'+12': 'RX12', '+5': 'RX5', '-12': 'R76'}

# Modeled subsystem -> annotated generated-schematic references (builder names such as RXN/CDH are renumbered) -> phase33 deck elements (empty = omitted).
MODEL_SCOPE = [
    {'subsystem': 'Converters U1/U2/U3, LC post-filters and servo injection U4/U5',
     'refs': ['U1', 'U2', 'U3', 'U4', 'U5', 'L1', 'L2'], 'deck': ['VP12', 'VP5', 'VM12', 'RP12S', 'CP12'],
     'modeled_as': 'stiff sources behind 20 mOhm and 57 uF',
     'omitted': 'switching, current limit, servo dynamics and pre-node droop under load steps'},
    {'subsystem': 'Shunts RSH1/RSH2/RSH3', 'refs': ['RSH1', 'RSH2', 'RSH3'], 'deck': ['RSH12', 'RSH5', 'RSHN'],
     'modeled_as': 'drawn resistances', 'omitted': 'none at DC'},
    {'subsystem': 'Tracking amplifiers, pre-bias and back-to-back pairs', 'refs': ['U13', 'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6', 'DZ1', 'Q59'],
     'deck': ['XU13A', 'XU13B', 'XU9B', 'XQ1', 'XQ2', 'XQ5', 'DZ1', 'DP12'],
     'modeled_as': 'vendor OPAx187 and CSD18543Q3A models; pre-bias diodes as DBODY',
     'omitted': 'BSS138 pre-bias device physics; model accuracy is not established'},
    {'subsystem': 'Common RAMP reference and start-order clamps', 'refs': ['CRMP2', 'RCP1', 'Q12', 'U15', 'U16'],
     'deck': ['RRMP', 'CRMP', 'BRST', 'XU15A', 'XU16B'],
     'modeled_as': 'drawn values; RAMP reset as a behavioural switch', 'omitted': 'Q12 BSS138 device behaviour'},
    {'subsystem': 'Disable gate pulldowns Q10/Q11 and -12 level shifter Q24/Q25', 'refs': ['Q10', 'Q11', 'Q24', 'Q25'],
     'deck': ['B10', 'B11', 'B25'], 'modeled_as': 'behavioural 3.5 ohm switches (35 ohm in re-entry decks)',
     'omitted': 'BSS138/DMP3036 switching delay and the CSD18543Q3A gate-charge removal time'},
    {'subsystem': 'Enable/minimum-off latch', 'refs': ['Q33', 'Q34', 'Q65', 'Q66', 'RHO1'], 'deck': ['BLAT', 'CHO', 'BENN'],
     'modeled_as': 'behavioural latch with the shortest drawn hold', 'omitted': 'transistor-level latch timing'},
    {'subsystem': 'Active discharge with hold-up', 'refs': ['Q51', 'Q52', 'Q54', 'Q55', 'Q56', 'Q57', 'RX12', 'RX5'],
     'deck': [], 'modeled_as': 'OMITTED',
     'omitted': 'all discharge switching, its ordering against the gate pulldowns, and RX12/RX5/RXN decay'},
    {'subsystem': 'Current limiters and fault latch', 'refs': ['U11', 'U12', 'U9', 'Q30', 'Q31', 'Q41'], 'deck': [],
     'modeled_as': 'OMITTED', 'omitted': 'detection, latch and switch-off timing; any delivered-current overshoot'},
    {'subsystem': 'Terminal OV/UV windows', 'refs': ['U6', 'U7', 'U8'], 'deck': [], 'modeled_as': 'OMITTED',
     'omitted': 'window trips during start, discharge and re-entry'},
    {'subsystem': 'OSC load', 'refs': ['J6', 'J7'], 'deck': ['CL12', 'RCL12', 'CL5', 'CLN'],
     'modeled_as': 'contract-maximum capacitance with 50 mOhm ESR; fixed resistors in loaded cases',
     'omitted': 'actual OSC load current versus rail voltage, asymmetric or nonlinear loads'},
]
OMITTED_DECK_NAMES = ['RX12', 'RX5', 'RXN', 'Q51', 'Q52', 'Q54', 'Q55', 'Q56', 'Q57', 'U11', 'U12', 'U6', 'U7', 'U8']


def recorded_peaks(refinement=REFINEMENT, execution=EXECUTION):
    """Failed 2 us (refinement receipt) and 5 us (execution record) adjacent-sample peaks, read as recorded."""
    refined = json.loads(Path(refinement).read_text())['cases']
    executed = json.loads(Path(execution).read_text())['analyses']['analyze_tracking.py']['results']
    peaks = {}
    for rail, case in FAILED_PEAKS.items():
        row = refined[case]['rails'][rail]
        ex = row['exception']
        peaks[rail] = {'case': case,
                       '5us_v_per_ms': executed[case]['adjacent_slope_screen'][rail]['maximum']['slope_v_per_ms'],
                       '2us_v_per_ms': row['worst_recorded_bound_exceedance']['slope_v_per_ms'],
                       '2us_current_a': ex['maximum_current_in_voltage_region_a'],
                       'exception': {'voltage_v': ex['voltage_ceiling_v'], 'slope_v_per_ms': ex['slope_ceiling_v_per_ms'],
                                     'current_a': ex['capacitive_current_ceiling_a']}}
    return peaks


def schematic_values(path=SCHEMATIC):
    text = Path(path).read_text()
    return dict(re.findall(r'\(property "Reference" "([^"]+)"[^()]*\([^)]*\)\s*\(effects\s*\(font \(size [^)]*\)\)\s*\)\s*\)\s*'
                           r'\(property "Value" "([^"]+)"', text))


def discharge_resistors(calc, values=None):
    """Discharge resistances from the generated schematic; refuse if the calculator constants have drifted."""
    values = schematic_values() if values is None else values
    resistors = {}
    for rail, ref in DISCHARGE_REFS.items():
        if ref not in values:
            raise ValueError(f'discharge resistor {ref} not found in the schematic')
        ohms = float(values[ref].split()[0])
        if ohms != calc.DISCHARGE_R[rail]:
            raise ValueError(f'{ref} is {ohms} ohm in the schematic but {calc.DISCHARGE_R[rail]} ohm in the calculator')
        resistors[rail] = ohms
    return resistors


def calculator():
    spec = importlib.util.spec_from_file_location('board_b20_calculator', CALCULATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def schematic_refs(path=SCHEMATIC):
    return set(re.findall(r'\(property "Reference" "([^"]+)"', Path(path).read_text()))


def deck_elements(path=DECK):
    names = set()
    for line in Path(path).read_text().splitlines():
        token = line.split()[0] if line.split() else ''
        if token and token[0].isalpha() and not token.startswith('.'):
            names.add(token.upper())
    return names


def scope_matrix(refs=None, deck=None):
    refs = schematic_refs() if refs is None else refs
    deck = deck_elements() if deck is None else deck
    rows = []
    for row in MODEL_SCOPE:
        missing_refs = [r for r in row['refs'] if r not in refs]
        missing_deck = [d for d in row['deck'] if d.upper() not in deck]
        if missing_refs or missing_deck:
            raise ValueError(f"{row['subsystem']}: schematic refs {missing_refs} or deck elements {missing_deck} not found")
        rows.append({**row, 'status': 'MODELED' if row['deck'] else 'OMITTED'})
    # deck names carry SPICE prefixes (XQ51, XU11A), so match the bare name, an X prefix and subunit suffixes
    leaked = [n for n in OMITTED_DECK_NAMES
              if any(d == n or (d.startswith('X' + n) and not d[len(n) + 1:].isdigit()) for d in deck)]
    if leaked:
        raise ValueError(f'omitted subsystems now appear in the deck: {leaked}; refresh the scope matrix')
    return rows


# ---------------------------------------------------------------- D1 startup
def ideal_tracking_slopes(calc):
    """Ideal k x RAMP tracking slope per rail at the RAMP capacitance tolerance corners (calculated only)."""
    ramps = calc.ramps()
    return {r: max(case[r]['slope0_v_per_ms'] for case in ramps['cases_c_tolerance']) for r in ('+12', '+5', '-12')}


def startup(calc, reference=D1_REFERENCE):
    extracted = json.loads(Path(reference).read_text())
    ref = extracted['analysis']['rails']

    def verdict(key):
        found = {rail: next(v for k, v in ref[rail]['hypotheses'].items() if k.startswith(key)) for rail in ref}
        return found['+5'] if found['+5'] == found['-12'] else '; '.join(f'{r}: {v}' for r, v in found.items())

    ring = extracted['timestep_artefact']
    source = f"run {extracted['run']['run_id']} ({extracted['identity']['status']}, {D1_REFERENCE.name})"
    ideal = ideal_tracking_slopes(calc)
    rows = {}
    peaks = recorded_peaks()

    def binding(rail):
        current_slope = peaks[rail]['exception']['current_a'] / calc.C_LOAD_MAX[rail] / 1e3
        slope = peaks[rail]['exception']['slope_v_per_ms']
        if math.isclose(current_slope, slope):
            return 'equal'
        return 'slope ceiling tighter' if slope < current_slope else 'current ceiling tighter'

    for rail, peak in peaks.items():
        c = calc.C_LOAD_MAX[rail]
        ex = peak['exception']
        rows[rail] = {
            'ideal_tracking_max_slope_v_per_ms': ideal[rail],
            'recorded_peak_over_ideal': round(peak['2us_v_per_ms'] / ideal[rail], 3),
            'step_change_5us_to_2us_pct': round(100 * (peak['2us_v_per_ms'] / peak['5us_v_per_ms'] - 1), 5),
            'capacitive_current_at_peak_a': round(c * peak['2us_v_per_ms'] * 1e3, 6),
            'recorded_esr_branch_current_a': peak['2us_current_a'],
            'exception_current_equivalent_slope_v_per_ms': round(ex['current_a'] / c / 1e3, 4),
            'exceeds_recorded_ceilings': peak['2us_v_per_ms'] > ex['slope_v_per_ms'] and peak['2us_current_a'] > ex['current_a'],
        }
    return {
        'rails': rows,
        'hypotheses': [
            {'id': 'D1-H1', 'claim': 'The designed common RAMP slope itself is too steep',
             'conclusion': f"{REFUTED} for the designed common RAMP (calculated); {verdict('D1-H1')} for the recorded v(ramp)",
             'evidence': 'Ideal k x RAMP tracking slope at the -10 % RAMP capacitance is at most '
                         f"{ideal['+5']} V/ms (+5) and {ideal['-12']} V/ms (-12); the recorded peaks are "
                         f"{rows['-12']['recorded_peak_over_ideal']}x-{rows['+5']['recorded_peak_over_ideal']}x the ideal "
                         'and lie inside the low-voltage exception regions only. The extracted v(ramp), scaled by the '
                         'tracking gain between 2 us bin averages within +/-100 us of each excursion, peaks at '
                         + ' and '.join(f"{ref[r]['scaled_common_ramp_peak_near_segment_v_per_ms']:.4f} V/ms ({r})" for r in ref)
                         + f' in {source}.'},
            {'id': 'D1-H6', 'claim': 'A start-order clamp release (U15/U16 on RAMP_P5/RAMP_M12 behind RCP1 1k) presents a '
                                     'fast reference-side edge to the +5/-12 trackers',
             'conclusion': f"{verdict('D1-H6 reference-side')} for a reference-side edge; {verdict('D1-H6 clamp-diode')} "
                           'for clamp-diode release',
             'evidence': 'Scaled per-rail reference peaks between 2 us bin averages are '
                         + ' and '.join(f"{ref[r]['scaled_reference_peak_near_segment_v_per_ms']:.4f} V/ms ({r}, ideal "
                                        f"{ref[r]['ideal_tracking_max_slope_v_per_ms']})" for r in ref)
                         + ('; the clamp diodes stay reverse-biased across each window (' if verdict('D1-H6 clamp-diode') == REFUTED
                            else '; clamp-diode voltage across each window (')
                         + '; '.join(f"{r}: {ref[r]['clamp_diode_voltage_v']['window_min']:.3f} to "
                                     f"{ref[r]['clamp_diode_voltage_v']['window_max']:.3f} V" for r in ref)
                         + ('). The excursions lie downstream of the reference' if verdict('D1-H6 reference-side') == REFUTED
                            else ')') + f'; {source}.'},
            {'id': 'D1-H7', 'claim': 'The adjacent-sample reference rule fired on a solver-timestep artefact, not a circuit edge',
             'conclusion': f"{verdict('D1-H7')}",
             'evidence': f"The {ring['rail']} adjacent-sample peak of {ref[ring['rail']]['adjacent_sample_scaled_reference_peak_v_per_ms']:.1f} "
                         f"V/ms is {ring['adjacent_peak_dv_v'] * 1e3:.3f} mV over {ring['adjacent_peak_dt_s'] * 1e9:.2f} ns, "
                         f"inside a {ring['cluster_samples']}-sample cluster (minimum step {ring['cluster_min_dt_s'] * 1e9:.3f} ns) "
                         f"where {ring['node']} rings {ring['node_peak_to_peak_in_cluster_v'] * 1e3:.3f} mV peak to peak with "
                         f"{ring['node_sign_reversals_in_cluster']} sign reversals as the XU16A clamp output reaches "
                         f"{ring['clamp_output_at_cluster_start_v']:.3f} V."
                         + (' The 2 us bin-average analysis no longer lets such a step fire the rule; the in-job '
                            'adjacent-sample classification is retained as superseded.' if SUPPORTED in verdict('D1-H7') else '')},
            {'id': 'D1-H2', 'claim': 'The excess is a maximum-step artefact',
             'conclusion': REFUTED + ' for maximum step; UNRESOLVED for other solver settings and macromodel accuracy',
             'evidence': f"5 us to 2 us changes the peak by {rows['+5']['step_change_5us_to_2us_pct']:+.5f} % (+5) and "
                         f"{rows['-12']['step_change_5us_to_2us_pct']:+.5f} % (-12); reltol/abstol/method and vendor-model "
                         'fidelity were not varied for these cases.'},
            {'id': 'D1-H3', 'claim': 'Slope and current exceedances are one constraint, not two',
             'conclusion': SUPPORTED,
             'evidence': 'The recorded ESR-branch currents equal C x dV/dt at the peak within ESR effects ('
                         + '; '.join(f"{r}: {rows[r]['capacitive_current_at_peak_a'] * 1e3:.2f} vs "
                                     f"{rows[r]['recorded_esr_branch_current_a'] * 1e3:.2f} mA" for r in rows)
                         + '), and each current ceiling corresponds to the slope ceiling at contract capacitance ('
                         + '; '.join(f"{peaks[r]['exception']['current_a'] * 1e3:g} mA / {calc.C_LOAD_MAX[r] * 1e6:g} uF = "
                                     f"{rows[r]['exception_current_equivalent_slope_v_per_ms']:g} V/ms against "
                                     f"{peaks[r]['exception']['slope_v_per_ms']:g} V/ms ({binding(r)})" for r in rows)
                         + '). For the modeled pure C + ESR load a correction must reduce the slope; a current-only '
                         'argument cannot pass. A load with a resistive or nonlinear part would separate the two.'},
            {'id': 'D1-H4', 'claim': 'No-load excursions come from the pair passing its pre-bias target near conduction onset '
                                     'with no load to pull the output back',
             'conclusion': UNRESOLVED,
             'evidence': 'Consistent with no-load-only occurrence and the low-voltage location, and with the phase-10 prose. '
                         'Distinguishing it needs one paired run changing only the pre-bias target (RT12O/RT5O/RT12NO) or '
                         'integrator CT on nom/adv, after design review. Not run.'},
            {'id': 'D1-H5', 'claim': 'Startup is strictly monotonic', 'conclusion': UNRESOLVED,
             'evidence': 'Small negative adjacent-sample increments remain; no numerical tolerance is adopted.'},
        ],
    }


# ---------------------------------------------------------------- D2 discharge and shutdown
def rc_voltage(v0, r_discharge, c, t, r_load=None):
    """Closed-form decay of one disconnected rail through its discharge resistor and an optional resistive load."""
    r = r_discharge if r_load is None else r_discharge * r_load / (r_discharge + r_load)
    return v0 * math.exp(-t / (r * c))


def direct_hazard(v12, vn, v5, absent_v):
    """R-ADG: one analog rail absent, the other at >= 8 V magnitude, and +5 V above 0.8 V.

    absent_v must be supplied with a stated basis; the contract does not define 'absent' numerically.
    Returns None (OPEN) without it.
    """
    if absent_v is None:
        return None
    a12, an = abs(v12), abs(vn)
    one_absent = (a12 <= absent_v and an >= ADG_OTHER_RAIL_MIN) or (an <= absent_v and a12 >= ADG_OTHER_RAIL_MIN)
    return one_absent and v5 > P5_HOLD_MAX


def sufficient_screen_violation(v12, vn, v5):
    """Definition-1 screen: +5 V above 0.8 V while either analog magnitude is at or below 1.5 V.

    A violation is not a direct hazard; the screen is only sufficient.
    """
    return v5 > P5_HOLD_MAX and min(abs(v12), abs(vn)) <= SCREEN_ANALOG_MIN


def rvee_violation(v12, vn, absent_v):
    if absent_v is None:
        return None
    return (abs(vn) <= absent_v and v12 > P12_WHILE_M12_ABSENT_MAX) or (abs(v12) <= absent_v and abs(vn) > M12_WHILE_P12_ABSENT_MAX)


def evaluate_discharge(calc, loads, absent_v, step_s=10e-6, stop_s=0.2, resistors=None):
    """Evaluate the voltage-form rows on per-rail closed-form decay after an ideal simultaneous disconnect."""
    resistors = discharge_resistors(calc) if resistors is None else resistors
    v0 = {r: calc.LOAD_BAND[r][1] for r in ('+12', '-12', '+5')}
    first = {'rvee': None, 'direct_hazard': None, 'screen': None}
    level_time = {}
    t = 0.0
    while t <= stop_s:
        v = {r: rc_voltage(v0[r], resistors[r], calc.C_LOAD_MAX[r], t, loads.get(r)) for r in v0}
        for r in v:
            if r not in level_time and abs(v[r]) <= calc.DISCHARGE_LEVEL[r]:
                level_time[r] = round(t, 6)
        checks = {'rvee': rvee_violation(v['+12'], v['-12'], absent_v),
                  'direct_hazard': direct_hazard(v['+12'], v['-12'], v['+5'], absent_v),
                  'screen': sufficient_screen_violation(v['+12'], v['-12'], v['+5'])}
        for key, hit in checks.items():
            if hit and first[key] is None:
                first[key] = {'t_s': round(t, 6), **{r: round(x, 4) for r, x in v.items()}}
        t += step_s
    return {'loads_ohm': loads, 'absent_threshold_v': absent_v, 'time_to_discharge_level_s': level_time,
            'all_within_100ms': all(level_time.get(r, math.inf) <= calc.DISCHARGE_TIME_MAX_S for r in v0),
            'first_rvee_violation': first['rvee'] if absent_v is not None else OPEN,
            'first_direct_hazard': first['direct_hazard'] if absent_v is not None else OPEN,
            'first_sufficient_screen_violation': first['screen']}


def zero_load_absent_limit(calc, resistors, low=0.5, high=6.0, resolution=0.01):
    """Smallest numeric 'absent' threshold (to resolution) at which zero-load decay violates R-VEE, by bisection."""
    if evaluate_discharge(calc, {}, high, resistors=resistors)['first_rvee_violation'] is None:
        return None
    while high - low > resolution:
        mid = (low + high) / 2
        if evaluate_discharge(calc, {}, mid, resistors=resistors)['first_rvee_violation'] is None:
            low = mid
        else:
            high = mid
    return round(high, 2)


def discharge(calc):
    resistors = discharge_resistors(calc)
    # ASSUMPTION for illustration only: 'absent' = 0.5 V, the +12 V discharge level (CALCULATED A1), applied to both rails.
    absent = calc.DISCHARGE_LEVEL['+12']
    limit = zero_load_absent_limit(calc, resistors)
    transient_load = {r: round(calc.STARTUP_LOAD_REF_V[r] / calc.I_TRANSIENT_MIN[r], 4) for r in ('+12', '-12', '+5')}
    cases = {
        'zero_load': evaluate_discharge(calc, {}, absent, resistors=resistors),
        'zero_load_absent_1_5v': evaluate_discharge(calc, {}, 1.5, resistors=resistors),
        'assumed_p12_loaded_only': evaluate_discharge(calc, {'+12': transient_load['+12']}, absent, resistors=resistors),
        'assumed_m12_loaded_only': evaluate_discharge(calc, {'-12': transient_load['-12']}, absent, resistors=resistors),
        'zero_load_absent_undefined': evaluate_discharge(calc, {}, None, resistors=resistors),
    }
    overlap = {r: round(calc.LOAD_BAND[r][1] / resistors[r], 4) for r in resistors}
    return {
        'assumptions': ['Ideal simultaneous disconnect at t = 0 (disconnect-before-discharge, AGND connected).',
                        'Discharge switch on-resistance omitted (it only lengthens decay).',
                        'Disconnect skew between the rails is taken as zero; the contract allows up to 1 ms and the '
                        'installed skew is unbounded (see disconnect_order).',
                        "Loads are fixed resistors at the 20 ms transient minimum; the OSC load-versus-voltage "
                        "characteristic is UNSOURCED.",
                        "'Absent' is not defined numerically by the contract; the cases use the rail discharge level "
                        "(0.5 V) as a labelled assumption, add the contract's informal 'about 1.5 V', and the undefined "
                        "case stays OPEN.",
                        'OSC +/-12 V loads are largely rail-to-rail, which couples the rails; one-rail-to-AGND loads are '
                        'an illustrative assumption, not the OSC load.'],
        'discharge_resistors_ohm': {f'{DISCHARGE_REFS[r]} ({r})': v for r, v in resistors.items()},
        'zero_load_rvee_absent_threshold_limit_v': limit,
        'cases': cases,
        'disconnect_overlap_current_bound_a': overlap,
        'disconnect_order': {'status': OPEN, 'reason': 'Disconnect and discharge start from the same EN_E state with no '
                             'designed ordering, through unequal paths: +12/+5 disconnect EN_E -> Q33 -> EN_N (REN 10k pull-up) '
                             '-> Q10/Q11; -12 disconnect Q24 -> RG3A 56k -> Q25; discharge from the CDH hold-up: Q56 -> DIS_P (R60 100k '
                             'pulldown) -> Q51/Q52, and Q54 -> R61 470k / R62 1M divider -> Q55. Relative timing needs device switching data and the '
                             'CSD18543Q3A gate-charge path, which the decks omit. Overlap current is limited by the discharge '
                             'resistors (above); that is a consequence, not compliance.'},
        'hypotheses': [
            {'id': 'D2-H1', 'claim': 'At zero load the discharge resistors alone meet the level, time and voltage-form rows',
             'conclusion': SUPPORTED + f' only for absent <= {limit - 0.01:.2f} V with ideal simultaneous disconnect (calculated); '
                           'disconnect order is D2-H3',
             'evidence': 'All rails reach their discharge level inside 100 ms. With absent = 0.5 V there is no R-VEE, '
                         'direct-hazard or screen event; R-VEE first fails at an absent threshold of '
                         f'{limit:.2f} V, and at 1.5 V it fails (zero_load_absent_1_5v).'},
            {'id': 'D2-H2', 'claim': 'Independent asymmetric loads can reorder decay into a forbidden state',
             'conclusion': SUPPORTED + ' under the stated resistive-load and absent-threshold assumptions; UNRESOLVED for the installed system',
             'evidence': 'A loaded rail collapses in about 3 ms while the other still exceeds 10 V, giving R-VEE and '
                         'direct-hazard events. Passive per-rail discharge does not couple the rails.'},
            {'id': 'D2-H3', 'claim': 'Outputs are disconnected before active discharge begins', 'conclusion': UNRESOLVED,
             'evidence': 'Same EN_E state, no designed ordering, unequal drive paths; switching data and an installed '
                         'timing bound are missing.'},
        ],
    }


# ---------------------------------------------------------------- D3 maximum delivered current
def delivered_current_bound(trip_max_a, response_s=None, di_dt_a_per_s=None):
    """Upper bound on delivered current after a trip-only limiter: trip maximum plus current growth until switch-off.

    A trip threshold is never returned as the delivered maximum; without both the response time and the
    load-side di/dt bound the result is OPEN.
    """
    if response_s is None or di_dt_a_per_s is None:
        return {'status': OPEN, 'bound_a': None,
                'reason': 'trip threshold is not a delivered-current maximum; response time or di/dt bound missing'}
    return {'status': 'CALCULATED', 'bound_a': trip_max_a + di_dt_a_per_s * response_s}


def maximum_current(calc):
    lim = calc.limiter()
    rows = {}
    for rail in ('+12', '-12', '+5'):
        margin = calc.I_MAX[rail] - lim[rail]['trip_max_a']
        rows[rail] = {'trip_max_a': lim[rail]['trip_max_a'], 'contract_max_a': calc.I_MAX[rail],
                      'margin_a': round(margin, 5),
                      'allowed_di_dt_a_per_us_at_1us_response': round(margin, 5),
                      'bound_without_timing': delivered_current_bound(lim[rail]['trip_max_a'])}
    tightest = min(((r, row['allowed_di_dt_a_per_us_at_1us_response']) for r, row in rows.items()), key=lambda x: x[1])
    return {
        'rails': rows,
        'response_chain': [
            {'stage': 'INA301A3 comparator', 'value': f'tp <= {calc.INA_TP_S * 1e6:g} us', 'class': 'G (datasheet)'},
            {'stage': '-12 V U9A OPA2187 comparator', 'value': 'slew-limited, about 70 us', 'class': 'T (typical, not a bound)'},
            {'stage': 'FAULT_N -> Q30/Q31 latch -> EN_N -> Q10/Q11/Q25 gate pulldown', 'value': None, 'class': UNSOURCED},
            {'stage': 'CSD18543Q3A pair turn-off (gate charge through BSS138)', 'value': None, 'class': UNSOURCED},
            {'stage': 'Load-side di/dt (OSC wiring/impedance, fault type)', 'value': None, 'class': UNSOURCED},
        ],
        'hypotheses': [
            {'id': 'D3-H1', 'claim': 'Trip thresholds inside the window establish the 2.1/2.0/0.5 A maximum',
             'conclusion': REFUTED,
             'evidence': 'The limiter trips and opens; it does not regulate. Delivered current grows until switch-off, '
                         'so the worst-case delivered peak is at least trip_max; trip_max is not an upper bound.'},
            {'id': 'D3-H2', 'claim': 'Delivered current including overshoot stays within the contract maximum',
             'conclusion': UNRESOLVED,
             'evidence': 'Needs a guaranteed detection-to-switch-off time and a load-side di/dt bound. Margins are '
                         + ' / '.join(f"{rows[r]['margin_a'] * 1e3:.2f}" for r in rows) + ' mA ('
                         + ' / '.join(rows) + f"), so even a 1 us total response allows at most {tightest[1] * 1e3:.2f} "
                         f"mA/us of growth on {tightest[0]}."},
        ],
    }


def reference_side_refuted(reference=D1_REFERENCE):
    rails = json.loads(Path(reference).read_text())['analysis']['rails'].values()
    return all(row['hypotheses']['D1-H6 reference-side edge'] == REFUTED for row in rails)


def findings():
    calc = calculator()
    return {
        'scope': 'PD20 D1-D3 diagnostics; arithmetic and source binding only. electrical_acceptance: NOT ESTABLISHED',
        'sources': {'schematic': str(SCHEMATIC.relative_to(ROOT)), 'deck': str(DECK.relative_to(ROOT)),
                    'calculator': str(CALCULATOR.relative_to(ROOT)),
                    'contract': 'Takazudo/zudo-osc-hole-field@433c88b design/architecture-278/integration/power-contract/'
                                'pd-interface-20v.md (sha256 8702890d4d13c4ba3fbd129dca98ccabf12b006aee7e99230e81ed4dad09556a)'},
        'model_scope': scope_matrix(),
        'd1_startup': startup(calc),
        'd2_discharge': discharge(calc),
        'd3_maximum_current': maximum_current(calc),
        'next_inputs': [
            ('D1: the reference side is refuted; separate downstream hypotheses (pre-bias overshoot D1-H4, clamp or servo '
             'amplifier saturation and recovery, pass-device or output-capacitor interaction) and the cheapest discriminating '
             'run are a proposal only; nothing is run before admission.'
             if reference_side_refuted() else
             'D1: the reference side is not refuted on every rail; resolve it before downstream hypotheses.'),
            'D2: OSC per-rail load current versus voltage during shutdown (or an agreed bound), a numeric definition of '
            "'absent', and device switching data for the disconnect/discharge edge.",
            'D3: a guaranteed detection-to-switch-off time and a load-side di/dt bound, or an explicitly agreed regulating '
            'current-limit change; no excess-current budget is adopted.',
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--check', type=Path, help='fail if the retained findings differ from a fresh evaluation')
    args = parser.parse_args(argv)
    text = json.dumps(findings(), indent=2) + '\n'
    if args.check:
        if args.check.read_text() != text:
            print(f'FAIL: {args.check} is stale; regenerate with --output', file=sys.stderr)
            return 1
        print('PASS: interface diagnostics are fresh (not electrical acceptance)')
        return 0
    if args.output:
        args.output.write_text(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
