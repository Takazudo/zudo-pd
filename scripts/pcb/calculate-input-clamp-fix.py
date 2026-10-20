#!/usr/bin/env python3
"""Board P input-clamp fix screens for manufacturing/input-clamp-fix.md.

SCREENING ARITHMETIC ONLY. No schematic, PCB, NVM or part selection is
changed. Manufacturer limits are quoted with their evidence class in
manufacturing/input-clamp-fix.md; series resistors, thermal assumptions and
the linear zener model are PROJECT_ASSUMPTIONS (PA). Nothing is measured.
The surge envelope (waveform, energy, cable inductance, repetition) is
undefined, so every margin holds only at the stated datasheet points.
Deterministic, Python standard library only.

Usage: python3 scripts/pcb/calculate-input-clamp-fix.py
"""

import sys

sys.dont_write_bytecode = True

# STUSB4500 DS12499 Rev 8 Table 20 (G-U: the owner bundle records mirror
# evidence; b1-gates read st.com directly, promotion is separate): VDD,
# VBUS_EN_SNK, VBUS_VS_DISCH, DISCH and POWER_OK2 28 V absolute maximum;
# CC1/CC2 and CC1DB/CC2DB 22 V; VDD operating 4.1-22 V.
STUSB_ABS = 28.0
STUSB_CC_ABS = 22.0

# Maximum VBUS in normal operation (PA): nominal + 5 % source tolerance.
VBUS_MAX = {"15 V": 15.75, "20 V": 21.0}

# Primary clamps: (label, VC, condition, class)
SMAJ16A_VC = 26.0          # G: 15.4 A, 10/1000 us, 25 C (owner bundle)
SMAJ16A_VBR_MAX = 19.7     # G: 1 mA, 25 C
SMAJ16A_TC = 0.001         # TYP: VBR coefficient 0.1 %/K, not a VC bound
# TVS clamps are 8/20 us only; initial Tj = 125 C is before the surge.
TVS1800 = {"27 C 40 A": 23.4, "125 C 35 A": 24.7}   # G, SLVSED4A, 8/20 us
TVS1800_VBR = (19.5, 23.8)                           # G, 1 mA
TVS2200 = {"27 C 40 A": 28.0, "125 C 35 A": 28.35}  # G, SLVSED5C, 8/20 us
TVS2200_VBR_MAX = 27.6                               # G, 1 mA

# Nexperia BZX84 series Rev 7 (G): VZ min/max at 5 mA, rdif max, SZ max,
# IR max at VR; Rth(j-a) <= 500 K/W, Tj <= 150 C, Ptot 250 mW.
ZENERS = {
    "BZX84-C20": dict(vz_min=18.8, vz_max=21.2, rdif=55.0, sz=0.018, ir_vr=14.0),
    "BZX84-C24": dict(vz_min=22.8, vz_max=25.6, rdif=70.0, sz=0.022, ir_vr=16.8),
}
IZT, RTH_JA = 5e-3, 500.0
R_SERIES = 470.0  # PA, as R13/R14 on the fitted Board P

# LTC4367 Rev C (G): OV reference 492.5 / 500 / 507.5 mV; tGATE(FAST) 2 typ /
# 6 max us (CGATE 2.2 nF); VIN absolute maximum 100 V.
LTC4367_REF = (0.4925, 0.500, 0.5075)
R_TOL = 0.01  # PA, 1 % divider resistors


def node_clamp(z, vin, r, t_amb, self_heat):
    """Upper bound on the zener node behind series r (same model as
    calculate-b1-gates.py): VZ max at 5 mA, no rdif credit below 5 mA, linear
    rdif above (PA), plus SZ max x (Tj - 25 C); Tj from Rth(j-a) if sustained."""
    tj = t_amb
    for _ in range(200):
        vz = z["vz_max"] + z["sz"] * (tj - 25.0)
        v = min(vin, max(vz, (vz - z["rdif"] * IZT + z["rdif"] * vin / r) / (1 + z["rdif"] / r)))
        i = (vin - v) / r
        tj = t_amb + (RTH_JA * v * i if self_heat else 0.0)
    return v, i, tj


def ov_window(target, ref):
    """OV trip window for a divider set so the typical trip equals target."""
    k = target / ref[1]
    lo = ref[0] * k * (1 - R_TOL) / (1 + R_TOL)
    hi = ref[2] * k * (1 + R_TOL) / (1 - R_TOL)
    return lo, hi


def main():
    print("SCREENING ARITHMETIC ONLY - nothing measured; surge envelope undefined;")
    print("margins hold only at the stated datasheet points\n")

    print("1. Primary clamp vs STUSB4500 28 V absolute maximum")
    print(f"  SMAJ16A (fitted, 15 V)  VC {SMAJ16A_VC:5.2f} V 10/1000 us 25 C (G): "
          f"margin {STUSB_ABS - SMAJ16A_VC:+.2f} V")
    for tj in (85.0, 125.0):
        vc = SMAJ16A_VC * (1 + SMAJ16A_TC * (tj - 25.0))
        print(f"  SMAJ16A TYP-scaled, initial Tj {tj:3.0f} C before surge (estimate, not a bound): VC {vc:5.2f} V, "
              f"margin {STUSB_ABS - vc:+.2f} V")
    for name, d in (("TVS1800 (15 V cand.)", TVS1800), ("TVS2200 (20 V cand.)", TVS2200)):
        for cond, vc in d.items():
            print(f"  {name:22s} VC {vc:5.2f} V 8/20 us {cond}{' (initial Tj, before surge)' if '125' in cond else ''} (G): "
                  f"margin {STUSB_ABS - vc:+.2f} V")
    for opt, vmax in VBUS_MAX.items():
        print(f"  {opt} VBUS max {vmax:5.2f} V (PA): SMAJ16A VBR min 17.8 V "
              f"{'clear' if vmax < 17.8 else 'CONDUCTS'}; TVS1800 VBR min {TVS1800_VBR[0]} V "
              f"{'clear' if vmax < TVS1800_VBR[0] else 'CONDUCTS'}; TVS2200 VRWM 22 V "
              f"{'clear' if vmax <= 22.0 else 'exceeds'}")

    print("\n2. Per-pin 470 ohm + zener behind the primary clamp (linear model PA)")
    cases = (
        ("15 V", "BZX84-C20", "SMAJ16A 25 C clamp, transient", SMAJ16A_VC, False),
        ("15 V", "BZX84-C20", "SMAJ16A init Tj 125 C TYP-scaled", SMAJ16A_VC * 1.1, False),
        ("15 V", "BZX84-C20", "sustained at SMAJ16A VBR max", SMAJ16A_VBR_MAX, True),
        ("15 V", "BZX84-C20", "TVS1800 init Tj 125 C clamp", TVS1800["125 C 35 A"], False),
        ("20 V", "BZX84-C24", "TVS2200 init Tj 125 C clamp", TVS2200["125 C 35 A"], False),
        ("20 V", "BZX84-C24", "sustained at TVS2200 VBR max", TVS2200_VBR_MAX, True),
    )
    for opt, zn, lab, vin, heat in cases:
        z = ZENERS[zn]
        for ta in (25.0, 70.0, 125.0):
            v, i, tj = node_clamp(z, vin, R_SERIES, ta, heat)
            pw = v * i
            print(f"  {opt} {zn} {lab:32s} in {vin:5.2f} V Ta/init Tj {ta:3.0f} C: node {v:5.2f} V "
                  f"(margin {STUSB_ABS - v:+.2f} V), I {i * 1e3:5.2f} mA, P {pw * 1e3:4.0f} mW"
                  f"{' > Ptot 250 mW (transient only)' if pw > 0.25 else ''}, Tj {tj:5.1f} C")
    for opt, zn in (("15 V", "BZX84-C20"), ("20 V", "BZX84-C24")):
        z = ZENERS[zn]
        print(f"  {opt} {zn}: VZ min {z['vz_min']:5.2f} V vs VBUS max {VBUS_MAX[opt]:5.2f} V "
              f"-> {z['vz_min'] - VBUS_MAX[opt]:+.2f} V; IR guaranteed only at "
              f"{z['ir_vr']} V (0.05 uA); IR at {VBUS_MAX[opt]} V UNAV")
    print("  VBUS_EN_SNK is fed through R11 + R12 = 250 kohm, not 470 ohm: the model is conservative there")
    print(f"  VBEN zener leakage through R11 100 kohm: 1 uA -> {1e-6 * 1e5:4.2f} V on Q1 VGS (PA limit)")

    print("\n3. Input OVP front end (LTC4367 class; ref G, divider 1 % PA)")
    for opt, target in (("15 V", 18.0), ("20 V", 23.5)):
        lo, hi = ov_window(target, LTC4367_REF)
        print(f"  {opt}: OV typ {target:4.1f} V -> trip {lo:5.2f}-{hi:5.2f} V; "
              f"above VBUS max {lo - VBUS_MAX[opt]:+.2f} V; below 28 V {STUSB_ABS - hi:+.2f} V")
    print("  Downstream exposure during tGATE(FAST) <= 6 us: UNAV (needs the surge envelope)")

    print("\n4. CC1/CC2 vs 22 V absolute maximum (CC-to-VBUS short)")
    for opt, vmax in VBUS_MAX.items():
        print(f"  {opt}: short at VBUS max {vmax:5.2f} V -> margin {STUSB_CC_ABS - vmax:+.2f} V")
    for name, vc in (("SMAJ16A 25 C", SMAJ16A_VC), ("TVS1800 125 C", TVS1800["125 C 35 A"]),
                     ("TVS2200 125 C", TVS2200["125 C 35 A"])):
        print(f"  short during a surge at {name} clamp {vc:5.2f} V -> margin {STUSB_CC_ABS - vc:+.2f} V")


if __name__ == "__main__":
    main()
