# V196 fail-OFF window: does not close with lifecycle tolerances; BOM-only retune recommended

**Verdict: the V196 voltage-qualification window does NOT close once resistor lifecycle
drift is included.** It closes only with initial tolerance plus TCR (L0), with 0.129 V of
margin. With the soldering-heat shift it is effectively zero (0.006 V, L1). With the
endurance shift it is negative (−0.116 V, L2). The recommended fix, option O3, changes
one resistor value: RMH2 180 k → 187 k. It needs no copper change and restores
**+0.155 V at L2**. It requires RAW ≥ 14.0 V to turn on, which is adequate for the
LED-first board but not for the 3 A common-board use.

This is arithmetic from the hashed primary documents in
[`analysis/SOURCES.json`](analysis/SOURCES.json), reproduced by
`analysis/failoff_window.py` → `analysis/failoff_window.json`. It is not a simulation or
a measurement. Pass/fail limits marked *proposed* have no external source.

## Why the window is needed (primary evidence)

HUSB238 Rev2.5 p10/p15 says _006DD uses **Next PDO** on RDO mismatch and asserts
**GATE During Contract**. The RDO is 15 V / 3 A (VSET 14 k, ISET 22.6 k; p9–10). The
search starts from the highest PDO and needs PDO V ≤ 15 V and PDO I ≥ 3 A. So a source
without a 15 V ≥ 3 A PDO, but with 12 V/3 A, produces a **12 V contract with GATE
asserted**. The same happens after re-advertisement (multiport redistribution).
Contract-qualified GATE therefore does not exclude 12 V. Only the voltage path can.
HUSB UVP is disabled by default (p11), and HUSB OVP is 115–125 % of the requested voltage
(17.25–18.75 V at 15 V; p6).

Requirements used here:

- **Reject:** RAW ≤ 12.6 V must be OFF. Conditional: 12 V +5 % static, as in V15. The
  12 V transient envelope is not retained.
- **Accept:** RAW ≥ floor must be ON. The floor is *proposed*: 13.5 V (14.25 V source
  minimum − 0.75 V unsourced allowance) or 14.0 V (O3).

## Tolerance inputs

| Item | Value | Source |
| --- | --- | --- |
| TPS3701 INA falling / rising | 397–403 mV / 400–413 mV, TJ −40…125 °C | TI SBVS240C 6.5 |
| TPS3701 IIN | ±25 nA | SBVS240C 6.5 |
| TPS25947 EN/UVLO and OVLO rising / falling | 1.183–1.223 V / 1.076–1.116 V | TI SLVSFC9C 6.5 |
| TPS25947 pin leakage | ±0.1 µA | SLVSFC9C 6.5 |
| QINH collector leakage | 1 µA | **assumption** carried from V15, not a manufacturer bound |
| RT0603BRD resistor | 0.1 %, 25 ppm/K | Yageo RT V.17 ordering code |
| Lifecycle shifts | ±(0.5 % + 0.05 Ω) each for resistance to soldering heat and 1000 h endurance | Yageo RT V.17 Table 4 |
| Temperature excursion | 100 K from 25 °C | assumption, covers the HUSB −40…85 °C ambient range |

Each resistor is treated as independently worst-case; no ratio tracking is assumed.
Levels: **L0** = 0.35 % (initial + TCR); **L1** = 0.85 % (+ soldering heat);
**L2** = 1.35 % (+ endurance).

## V196 results

| Path | Level | Rising (ON) band | Falling (OFF) band | Reject-12.6 margin |
| --- | --- | --- | --- | --- |
| TPS3701, 313 k / 10 k | L0 | 12.825–13.439 | 12.729–13.113 | **+0.129** |
| | L1 | 12.701–13.569 | 12.606–13.241 | **+0.006** |
| | L2 | 12.579–13.702 | 12.484–13.370 | **−0.116 FAIL** |
| U2 UV, 97.6 k / 10 k (+1 µA QINH) | L2 | 12.316–13.595 | 11.192–12.415 | none (backup only) |
| U2 OV, 133 k / 10 k | L2 | 16.485–17.948 | 14.992–16.379 | n/a |

Consequences:

- **At L2, a 12.6 V cold-start 12 V contract can pass both stages.** U2's UV rising
  minimum (12.32 V) and TPS3701's rising minimum (12.58 V) are both below 12.6 V.
- At L1 and L2, the accept floor of 13.5 V also fails (TPS3701 rising maximum 13.57 V
  and 13.70 V).
- U2 OV falling minimum at L2 is 14.99 V. After an OV trip, recovery at a nominal
  15.0 V is not guaranteed. OV rising minimum 16.49 V stays above the retained 15 V
  transient high of 16.25 V.

## Options

| Option | Change | Result | Orderable evidence | Cost / impact |
| --- | --- | --- | --- | --- |
| **O3 (recommended for this LED-first revision)** | RMH2 180 k → **187 k** (RT0603BRD07187KL, 0.1 %/25 ppm); Rtop = 320 k, Rb = 10 k. Value change only, same 0603 land | L2: OFF guaranteed ≤ 12.755 V (**+0.155 V**); rising band 12.851–13.999 V; once ON, stays ON down to 13.660 V. At L2 the cold-start 12 V case is rejected (rising minimum > 12.6) | MPN pattern from the Yageo RT ordering code; **JLC/LCSC code not verified** (LCSC search returned 403, not bypassed) | Supported scope becomes "RAW ≥ 14.0 V". Against the 14.25 V source minimum that leaves a 0.25 V input-path drop budget; at an illustrative 0.41 A LED load that is ≤ 0.61 Ω cable + connector. Not adequate for 2–3 A common-board use |
| O2 | Keep 006DD. Replace the 313 k / 10 k discrete pair with a ratio-specified precision divider or network, or a monitor with a tighter threshold spread | Could restore the 13.5 V floor and the 12.6 V rejection for the common board | **None obtained**: no candidate with primary ratio-drift data or JLC availability was found in this pass | New part and land; needed for the PD-derivative board |
| O1 | HUSB238 variant **_004DD** ("Request 5V" on mismatch, GATE During POR; Rev2.5 p15) | A mismatch falls to 5 V, which U2 UV rejects with several volts of margin; 12 V never appears | JLC lists HUSB238_004DD only as C9900000966, brand "JLCPCB Assembly", stock 0 (2026-10-31 snapshot). Hynetek-brand listing not found | Under the literal p10 rule the **highest** PDO is tested first, so a 20 V-capable charger (5/9/15/20 V) would get 5 V. Severe compatibility loss; changes the user-selected part. Not recommended |

**Recommendation: O3 now** (BOM-only, applied in a later candidate revision after
approval; V198 below is field-sync only). Keep the stated scope: LED-first board,
15 V-capable PD source with RAW ≥ 14.0 V at the board. Treat O2 as the required
investigation for the common/PD derivative board, per the #145 staged plan.

## Related closures

**VSET/ISET decode (evidence gap).** The pin current is 95–105 µA (p5), so RVSET 14 k
1 % gives 1.316–1.484 V nominal. Hynetek publishes no decode band boundaries.

- A decode error toward 12 k or 17.8 k cannot be ruled out.
- If VSET is open (assembly defect), it reads as 20 V. A 20 V contract is then blocked by
  the U2 OV rising maximum of 17.95 V (L2). At 20 V, U2 is still inside its 23 V ROC and
  the HUSB inside its 21 V ROC. Result: fail-OFF, but not damage-qualified against
  transients.

**Startup pulse-free (conditionally closed).**

- For RAW ≤ 12.32 V, U2's own UV divider holds EN below its rising threshold at every L2
  corner, independent of QINH or TPS3701.
- TPS3701 is valid once VDD > 1.8 V for 150 µs (typ). Before that, its OUTA is
  undetermined, but RAW is far below the U2 UV threshold.
- This relies on the source presenting vSafe5V (or a ramp) before any higher voltage.
  That is USB Type-C/PD behaviour, not retained as a primary document here, so it is an
  assumption.

**Maximum output-cut delay on contract loss.**

| Event | Cutting path | Delay evidence |
| --- | --- | --- |
| Detach / hard reset (VBUS falls) | U2 UV falling or TPS3701 OUTA | TPS3701 tpd(HL) 9.9 µs *typ*, then U2 tD,OFF 25.32 µs *typ* after the threshold is crossed. No guaranteed maxima. Total time also depends on the VBUS fall rate |
| Overvoltage | U2 OVLO | tOVLO 1.2 µs *typ*; HUSB OVP adds tDB_OV 50 µs typ |
| Renegotiation to 12 V | TPS3701 only | As above, once RAW < falling threshold. Requires O3 at lifecycle corners |
| Contract lost while VBUS stays at 15 V | HUSB GATE release only | **UNBOUNDED**: no GATE release delay is specified in Rev2.5. The voltage path cannot detect this case. Architectural limitation, kept explicit |

There is no guaranteed maximum anywhere in this chain; all available values are typical.
The output then decays through COUT 4.7 µF + RBLEED 2.2 kΩ + Board L load.

**Missing input TVS (open; needs a layout revision).**

- V196 has no TVS on RAW. The bulk is only C1 1 µF + CMON 100 nF, so hot-plug ringing
  on a 15 V cable can approach twice the settled voltage. That would exceed the U2 abs
  max VIN of 28 V (SLVSFC9C 6.1) and the HUSB VIN/GATE abs max of 30 V (Rev2.5 p7). The
  ringing amplitude is not modelled.
- The repo's existing record `component-high-diode-smaj20a-c571370` (SMAJ20A / C571370,
  used on the old Board P) gives VRWM 20 V, VBR 22.2–24.5 V, VC 32.4 V max at 12.3 A
  10/1000 µs. Its standoff suits a 15 V rail and also a 20 V misdecode case.
- Its rated-pulse clamp is above U2's 28 V abs max, so it bounds energy but does **not**
  guarantee U2 protection at rated surge. Low-current clamp behaviour is not in the
  retained record.
- Recommendation: add an SMAJ20A footprint at J1 VBUS in the next layout revision
  (reusing the evidenced part). Characterise hot-plug ringing on the first prototype with
  the stated stop condition: RAW peak ≥ 28 V. Adding the part changes copper, so it is
  a manager/owner decision, not part of V198.

## Sourcing observation for U1 (dated, not a quote)

JLC part page C55013903 (Hynetek HUSB238_006DD), 2026-10-31 snapshot:

- library type "expand"
- overseas stock 0
- pre-sale 0
- pre-order minimum purchase 441
- reel 3000
- loss number 4

This bears on the BOM's MOQ/surplus line: two boards would need far fewer than 441 if a
pre-order is required. Recheck at order preparation.
