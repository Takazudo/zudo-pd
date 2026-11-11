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
VGS_RISE_MIN_V = 0.2            # threshold-limited dead zone: Vgs climbs at least this up to t_on
RELEASE_DELAY_S = 200e-6        # floor release: driver exit follows the servo error's sign change within this
FLOOR_FLAT_V = 0.005            # floor release: output within this of its exit value over the last FLOOR_FLAT_S of parking
FLOOR_FLAT_S = 1e-3
SETTLED_S = 2e-3                # supply PWLs reach their final values at 2 ms; reachability is judged after this

# Servo topology from the executed decks: rail -> (case, driver node, amplifier instance, gate column in the
# main waveform, gate offset source, FET source node, source-current column, integrator node).
SERVO = {
    '+5': {'case': 'nom', 'driver': 'p5_drv', 'amplifier': 'XU13B', 'gate_column': 9, 'gate_node': 'p5_g',
           'gate_offset': 'VO2', 'fet': 'XQ3', 'source': 'p5_cs', 'current_column': 6, 'feedback': 'trk5'},
    '-12': {'case': 'adv', 'driver': 'm12_drv', 'amplifier': 'XU9B', 'gate_column': 10, 'gate_node': 'm12_g',
            'gate_offset': 'VO3', 'fet': 'XQ5', 'source': 'm12_cs', 'current_column': 7, 'feedback': 'trk12n_fb'},
}
# Main waveform columns (after time) as written by the decks' first wrdata line.
MAIN_VECTORS = ('p12_out', 'p5_out', 'm12_out', 'ramp', 'VP12', 'VP5', 'VM12', 'p12_g', 'p5_g', 'm12_g', 'enn')
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
    if offset[1] != spec['gate_node'] or offset[2] != fet[2] or fet[3] != spec['source']:
        raise ValueError(f"{spec['fet']}: gate/source wiring differs from the registered topology")
    main = next(line for line in deck.splitlines() if line.startswith('wrdata ') and line.split()[1].endswith('.dat'))
    names = [re.sub(r'^[vi]\((.*)\)$', r'\1', x) for x in main.split()[2:]]
    if tuple(names) != MAIN_VECTORS or names[spec['gate_column'] - 1] != spec['gate_node']:
        raise ValueError(f'main waveform vectors {names} differ from the registered order')
    return {'supplies_v': sorted(supplies), 'gate_offset_v': float(offset[3]), 'plus_input': amp[1], 'minus_input': amp[2]}


def bins(edges, mean):
    return [(edges[i], mean(edges[i], edges[i + 1])) for i in range(len(edges) - 1)]


UNRESOLVED_VERDICTS = {
    'servo wound up at a supply before conduction': UNRESOLVED,
    'windup released when the reference passes the pre-bias floor': UNRESOLVED,
    'peak slope coincides with driver recovery': UNRESOLVED,
    'dead zone set by': UNRESOLVED,
}


def unresolved(reason, **extra):
    return {'status': UNRESOLVED, 'reason': reason, 'verdicts': dict(UNRESOLVED_VERDICTS), **extra}


def evaluate(series, segment_start, segment_end, gain, sign, supplies, gate_offset, lower_band_reachable):
    """Pre-registered verdicts on 2 us bin means (see d1-servo-criteria.md).

    series: name -> callable(t0, t1) bin mean, for out, ref, current (supply current), gate, driver, source and
    error (servo input error, + input minus - input: positive drives the driver toward the upper supply).
    lower_band_reachable: whether the driver's 2 us bin mean enters the band of its lower (pass-pair-off) supply
    somewhere after the supplies settle, so a REFUTED windup cannot come from an unreachable band.
    """
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
        return unresolved('pass pair not conducting at the failed segment')
    on = seg
    while on > 0 and conducting[on - 1]:
        on -= 1
    if on == 0:
        return unresolved('conduction starts before the analysis window')
    lag_start = on
    while lag_start > 0 and lag[lag_start - 1] > LAG_START_V:
        lag_start -= 1
    band = [min(abs(val('driver', i) - s) for s in supplies) <= RAIL_BAND_V for i in range(len(t))]
    parked = [i for i in range(on) if band[i]]
    parked_s = len(parked) * BIN_S
    exit_index = None
    if parked:
        last = parked[-1]
        while last + 1 < len(t) and band[last + 1]:
            last += 1
        exit_index = last + 1 if last + 1 < len(t) else None
    wound = parked_s >= MIN_SATURATION_S
    if wound:
        windup = SUPPORTED
    elif not parked and lower_band_reachable:
        windup = REFUTED
    else:
        windup = UNRESOLVED
    crossing = None
    for i in range(on, 0, -1):
        if val('error', i - 1) <= 0 < val('error', i):
            crossing = i
            break
    if wound:
        lower = [val('driver', i) < sum(supplies) / 2 for i in parked]
        consistent = sum((val('error', i) < 0) == low for i, low in zip(parked, lower)) / len(parked)
        flat_bins = [i for i in parked if t[parked[-1]] - t[i] <= FLOOR_FLAT_S]
        flat = max(abs(val('out', i) - val('out', parked[-1])) for i in flat_bins) <= FLOOR_FLAT_V
        if exit_index is None or crossing is None:
            floor = UNRESOLVED
        elif flat and 0 <= t[exit_index] - t[crossing] <= RELEASE_DELAY_S:
            floor = SUPPORTED
        elif t[exit_index] < t[crossing]:
            floor = REFUTED
        else:
            floor = UNRESOLVED
        floor_level_v = val('out', parked[-1])
        floor_lag_v = lag[parked[-1]]
    else:
        floor, consistent, flat, floor_level_v, floor_lag_v = 'NOT APPLICABLE (no windup)', None, None, None, None
    exit_time = None if exit_index is None else t[exit_index]
    coincides = exit_time is not None and t[on] - RECOVERY_LEAD_S <= exit_time <= segment_start
    climb_from = exit_index if wound and exit_index is not None else lag_start
    linear = climb_from <= on and not any(band[i] for i in range(climb_from, on + 1))
    climb_v = vgs[on] - vgs[climb_from]
    if wound and coincides:
        dead_zone = 'HELD AT SUPPLY UNTIL CONDUCTION'
    elif wound and linear and climb_v >= VGS_RISE_MIN_V and exit_time < t[on] - RECOVERY_LEAD_S:
        dead_zone = (f'CONDUCTION THRESHOLD AFTER WINDUP (driver left the supply {(t[on] - exit_time) * 1e3:.3f} ms '
                     f'before conduction; Vgs climbed {climb_v:.3f} V)')
    elif windup == REFUTED and linear and climb_v >= VGS_RISE_MIN_V and lag_start < on:
        dead_zone = 'CONDUCTION THRESHOLD (no windup; linear Vgs climb to conduction)'
    else:
        dead_zone = UNRESOLVED
    ms = lambda x: None if x is None else round(x * 1e3, 6)
    return {
        'status': 'EVALUATED',
        'conduction_onset_ms': ms(t[on]),
        'conduction_onset_to_segment_us': round((segment_start - t[on]) * 1e6, 3),
        'ideal_lag_start_ms': ms(t[lag_start]) if lag_start < on else None,
        'driver_parked_in_window_before_conduction_us': round(parked_s * 1e6, 3),
        'driver_last_supply_exit_ms': ms(exit_time),
        'exit_to_conduction_us': None if exit_time is None else round((t[on] - exit_time) * 1e6, 3),
        'exit_to_segment_us': None if exit_time is None else round((segment_start - exit_time) * 1e6, 3),
        'servo_error_last_rise_through_zero_before_conduction_ms': None if crossing is None else ms(t[crossing]),
        'parked_direction_matches_error_share': consistent,
        'output_flat_at_floor_before_exit': flat,
        'output_at_driver_exit_v': floor_level_v,
        'ideal_lag_at_driver_exit_v': floor_lag_v,
        'maximum_lag_v': max(lag[climb_from:seg + 1]),
        'lag_at_segment_v': lag[seg],
        'driver_v': {'climb_start': val('driver', climb_from), 'conduction_onset': val('driver', on),
                     'segment': val('driver', seg)},
        'vgs_v': {'climb_start': vgs[climb_from], 'conduction_onset': vgs[on], 'segment': vgs[seg]},
        'verdicts': {
            'servo wound up at a supply before conduction': windup,
            'windup released when the reference passes the pre-bias floor': floor,
            'peak slope coincides with driver recovery': 'YES' if coincides else 'NO',
            'dead zone set by': dead_zone,
        },
    }
