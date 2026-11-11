# D1 T2 peak-hold anti-windup clamp on −12 V, with the enable-edge threshold corners — pre-registered 2026-11-11

**This is a model evaluation of a candidate. Nothing is adopted.** It makes no claim about any real part.
- electrical_acceptance stays NOT ESTABLISHED, and the recorded failures stay failures (+5 V 0.954850860 V/ms /
  114.510041 mA, −12 V 1.474778000 V/ms / 265.259332 mA).
- No spec, schematic, PCB, calculator, ceiling, tolerance, solver option or model changes.
- A −12 V only pass does not close D1. **D1 stays held until +5 V has an answer** (owner decision 2026-11-11).

`t2_clamp.py` implements exactly these decks and rules, and `test_t2_clamp.py` keeps the numbers in step.
The paper check that admitted this evaluation is [d1-t2-paper-check-20261111.md](d1-t2-paper-check-20261111.md).

## Scope (owner decision 2026-11-11, option 1)

**T2 on +5 V is REJECTED by construction.**
- RG2P (100 kΩ, P5_G to P5_CS) carries Vgs/100 kΩ.
- With the pair off, that current leaves P5_CS only through Q4's body diode, into P5_OUT. Any gate held near the
  edge at no load therefore injects 8–20 µA into the output, against a 1.6 µA divider drain. That is a
  threshold-dependent pedestal.

**Constraint on any future gate-hold scheme.** On +5 V and +12 V (RG1P, and Q2's body diode into P12_OUT), avoiding
an output pedestal at no load needs an idle Vgs of about 0.16 V or less (Vgs / 100 kΩ ≤ 1.6 µA). That leaves
almost the whole dead zone. The constraint holds until the gate pull-down return is changed.

**−12 V is evaluated here.** RG3P's current leaves M12_CS through Q5's body diode to M12_SH, and Q6's diode
stays reversed by about 12 V, so no gate-network current reaches the output.

## The candidate (single values; tolerances stated, not swept)

| Element | Deck line | Value | Tolerance and part class (adoption paper only) |
| --- | --- | --- | --- |
| Peak capture diode | `DT2K m12_drv t2k DBODY` | existing DBODY model | low-leakage small-signal diode |
| Capture gate | `BT2K t2k t2h …` | on while v(ennd) > 1.2 V (tanh × 30) | logic from RAMP_RST timing |
| Hold capacitor C_H | `CT2H t2h m12_pre` | 100 nF | C0G, ±5 % |
| Hold bleed R_B | `RT2B t2h m12_pre` | 10 MΩ | ±1 % |
| Hold reset | `BT2R t2h m12_pre …` | on while EN_N is high (the decks' disable shape) | switch on EN_N |
| Hold buffer | `XT2A t2h t2hb p5sup t2n t2hb OPAx187` | unity follower | second OPA2187 section |
| Difference stage | `XT2B t2p t2m p5sup t2n t2o OPAx187` | out = V_R + k·(DRV − held), k = 4.99 | first OPA2187 section |
| R_1 (two) | `RT2P1`, `RT2M1` | 1.00 MΩ | ±0.1 % |
| R_2 (two) | `RT2P2` to V_R, `RT2M2` | 4.99 MΩ | ±0.1 % |
| V_R | `ref25` | existing 2.5 V reference node | as the reference |
| Clamp diode | `DT2C t2c t2o DBODY` | existing DBODY model | low-leakage small-signal diode |
| R_C | `RT2C t2c t2g` | 499 kΩ | ±1 % |
| Clamp gate | `BT2G t2g trk12n_fb …` | the decks' own RAMP reset shape (v(ennd) > 1.0, tanh × 8) | switch on RAMP_RST |
| Op-amp supply | `VT2N t2n m12_pre 0` | 0 V; measures the candidate's own −12 V supply current | P5_SUP / M12_PRE, like U15/U16 |

- **Models.** The clamp and buffer use the deck's existing OPAx187 macro; the diodes use the deck's existing
  DBODY. Switches use the decks' existing behavioural idiom: 3.5 Ω on, a permanent 100 MΩ term. No vendor model
  bytes are added. The OPA2187 owner and inventory check is paper only, for an adoption package.
- **Changed from the paper check.** The paper check's k = 10, R_C = 1 MΩ became k = 4.99, R_C = 499 kΩ. The
  ratio k / R_C is the same, so the loop is the same, and the offset now fits the 5 V supply with V_R = 2.5 V.
  The floor became about 1.0 V below the peak instead of about 0.86 V.
- **What Δ is.** The designed floor is DRV held about **1.0 V below its enable-edge peak** (prediction below).
  It comes from the capture diode drop (about 0.32 V at the bleed current) plus the difference-stage offset
  (V_R + clamp-diode drop + I_C·R_C) / k ≈ (2.5 + 0.36 + 0.53 + 0.01) / 4.99 ≈ 0.68 V.
- **Hold droop.** τ = C_H × (R_B ∥ 100 MΩ) = 0.909 s. Over the longest idle the cases cover, from the peak to the
  reference start (about 50 ms), the hold falls about 5 %, about 0.12 V. Over the longest clamp-active span, peak
  to v(ennd) ≈ 0.3 V (about 105 ms), it falls about 11 %, about 0.25 V. Droop only lowers the floor (less drive),
  the safe direction.
- **Stale high is excluded by construction.** The hold is reset while EN_N is high. It captures only early in the
  reset window, not during tracking. The clamp only pushes DRV up to a floor below the held edge, so it cannot
  turn the pair on.
- **First power-up.** Before the first enable the hold is reset and the clamp output sits at about V_R (inactive).
  In the decks EN_N is high for 40 ms, so v(ennd) is 2.89 V at enable and the capture window lasts about 41 ms.
  The edge is found 27–32 ms after enable.

## Cases (one dispatch; at most two dispatches, the second only if the first is RUN FAILED)

All cases run after the existing nom/adv identity control reproduces. Labels run in this order:

| Label | Deck(s) | Change from the retained deck | Purpose |
| --- | --- | --- | --- |
| base | nomR, reR6, reR20 | none; each with its accepted solver variant (reR6 abstol, reR20 rshunt) | Loaded baselines. They must reproduce their recorded waveform hashes |
| e12lo, e12hi | nom | `VO3` −0.66 V / +0.54 V; 240 ms disable; gate output line | Enable-edge corners; baselines for t2lo/t2hi |
| e5lo, e5hi | nom | `VO2` −0.66 V / +0.54 V; same additions | Enable-edge corners (+5 V report) |
| ctrl | adv | T2 block with its output returned to GND (inert); Q6 drain ammeter; same additions | Inert-candidate control |
| t2 | nom, adv | T2 block; Q6 drain ammeter; same additions | Model corner and the recorded D1 failure deck |
| t2lo, t2hi | nom | `VO3` −0.66 / +0.54 V plus T2 | Threshold corners |
| t2load | nomR, reR6, reR20 | T2 block; Q6 drain ammeter | Full load; 19.0 ms and 20 ms off re-enable |

- **Corner mapping.** The corners map the model's 250 µA point (2.163 V on the +5 V ramp) onto the guaranteed
  VGS(th) of 1.5 V and 2.7 V. A positive offset lowers the internal gate, which emulates a higher threshold.
- **Re-enable.** reR6 requests the re-enable 6 ms after disable. The minimum-off interlock (RHO 300 kΩ, CHO
  0.6 µF) holds it until about 19.0 ms. reR20 re-enables at 20 ms. Both decks are at full load.
- **The Q6 drain ammeter** (`VIQ6 m12_out t2q6 0`) measures the channel current into the output. It is present in
  every T2 deck and in the control.
- **Output-only lines.** `wrdata <deck>-t2.txt` saves DRV, the hold and buffer, the clamp nodes, TRK12N_FB,
  TRK12N, MABS_N, M12_PRE, i(VIQ6), i(VT2N) and v(ennd).
- **Supply current.** In every T2 deck the −12 V supply current used by the rules is i(VM12) − i(VT2N). That is
  the supply current without the candidate's own op-amp supply.

## Enable-edge corner verdict (e12lo, e12hi, e5lo, e5hi)

Each corner is measured on its own rail: the peak internal Vgs over 40–110 ms, the onset Vgs, the minimum distance
between them, the peak 2 µs supply-current bin and the enable-window output extremes.

The corner **CONFIRMS** the recorded negative (`interface_diagnostics.enable_edge`) if no 2 µs bin reaches 5 mA (rule 7)
and, on +5 V only, the enable-window output stays below the recorded 0.8 V quantity. No −12 V enable-edge bound is
recorded, so on −12 V the extremes are reported without a voltage criterion. Anything else **CONTRADICTS** it, and
the result goes to the owner.

## Execution rules

- **Status.** ABORTED, RUN FAILED and NOT EVALUATED are defined exactly as in
  [d1-gap-criteria.md Amendment 1](d1-gap-criteria.md). ABORTED means not evaluated. Nothing is retried in the same
  dispatch, and no solver option, tolerance or model changes.
- **Control gate.** The T2 labels run only if ctrl is COMPLETE and REPRODUCED. The verdict is computed once, after
  ctrl, and kept in `t2/control-gate.json`.
- **REPRODUCED** means the inert control fails rule 1 on −12 V the same way as the record: the screen fails, the
  peak slope in the exception region exceeds 1.47 V/ms, and the capacitor current there exceeds 0.265 A. Its
  differences from the recorded values are reported.
- If the control aborts or does not reproduce, the realization is the finding. T2 is then NOT EVALUATED, and
  the evaluation stops.
- **Loaded baselines.** If a loaded baseline does not reproduce its recorded waveform hash, its T2 case is NOT
  EVALUATED.

## Pass rules

### No-load cases: t2/nom, t2/adv, t2lo/nom, t2hi/nom

Rules 1–9 are [d1-gap-criteria.md](d1-gap-criteria.md) rules 1–9, unchanged, on −12 V. They run against each case's
baseline:
- t2/nom against nom and t2/adv against adv, both from the reproduced reference-extraction pair;
- t2lo against e12lo and t2hi against e12hi.

Rule 6 is judged against that baseline at the 1e-5 V resolution. The control's own difference from adv is reported
beside it as the loading-only reference; it does not change the verdict. A rule that the corner's own baseline also
fails still fails; it is reported as such and is not waived.

| Rule | Criterion |
| --- | --- |
| 10 Idle channel current | Over 95–115 ms, the maximum 2 µs bin of i(VIQ6) is at most **0.5 ×** the minimum 2 µs bin of the output drain. The drain is the RMA1 current, (v(mabs_n) − v(m12_out)) / 100 kΩ, plus the RT12NB current, (v(trk12n) − v(m12_out)) / 750 kΩ. Reported per corner, with the mean |
| 11 No limit cycle while idle | Over 95–115 ms, DRV's 2 µs bin means, minus their least-squares line, have a peak-to-peak of at most **10 mV** |
| 12 Release step | Release is the first 2 µs bin after 110 ms where the clamp current, (v(t2g) − v(t2c)) / 499 kΩ, falls below 10 % of its 110–115 ms mean. The DRV mean over the 50 µs after release minus the mean over the 50 µs before differs by at most **50 mV**. The output side is carried by rule 4 |
| 13 Clamp engaged | The mean clamp current over 110–115 ms is at least **0.1 µA**. Otherwise the case is baseline behaviour, not a correction |
| 14 Hold reset while disabled | The hold, v(t2h) − v(m12_pre), stays at most **10 mV** over 30–40 ms and 245–250 ms |

### Loaded cases: t2load against base (nomR, reR6, reR20)

Windows: startup 40–245 ms (nomR) or 40–150 ms (reR6, reR20), and re-enable 150–315 ms. The decks' own
reltol (1e-3) and vntol (1e-5 V) are the resolution.

| Rule | Criterion |
| --- | --- |
| L1 Screens | Each rail's adjacent-sample screen at its normal limit (no exception: these are loaded) passes wherever the baseline's passes |
| L2 Tracking unchanged | Every output's 2 µs bin means stay within 1e-3·\|baseline\| + 1e-5 V of the baseline |
| L3 Startup current unchanged | The peak 2 µs bin of \|i(VM12) − i(VT2N)\| is at most the baseline's × (1 + 1e-3) |
| L4 Hold reset at re-enable (reR6, reR20) | Over the 1 ms before re-enable, the hold is at most 10 mV above M12_PRE |

### Verdict

**T2 −12 V PASS** needs all of the following:
- the control REPRODUCED;
- all four no-load cases COMPLETE and passing rules 1–14;
- all three loaded cases COMPLETE and passing L1–L4.

Any evaluated failure is a FAIL. Anything else is NOT EVALUATED, including a completed case whose evaluation raises
an error, and a loaded case whose own baseline did not reproduce.

**Re-enable instant.** It is the first fall of EN_N below 2.5 V that follows its rise above 2.5 V after the 150 ms
disable request.

**Low-side margins.** These are unchanged by construction when rule 10 holds. The candidate's own currents return
to M12_PRE upstream of the shunt; only the idle channel current is sensed. Rule 10 bounds that current below
about 0.5 µA, while the margins are reported to 0.01 mA.

**Disconnect-before-discharge order and AGND connection.** These are unchanged by construction. The turn-off path
(B25, RG3, RG3P, DZ3) and the discharge return are untouched, and rules 8, 9 and 14 test the disable edge. The
clamp's ~1 µA return from the summing node to M12_PRE parallels RT12NO's existing path.

**+12 V and +5 V are reported only.** They appear through rules 2 and L1–L2; no correction is proposed.

## The 19–20 ms off case: what counts

- **Full load (reR6 at 19.0 ms, reR20 at 20 ms).** Pass means L1–L4 hold.
- **No load.** These decks have no discharge path, so a no-load re-enable does not restart from 0 V. The no-load
  quick re-enable is therefore analysed on paper:
  - After 19.0 ms off, v(ennd) has recharged only to 1.66 V, so the capture window is about 15 ms. The edge is
    found 27–32 ms after enable.
  - The hold therefore keeps a pre-edge level, and the floor sits lower: a partial benefit, or none.
  - **Falling back to baseline behaviour there is a recorded limitation, not a pass.** It is left for the owner
    to weigh at adoption.
- **What could close it (not evaluated; each needs its own decision).**
  - A fast-recharge diode across RRMD, so CRMD resets within the off time. RAMP would then be held for the full
    ~76 ms after any re-enable, which is a re-entry timing change.
  - A minimum off time of about 46 ms or more. That is CHO about 1.45 µF at RHO 300 kΩ, to keep capture through
    the edge with margin.

## Predictions (stated before the run)

**At the idle point (model corner):**

| Quantity | Predicted |
| --- | --- |
| DRV below its peak | about 1.0 V at engagement, 1.1 V mean over 95–115 ms (droop) |
| Internal Vgs | about 1.34 V, about 0.95 V below the enable peak |
| Channel current | about 0.03 µA (inference from the +5 V ramp's 210 mV per decade) |
| Output drain | about 1.08 µA, so rule 10 holds by a factor of about 15 |
| Clamp current | about 1.07 µA |
| Release step | about 11 mV, away from conduction (1.07 µA through the 10 kΩ zero) |
| Limit cycle | none (crossover about 160 Hz, phase margin about 90°) |

**Corners.** These are the same relative to each corner's own edge, because the hold captures the part's own
edge.

**The D1 failure deck (t2/adv).** DRV starts the catch-up about 2.1 V closer to the edge than baseline. The peak
slope and capacitor current are predicted to fall, but whether they clear 1.47 V/ms and 0.265 A is **uncertain**.

**Rule 6 is at risk at the microvolt level.** The candidate loads DRV slightly (the capture diode and the
difference stage), and the control's difference from adv measures that loading.

**Loaded cases.** The clamp is predicted never to engage at full load: DRV stays above the floor. L1–L4 are
predicted to hold.

**Unverified model behaviour.** The hold buffer's input sits at its negative supply while the hold is reset.
The OPAx187 macro's behaviour there was not checked locally, because the vendor model is not in the repository.
Rules 5 and 14 would catch a phase reversal that injected current while the output is disabled.
