"""Pre-registered D1 servo/dead-zone criteria (#235); fixed before the servo-node extraction run.

The criteria mirror d1-servo-criteria.md (a test keeps the two in step). Every quantity is a mean over
2 us bins (the refined maximum step) so a sub-grid solver-timestep ring cannot decide a verdict.
Thresholds are classification bands for this diagnosis only, never contract tolerances.
"""
import re

SUPPORTED, REFUTED, UNRESOLVED = 'SUPPORTED', 'REFUTED', 'UNRESOLVED'

BIN_S = 2e-6
WINDOW_BEFORE_S = 20e-3         # analysis window starts this long before the failed segment
WINDOW_AFTER_S = 1e-3           # and ends this long after it
CONDUCTION_A = 5e-3             # pass pair conducting: |source current| at or above this
LAG_START_V = 0.05              # dead zone starts when the output lags k x reference by more than this
RAIL_BAND_V = 0.1               # driver saturated: within this of an amplifier supply
MIN_SATURATION_S = 10e-6        # saturated bins inside the dead zone needed to call it saturated
RECOVERY_LEAD_S = 100e-6        # recovery coincides with the excursion if it lies in [t_on - this, segment start]
VGS_RISE_MIN_V = 0.2            # threshold-limited dead zone: Vgs climbs at least this from t_lag to t_on

# Servo topology from the executed decks: rail -> (case, driver node, amplifier instance, gate column in the
# main waveform, gate offset source, FET source node, source-current column, integrator node).
SERVO = {
    '+5': {'case': 'nom', 'driver': 'p5_drv', 'amplifier': 'XU13B', 'gate_column': 9, 'gate_offset': 'VO2',
           'fet': 'XQ3', 'source': 'p5_cs', 'current_column': 6, 'feedback': 'trk5'},
    '-12': {'case': 'adv', 'driver': 'm12_drv', 'amplifier': 'XU9B', 'gate_column': 10, 'gate_offset': 'VO3',
            'fet': 'XQ5', 'source': 'm12_cs', 'current_column': 7, 'feedback': 'trk12n_fb'},
}
SERVO_VECTORS = ('p5_drv', 'trk5', 'p5_cs', 'm12_drv', 'trk12n_fb', 'm12_cs', 'ctz')
# Node -> independent source whose final PWL value is that node's supply (m12_pre is m12_src behind 20 mOhm).
SUPPLY_SOURCES = {'vin': 'VIN', 'p5sup': 'VSUP', 'm12_pre': 'VM12'}


def deck_elements(deck):
    return {line.split()[0]: line.split() for line in deck.splitlines() if line and line[0].isalpha()}


def final_pwl(parts):
    values = re.findall(r'[-+0-9.eE]+[a-zA-Z]*', ' '.join(parts[3:]).replace('PWL(', ' ').replace(')', ' '))
    return float(values[-1])


def topology(deck, rail):
    """Supplies of the servo amplifier and the gate offset, read from the executed deck."""
    spec = SERVO[rail]
    elements = deck_elements(deck)
    amp = elements[spec['amplifier']]
    if amp[5] != spec['driver']:
        raise ValueError(f"{spec['amplifier']}: output {amp[5]} is not {spec['driver']}")
    supplies = []
    for node in amp[3:5]:
        supplies.append(0.0 if node == '0' else final_pwl(elements[SUPPLY_SOURCES[node]]))
    offset = elements[spec['gate_offset']]
    fet = elements[spec['fet']]
    if offset[2] != fet[2] or fet[3] != spec['source']:
        raise ValueError(f"{spec['fet']}: gate/source wiring differs from the registered topology")
    return {'supplies_v': sorted(supplies), 'gate_offset_v': float(offset[3])}


def bins(edges, mean):
    return [(edges[i], mean(edges[i], edges[i + 1])) for i in range(len(edges) - 1)]


def evaluate(series, segment_start, segment_end, gain, sign, supplies, gate_offset):
    """series: name -> callable(t0, t1) returning the bin mean; names out, ref, current, gate, driver, source."""
    first = segment_start - WINDOW_BEFORE_S
    edges = [first + k * BIN_S for k in range(int(round((WINDOW_BEFORE_S + WINDOW_AFTER_S) / BIN_S)) + 1)]
    b = {name: bins(edges, f) for name, f in series.items()}
    t = [x for x, _ in b['out']]
    val = lambda name, i: b[name][i][1]
    seg = max(i for i in range(len(t)) if t[i] <= segment_start)
    lag = [sign * (sign * gain * val('ref', i) - val('out', i)) for i in range(len(t))]
    vgs = [val('gate', i) - gate_offset - val('source', i) for i in range(len(t))]
    conducting = [abs(val('current', i)) >= CONDUCTION_A for i in range(len(t))]
    if not conducting[seg]:
        return {'status': UNRESOLVED, 'reason': 'pass pair not conducting at the failed segment'}
    on = seg
    while on > 0 and conducting[on - 1]:
        on -= 1
    start = on
    while start > 0 and lag[start - 1] > LAG_START_V:
        start -= 1
    if start == on or start == 0:
        return {'status': UNRESOLVED, 'reason': 'no dead zone with lag above the band before conduction in the window'}
    near_rail = [min(abs(val('driver', i) - s) for s in supplies) <= RAIL_BAND_V for i in range(len(t))]
    saturated = [i for i in range(start, on) if near_rail[i]]
    saturated_s = len(saturated) * BIN_S
    recovery = None
    if saturated:
        last = saturated[-1]
        while last + 1 < len(t) and near_rail[last + 1]:
            last += 1
        recovery = t[last + 1] if last + 1 < len(t) else None
    coincides = recovery is not None and t[on] - RECOVERY_LEAD_S <= recovery <= segment_start
    if saturated_s >= MIN_SATURATION_S and coincides:
        servo = SUPPORTED
    elif not any(near_rail[i] for i in range(start, seg + 1)):
        servo = REFUTED
    else:
        servo = UNRESOLVED
    linear_from = start
    if recovery is not None:
        linear_from = min(i for i in range(len(t)) if t[i] >= recovery)
    linear = linear_from <= on and not any(near_rail[i] for i in range(linear_from, on + 1))
    climbs = linear and vgs[on] - vgs[linear_from] >= VGS_RISE_MIN_V
    if near_rail[start] and saturated_s >= MIN_SATURATION_S and coincides:
        dead_zone = 'PRE-BIAS FLOOR (servo parked at a supply by the floor-induced error until conduction)'
    elif climbs and saturated_s >= MIN_SATURATION_S:
        dead_zone = (f'MIXED (parked for {saturated_s * 1e6:.0f} us, then linear Vgs climb for '
                     f'{(t[on] - t[linear_from]) * 1e6:.0f} us to conduction)')
    elif climbs and not saturated:
        dead_zone = 'CONDUCTION THRESHOLD (linear servo slewing Vgs up to conduction)'
    else:
        dead_zone = UNRESOLVED
    nearest = lambda i: min(supplies, key=lambda s: abs(val('driver', i) - s))
    return {
        'status': 'EVALUATED',
        'dead_zone_ms': [round(t[start] * 1e3, 6), round(t[on] * 1e3, 6)],
        'dead_zone_duration_us': round((t[on] - t[start]) * 1e6, 3),
        'conduction_onset_to_segment_us': round((segment_start - t[on]) * 1e6, 3),
        'output_floor_v': val('out', max(start - int(round(500e-6 / BIN_S)), 0)),
        'maximum_lag_v': max(lag[start:seg + 1]),
        'lag_at_segment_v': lag[seg],
        'driver_v': {'dead_zone_start': val('driver', start), 'conduction_onset': val('driver', on),
                     'segment': val('driver', seg), 'nearest_supply_at_start_v': nearest(start)},
        'driver_saturated_in_dead_zone_us': round(saturated_s * 1e6, 3),
        'driver_recovery_ms': None if recovery is None else round(recovery * 1e3, 6),
        'recovery_to_segment_us': None if recovery is None else round((segment_start - recovery) * 1e6, 3),
        'vgs_v': {'dead_zone_start': vgs[start], 'conduction_onset': vgs[on], 'segment': vgs[seg]},
        'verdicts': {
            'servo saturation and windup recovery': servo,
            'peak slope coincides with driver recovery': 'YES' if coincides else 'NO',
            'dead zone set by': dead_zone,
        },
    }
