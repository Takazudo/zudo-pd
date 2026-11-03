#!/usr/bin/env python3
"""60 W-class (20 V / 3 A) usage-limit envelope for manufacturing/power-limit-60w.md.

SCREENING ARITHMETIC ONLY. Nothing here is measured. Every converter efficiency
is a PROJECT_ASSUMPTION (PA) reused unchanged from
scripts/pcb/calculate-supply-alternatives.py; the switcher-direct input-power
method, source-band output voltages, board-input points and hold-up
integration are reused unchanged from scripts/pcb/calculate-product-lineup.py.
Limiter ratios come from manufacturing/b1-gates.md (LTC4282, G + PA shunt) and
manufacturing/design-gaps-20v.md (INA301 comparator chain, G-U + PA). OSC
demand is owned by the OSC ledger; this script never changes it and invents no
OSC circuit numbers. Output is deterministic and uses only the standard library.

Usage (from the repository root):
  python3 scripts/pcb/calculate-power-limit-60w.py [--root PATH]
A copy kept elsewhere also runs from the repository root.
ROOT defaults to the repository containing this file, else the current directory.
"""

import argparse
import importlib.util
from pathlib import Path

CONTRACT_V = 20.0
CONTRACT_A = 3.0  # 20 V / 3 A fixed PDO (60 W PDP); S (USB PD rules via Renesas; primary UNAV)

# Trip tolerance ratios (max/min) used to place a trip whose maximum is 3.0 A.
# LTC4282: 12.1/12.5/12.9 mV (G) + 0.5 % shunt (PA) -> 1.077 (b1-gates R3);
#   a limiter with a fault timer.
# INA301 comparator chains, design-gaps-20v GAP-5 (G-U + PA), computed there
#   for a 20.5 mV / 2.05 V sense signal; reused unchanged, which is
#   conservative only if the input shunt x gain gives at least that signal
#   (>= 6.9 mohm at 3 A, PA; shunt not chosen).
#   Reference path 1.035 (+/-1.73 %): external LIMIT drive permitted (G-U,
#   SBOS713A 7.3.3.2); ILIMIT x divider/buffer source impedance UNAV.
#   Resistor path 1.059 (+/-2.88 %).
# INA301 is a trip comparator, not a limiter: it gives no hold-up credit.
LIMITERS = [
    ("none", 1.000),      # source OCP decides; not a safe trip
    ("INA-ref", 1.035),   # INA301 + reference-driven LIMIT
    ("INA-res", 1.059),   # INA301 + resistor-set LIMIT
    ("LTC4282", 1.077),   # LTC4282 hot-swap limiter + fault timer
]
# Limiters that may feed hold-up: LTC4282 alone, and an LTC4282-class
# limiter stacked under the INA301 reference trip (max below trip minimum).
HOLDUP_LIMITERS = [("LTC4282", 1.077), ("LTC+INA-ref", 1.077 * 1.035)]
GUARD = 0.05  # PA guard below the trip minimum (as in measurement plan M1)

# OSC demand decomposition (OSC-owned; calculated, unverified; none measured).
# zudo-osc-hole-field#288 comment 6285046629, record PR #289 commit 17fd7469.
OSC_ROWS = [
    ("normal typical", {"plus12": 0.882, "minus12": 0.822, "plus5": 0.109}),
    ("usage-limit cand. (OSC)", {"plus12": 1.386, "minus12": 1.287, "plus5": 0.203}),
    ("x1.1 rule 1.6/1.5/0.3", {"plus12": 1.6, "minus12": 1.5, "plus5": 0.3}),
    ("heavy realistic patch", {"plus12": 1.535, "minus12": 1.436, "plus5": 0.221}),
    ("continuous req.", {"plus12": 1.7, "minus12": 1.6, "plus5": 0.3}),
    ("startup envelope", {"plus12": 1.759, "minus12": 1.658, "plus5": 0.287}),
    ("20 ms transient req.", {"plus12": 2.0, "minus12": 1.9, "plus5": 0.4}),
]
# OSC fitted-capacitance startup row at the 10 ms minimum soft start
# (OSC-owned; calculated, unverified). zudo-osc-hole-field#288 integration
# review W1-W7, record PR #289 at 195b3f5.
FITTED_STARTUP = {"plus12": 1.610, "minus12": 1.498, "plus5": 0.240}
# Slower-ramp screen (PA): the steady part is the heavy realistic patch and the
# capacitance-charging excess scales as 10 ms / ramp time. A paper fit is not
# acceptance: OSC tolerance of slow ramps is unverified, and the contract's
# 20 ms transient, accuracy and reserve rules are unchanged.
RAMP_MS = [10, 12, 15, 20, 30, 50]
V_USER = {"plus12": 12.0, "minus12": 12.0, "plus5": 5.0}  # user-terms magnitudes

# Q1 conduction at 3 A, 25 C max RDS(on) at -4.5 V (G): AO3401A from
# supply-capability.json; AOD4185L 20 mohm from supply-alternatives.md.
Q1_RDS = {"AO3401A (fitted)": 0.065, "AOD4185L (B1 candidate)": 0.020}

HOLDUP_MF = [0.0, 1.0, 2.2, 4.7, 10.0]  # PA grid points; minimum between them not computed


def verdict(lo, hi, lim):
    """PASS only with strictly positive worst-case margin; zero or negative
    worst case with a passing best case is EDGE."""
    if hi < lim:
        return "PASS"
    if lo < lim:
        return "EDGE"
    return "FAIL"


def default_root():
    for p in Path(__file__).resolve().parents:
        if (p / "scripts/pcb/calculate-product-lineup.py").is_file():
            return p
    return Path.cwd()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def scaled(point, k, rails):
    return {r: point[r] * k for r in rails}


def k_max(L, m, anc, eta, point, p_avail):
    """Largest scale k of an OSC-shaped point whose board-input power fits."""
    lo, hi = 0.0, 4.0
    for _ in range(80):
        k = (lo + hi) / 2
        if L.p_in(m, scaled(point, k, m.RAILS), anc, eta, L.VOUT_BAND) <= p_avail:
            lo = k
        else:
            hi = k
    return lo


def single_rail_max(L, m, anc, eta, base, rail, p_avail):
    lo, hi = 0.0, 6.0
    for _ in range(80):
        x = (lo + hi) / 2
        loads = dict(base)
        loads[rail] = x
        if L.p_in(m, loads, anc, eta, L.VOUT_BAND) <= p_avail:
            lo = x
        else:
            hi = x
    return lo


def max_peak_power(L, v0, i_lim, c, v_floor):
    """Largest constant board-input power a limiter at i_lim plus bulk c (F)
    can carry for 20 ms without the bulk falling below v_floor."""
    if c == 0.0:
        return v0 * i_lim
    lo, hi = v0 * i_lim, 4 * v0 * i_lim
    for _ in range(50):
        mid = (lo + hi) / 2
        if L.holdup_v(mid, v0, i_lim, c, steps=4000) >= v_floor:
            lo = mid
        else:
            hi = mid
    return lo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(default_root()))
    root = Path(ap.parse_args().root)
    L = load(root / "scripts/pcb/calculate-product-lineup.py", "lineup")
    m = L.load_parent(root)
    probes, anc, _ = m.load_probes(root)
    rails = m.RAILS
    osc = {"canonical": probes["planning"], "continuous": probes["continuous"],
           "transient_20ms": probes["transient"], "startup_env": L.STARTUP_ENVELOPE}
    vd, vc = L.board_points(m, CONTRACT_V, CONTRACT_A)
    vbs = (("derated", vd), ("cable", vc))

    print("SCREENING ARITHMETIC ONLY - nothing measured; efficiencies PA; thermal,")
    print("ripple, startup, source OCP behavior NOT RUN; every board an unvalidated draft\n")

    print("1. Input chain, 20 V / 3 A contract (W)")
    print(f"  source port nominal {CONTRACT_V * CONTRACT_A:.1f} W (charger PDP, not rail output)")
    for tag, vb in vbs:
        print(f"  board input {tag} {vb:.2f} V x 3.00 A = {vb * CONTRACT_A:.2f} W; "
              f"upstream loss lumped in PA derate {CONTRACT_V * CONTRACT_A - vb * CONTRACT_A:.2f} W")
    for q, r in Q1_RDS.items():
        print(f"  Q1 {q}: {CONTRACT_A ** 2 * r:.3f} W at 3 A (25 C max RDS(on), inside the derate)")
    for e in m.ETA:
        print(f"  input W per rail W, eta {e}: " +
              ", ".join(f"{r} {1 / m.ETA[e][r]:.3f}" for r in rails))

    print("\n2. Usable board-input current below the trip (contract / ratio)")
    for name, ratio in LIMITERS:
        i = CONTRACT_A / ratio
        print(f"  {name:8s} ratio {ratio:.3f}: legit max {i:.3f} A "
              f"({vd * i:.2f} W derated, {vc * i:.2f} W cable)")

    print("\n3. OSC contract points: board-input current (min-max over eta and V points)")
    for name, pt in osc.items():
        vals = [L.p_in(m, pt, anc, m.ETA[e], L.VOUT_BAND) / vb for e in m.ETA for _, vb in vbs]
        lo, hi = min(vals), max(vals)
        pout = L.p_out(m, pt, L.VOUT_BAND)
        cells = []
        for lname, ratio in LIMITERS:
            lim = CONTRACT_A / ratio
            v = verdict(lo, hi, lim)
            cells.append(f"{lname}:{v} ({lim - hi:+.3f} A worst)")
        print(f"  {name:15s} rail out {pout:5.2f} W  in {lo:.3f}-{hi:.3f} A | " + " | ".join(cells))

    print("\n4. Continuous rail-output envelope at OSC continuous shape (all rails scaled)")
    for lname, ratio in LIMITERS:
        lim = CONTRACT_A / ratio
        res = []
        for e in m.ETA:
            for _, vb in vbs:
                k = k_max(L, m, anc, m.ETA[e], probes["continuous"], vb * lim)
                res.append(k)
        k_lo, k_hi = min(res), max(res)
        p_lo = L.p_out(m, scaled(probes["continuous"], k_lo, rails), L.VOUT_BAND)
        p_hi = L.p_out(m, scaled(probes["continuous"], k_hi, rails), L.VOUT_BAND)
        cur = "/".join(f"{probes['continuous'][r] * k_lo:.2f}" for r in rails)
        print(f"  {lname:8s} k {k_lo:.3f}-{k_hi:.3f} of 1.7/1.6/0.3; "
              f"rail out {p_lo:.2f}-{p_hi:.2f} W; worst-case currents {cur} A")

    print("\n5. One rail raised alone, the other two at canonical planning (A, worst case)")
    for lname, ratio in (LIMITERS[0], LIMITERS[3]):
        lim = CONTRACT_A / ratio
        cells = []
        for r in rails:
            vals = [single_rail_max(L, m, anc, m.ETA[e], probes["planning"], r, vb * lim)
                    for e in m.ETA for _, vb in vbs]
            cells.append(f"{r} {min(vals):.2f}-{max(vals):.2f}")
        print(f"  {lname:8s} " + "  ".join(cells) +
              "  (MF-MSMF250 hold 2.50 A at 23 C caps a rail first)")

    print("\n6. 20 ms peak envelope, OSC transient shape (droop to 14.0 V floor)")
    print("   no trip or comparator-only trip: no hold-up credit (C 0 rows of LIMITERS)")
    for lname, ratio in LIMITERS[1:]:
        lim = CONTRACT_A / ratio
        ks = [k_max(L, m, anc, m.ETA[e], probes["transient"], vb * lim)
              for e in m.ETA for _, vb in vbs]
        p_lo = L.p_out(m, scaled(probes["transient"], min(ks), rails), L.VOUT_BAND)
        p_hi = L.p_out(m, scaled(probes["transient"], max(ks), rails), L.VOUT_BAND)
        print(f"  {lname:11s} no hold-up: rail out {p_lo:.2f}-{p_hi:.2f} W")
    print("   hold-up behind a limiter (limit min = 3.0 A / ratio)")
    for lname, ratio in HOLDUP_LIMITERS:
        lim = CONTRACT_A / ratio
        for c_mf in HOLDUP_MF:
            ks = []
            for e in m.ETA:
                for _, vb in vbs:
                    pk = max_peak_power(L, vb, lim, c_mf / 1000, L.HOLDUP_FLOOR_V)
                    ks.append(k_max(L, m, anc, m.ETA[e], probes["transient"], pk))
            k_lo, k_hi = min(ks), max(ks)
            p_lo = L.p_out(m, scaled(probes["transient"], k_lo, rails), L.VOUT_BAND)
            p_hi = L.p_out(m, scaled(probes["transient"], k_hi, rails), L.VOUT_BAND)
            ok = "covers 2.0/1.9/0.4" if k_lo >= 1.0 else ("EDGE" if k_hi >= 1.0 else "short")
            print(f"  {lname:11s} ratio {ratio:.3f} ({lim:.3f} A) C {c_mf:4.1f} mF: k {k_lo:.3f}-{k_hi:.3f}, "
                  f"rail out {p_lo:.2f}-{p_hi:.2f} W ({ok})")

    print("\n7. Per-rail trips at OSC interface maximum vs the input contract")
    for name, pt in (("interface max 2.1/2.0/0.5", L.INTERFACE_MAX),
                     ("transient 2.0/1.9/0.4", probes["transient"])):
        vals = [L.p_in(m, pt, anc, m.ETA[e], L.VOUT_BAND) / vb for e in m.ETA for _, vb in vbs]
        print(f"  {name:28s} board input {min(vals):.3f}-{max(vals):.3f} A vs 3.0 A")
    for tag, ratio in (("sum <= 3.0 A", 1.0), ("sum <= LTC4282-class minimum", 1.077)):
        ks = [k_max(L, m, anc, m.ETA[e], L.INTERFACE_MAX, vb * CONTRACT_A / ratio)
              for e in m.ETA for _, vb in vbs]
        print(f"  per-rail trip maxima, {tag}: {min(ks):.3f} x interface max = " +
              "/".join(f"{L.INTERFACE_MAX[r] * min(ks):.2f}" for r in rails) + " A")

    print("\n8. Recharge time of hold-up 14.0 V -> board input after a peak (s, worst case)")
    for lname, ratio in HOLDUP_LIMITERS:
        lim = CONTRACT_A / ratio
        for c_mf in (4.7, 10.0):
            cells = []
            for name in ("canonical", "continuous"):
                worst_t = 0.0
                for e in m.ETA:
                    for _, vb in vbs:
                        spare = vb * lim - L.p_in(m, osc[name], anc, m.ETA[e], L.VOUT_BAND)
                        energy = 0.5 * c_mf / 1000 * (vb ** 2 - L.HOLDUP_FLOOR_V ** 2)
                        worst_t = float("inf") if spare <= 0 else max(worst_t, energy / spare)
                        if worst_t == float("inf"):
                            break
                cells.append(f"{name} {'never (no spare power)' if worst_t == float('inf') else f'{worst_t:.2f}'}")
            print(f"  {lname:11s} C {c_mf:4.1f} mF: " + ", ".join(cells))

    print("\n9. R60 candidate caps: OSC continuous shape, worst eta and board point,")
    print("   board input <= (1 - guard) x trip minimum; caps rounded down to 10 mA")
    r60 = {}
    for lname, ratio in (("LTC4282", 1.077), ("INA-ref", 1.035)):
        lim = CONTRACT_A / ratio * (1 - GUARD)
        k = min(k_max(L, m, anc, m.ETA[e], probes["continuous"], vb * lim)
                for e in m.ETA for _, vb in vbs)
        caps = {r: int(probes["continuous"][r] * k * 100 + 1e-9) / 100 for r in rails}
        r60[lname] = (lim, caps)
        w_user = sum(V_USER[r] * caps[r] for r in rails)
        w_band = L.p_out(m, caps, L.VOUT_BAND)
        worst = max(L.p_in(m, caps, anc, m.ETA[e], L.VOUT_BAND) / vb for e in m.ETA for _, vb in vbs)
        print(f"  {lname:8s} input <= {lim:.3f} A: k {k:.3f}; caps " +
              "/".join(f"{caps[r]:.2f}" for r in rails) +
              f" A = {w_user:.1f} W at 12/12/5 V ({w_band:.1f} W at band maxima); "
              f"caps draw {worst:.3f} A worst")

    print("\n10. OSC decomposition rows (OSC-owned, calc/unverified) vs envelope and R60")
    print("    worst-case board input vs (1 - guard) x trip minimum; per-rail vs R60 caps")
    for name, pt in OSC_ROWS:
        vals = [L.p_in(m, pt, anc, m.ETA[e], L.VOUT_BAND) / vb for e in m.ETA for _, vb in vbs]
        lo, hi = min(vals), max(vals)
        w_user = sum(V_USER[r] * pt[r] for r in rails)
        cells = [f"3.0 A {verdict(lo, hi, CONTRACT_A)} {CONTRACT_A - hi:+.3f}"]
        for lname, (lim, caps) in r60.items():
            within = all(pt[r] <= caps[r] for r in rails)
            cells.append(f"{lname}+guard {verdict(lo, hi, lim)} {lim - hi:+.3f}; "
                         f"caps {'within' if within else 'EXCEEDS'}")
        print(f"  {name:24s} {w_user:5.1f} W  in {lo:.3f}-{hi:.3f} A | " + " | ".join(cells))

    print("\n11. Slower common startup ramp vs OSC fitted startup row (PA scaling,")
    print("    calc only; does not cover the 20 ms transient or accuracy/reserve rules)")
    steady = dict(OSC_ROWS)["heavy realistic patch"]
    excess = {r: FITTED_STARTUP[r] - steady[r] for r in rails}
    caps = r60["LTC4282"][1]
    cases = [("60 W LTC4282+guard", CONTRACT_A, r60["LTC4282"][0], caps),
             ("60 W INA-ref+guard", CONTRACT_A, r60["INA-ref"][0], r60["INA-ref"][1]),
             ("70 W 3.5 A, no trip", 3.5, 3.5, None)]
    for name, amps, lim, rcaps in cases:
        pts = L.board_points(m, CONTRACT_V, amps)
        cells = []
        for t in RAMP_MS:
            pt = {r: steady[r] + excess[r] * 10 / t for r in rails}
            hi = max(L.p_in(m, pt, anc, m.ETA[e], L.VOUT_BAND) / vb for e in m.ETA for vb in pts)
            cells.append(f"{t} ms {lim - hi:+.3f}")
        need = ""
        if rcaps:
            t_min = max(10 * excess[r] / (rcaps[r] - steady[r]) if excess[r] > 0 else 0
                        for r in rails)
            need = f"; R60 caps need ramp >= {max(t_min, 10):.1f} ms"
        print(f"  {name:20s} input margin " + ", ".join(cells) + need)
    print("  +12 V at 20 ms: " + f"{steady['plus12'] + excess['plus12'] / 2:.4f} A")


if __name__ == "__main__":
    main()
