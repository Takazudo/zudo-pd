# D1 T2 rev 2 (a2 output limiter) on −12 V under the revised rules — DRAFT, not yet pre-registered

**Status: DRAFT.** One number is open: the board maximum operating temperature for the DT2C hot case (`HOT_T_C`).
The owner is asking Takazudo for it, and also whether the let-through-held state is in scope. This file becomes the
pre-registration only when that number is filled in, the owner admits it, and it is merged. Nothing has been
dispatched.

**This is a model evaluation of a candidate. Nothing is adopted.** The usual limits hold:
- electrical_acceptance stays NOT ESTABLISHED, and the recorded failures stay failures (+5 V 0.954850860 V/ms /
  114.510041 mA, −12 V 1.474778000 V/ms / 265.259332 mA);
- no spec, schematic, PCB, calculator, ceiling, tolerance or solver option changes;
- a −12 V result does not close D1. +5 V (option B plus the T2 form) follows only after the −12 V result is in.

The code is `t2_rev2.py`, held in step by `test_t2_rev2.py`. The workflow input is `t2_rev2_evaluation`. Admission
came from owner decisions of 2026-11-12:
- (a2) taken to simulation evaluation;
- FJH1100 bound for DT2C;
- BAS116LT1G bound for DT2K;
- the window switch moved to the inverting input;
- the DT2K leakage requirement set by simulation at the 80 nA row;
- VF-spread and ladder cases added.

The paper inputs are:
- [d1-t2-a2-dc-checks-20261112.md](d1-t2-a2-dc-checks-20261112.md);
- the ways-forward comparison, `/mnt/project-files/d1/t2-ways-forward-20261112.md`.

Attempt 1 ([d1-t2-criteria.md](d1-t2-criteria.md)) stays FAILED and is not re-evaluated.

## The candidate (single values)

Everything not listed here is attempt 1's, unchanged: DT2K capture through BT2K, C_H 100 nF, R_B 10 MΩ, BT2R, XT2A,
R_1 1 MΩ, R_2 4.99 MΩ and V_R = REF25.

| Element | Deck line | Value | Change from attempt 1 |
| --- | --- | --- | --- |
| Difference stage | `XT2B t2p t2m p5sup t2n t2a OPAx187` | k = 4.99 | Output node renamed t2a. Feedback `RT2M2 t2m t2a` stays at the op-amp output |
| Output limiter R_O | `RT2O t2a t2o` | 100 kΩ ±1 % | New |
| Limiter diode D_L | `DT2L t2o t2l DT2LX` + `VT2L t2l 0 0` (ammeter) | FJH1100 model as a stand-in | New. t2o ≤ about +VF. Needs no low leakage |
| Clamp diode DT2C | `DT2C t2c t2o DT2CX` | FJH1100 | Sourced model, replacing DBODY |
| R_C | `RT2C t2c t2g` | 402 kΩ ±1 % | 499 → 402 kΩ, so R_C + R_O = 502 kΩ keeps k / R |
| Connection | `VT2G t2g trk12n_fb 0` | permanent; inert control: `VT2G t2g 0 0` | **BT2G deleted.** No switch on the summing node |
| Window | `RT2W t2m t2w` 100 kΩ + `BT2W t2w m12_pre` | closed while v(ennd) < 1.0 (the complement of the reset shape) | New. It forces XT2B high outside the reset window |
| Capture diode DT2K | `DT2K m12_drv t2k DT2KX` | BAS116LT1G | Sourced model, replacing DBODY |
| Leakage | `BT2CL t2o t2c`, `BT2KL t2k m12_drv`, `BT2LL t2l t2o` | Each row's guaranteed maximum, from 0 V up to the row's test voltage. A bias above it takes the next row. FJH1100 is 3 pA up to 5 V and 10 pA from 5 to 15 V. BAS116L is 5 nA up to 75 V | New |

### Diodes: every model value traced; inferences named
| Role | Part | Evidence | Rows used | Inferences |
| --- | --- | --- | --- | --- |
| DT2C, D_L | onsemi FJH1100 | Rev. B1, sha256 `1301249b…`, staged at `/mnt/project-files/d1/fjh1100-evidence/` | CT max 2.0 pF at 0 V (CJO, M = 0); IR max 3.0 pA at 5 V; 15 V working inverse voltage (rating); BV min 30 V (test) | IR at ≤ 0.6 V taken as the 5 V row. VF is typical only (IS, N from 530 / 605 mV at 1 / 10 µA). **No hot row** |
| DT2K | onsemi BAS116LT1G | BAS116LT1/D Rev. 14, sha256 `ce1244d9…`, staged at `/mnt/project-files/d1/dt2k-evidence/` | VR 75 V continuous (rating); IR max 5.0 nA at 75 V, 25 °C; IR max 80 nA at 75 V, TJ 150 °C; CD max 2 pF at 0 V; VF max 900 / 1000 mV at 1 / 10 mA | IR is monotonic in temperature, so the 150 °C row bounds every lower temperature. The 75 V rows apply at ≤ 1.3 V. VF at µA is extrapolated from the 1 mA and 10 mA maxima (about 0.57 V at 0.5 µA) |

Neither part has an LCSC ID. Both are staged outside the inventory, and a repo owner bundle is deferred until the
part is a fitted candidate (owner decision). FJH1100 is light-sensitive.

### Requirements as decided
| Role | Stated reverse rating | Leakage | Capacitance |
| --- | --- | --- | --- |
| DT2C | ≥ 10.6 V (worst case with D_L open). FJH1100 15 V gives 1.42× | IR ≤ about 1.95 nA predicted at rule 6(b) (measured here by the ladder) | Cd(0 V) ≤ 3.5 pF |
| DT2K | ≥ 27.5 V (1.5 × the 18.34 V rail-bounded worst case). BAS116L 75 V gives 4.1× on 18.34 V | **Passes every rule at the 80 nA, 150 °C row** (case k80n). The earlier 5 nA figure is withdrawn: it was a hold-droop budget with an overstated basis (0.48 µA assumed; the bleed is about 0.24 µA) | None (2 pF couples 2e-5 into the hold and has no path to fb) |
| D_L | ≥ 12.8 V (rail-bounded) | None | None |

The 30 V DT2K figure of the 2026-11-12 requirements note was an estimate-based project number (2 × 14.2 V), not a
contract value. The bound is 18.34 V.

## DC checks (done before registration)

Full derivations are in [d1-t2-a2-dc-checks-20261112.md](d1-t2-a2-dc-checks-20261112.md).

| Check | Result |
| --- | --- |
| DT2K reverse voltage | ≤ 18.34 V: P5_SUP max 5.0423 V + \|M12_PRE\| 12.3 V + 2 × 0.5 V input clamps. U3 overvoltage is outside the board's fault boundary (OPA2187 40 V) |
| DT2C reverse voltage | ≤ 6.6 V normal, ≤ 10.6 V with D_L open (fb ≥ −5.54 V via CT12N / RCTZ) |
| D_L reverse voltage | ≤ 12.8 V rail-bounded; about 9.9 V engaged with DRV at M12_PRE |
| Limiter current | 37.1–46.3 µA over the P5_SUP band, the output swing and the VF spread |
| D3 margins | **None consumed.** The limiter current flows P5_SUP → XT2B → R_O → D_L → GND and passes no shunt (RSH12 / RSH5 / RSHN) and no output. The maximum-delivered margins (15.15 / 4.56 / 39.16 mA) and the low-side margins (41.6 / 42.2 / 36.9 mA transient minimum; 8.94 / 13.29 / 29.09 mA startup) are unchanged |
| P5_SUP and AGND | +46 µA at most on P5_SUP. U14's own feedback divider takes 80 µA, against the 2 A device design point. There is no P5_SUP current budget to collide with. GND receives a new static 37–46 µA, which adds 46 nV per mΩ of shared return. The AGND connection is unchanged |
| −12 supply current (rules 3, L3) | Unchanged: the limiter current leaves through XT2B's positive rail |
| Hold droop, first power-up, stale high | Unchanged from attempt 1 (hold side untouched) |
| XT2B inputs: retained VCM row (V−) − 0.1 V to (V+) − 2 V, abs max rails ± 0.5 V | See the table below |

**XT2B inputs across the VF variants.** VF moves only t2o and the limiter current. It does not move t2p or t2m,
because the feedback is taken at t2a.

| State | t2p | t2m | Retained VCM | Abs max |
| --- | --- | --- | --- | --- |
| Running (window closed, output high) | (4.99·DRV + 2.5) / 5.99. At DRV = M12_PRE: −9.83 V | Pulled toward M12_PRE: −11.73 V (t2hb −9.4 V) to −11.99 V (t2hb at M12_PRE). That is 0.31 V or more above V− | Holds while DRV ≤ +3.08 V. t2p > t2m, so the output stays high | Holds |
| Reset window (linear) | Same as t2p above | Equals t2p | Holds while DRV ≤ +3.08 V | Holds |
| DRV saturated high (above +3.08 V; possible only with U9B railed high through DZ3 / RG3) | Up to 4.62 V | — | **Outside the retained row.** This is unchanged from attempt 1: the t2p divider is the same | Holds (≤ P5_SUP + 0.5 V) |

The VS 8–36 V VCM row is not in the retained extract. The deck reports the actual extremes (`a2` metrics) beside
the verdict.

## Cases (one dispatch)

The cases run after the existing nom/adv identity control reproduces, in the order of `t2_rev2.py labels`:

| Label | Deck(s) | Block | Role in the verdict |
| --- | --- | --- | --- |
| base, e12lo, e12hi, e5lo, e5hi | as attempt 1 | — | Baselines and corners, as attempt 1 |
| ctrl | adv | inert control (R_C to GND) | Control gate, as attempt 1 |
| t2, t2lo, t2hi, t2load | as attempt 1 | sourced rows at 25 °C, typical VF | **Required** (sourced cases) |
| vflo, vfhi | nom, adv | D_L VF at 45 µA = 0.46 V / 1.05 V (typical 0.654). The low value is typical − 0.2 V (PROJECT, −2 mV/°C over 100 K); the high value is the 50 mA maximum | **Required** |
| cvflo, cvfhi | nom, adv | DT2C VF at 1 µA (the clamp current) = 0.33 V / 1.05 V. Typical is 0.530; the same low and high rules as D_L | **Required** |
| kvflo, kvfhi | nom, adv | DT2K VF at 0.5 µA = 0.42 V / 0.72 V (the model's 0.57 V ± 0.15 V, PROJECT inference) | **Required** |
| k80n | adv | DT2K IR = 80 nA (the guaranteed 150 °C row), everything else sourced | **Required.** It decides DT2K's leakage requirement |
| k1u | adv | DT2K IR = 1 µA | **Informational**: it locates the DT2K crossing and cannot pass or fail the candidate |
| ir1n, ir2n | adv | DT2C IR = 1 nA / 2 nA | **Informational**: they locate the DT2C rule 6(b) crossing |
| hot | nom, adv | DT2C and D_L IR = 3 pA × 2^((T − 25) / 7) at T = `HOT_T_C`; DT2K IR = 80 nA | **Separate hot verdict** |

Every extra case compares with the pinned reference pair (`run/nom`, `run/adv`).

## Execution rules

- **Separate dispatch.** The workflow rejects `t2_evaluation` and `t2_rev2_evaluation` together, because they
  share the t2 work tree and the control gate.

- **As attempt 1.** Status definitions, the control gate (ctrl COMPLETE and REPRODUCED before any candidate
  label) and the loaded-baseline identity are unchanged. ABORTED means not evaluated and is not retried with pinned
  settings.
- **Matched-variant ladder (admitted).** Only a pinned ABORTED case and its baseline chain are rerun, together, at
  abstol 1e-8, then rshunt 1e9. The variant baseline must match its pinned record within the L2 tolerance over the
  whole run. The t2/adv cross-check runs at each step used.
- Ladder results are **VARIANT-EVALUATED**, never PASS or FAIL. They are reported beside the pinned verdict and
  never replace it.

## Pass rules

- **No-load cases** (t2/nom, t2/adv, t2lo, t2hi and every extra case): rules 1–9 are the revised rules
  (`rules_revision.judge`, [d1-rules-revision-20261112.md](d1-rules-revision-20261112.md)).
  - Rule 6 = (a) the contract screens in the enable window (+5 V below 0.8 V, each analog rail's magnitude below
    1.5 V) and (b) an excursion beyond the baseline extreme of at most 1e-3·|v| + 1e-5 V.
  - Rule 9 uses the same tolerance at the rail level.
- **Rules 10–14** are attempt 1's, unchanged. The clamp current is (v(t2g) − v(t2c)) / 402 kΩ, with t2g ≡ TRK12N_FB.
- **Loaded cases:** L1–L4, unchanged.

### Reported beside each verdict (not pass rules)
The `a2` metrics:
- limiter current, disabled (30–40 ms) and running (200–235 ms);
- t2o maximum in the enable window;
- XT2B input extremes over 20–235 ms (rails settled, before the disable) against the retained VCM row and the
  abs max;
- each diode's peak reverse voltage against its stated rating and its highest leakage row, on the no-load, extra and
  loaded cases. The loaded decks use their startup window only for the input range, and nomR alone for the running
  limiter current;
- the rule 6(b) margin.

### Verdicts
- **Candidate (−12 V).** PASS needs the control REPRODUCED, every sourced case passing (attempt 1's PASS
  definition), and every **required** extra case (vflo, vfhi, cvflo, cvfhi, kvflo, kvfhi on nom and adv; k80n on adv)
  COMPLETE and passing. Any evaluated failure is FAIL. Anything else is NOT EVALUATED.
- **Hot DT2C (separate).** It is PASS or FAIL on its own, at `HOT_T_C`. It does not change the candidate verdict.
- **DT2C failure IR.** A straight line through the rule 6(b) margins of t2/adv (3 pA), ir1n and ir2n gives the
  zero crossing. It is also stated as a temperature: T = 25 + 7·log2(IR / 3 pA). The fit is a PROJECT inference.
- **Standing limitation, whatever the result.** FJH1100 over-temperature IR is UNSOURCED. That blocks adoption
  until it is sourced or bench-measured. The BAS116L inferences (monotonic in temperature; the 75 V rows applied at
  ≤ 1.3 V) are recorded beside the verdict.

## Predictions (stated before the run)

| Quantity | Predicted |
| --- | --- |
| Rule 6(b), sourced cases | About 20 µV coupling + 4.2 µV loading against 107 µV: pass |
| DT2C failure IR | About 1.95 nA, which is 90.4 °C on the 7 °C doubling |
| Hot DT2C | PASS if `HOT_T_C` < about 90 °C local to DT2C, FAIL above. **If the owner's temperature is 90.4 °C or more, this is a predicted fail before dispatch, and the owner decides whether to run at all** |
| k80n | Floor lowered by about 34 mV (3 % of the 1.16 V below-peak). No rule failure expected; unproven, because rule 1 is exposed to the extra windup |
| Limiter current | 37–46 µA running; about 23 µA disabled (output about 2.76 V) |
| Release swing at t2o | Cd × about 1.4 V ≈ 2.8 pC, giving 0.28 mV DRV against rule 12's 50 mV |
| XT2B inputs | Within the retained VCM row except where DRV exceeds +3.08 V. Within abs max throughout |

## Open before registration
1. `HOT_T_C`: the board maximum operating temperature (and whether let-through-held is in scope). The repo states
   no board maximum. The desk thermal model assumes a 40 °C ambient (`boards/board-b20-draft/thermal-check.json`).
