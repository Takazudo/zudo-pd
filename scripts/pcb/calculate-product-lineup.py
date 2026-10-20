#!/usr/bin/env python3
"""Per-PDO capability screen for manufacturing/product-lineup.md.

SCREENING ARITHMETIC ONLY. No simulation, bench, thermal, efficiency, ripple
or startup measurement exists for any option. Every board is an unvalidated
draft. Converter efficiencies are PROJECT_ASSUMPTION (PA) and are reused,
unchanged, from scripts/pcb/calculate-supply-alternatives.py, together with its
ancillary-current, PTC and input-power methods. The path (b) hold-up uses the
constant-current-limiter / constant-power-load integration of the B1 gate
screen (R3b) so both reports agree. Output is deterministic and uses only the
Python standard library.

Inputs (ROOT-relative):
  scripts/pcb/calculate-supply-alternatives.py  efficiency sets and methods
  manufacturing/supply-capability.json          OSC probe loads, ancillary currents

Demand is owned by the OSC ledger (zudo-osc-hole-field PR #289, head
6491ff72ec90166d6c7a8287f487ee62260839aa). Requirements are never relaxed and
the supply never throttles OSC demand: rails are all-on or all-off.

Usage: python3 scripts/pcb/calculate-product-lineup.py [--root PATH]
"""

import argparse
import importlib.util
import math
from pathlib import Path

# Offered contracts (V, A). Which PDOs a charger class must offer follows the
# USB PD power rules as summarized by Renesas (G-U). Above 3 A needs a 5 A
# e-marked cable; without one the source caps at 3 A (G-U).
PDO_CASES = [
    ("45 W: 15 V / 3 A", 15.0, 3.0, "3 A"),
    ("45 W: 20 V / 2.25 A", 20.0, 2.25, "3 A"),
    ("60 W, or 65/100 W on a 3 A cable: 20 V / 3 A", 20.0, 3.0, "3 A"),
    ("65 W: 20 V / 3.25 A", 20.0, 3.25, "5 A e-marked"),
    ("70 W: 20 V / 3.5 A", 20.0, 3.5, "5 A e-marked"),
    ("80 W: 20 V / 4 A", 20.0, 4.0, "5 A e-marked"),
    ("90 W: 20 V / 4.5 A", 20.0, 4.5, "5 A e-marked"),
    ("100 W: 20 V / 5 A", 20.0, 5.0, "5 A e-marked"),
]

# OSC source-band upper voltages (OSC ledger review R2). They govern; the
# 12/12/5 V magnitudes of the parent screen are printed for comparison.
VOUT_BAND = {"plus12": 12.3, "minus12": 12.2, "plus5": 5.1}

# OSC ledger rows not present in supply-capability.json (A, PR #289 head).
STARTUP_ENVELOPE = {"plus12": 1.759459, "minus12": 1.658229, "plus5": 0.286686}
INTERFACE_MAX = {"plus12": 2.1, "minus12": 2.0, "plus5": 0.5}

# Candidate low-model labels for lighter (non-OSC) products, A.
LOW_LABELS = {
    "PD targets 1.2/0.8/0.5": {"plus12": 1.2, "minus12": 0.8, "plus5": 0.5},
    "balanced 1.0/1.0/0.3": {"plus12": 1.0, "minus12": 1.0, "plus5": 0.3},
}

# Best retrieved sink input limiter (b1-gates R3): ADI LTC4282 Rev C, VSENSE
# limit 12.1 / 12.5 / 12.9 mV (G) plus a 0.5 % shunt (PA): max/min ratio 1.077,
# about +/-3.7 % effective. Integrated +/-10 %-class eFuses are far wider.
LTC4282_RATIO = 1.077
HOLDUP_FLOOR_V = 14.0     # PA converter floor used by b1-gates R3
J5_CONTACT_A = 3.0        # G, XFCN drawing via owner bundle
PTC_HOLD_23C = 2.50       # G, Bourns MF-MSMF250/16X


def load_parent(root):
    path = root / "scripts/pcb/calculate-supply-alternatives.py"
    spec = importlib.util.spec_from_file_location("supply_alternatives", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def p_in(m, loads, anc, eta, vout):
    """Board-input power, the parent's switcher-direct method with a vout map."""
    total = 0.0
    for k in m.RAILS:
        i = loads[k] + anc[k]
        total += (vout[k] * i + i * i * (m.R_PTC_MAX + m.R_FILTER)) / eta[k]
    return total


def p_out(m, loads, vout):
    return sum(vout[k] * loads[k] for k in m.RAILS)


def board_points(m, v, i_contract):
    """Derated point (parent 14.0/15 rule, which already holds Q1, cable and
    connector loss) and, for 20 V only, the parent's extra cable-drop case
    (18.67 -> 18.4 V at 3 A) scaled by contract current. At 15 V the parent
    floor is the only point, so both values are 14.0 V."""
    vd = round(v * m.DERATE, 2)
    if v < 20.0:
        return vd, vd
    r_extra = (round(20.0 * m.DERATE, 2) - 18.4) / 3.0
    return vd, round(vd - i_contract * r_extra, 2)


def i_range(m, loads, anc, vout, vb):
    vals = [p_in(m, loads, anc, m.ETA[e], vout) / vb for e in m.ETA]
    return min(vals), max(vals)


def verdict(lo, hi, limit):
    if hi <= limit:
        return "PASS"
    if lo <= limit:
        return "EDGE"
    return "FAIL"


def max_cont(m, anc, eta, vout, vb, ilim, probe):
    lo, hi = 0.0, 4.0
    for _ in range(80):
        k = (lo + hi) / 2
        loads = {"plus12": probe["plus12"] * k, "minus12": probe["minus12"] * k,
                 "plus5": probe["plus5"]}
        if p_in(m, loads, anc, eta, vout) / vb <= ilim:
            lo = k
        else:
            hi = k
    return probe["plus12"] * lo, probe["minus12"] * lo


def holdup_v(p_load, v0, i_lim, c, t_end=0.020, steps=20000):
    """Bulk voltage after t_end with a constant-current limiter feeding a
    constant-power load (same Euler method as b1-gates R3b)."""
    v, dt = v0, t_end / steps
    for _ in range(steps):
        v += (i_lim - p_load / v) / c * dt
        if v <= 1.0:
            return 0.0
    return v


def min_holdup_c(p_load, v0, i_lim, v_floor):
    if i_lim * v_floor >= p_load:
        return 0.0
    lo, hi = 1e-5, 1.0
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        if holdup_v(p_load, v0, i_lim, mid) >= v_floor:
            hi = mid
        else:
            lo = mid
    return hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    root = Path(ap.parse_args().root)
    m = load_parent(root)
    probes, anc, _ = m.load_probes(root)
    demand = {"planning": probes["planning"], "continuous": probes["continuous"],
              "transient": probes["transient"], "startup_env": STARTUP_ENVELOPE}

    print("SCREENING ARITHMETIC ONLY - efficiencies PA (parent sets base/-3pt/-5pt);")
    print("thermal, ripple, startup NOT RUN; every board an unvalidated draft\n")
    print("Governing output voltages (OSC source-band upper):", VOUT_BAND)

    print("\n1. Board-input current range (A) over eta sets, source-band voltages")
    print("   verdict vs contract: PASS all sets / EDGE base only / FAIL")
    for label, v, ic, cable in PDO_CASES:
        vd, vc = board_points(m, v, ic)
        print(f"\n  [{label}] cable {cable}; board input {vd:.2f} V derated, {vc:.2f} V cable")
        for name, loads in demand.items():
            cells = []
            for tag, vb in (("derated", vd), ("cable", vc)):
                lo, hi = i_range(m, loads, anc, VOUT_BAND, vb)
                cells.append(f"{tag} {lo:4.2f}-{hi:4.2f} {verdict(lo, hi, ic)}")
            print(f"    {name:12s} " + " | ".join(cells))
        lo, hi = i_range(m, demand["continuous"], anc, VOUT_BAND, vc)
        print(f"    J5 per contact at continuous (equal split): {hi / 2:.2f} A vs {J5_CONTACT_A} A")

    print("\n2. Max continuous-shaped +12/-12 (A), +5 V held at 0.3 A, cable point")
    for label, v, ic, _ in PDO_CASES:
        _, vc = board_points(m, v, ic)
        res = [max_cont(m, anc, m.ETA[e], VOUT_BAND, vc, ic, probes["continuous"])
               for e in m.ETA]
        a = [r[0] for r in res]
        b = [r[1] for r in res]
        cap = " (Board B PTC hold 2.50 A at 23 C caps it)" if max(a) > PTC_HOLD_23C else ""
        print(f"  {label:48s} +12 {min(a):4.2f}-{max(a):4.2f}  -12 {min(b):4.2f}-{max(b):4.2f}{cap}")

    print("\n3. Converter + series loss at continuous, source-band (W, cable point)")
    for label, v, ic, _ in PDO_CASES:
        _, vc = board_points(m, v, ic)
        po = p_out(m, probes["continuous"], VOUT_BAND)
        losses = [p_in(m, probes["continuous"], anc, m.ETA[e], VOUT_BAND) - po for e in m.ETA]
        print(f"  {label:48s} Pout {po:5.2f} W, loss {min(losses):4.2f}-{max(losses):4.2f} W")

    print("\n4. Transient by sink-side limit plus hold-up (path b)")
    print("   LTC4282 ratio 1.077 (G + PA shunt): limit min = contract / 1.077")
    for label, v, ic, _ in PDO_CASES:
        vd, vc = board_points(m, v, ic)
        _, i_tr = i_range(m, probes["transient"], anc, VOUT_BAND, vc)
        if i_tr <= ic:
            print(f"  {label:48s} transient {i_tr:.2f} A within contract: path b not needed")
            continue
        _, i_cont = i_range(m, probes["continuous"], anc, VOUT_BAND, vc)
        if i_cont >= ic:
            print(f"  {label:48s} continuous {i_cont:.2f} A >= {ic} A: no window")
            continue
        ilim = ic / LTC4282_RATIO
        allowed = (ic - i_cont) / (ic + i_cont)
        state = "window" if ilim >= i_cont else "NO WINDOW"
        c1, cf = [], []
        for e in m.ETA:
            pt = p_in(m, probes["transient"], anc, m.ETA[e], VOUT_BAND)
            for vb in (vd, vc):
                c1.append(min_holdup_c(pt, vb, ilim, vb - 1.0) * 1000)
                cf.append(min_holdup_c(pt, vb, ilim, HOLDUP_FLOOR_V) * 1000)
        print(f"  {label:48s} continuous max {i_cont:.2f} A, allowed +/-{allowed * 100:.1f} %; "
              f"LTC4282 min {ilim:.3f} A: {state}; hold-up 1 V droop "
              f"{min(c1):.1f}-{max(c1):.1f} mF, to {HOLDUP_FLOOR_V} V {min(cf):.1f}-{max(cf):.1f} mF")

    print("\n5. Low model (15 V / 3 A, switcher-direct) candidate labels, 14.0 V floor")
    for name, loads in LOW_LABELS.items():
        lo, hi = i_range(m, loads, anc, VOUT_BAND, 14.0)
        print(f"  {name:24s} {lo:4.2f}-{hi:4.2f} A vs 3 A: {verdict(lo, hi, 3.0)}")

    print("\n6. MF-MSMF250/16X hold-current crossing at the continuous load (A)")
    for k in m.RAILS:
        t = m.ptc_crossing(probes["continuous"][k]) if probes["continuous"][k] > 0.94 else None
        cross = f"hold = continuous at ~{t:.0f} C" if t else "below 85 C hold"
        print(f"  {k:8s} continuous {probes['continuous'][k]} A: {cross}; "
              f"OSC interface max {INTERFACE_MAX[k]} A (no device enforces it)")


if __name__ == "__main__":
    main()
