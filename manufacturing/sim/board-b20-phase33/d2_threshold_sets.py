"""Deck sets for d2_threshold_band.py. Exploratory sets are design aids, not criterion readings."""
import itertools
import d2_threshold_band as tb

DIS_DECK = 4.9             # the published decks' drive level
DIS_BAND = (4.16, 4.6)     # (late, early) CALCULATED/PA: see decision.md "drive level"

STRESS = [('hlrh', 'phnlfl', 'zmz', 'pl-ne'), ('hhrh', 'phnlfl', 'zmz', 'pl-ne'), ('hlrh', 'phnlfl', 'zmz', 'pl-nl'),
          ('hhrl', 'plnhfh', 'mzm', 'pe-nl'), ('hhrl', 'ceil', 'mzp', 'pe-nl'), ('hhrh', 'plnhfh', 'mzm', 'pe-nl'),
          ('hlrh', 'phnlfl', 'zmz', 'nom'), ('hhrl', 'plnhfh', 'mzm', 'nom')]


def stress(cands, dis_list):
    out = {}
    for cand in cands:
        for (combo, bank, loads, edge), (dtag, dis) in itertools.product(STRESS, dis_list):
            label, c = tb.case(cand, combo, bank, loads, edge, dis, tag=f'-{dtag}')
            out[label] = c
    return out


@tb.register('verify')
def verify():
    return stress(['asdrawn'], [('d49', DIS_DECK), ('dband', DIS_BAND)])

# ---- exploratory candidates (design aid) ----------------------------------------------------------------------
P_NET = {'P0': ((10e3, 0.01), (22e-9, 0.10)), 'P1': ((4.7e3, 0.01), (22e-9, 0.10)), 'P2': ((4.7e3, 0.01), (27e-9, 0.05)),
         'P3': ((4.02e3, 0.001), (27e-9, 0.05)), 'P4': ((3.09e3, 0.001), (27e-9, 0.05)),
         'P6': ((4.02e3, 0.001), (22e-9, 0.10)), 'P7': ((8.2e3, 0.001), (22e-9, 0.10))}
N_NET = {'N0': ((4.7e3, 0.01), [(47e-9, 0.05), (22e-9, 0.10)]), 'N1': ((4.7e3, 0.01), [(47e-9, 0.05)]),
         'N2': ((4.02e3, 0.001), [(47e-9, 0.05), (22e-9, 0.10)]), 'N3': ((4.02e3, 0.001), [(47e-9, 0.05)]),
         'N5': ((3.09e3, 0.001), [(47e-9, 0.05), (27e-9, 0.05)])}
for _p, (_rdg, _cdg) in P_NET.items():
    for _n, (_r61, _cdgn) in N_NET.items():
        tb.CAND[_p + _n] = {'rdg': _rdg, 'cdg': _cdg, 'r61': _r61, 'r62': (47.5e3, 0.001), 'cdgn': _cdgn}


@tb.register('explore1')
def explore1():
    cands = [p + n for p in ('P1', 'P2', 'P3', 'P4', 'P6') for n in ('N0', 'N1', 'N3')]
    return stress(cands, [('d49', DIS_DECK), ('dband', DIS_BAND)])

# ---- second exploratory pass: all-C0G networks, wider drive band, hot/cold correlated threshold shift ----------
DIS_BAND2 = (4.1, 4.65)
N_NET.update({'N6': ((4.02e3, 0.001), [(47e-9, 0.05), (27e-9, 0.05)]), 'N7': ((4.7e3, 0.01), [(47e-9, 0.05), (27e-9, 0.05)])})
P_NET.update({'P8': ((4.7e3, 0.01), (27e-9, 0.05))})
for _p, (_rdg, _cdg) in P_NET.items():
    for _n, (_r61, _cdgn) in N_NET.items():
        tb.CAND[_p + _n] = {'rdg': _rdg, 'cdg': _cdg, 'r61': _r61, 'r62': (47.5e3, 0.001), 'cdgn': _cdgn}
STRESS2 = STRESS + [('hlrl', 'phnlfl', 'zmz', 'pl-ne'), ('hhrl', 'plnhfl', 'mzz', 'pe-nl'), ('hlrl', 'plnhfh', 'mzm', 'pe-nl'),
                    ('hlrh', 'phnlfh', 'zmm', 'pl-ne'), ('hlrh', 'ceil', 'zmz', 'pl-ne'), ('hhrl', 'plnlfl', 'mzz', 'pe-nl')]
HOT, COLD = -0.30, +0.12


@tb.register('explore2')
def explore2():
    out = {}
    for cand in ('P3N0', 'P3N6', 'P3N7', 'P2N6', 'P4N6', 'P2N0'):
        for (combo, bank, loads, edge), (ttag, shift) in itertools.product(STRESS2, (('t25', 0.0), ('hot', HOT), ('cold', COLD))):
            label, c = tb.case(cand, combo, bank, loads, edge, DIS_BAND2, vth_shift=shift, tag=f'-{ttag}')
            out[label] = c
    return out


@tb.register('explore3')
def explore3():
    out = {}
    for combo, bank, loads, edge in itertools.product(tb.sc.COMBOS, tb.fd.banks(), ('zmz', 'mzm', 'zmm', 'mzz', 'zzz', 'mmm'),
                                                      ('pl-ne', 'pe-nl')):
        label, c = tb.case('P3N0', combo, bank, loads, edge, DIS_BAND2, tag='-t25')
        out[label] = c
    return out

# ================================================================================================================
# FORMAL sets of d2-threshold-band-criteria.md (fixed before the dispatch)
tb.CAND['C1'] = {'rdg': (4.02e3, 0.001), 'cdg': (27e-9, 0.05), 'r61': (4.7e3, 0.01), 'r62': (47.5e3, 0.001),
                 'cdgn': [(47e-9, 0.05), (22e-9, 0.10)]}
DRIVE = (4.10, 4.65, 4.40)      # hold-up drive: with the late Q51/Q52 corner, with the early corner, nominal
EXTREME_LOADS = [a + b + c for a, b, c in itertools.product('zm', repeat=3)]
MIXED, SAME = ('pl-ne', 'pe-nl'), ('pl-nl', 'pe-ne')
X7R_PA = (0.85 * 0.75, 1.15)    # C45: -15 % class limit and -25 % DC bias (PA) early; +15 % class limit late


def grid(cand, edges, loads, dis, tag, **kw):
    out = {}
    for combo, bank, load, edge in itertools.product(tb.sc.COMBOS, tb.fd.banks(), loads, edges):
        label, c = tb.case(cand, combo, bank, load, edge, dis, tag=tag, **kw)
        out[label] = c
    return out


@tb.register('G')
def set_g():
    out = grid('C1', MIXED, list(tb.sq.load_corners()), DRIVE, '-g')
    out.update(grid('C1', SAME, EXTREME_LOADS, DRIVE, '-g'))
    out.update(grid('C1', ('nom',), EXTREME_LOADS, DRIVE, '-g'))
    return out


@tb.register('CTL')
def set_ctl():
    return grid('asdrawn', MIXED, EXTREME_LOADS, DRIVE, '-ctl')


@tb.register('PA-HOT')
def set_hot():
    return grid('C1', MIXED, EXTREME_LOADS, DRIVE, '-hot', vth_shift=HOT, x7r=X7R_PA)


@tb.register('PA-COLD')
def set_cold():
    return grid('C1', MIXED, EXTREME_LOADS, DRIVE, '-cold', vth_shift=COLD, x7r=X7R_PA)


@tb.register('L49')
def set_l49():
    return grid('C1', MIXED, EXTREME_LOADS, DIS_DECK, '-l49')


@tb.register('CTL-SAME')   # criteria amendment 1
def set_ctl_same():
    return grid('asdrawn', SAME, EXTREME_LOADS, DRIVE, '-ctl')
