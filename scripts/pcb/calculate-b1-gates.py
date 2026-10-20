#!/usr/bin/env python3
"""B1 gate screens for manufacturing/b1-gates.md.

SCREENING ARITHMETIC ONLY. Option B1 = 20 V / 3 A USB-PD, Board B
switcher-direct (TPS54560 bucks to +12 V / +5 V, TPS54560 inverting
buck-boost to -12 V, LC post-filters, MF-MSMF250/16X-2 PTCs). No schematic,
PCB or part selection is changed. Every filter value, efficiency, parasitic
and load step below is a PROJECT_ASSUMPTION (PA); manufacturer limits are
quoted with their class in manufacturing/b1-gates.md. Ripple, stability,
thermal, surge and startup checks remain NOT RUN; this is frequency-domain
and energy arithmetic only. Deterministic, Python standard library only.

Inputs (ROOT-relative): manufacturing/supply-capability.json via
scripts/pcb/calculate-supply-alternatives.py (probe loads, ancillary
currents, PA efficiency sets).

Usage: python3 scripts/pcb/calculate-b1-gates.py [--root PATH]
"""

import argparse
import cmath
import importlib.util
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
RAILS = ("plus12", "minus12", "plus5")

# OSC source contract (OSC ledger, PR #289 6491ff7, supply-architecture.json)
BAND = {"plus12": (12.00, 12.30), "minus12": (12.00, 12.20), "plus5": (5.05, 5.10)}
RIPPLE_LIMIT_MVPP = 1.0

# TPS54560 (G): VFB 0.792 / 0.800 / 0.808 V over TJ -40..150 C, VIN 4.5..60 V;
# RT-mode fsw 450 / 500 / 550 kHz at RT 200 kohm.
VREF, VREF_TOL = 0.800, 0.01
FSW_MIN = 450e3
# Precision DC servo candidate: REF50xxI 0.05 % initial, 3 ppm/C max (G-U,
# TI product page); delta-T 65 C and 0.05 % divider resistors are PA.
SERVO_INIT, SERVO_TC, SERVO_DT = 0.0005, 3e-6, 65.0
DIV_TOL_INTERNAL, DIV_TOL_SERVO = 0.001, 0.0005
R_PTC_MAX = 0.100  # MF-MSMF250/16X R1max (G)
I_MAX_TERMINAL = {"plus12": 2.0, "minus12": 1.9, "plus5": 0.4}  # 20 ms transient
VIN_MIN, VIN_MAX = 18.4, 21.0  # PA board-input range (cable case to 20 V + 5 %)
VF = 0.5  # PA catch-diode drop

# Candidate filters (all PA). C values are effective after DC bias.
FILT = {
    "plus12": dict(kind="buck", vout=12.0, iout=2.0, L1=10e-6, C1=24e-6, esr1=1e-3,
                   Lf=2.2e-6, dcr=0.010, Cp=2e-12, C2=20e-6, esr2=2e-3, esl2=0.5e-9,
                   Cd=100e-6, Rd=0.33, esld=5e-9, fc=20e3, step=0.5),
    "plus5": dict(kind="buck", vout=5.0, iout=0.4, L1=6.8e-6, C1=40e-6, esr1=1e-3,
                  Lf=2.2e-6, dcr=0.010, Cp=2e-12, C2=20e-6, esr2=2e-3, esl2=0.5e-9,
                  Cd=220e-6, Rd=0.33, esld=5e-9, fc=20e3, step=0.2),
    "minus12": dict(kind="inv", vout=12.0, iout=1.9, L1=10e-6, C1=40e-6, esr1=1e-3,
                    Lf=4.7e-6, dcr=0.015, Cp=2e-12, C2=20e-6, esr2=2e-3, esl2=0.5e-9,
                    Cd=100e-6, Rd=0.47, esld=5e-9, fc=10e3, step=0.5),
}
NHARM = 50  # harmonics evaluated (to 22.5 MHz); edge spikes beyond: NOT RUN

# Input limiter candidates: (label, ratio max/min of current limit, class)
LIMITERS = [
    ("TPS25982 integrated eFuse, 2 A row, -40..125 C (G)", 2.43 / 1.53),
    ("LM5069 VCL 48.5/61.5 mV + 0.5 % Rsense (G + PA)", (61.5 / 48.5) * (1.005 / 0.995)),
    ("LTC4282 12.1/12.9 mV zero-scale + 0.5 % Rsense (G + PA)", (12.9 / 12.1) * (1.005 / 0.995)),
]
I_CONTRACT = 3.0

# STUSB4500 (G, DS12499 Rev 8): VDD, VBUS_EN_SNK, VBUS_VS_DISCH abs max 28 V;
# IDD idle 210 uA max at VDD 5 V; VDD operating 4.1..22 V.
# BZX84-C24 (G, Nexperia Rev 7): VZ 22.8..25.6 V at 5 mA, rdif <= 70 ohm,
# SZ <= 22.0 mV/K at 5 mA, Rth(j-a) <= 500 K/W (FR4 standard footprint).
STUSB_ABS, VDD_MIN_OP, IDD_IDLE_MAX = 28.0, 4.1, 210e-6
VZ_MAX, IZT, RDIF, SZ_MAX, RTH_JA = 25.6, 5e-3, 70.0, 0.022, 500.0
# TVS2200 (G, SLVSED5C): VBR 24.6/25.9/27.6 V at 1 mA; VCLAMP max 28.0 V at
# 40 A / 27 C and 28.35 V at 35 A / 125 C (8/20 us). Worst guaranteed case.
TVS2200_CLAMP, TVS2200_VBR_MAX = 28.35, 27.6
# OSC load capacitance ceiling (OSC contract): nominal, +/-20 %; ESR PA.
C_OSC = {"plus12": 150e-6, "minus12": 150e-6, "plus5": 100e-6}
ESR_OSC = 0.02
# VREG_2V7 loads seen through VDD (Board P spec): R15/R16 4.7 kohm pull-ups.
I_PULLUPS_LOW = 2 * 2.7 / 4.7e3


def load_alt(root):
    spec = importlib.util.spec_from_file_location(
        "alt", root / "scripts/pcb/calculate-supply-alternatives.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pin_at(mod, loads, anc, eta, vout):
    total = 0.0
    for k in RAILS:
        i = loads[k] + anc[k]
        total += (vout[k] * i + i * i * (mod.R_PTC_MAX + mod.R_FILTER)) / eta[k]
    return total


def zpar(*zs):
    return 1 / sum(1 / z for z in zs)


def transfer(f, p):
    """|v_out / v_C1| of the second stage with an R-C damping leg."""
    w = 2 * math.pi * f
    zl = zpar(complex(p["dcr"], w * p["Lf"]), 1 / complex(0, w * p["Cp"]))
    zc2 = complex(p["esr2"], w * p["esl2"] - 1 / (w * p["C2"]))
    zd = complex(p["Rd"], w * p["esld"] - 1 / (w * p["Cd"]))
    zo = zpar(zc2, zd)
    return abs(zo / (zl + zo))


def zout(f, p, c_osc=0.0):
    """Terminal output impedance with C1 as an ideal source (PA)."""
    w = 2 * math.pi * f
    zl = complex(p["dcr"], w * p["Lf"])
    legs = [complex(p["esr2"], w * p["esl2"] - 1 / (w * p["C2"])),
            complex(p["Rd"], w * p["esld"] - 1 / (w * p["Cd"]))]
    if c_osc:
        legs.append(complex(ESR_OSC, -1 / (w * c_osc)))
    return abs(zpar(zl, *legs))


def zout_peak(p, c_osc=0.0):
    best = (0.0, 0.0)
    for i in range(400):
        f = 1e3 * 10 ** (i / 133.0)
        z = zout(f, p, c_osc)
        if z > best[0]:
            best = (z, f)
    return best


def first_stage(p):
    """(ripple pp at C1 in V, waveform) at the worst input for each topology."""
    f, v = FSW_MIN, p["vout"]
    if p["kind"] == "buck":
        d = (v + VF) / (VIN_MAX + VF)
        di = (VIN_MAX - v) * d / (p["L1"] * f)
        return di / (8 * f * p["C1"]) + di * p["esr1"], "tri", d, di
    d = (v + VF) / (VIN_MIN + v + VF)
    il = p["iout"] / (1 - d)
    di = VIN_MIN * d / (p["L1"] * f)
    return p["iout"] * d / (f * p["C1"]) + (il + di / 2) * p["esr1"], "saw", d, di


def ripple_out(p):
    vpp, shape, d, di = first_stage(p)
    s = 0.0
    for n in range(1, NHARM + 1):
        if shape == "tri":
            if n % 2 == 0:
                continue
            b = (vpp / 2) * 8 / (math.pi ** 2 * n * n)
        else:
            b = vpp / (math.pi * n)
        s += b * transfer(n * FSW_MIN, p)
    return vpp, 2 * s, transfer(FSW_MIN, p), d, di


def holdup(p_load, v0, i_lim, c, t_end=0.020, steps=20000):
    v, dt = v0, t_end / steps
    for _ in range(steps):
        v += (i_lim - p_load / v) / c * dt
        if v <= 1.0:
            return 0.0
    return v


def min_c(p_load, v0, i_lim, v_floor):
    if i_lim * v_floor >= p_load:
        return 0.0
    lo, hi = 1e-5, 1.0
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        if holdup(p_load, v0, i_lim, mid) >= v_floor:
            hi = mid
        else:
            lo = mid
    return hi


def node_clamp(vbus, r, t_amb=25.0, self_heat=False):
    """Zener node voltage behind series r. Upper bound: VZ max at 5 mA, no
    rdif credit below 5 mA, linear rdif above (PA), plus SZ max x (Tj - 25 C).
    Tj from Rth(j-a) when self_heat (sustained); solved self-consistently."""
    tj = t_amb
    for _ in range(200):
        vz = VZ_MAX + SZ_MAX * (tj - 25.0)
        v = min(vbus, max(vz, (vz - RDIF * IZT + RDIF * vbus / r) / (1 + RDIF / r)))
        i = (vbus - v) / r
        tj = t_amb + (RTH_JA * v * i if self_heat else 0.0)
    return v, i, tj


def fixed_current_bound(vbus, r, t_amb):
    """Non-self-consistent upper bound: current fixed at (vbus - VZ max)/r."""
    i = (vbus - VZ_MAX) / r
    tj = t_amb + RTH_JA * VZ_MAX * i
    return VZ_MAX + SZ_MAX * (tj - 25.0), i, tj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    root = Path(ap.parse_args().root)
    mod = load_alt(root)
    probes, anc, _ = mod.load_probes(root)
    vmax = {k: BAND[k][1] for k in RAILS}

    print("SCREENING ARITHMETIC ONLY - filter/efficiency values PA; ripple, stability,"
          " surge, thermal, startup NOT RUN\n")
    print("R2. Board input current at OSC source-band maxima (12.3/12.2/5.1 V), A")
    icont = {}
    for es, eta in mod.ETA.items():
        for name in ("planning", "continuous", "transient"):
            p = pin_at(mod, probes[name], anc, eta, vmax)
            icont[(es, name)] = (p, p / 18.67, p / 18.4)
            print(f"  {es:5s} {name:10s} Pin {p:6.2f} W  18.67 V {p / 18.67:5.3f}  "
                  f"18.4 V {p / 18.4:5.3f}")
    i_cont_max = max(v[2] for (e, n), v in icont.items() if n == "continuous")
    i_cont_min = min(v[1] for (e, n), v in icont.items() if n == "continuous")

    print("\nR3a. Input-limit window: need I_lim,min >= I_cont and I_lim,max <= 3.0 A")
    for lab, i in (("PD screen base", 2.56), ("PD screen -5pt @18.4 V", 2.76),
                   ("OSC basis min", i_cont_min), ("OSC basis max", i_cont_max)):
        print(f"  {lab:24s} I_cont {i:5.3f} A -> allowed max/min ratio {I_CONTRACT / i:5.3f}"
              f" (+/-{(I_CONTRACT / i - 1) / (I_CONTRACT / i + 1) * 100:4.2f} %)")
    for lab, ratio in LIMITERS:
        imin = I_CONTRACT / ratio
        print(f"  {lab:58s} ratio {ratio:5.3f}; with max at 3.0 A, min {imin:5.3f} A")

    print("\nR3b. Hold-up for 20 ms at constant transient power, limiter at its minimum")
    i_lim = I_CONTRACT / LIMITERS[2][1]
    for es in mod.ETA:
        p = icont[(es, "transient")][0]
        pc = icont[(es, "continuous")][0]
        for v0 in (18.67, 18.4):
            cells = []
            for vf in (v0 - 1.0, 14.0):
                c = min_c(p, v0, i_lim, vf)
                cells.append(f"floor {vf:5.2f} V: {c * 1e3:5.2f} mF")
            margin = i_lim - pc / v0
            rec = (min_c(p, v0, i_lim, v0 - 1.0) * 1.0 / margin) if margin > 0 else float("inf")
            print(f"  {es:5s} V0 {v0:5.2f} Pin_tr {p:5.2f} W I_lim {i_lim:5.3f} A  "
                  + "  ".join(cells)
                  + f"  recharge margin {margin * 1000:6.0f} mA, 1 V recharge {rec * 1000:7.0f} ms")
    for c, i in ((4.7e-3, 1.0), (4.7e-3, 2.0), (10e-3, 1.0)):
        print(f"  pre-enable charge {c * 1e3:4.1f} mF to 20 V at {i:.1f} A: {c * 20 / i * 1000:5.0f} ms")

    print("\nR4a. Ripple screen (worst Vin, fsw 450 kHz min, harmonics 1..50)")
    for k in RAILS:
        p = FILT[k]
        vpp, out, h1, d, di = ripple_out(p)
        f0 = 1 / (2 * math.pi * math.sqrt(p["Lf"] * p["C2"]))
        z0 = math.sqrt(p["Lf"] / p["C2"])
        peak = max(transfer(f0 * (0.5 + 0.01 * i), p) for i in range(150))
        print(f"  {k:7s} D {d:.3f} dIL {di:4.2f} A  C1 ripple {vpp * 1000:5.1f} mVpp  "
              f"f0 {f0 / 1000:4.1f} kHz Z0 {z0:4.2f} ohm peak gain {peak:4.2f}  "
              f"H(fsw) 1/{1 / h1:5.0f}  out {out * 1000:6.3f} mVpp vs {RIPPLE_LIMIT_MVPP} mVpp")
        print(f"          ESL/Lf floor 1/{p['Lf'] / p['esl2']:5.0f}; Lf self-resonance "
              f"{1 / (2 * math.pi * math.sqrt(p['Lf'] * p['Cp'])) / 1e6:5.1f} MHz (PA Cp)")

    print("\nR4b. Source-band budget (half-band vs worst-case sum), V")
    for k in RAILS:
        p = FILT[k]
        lo, hi = BAND[k]
        vset = (lo + hi) / 2
        half = (hi - lo) / 2
        kdiv = 1 - VREF / vset
        e_int = vset * (VREF_TOL + 2 * DIV_TOL_INTERNAL * kdiv)
        e_srv = vset * (SERVO_INIT + SERVO_TC * SERVO_DT + 2 * DIV_TOL_SERVO * kdiv)
        zpk, fpk = zout_peak(p)
        dstep = p["step"] * zpk
        rip = ripple_out(p)[1] / 2
        ptc = I_MAX_TERMINAL[k] * R_PTC_MAX
        for lab, e in (("internal VFB", e_int), ("precision servo", e_srv)):
            tot = e + dstep + rip
            if e + rip > half:
                verdict = "FAIL (setpoint alone)"
            else:
                verdict = ("UNRESOLVED: step amplitude/edge PA" + (", exceeds at PA step"
                           if tot > half else ""))
            print(f"  {k:7s} {lab:15s} half-band {half:5.3f}  setpoint {e:5.3f}  step "
                  f"{dstep:5.3f} (|Zout| {zpk:4.2f} ohm @ {fpk / 1e3:4.1f} kHz)  "
                  f"ripple/2 {rip * 1e3:6.3f} mV  sum {tot:5.3f}  {verdict}")
        tcr = vset * 10e-6 * SERVO_DT
        print(f"  {k:7s} UNAV servo terms: divider TCR tracking 10 ppm/K x 65 K = "
              f"{tcr:5.3f} V; long-term drift, solder shift, authority clamp UNAV")
        for frac in (0.8, 1.0, 1.2):
            z, f = zout_peak(p, C_OSC[k] * frac)
            print(f"  {k:7s} with OSC load C {C_OSC[k] * frac * 1e6:5.0f} uF: peak |Zout| "
                  f"{z:4.2f} ohm @ {f / 1e3:4.1f} kHz -> step {p['step'] * z:5.3f} V")
        print(f"  {k:7s} PTC drop outside loop at R1max, {I_MAX_TERMINAL[k]} A: {ptc:5.3f} V "
              f"= {ptc / (hi - lo) * 100:4.0f} % of the band width")

    print("\nTVS. BZX84-C24 local clamp behind 470 ohm (VZ/rdif/SZ/Rth G; linear model PA)")
    print(f"  TVS2200 margin: {STUSB_ABS - 28.0:+.2f} V at 40 A/27 C, "
          f"{STUSB_ABS - TVS2200_CLAMP:+.2f} V at 35 A/125 C")
    for lab, vbus, heat in (("8/20 us transient at clamp, no RC", TVS2200_CLAMP, False),
                            ("sustained at TVS VBR max", TVS2200_VBR_MAX, True)):
        for ta in (25.0, 50.0, 70.0):
            v, i, tj = node_clamp(vbus, 470.0, ta, heat)
            print(f"  {lab:36s} Ta {ta:4.0f} C: node {v:5.2f} V (margin "
                  f"{STUSB_ABS - v:5.2f} V), I {i * 1e3:4.2f} mA, P {v * i * 1e3:4.0f} mW, "
                  f"Tj {tj:5.1f} C")
    for ta in (50.0, 70.0):
        v, i, tj = fixed_current_bound(TVS2200_VBR_MAX, 470.0, ta)
        print(f"  sustained, fixed-current bound       Ta {ta:4.0f} C: node {v:5.2f} V (margin "
              f"{STUSB_ABS - v:5.2f} V), I {i * 1e3:4.2f} mA, P {VZ_MAX * i * 1e3:4.0f} mW, "
              f"Tj {tj:5.1f} C")
    i_vben = (TVS2200_CLAMP - VZ_MAX) / 250e3
    print(f"  VBEN via R11+R12 250 kohm: I <= {i_vben * 1e6:4.1f} uA; node <= "
          f"{VZ_MAX + SZ_MAX * 45:5.2f} V at 70 C (no self-heat)")
    print(f"  VBEN zener leakage at 21 V through R11 100 kohm: 1 uA -> VGS {1e-6 * 1e5:4.2f} V")
    print(f"  VREG_2V7 pull-up load with SCL/SDA low: {I_PULLUPS_LOW * 1e3:4.2f} mA")
    for idd in (IDD_IDLE_MAX, IDD_IDLE_MAX + I_PULLUPS_LOW, 2e-3):
        rmax = (4.75 - VDD_MIN_OP) / idd
        print(f"  VDD series R limit for {idd * 1000:4.2f} mA (vSafe5V 4.75 V PA): "
              f"R <= {rmax:6.0f} ohm; drop at 470 ohm {idd * 470:5.3f} V")


if __name__ == "__main__":
    main()
