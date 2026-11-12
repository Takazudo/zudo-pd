"""Rules 1-9 as revised for future pre-registrations (d1-rules-revision-20261112.md, owner decision 2026-11-12).

Only rules 6 and 9 differ from gap_sensitivity.judge:
- rule 6 = (a) contract screens in the enable window (+5 V below 0.8 V, each analog rail's magnitude below 1.5 V)
  and (b) excursion beyond the baseline extreme of at most reltol*|v| + vntol;
- rule 9 = the after-disable excursion uses the same reltol*|v| + vntol tolerance.
Pre-registrations made before the revision keep gap_sensitivity.judge; no recorded verdict is re-evaluated here.
"""
import gap_sensitivity as gap

RELTOL = 1e-3                       # the decks' own .options reltol
PLUS5_SCREEN_V = 0.8                # canonical OSC interface 433c88b, recorded in execution-20261110.md
ANALOG_SCREEN_V = 1.5               # same source: the sufficient analog-presence threshold


def tolerance(v):
    """SPICE's own convergence tolerance at voltage v."""
    return RELTOL * abs(v) + gap.VNTOL_V


def contract_screens(record):
    """Enable-window extremes of every output against the contract screens (rule 6a)."""
    out = {}
    for rail, (index, _, _, _) in gap.OTHER_RAILS.items():
        lo, hi = gap.extremes(record['times'], [r[index] for r in record['rows']], *gap.ENABLE_WINDOW_S)
        if rail == '+5':
            out[rail] = {'maximum_v': hi, 'screen_v': PLUS5_SCREEN_V, 'passes': hi < PLUS5_SCREEN_V}
        else:
            magnitude = max(abs(lo), abs(hi))
            out[rail] = {'magnitude_v': magnitude, 'screen_v': ANALOG_SCREEN_V, 'passes': magnitude < ANALOG_SCREEN_V}
    return out


def within_tolerance(variant_extremes, baseline_extremes):
    lo, hi = baseline_extremes
    return variant_extremes[0] >= lo - tolerance(lo) and variant_extremes[1] <= hi + tolerance(hi)


def judge(rail, variant_screens, baseline_screens, v, b, record):
    """Revised pass rules; the keys keep gap_sensitivity's order so rule numbers are unchanged."""
    rules = gap.judge(rail, variant_screens, baseline_screens, v, b)
    screens = contract_screens(record)
    rules['enable edge no excursion beyond baseline'] = (
        all(s['passes'] for s in screens.values())
        and within_tolerance(v['enable_edge_extremes_v'], b['enable_edge_extremes_v']))
    if 'after_disable_vgs_max_v' in v:
        sign = gap.RAILS[rail]['sign']
        floor = sign * b['disabled_extremes_v'][0 if sign > 0 else 1]
        after = [sign * x for x in v['after_disable_extremes_v']]
        top = max(sign * x for x in v['pre_disable_extremes_v'])
        rules['disable edge: no excursion of either polarity'] = (max(after) <= top + tolerance(top)
                                                                  and min(after) >= floor - tolerance(floor))
    return rules


def detail(rail, v, b, record):
    """Reported beside the verdict: the screens and each tolerance actually applied."""
    lo, hi = b['enable_edge_extremes_v']
    out = {'contract_screens': contract_screens(record),
           'enable_edge_tolerance_v': {'minimum': tolerance(lo), 'maximum': tolerance(hi)},
           'below_baseline_minimum_v': lo - v['enable_edge_extremes_v'][0],
           'above_baseline_maximum_v': v['enable_edge_extremes_v'][1] - hi}
    if 'pre_disable_extremes_v' in v:
        sign = gap.RAILS[rail]['sign']
        top = max(sign * x for x in v['pre_disable_extremes_v'])
        out['disable_edge_excursion_v'] = max(sign * x for x in v['after_disable_extremes_v']) - top
        out['disable_edge_tolerance_v'] = tolerance(top)
    return out
