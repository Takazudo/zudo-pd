> Historical audit artifact: the EC11 encoder findings below describe the former design. The current Board L uses ALPS RK10J11E0034 C470643 absolute brightness control; consult its owner evidence and the current inventory.

# Circuit recheck — Wave-3 locked decisions

Date: 2026-08-02. Issue: [#47](https://github.com/Takazudo/zudo-led-lamp/issues/47) under epic
[#39](https://github.com/Takazudo/zudo-led-lamp/issues/39). Base: `base/circuit-recheck` after Wave-2
(#42–#46) merged.

This artifact converts Wave-2 evidence into mechanically implementable specs for Wave-4 (#48 registry/generator,
#49 docs). Every number below is re-derived from fact records as they exist in this branch; fact IDs and exact
conditions are cited inline. Nothing here authorizes energization, a new inventory line, a connectivity change,
or a firmware behavior change.

Constraints honored: existing inventory lines only (32 orderable lines, 29 fitted / 3 DNP unchanged); no
connectivity changes; CTRL annotation-only; #32/#34/#35 stay open.

---

## Decision 1 — Encoder: NOT confirmed. No metadata change.

**Outcome: the not-confirmed branch of #47 decision 1 fires. Wave-4 makes no encoder metadata change.**

Wave-2 (#42) attempted manufacturer-primary retrieval and failed. Per `src-c2991196-primary-retry`
(`authority_class: MANUFACTURER_PRIMARY`, `availability: SOURCE UNAVAILABLE`, retrieval 2026-08-02):

- `https://tech.alpsalpine.com/e/products/detail/EC11L1525G01/` returns HTTP 403 across repeated attempts and
  header variants; the legacy `alps.com` URL redirects to `tech.alpsalpine.com/e/info/detail/EC11L1525G01/`,
  also 403.
- Control test: the currently catalogued sibling `EC11E15244G1` detail page returns HTTP 200 with the same
  client, so this is **not** a generic bot filter — the block is specific to this part.
- No `EC11L` series entry appears in any of the four current encoder sub-category listings (sub/01: ec11e,
  ec11n; sub/02: ec12d, ec12e, ec18a; sub/03: ec05e, ec10e; sub/04: ec21a, ec28a, ec35a, ec35ah, ec35b, ec40a,
  ec45a, ec50a, ec60a, ec60b). The general EC11 series catalog PDF also returned 403.

`fact-c2991196-detents` ("15 pulses and 30 detents per 360 degrees; detent step 12 ± 3 degrees") therefore
remains `UNSOURCED`, sourced only from `src-c2991196-spec` (`MANUFACTURER_MIRROR`, KK-2010-9648, 2010-07-13).
`fact-c2991196-lifecycle` remains "current lifecycle status is not established". `fact-c2991196-label-conflict`
stays as-is.

### Why no correction is authorized

A metadata correction would have to be justified by mirror-only evidence, which the audit contract forbids for a
`GUARANTEED_ELECTRICAL` claim. The three project surfaces disagree in two different directions:

| Surface | Claim |
|---|---|
| `scripts/schgen/board_l_spec.py:31` SW1 display value | `EC11 15-detent` |
| `src-c2991196-spec` mirror (KK-2010-9648) | 15 pulses / 30 detents per revolution |
| `architecture/board-l.mdx:304-307`, `research/control-knob.mdx:36` | 30 pulses / 15 detents per revolution |

Correcting any one of them from mirror bytes would harden a number the primary source cannot substantiate, and
the firmware UI scale factor (`board-l.mdx:300-309`) depends on it. That is a dedicated design change, not a
Wave-4 sweep.

### Additional lifecycle finding (new, beyond the metadata question)

The catalog-structure observation is a **procurement** signal, not just an evidence gap: the exact model appears
withdrawn from Alps Alpine's current online catalog while siblings remain listed. Combined with the still-open
`fact-c2991196-lifecycle`, the risk is that `EC11L1525G01` (LCSC C2991196) is end-of-life and a future build
cannot source it. This does not change the design now — it is a fact to carry on #32.

### Locked instructions

- **#48:** no encoder change of any kind. `board_l_spec.py:31` SW1 tuple stays `('EC11L1525G01', 'EC11
  15-detent', 'C2991196', 'zudo-led-lamp:SW-TH_ALPS_EC11L1525G01', False, (165.1, 101.6))`. No
  `LABEL_OVERRIDES` change. No `component-alps-ec11l1525g01` fact, source, or SKILL.md change — Wave-2 already
  recorded the withdrawal observation in `SKILL.md` line 9 and in `src-c2991196-primary-retry`.
- **#49:** no pulses/detents *number* changes anywhere. Add an unresolved-status caveat only (exact text in the
  #49 spec) to `architecture/board-l.mdx` and `research/control-knob.mdx` pointing at #32. A caveat naming the
  conflict is not a metadata correction; it is the honest state.
- **#32:** stays open, with a dated status comment recording the 403 pattern, the control test, the absent
  `EC11L` catalog rows, and the lifecycle implication.

---

## Decision 2 — NTC: 0.1 mA is an operating maximum. R26 moves 10 kΩ → 100 kΩ (existing line C25803).

**Outcome: the operating-maximum branch of #47 decision 2 fires. An existing inventory line closes the
envelope, so this is a value change, not annotation-only. No follow-up issue needed for the NTC.**

### The binding limit

`fact-c13564-max-current` = **0.1 mA**, class `RECOMMENDED_OPERATION`, verdict `PASS - primary-source
confirmed`, source `src-c13564-current`. Wave-2 (#44) established the semantics: Murata's own column header
(translated from Japanese) reads **"Maximum Operating Current (25 °C)"**, repeated on every page (physical
indices 0–4); the older catalog `src-c13564-catalog` (physical page index 7) defines the parallel English term
"Permissive Operating Current" as the current that keeps the thermistor's self-heating rise to max. 1 °C.

This is an **operating** ceiling on the installed divider current, not a measurement/test condition. The
installed current must therefore be checked across temperature.

### Beta-conversion caveat (applies to every R–T number below)

`fact-c13564-curve-caveat` is `UNSOURCED`: no guaranteed R–T table, no installed dissipation factor, and no
thermal time constant exist for this exact part in any reachable primary or mirror source (dated attempt
2026-08-02; Murata SimSurfing returned only a client-rendered shell). Every resistance-vs-temperature value here
is computed from `fact-c13564-resistance` (10 kΩ ±1 % at 25 °C) and `fact-c13564-beta` (B25/50 = 3380 K ±1 %,
with B25/85 typical 3434 K) through R(T) = R25·exp(B·(1/T − 1/298.15)). That is a **beta-only extrapolation**,
explicitly not a guaranteed curve, and it is extrapolated past the 25–50 °C interval that defines B25/50.

Consequence for how the decision is made: **prefer margin over precision.** A candidate that passes only by a
few percent of a beta-extrapolated number is not proven to pass.

### Worst-case divider current

Topology (`fact-c13564-topology`): `V3P3 → R26 → NTC_SENSE → RT1 → GND`, `C24` shunts `NTC_SENSE`, `U3.11`
(PA4) senses it.

I_max = V3P3_max / (R26_min + R_NTC_min(hot)), with:

- V3P3_max = **3.33 V** — `fact-ap63203-vout-max`, `GUARANTEED_ELECTRICAL`, `PASS`, conditions "CCM, recommended
  ambient/input range".
- R26_min = R26_nom × 0.99 — 1 % F tolerance (`fact-c17414-tolerance`, `fact-c4216-tolerance`,
  `fact-c25803-tolerance`, all `PASS`).
- R_NTC_min(hot) uses R25_min = 9.9 kΩ **and** B_max = 3413.8 K (for T > 25 °C the exponent is negative, so the
  minimum resistance takes the *maximum* beta).

| R26 candidate | R26_min | I at 25 °C | 65 °C | 80 °C | 100 °C | 125 °C | NTC→0 asymptote |
|---|---|---|---|---|---|---|---|
| **10 kΩ C17414 (as built)** | 9 900 Ω | 168.2 µA | 267.4 µA | 288.0 µA | 305.8 µA | 318.4 µA | 336.4 µA |
| **33 kΩ C4216** | 32 670 Ω | 78.2 µA | 94.5 µA | 97.0 µA | 98.9 µA | **100.2 µA** | **101.9 µA** |
| **100 kΩ C25803** | 99 000 Ω | 30.6 µA | 32.8 µA | 33.1 µA | 33.3 µA | 33.5 µA | **33.6 µA** |

Beta-derived hot-end minima used above: 2 555.2 Ω (65 °C), 1 664.1 Ω (80 °C), 991.2 Ω (100 °C), 558.1 Ω
(125 °C). The doc's own 1.71 kΩ at 80 °C reproduces exactly at nominal R25/B (1 710.9 Ω), confirming the model.

### Verdicts

**10 kΩ C17414 (as built) — FAILS, and fails at room temperature.** 168.2 µA is **1.68×** the 0.1 mA operating
maximum at 25 °C, rising to 2.88× at the `CRITICAL` threshold temperature. This is the defect Wave-2 exposed:
`board-l.mdx:407` computes the divider current correctly (165 µA nominal) but compares it against the wrong
limit — the 100 mW `fact-c13564-power` rating (itself `UNSOURCED`) instead of the 0.1 mA operating maximum.

**33 kΩ C4216 — REJECTED.** The codex flag was right. Two independent reasons:

1. **The asymptote itself fails.** As R_NTC → 0 (hot end, or a shorted/damaged thermistor), I → V3P3_max /
   R26_min = 3.33 / 32 670 = **101.9 µA > 100 µA**. There is no temperature at which 33 kΩ can be *guaranteed*
   compliant; it exceeds the limit before the NTC contributes anything. The crossing happens at **119.4 °C**,
   inside the −40…+125 °C range of `fact-c13564-temperature`.
2. **Where it does pass, it passes on air.** At 80 °C the margin is 3.0 % (97.0 µA) and at 100 °C it is 1.1 %
   (98.9 µA) — computed from a beta extrapolation whose own model uncertainty is larger than that. Using the
   typical B25/85 = 3434 K instead of B25/50 = 3380 K moves R(80 °C) by −2.8 %, which alone consumes the entire
   margin. Accepting 33 kΩ would mean asserting a guaranteed limit is met using a number the registry marks
   `UNSOURCED`.

**100 kΩ C25803 — SELECTED.** Worst case is **33.6 µA**, which is the NTC→0 asymptote, i.e. an
upper bound that holds at *every* temperature and under a shorted-thermistor fault, with no dependence on the
beta model at all. That is **33.6 % of the operating maximum — a 2.97× margin**, established from
`fact-ap63203-vout-max` and `fact-c25803-resistance`/`fact-c25803-tolerance` only. This is the outcome the
"prefer margin over precision" rule demands.

### Inventory impact — no new line

`line-c25803` (`0603WAF1003T5E`, UNI-ROYAL, C25803, package `R0603`, owner `component-project-passives`) already
exists and is currently placed only at `board-p:R11`. Adding `board-l:R26` to it and removing `board-l:R26` from
`line-c17414` keeps the totals at **32 orderable / 29 fitted / 3 DNP**. Both lines are owned by
`component-project-passives`, so no owner-skill change is needed.

Footprint changes from `zudo-led-lamp:R0805` to `zudo-led-lamp:R0603`. This is required, not optional:
`validate.py:203-205` derives each line's package from the generator footprint and rejects a conflicting package
for the same LCSC, and `board-p:R11` already uses `R0603`. `boards/board-l/board-l.kicad_pcb` contains no
footprints (no layout exists yet), so nothing downstream breaks.

### ADC re-check against `fact-c529334-adc`

`fact-c529334-adc` (`RECOMMENDED_OPERATION`, `UNSOURCED`, src-c529334-ds Tables 56/59/60): "12-bit ADC input
resistance allowance rises from 50 Ω at 1.5 cycles to 50 kΩ at 160.5 cycles; PA4 is ADC_IN4."

Source resistance seen by the ADC is R26 ∥ R_NTC, maximised at the cold end with R26_max = 101 kΩ and
R_NTC_max (R25_max = 10.1 kΩ, B_max = 3413.8 K):

| NTC temperature | R_NTC max | R26 ∥ R_NTC | vs the 50 kΩ / 160.5-cycle allowance |
|---|---|---|---|
| −30 °C | 134 624 Ω | 57 707 Ω | **exceeds** |
| −25 °C | 101 453 Ω | 50 613 Ω | **exceeds** |
| **−20 °C** | 77 314 Ω | **43 792 Ω** | OK (12 % margin) |
| 0 °C | 28 803 Ω | 22 412 Ω | OK |
| 25 °C | 10 100 Ω | 9 182 Ω | OK |
| 80 °C | 1 698 Ω | 1 670 Ω | OK |

**Locked:** the ADC channel must use the **160.5-cycle sample time** (the part's maximum), and the sensing
chain's stated validity floor is **−20 °C at RT1**. Below roughly −25 °C the source impedance exceeds the
datasheet allowance and the reading is not specified. For an indoor lamp this is not a functional limit, but it
must be documented rather than discovered.

Mitigating detail worth recording: `C24` = 100 nF sits directly on `NTC_SENSE`
(`fact-c14663-capacitance`, 0.1 µF ±10 %). Against an STM32G0 sampling capacitor of a few pF this is roughly
four orders of magnitude larger, so the sampling charge is supplied by C24 rather than through the divider. The
160.5-cycle requirement above is therefore conservative — which is the intent.

### Retabulated thresholds

The divider is fed from `V3P3` and the ADC reference is `VDDA` = `V3P3` (`board-l.mdx:473`, net `V3P3` includes
`U3.VDD(4)`). The conversion is therefore **ratiometric**: the ADC code depends only on the resistance ratio,
so rail tolerance cancels in the threshold. Rail tolerance still matters for the *current* envelope above,
because that is not ratiometric. Code = 4095 × R_NTC / (R26 + R_NTC).

| Board temperature | NTC resistance | PA4 voltage at 3.3 V | 12-bit ADC code | Firmware action |
|---|---|---|---|---|
| 25 °C | 10.00 kΩ | 0.300 V | 372 | normal |
| 65 °C | 2.616 kΩ | 0.0841 V | **104** | `DERATE_START` — begin linear roll-off |
| 80 °C | 1.711 kΩ | 0.0555 V | **69** | `CRITICAL` — hard off |

Resolution in the derate band: 104 − 69 = 35 counts over 15 °C = **2.37 counts/°C, i.e. 0.42 °C per LSB**. This
is 7.1× coarser than the outgoing 10 kΩ divider (849 → 598 counts, 16.7 counts/°C) and remains adequate for a
thermal roll-off, but it is a real cost of the change and must be stated, not buried.

Trip-point uncertainty, stated because the R–T model is beta-only: the ±1 % on R25 and ±1 % on B give ±2.03 %
in R at 80 °C, which at the local sensitivity of −2.71 %/°C is ±0.75 °C; substituting the typical B25/85 =
3434 K for B25/50 = 3380 K moves the same point by a further ≈1.0 °C. **The trip temperatures carry roughly
±2 °C of model uncertainty and are nominal design points, not guaranteed trip temperatures.**

Self-heating, recomputed: at 25 °C the divider draws 3.3 / 110 kΩ = 30.0 µA, so the NTC dissipates
(30.0 µA)² × 10 kΩ = **9.0 µW**. Against `fact-c13564-dissipation` (1 mW/°C, typical/`UNSOURCED`) that is a
0.009 °C rise. The old 165 µA figure gave 0.27 mW / 0.27 °C. Note the honest framing: self-heating was never
the binding constraint — the stated 0.1 mA operating maximum is, and it was being exceeded by 68 % while the
doc reported comfort against a rating that does not govern.

### Registry wording correction (from #44)

`.claude/skills/component-murata-ncp18xh103f03rb/SKILL.md` line 8 currently ends "...B-value context, and
maximum measurement current." That phrase is now **wrong** — the value is an operating maximum. #48 corrects it.

Deliberately **not** corrected: `review-artifacts/issue-24-independent-audit.md:97` uses the same old phrase.
That file is a dated point-in-time audit record; rewriting it would falsify history. Leave it.

### Locked instructions

- **#48:** `board_l_spec.py` R26 → `('0603WAF1003T5E', '100k', 'C25803', 'zudo-led-lamp:R0603', False, (358.14,
  177.8))`; `inventory.json` placement move; `rule-ntc-adc-firmware` record/fact swap plus two conditioned
  calculations; forward-test case update; NTC SKILL.md wording fix. Exact edits are in the #48 body.
- **#49:** retabulate the thermal table, fix `board-l.mdx:399` and `:510` (10 kΩ → 100 kΩ), replace the
  self-heating sentence, add the sample-time / validity-floor / beta-uncertainty caveats.

---

## Decision 3 — LED Vf spread: locked acceptance limit 0.30 V per assembled 3-LED string.

**Outcome: numeric bound computed and locked; measurement protocol defined; ballast stays 33 Ω 2512 (no new
parts).**

### Model

Eight parallel branches, each one 33 Ω ballast plus three series LEDs, between `LED_P` and `LED_N`
(`fact-c210315-topology`, `fact-c2934070-topology`). Treating each LED as a fixed forward-voltage drop at the
operating point, branch j carries I_j = (V_node − V_j)/R_j where V_j is the branch's 3-LED total. Solving with
the hot (lowest-Vf, lowest-R) branch against seven identical high branches separated by a spread S:

    I_hot = (I_total + 7·S/R_hi) / (1 + 7·R_lo/R_hi)

The S term is independent of I_total, which means a total-current perturbation divides between branches almost
equally in absolute terms — so ripple adds a fixed offset rather than scaling the imbalance.

Inputs, all from PASS facts:

- I_total peak = **0.6303030303 A** — `fact-al8860-peak-current`. This is the mean at maximum sense threshold
  (`fact-al8860-sense-max` 0.104 V) over minimum initial sense resistance (`fact-rlp25-resistance-min` 0.198 Ω)
  = 0.5252525253 A (`fact-al8860-current-max`, the "+5 %" sense tolerance), raised by half of the 40 %
  peak-to-peak coil ripple (`fact-al8860-ripple-fraction` = 0.4, `PASS`, "internally set coil peak-to-peak
  ripple relative to ILED"), i.e. ×1.2.
- R = **33 Ω ±1 %** — `fact-c2934070-resistance`, `fact-c2934070-tolerance`, both `PASS`.
- Limit = **90 mA** — `fact-c210315-forward-current-max`, `ABSOLUTE_MAXIMUM`, `PASS`, "absolute maximum; not an
  operating target".

### Result

| Ballast spread assumed | Max allowable string-total Vf spread S |
|---|---|
| ideal (identical resistors) | 0.4229 V |
| **±1 % initial tolerance** (`fact-c2934070-tolerance`) | **0.3677 V** |
| ±1.25 % (initial + realistic differential TCR) | 0.3539 V |
| ±2 % (initial + worst-case differential TCR over a 60 °C excursion) | 0.3125 V |

The TCR rows use `fact-c2934070-tcr` = ±100 ppm/°C. The differential term only exists if two ballast resistors
sit at different temperatures or have opposite-sign TCR; 0.5 % is realistic for a 25 °C spread across the array
row, 1.2 % is the pathological bound.

**LOCKED ACCEPTANCE LIMIT: 0.30 V**, defined as `max(string total Vf) − min(string total Vf)` across the eight
assembled 3-LED strings. Not "±0.30 V" — the limit is on the full spread. This sits inside the tightest
computed bound (0.3125 V) and 18 % inside the ±1 % bound, leaving 54–68 mV of guard band to absorb measurement
uncertainty. Note that the estimate carried into #47 (≈0.45 V/string) was optimistic; it omitted the ballast
tolerance and the 7/8 redistribution factor.

The bound applies **per assembled 3-LED string, not per LED**. Per-LED matching cannot be the acceptance
criterion: 0.30 V across three series LEDs is 0.10 V per LED, which is exactly the datasheet's own stated Vf
measurement tolerance (`fact-c210315-vf-min`/`-vf-max`, "±0.1 V measurement tolerance"). Per-LED sorting is the
*means*; the assembled string total is the *gate*.

### The finding that matters more than the bound

| Vf spread S | Hot-branch peak | % of the 90 mA absolute maximum |
|---|---|---|
| 0 V (perfectly matched) | 80.18 mA | **89.1 %** |
| 0.30 V (locked limit) | 88.19 mA | 98.0 % |
| 0.3677 V (computed bound) | 90.00 mA | 100.0 % |
| 1.80 V (full retained 2.6–3.2 V window, unmitigated) | 128.27 mA | 142.5 % |

**Even with perfectly matched strings the design sits at 89 % of the LED's absolute-maximum forward current on
a peak basis.** The driver's own guaranteed worst case — maximum sense threshold, minimum sense resistor, full
ripple peak — consumes 89 % of the limit before any Vf mismatch exists. The entire Vf-matching budget is the
remaining 9.8 mA. No achievable matching bound moves the design below 89 %, because the floor is set by the
driver, not the LEDs.

Within this plan's constraints (existing lines only) there is no lever for more margin: raising RS1 to lower
I_LED or increasing the ballast both require a new part. This is raised as a follow-up issue rather than fixed
here.

On a **mean** basis the picture is comfortable — at the locked 0.30 V limit the hot branch averages 74.8 mA
(83 % of 90 mA) and dissipates 194.6 mW at Vf = 2.6 V, 64 % of the 306 mW `fact-c210315-power-max`. Both
readings belong in the doc: peak against the absolute maximum is the conservative gate #47 specified (there is
no retained pulsed-current rating to compare against instead), mean is what governs junction temperature.

### Correction to the existing doc model

`board-l.mdx:126-138` currently models imbalance as ±0.9 V-from-centre against a nominal 500 mA total with no
ripple and no resistor tolerance, arriving at exactly 90 mA and concluding "even at the datasheet's full Vf
spread, no LED exceeds its package power rating." That conclusion does not survive the driver's own tolerances:
the same full spread gives 128.3 mA peak / 114.9 mA mean, i.e. 142 % / 128 % of the absolute maximum. The
landing-exactly-on-90 mA result was an artifact of using nominal current.

Separately, `board-l.mdx:596-598` compares LED dissipation against a **288 mW** "package rating". That number
is derived (3.2 V × 90 mA), not the datasheet's. `fact-c210315-power-max` = **306 mW**, `ABSOLUTE_MAXIMUM`,
`PASS`. #49 corrects the denominator and the resulting percentages (0.19 W → 62 %, not 65 %).

### Measurement protocol for #35

Because the criterion is a **spread**, common-mode instrument error cancels; only differential repeatability
matters. Every LED and every string must be measured by the identical method.

1. **Current:** 60 mA DC ±1 %, the datasheet condition for `fact-c210315-vf-min`/`-vf-max`. The operating mean
   branch current is 65.7 mA; the 60 → 65.7 mA difference acts through the LED's dynamic resistance and is
   common-mode across parts, so it does not shift the spread.
2. **Thermal method** — one of these, applied identically to all 24 LEDs:
   - *Preferred:* pulsed — a single 10 ms pulse at 60 mA, duty ≤ 1 %, Vf sampled in the final 1 ms.
   - *Acceptable:* DC with a 30 s soak, reading taken once drift is below 1 mV per 10 s.
3. **Ambient:** 25 ±3 °C; LED solder-point temperature ≤ 30 °C at the moment of reading
   (`fact-c210315-solder-temperature-max` = 85 °C is the process limit, not a measurement condition).
4. **Instrument:** 1 mV resolution or better. Differential uncertainty must be ≤ 10 mV — verify by measuring one
   reference LED five times; max − min must be ≤ 5 mV. 10 mV consumes 3.3 % of the 0.30 V budget and fits
   inside the 54 mV guard band.
5. **Matching (deterministic, no judgment):** measure all 24 LEDs individually. Sort descending by Vf. Walking
   the sorted list in order, assign each LED to whichever of the eight groups currently has the smallest running
   sum, breaking ties by lowest group index. This is the standard LPT greedy partition.
6. **Gate:** after assembly, measure the eight string totals under the same conditions. Accept only if
   `max − min ≤ 0.30 V`. If the reel cannot meet it, **escalate — do not re-group by hand and do not relax the
   limit**; the honest options are a different reel, a tighter incoming bin, or a ballast/sense change outside
   this plan.
7. **Scope:** this is an incoming/assembly acceptance gate. It does not close #35's CCT/photometric items and is
   not authorization to energize.

---

## Decision 4 — CTRL: annotation only. Guaranteed floor 2.498 V ⇒ 99.9 % of I_NOM.

**Outcome: no value, part, or connectivity change. Doc annotation only, per the #47 hard constraint.**

Divider: `PWM_DIM` (`U3.13`, PA6 TIM3_CH1) → R20 10 kΩ → `CTRL` → R21 33 kΩ → GND, with C21 100 nF at `CTRL`
(`fact-c4216-ctrl-topology`, `fact-c17414-reset-ctrl-topology`, generator net `CTRL`).

At 100 % PWM duty, V_CTRL = V_PWM_DIM × R21/(R20+R21):

| Case | Rail | R20 | R21 | Ratio | V_CTRL |
|---|---|---|---|---|---|
| nominal | 3.30 V | 10 kΩ | 33 kΩ | 0.767442 | 2.5326 V |
| **worst low** (`fact-ap63203-vout-min`, R20 max, R21 min) | **3.27 V** | 10.1 kΩ | 32.67 kΩ | 0.763853 | **2.4978 V** |
| worst high (`fact-ap63203-vout-max`, R20 min, R21 max) | 3.33 V | 9.9 kΩ | 33.33 kΩ | 0.770992 | 2.5674 V |

Against `fact-al8860-ctrl` ("floating gives normal operation; below 0.2 V disables; 0.3–2.5 V analog dims; PWM
below 500 Hz preserves best range", `PASS`) and its stated 5–100 % analog-dimming span, a linear 0.3 V → 5 % /
2.5 V → 100 % mapping puts the guaranteed floor at **99.90 % of I_NOM** (the simple proportional model
V/2.5 gives 99.91 %). The shortfall against the doc's "100 % duty = 100 % of I_NOM" claim
(`board-l.mdx:259`) is **0.10 percentage points**.

So the claim is not wrong in any practical sense — it is *nominally* true and off by 0.1 % at the guaranteed
corner. #49 states it as nominal with the guaranteed floor named, which is all decision 4 authorizes.

Two things must be stated honestly alongside it:

- **The floor assumes `PWM_DIM` drives to the rail.** No STM32G031 output-level fact is retained — there is no
  `fact-c529334-*` for V_OH — so the drop across the GPIO is not covered by evidence. Physically it is
  negligible: the divider draws 76.7 µA, so even a 50 Ω driver contributes ≈3.8 mV. But if one applied a
  datasheet-style guaranteed V_OH of VDD − 0.4 V (specified at milliamp loads, not at 77 µA), the floor would
  fall to 2.192 V ⇒ 86.7 % of I_NOM. The 99.9 % figure is therefore conditional on an assumption the registry
  does not currently substantiate. Record it as an open item; do not present 99.9 % as unconditional.
- **The worst-high case puts 2.567 V on CTRL**, above the 2.5 V top of the analog-dim range. That is benign for
  dimming (it saturates at full current) but no CTRL absolute-maximum rating is retained in
  `component-al8860mp-13`. Also an open item, not a change.

Resistor stress is trivial and needs no action: R20 dissipates 0.059 mW against a 125 mW rating
(`fact-c17414-power`), R21 0.194 mW against 100 mW (`fact-c4216-power`).

---

## Extra Wave-2 context folded into the Wave-4 doc spec

- **AL8860 duty band is now primary.** `fact-al8860-duty-band` = "25 to 75 %", `RECOMMENDED_OPERATION`, `PASS`,
  conditions: "DSW parameter, internal buck-switch operating duty-cycle recommended range, guaranteed by design;
  distinct from the 98 % DSW(MAX) absolute maximum duty cycle and from the 5–100 % CTRL-pin analog-dimming
  range." The doc's 77 %-nominal design point (`board-l.mdx:161`, `:176`) is unchanged and already honest about
  sitting 2 points above the band; #49 adds the fact-ID citation and the three-way distinction, which is the
  part readers currently have to infer.
- **FNR4030 heating-current margin is now primary-confirmed and negative.** `fact-fnr-irated-margin` =
  **−0.7 A** (`PASS`): the part's 2.0 A max-design Irms against the AP63203's 2.7 A recommended full-load
  inductor rating (`fact-ap63203-required-inductor-current`, = 2 A load × 1.35 headroom per
  `fact-ap63203-current-headroom`). The justification is load, not rating: the V3P3 budget line
  (`board-l.mdx:568`) is **25 mA worst case**, three orders of magnitude below the envelope the 2.7 A figure
  describes. #49 cites the fact and states an explicit budget cap. Note the R26 change *reduces* V3P3 load by
  ≈135 µA (165 → 30 µA) — far below the table's resolution, so **no power-budget retabulation is needed**.

---

## Conditioned calculations to encode (#48)

All four verified against `validate.py`'s `arithmetic()` evaluator; results are exact Python floats and must be
written verbatim or the `result is stale` check fails at 1e-12 tolerance.

`rule-ntc-adc-firmware` — after swapping `rec-c17414` → `rec-c25803` in `record_ids` and
`fact-c17414-resistance` → `fact-c25803-resistance` + `fact-c25803-tolerance` in `fact_ids`:

| calculation_id | result | scenario |
|---|---|---|
| `calc-ntc-divider-current-margin` | `margin_ma` = `0.06636363636363637` | `rail_v` = 3.33 |
| | `margin_ma` = `0.06666666666666668` | `rail_v` = 3.3 |
| `calc-ntc-adc-source-impedance` | `r_source_ohm` = `43792.0411340983` | `r_ntc_ohm` = 77314.35 |
| | `r_source_ohm` = `9181.818181818182` | `r_ntc_ohm` = 10100.0 |

`rule-al8860-led-stage` — after adding `fact-c2934070-tolerance` to `fact_ids` (`rec-c2934070` is already in
`record_ids`):

| calculation_id | result | scenario |
|---|---|---|
| `calc-led-hot-branch-peak` | `current_a` = `0.08017708571864743` | `spread_v` = 0 |
| | `current_a` = `0.08819174108846653` | `spread_v` = 0.3 |
| | `current_a` = `0.128265017937562` | `spread_v` = 1.8 |
| `calc-led-hot-branch-headroom` | `headroom_ma` = `9.822914281352567` | `spread_v` = 0 |
| | `headroom_ma` = `1.8082589115334713` | `spread_v` = 0.3 |
| | `headroom_ma` = `-38.26501793756202` | `spread_v` = 1.8 |

No CTRL calculation is encoded: it would require pulling `rec-ap63203wu-7` and `rec-c17414` into
`rule-al8860-led-stage`, which is a scope expansion the annotation-only constraint forbids.

---

## Corrections (post-review, same session, 2026-08-02)

Two defects found in review of the text above. The original wording is left intact; these entries supersede
it. Both concern Decision 3.

### Correction 1 — "Inputs, all from PASS facts" is wrong; the peak-current chain is `NEEDS BENCH`

Decision 3's *Model* section introduces its inputs as "all from PASS facts". That is not true of the first
one. `fact-al8860-peak-current` (0.6303030303 A) carries verdict **`NEEDS BENCH`**, and so do both facts it
depends on:

| Fact | Verdict | Provenance |
|---|---|---|
| `fact-al8860-peak-current` | **NEEDS BENCH** | CALCULATED from `fact-al8860-current-max` × (1 + `fact-al8860-ripple-fraction`/2) |
| `fact-al8860-current-max` | **NEEDS BENCH** | CALCULATED from `fact-al8860-sense-max` / `fact-rlp25-resistance-min` |
| `fact-rlp25-resistance-min` | **NEEDS BENCH** | CALCULATED from `fact-rlp25-resistance` × (1 − `fact-rlp25-tolerance`) |

The four *leaf* facts underneath (`fact-al8860-sense-max`, `fact-al8860-ripple-fraction`,
`fact-rlp25-resistance`, `fact-rlp25-tolerance`) are all `PASS - primary-source confirmed` against
`MANUFACTURER_PRIMARY`, `AVAILABLE` sources. What is unverified is the *composition*: each derived fact's own
`conditions` field records "TCR and self-heating unresolved", so stacking maximum sense threshold onto minimum
initial sense resistance onto full ripple peak produces a datasheet worst case that no bench measurement has
confirmed.

Consequence: every number in Decision 3 that flows from `fact-al8860-peak-current` — the 80.18 / 88.19 /
90.00 / 128.27 mA hot-branch peaks, the 89.1 % / 98.0 % / 100.0 % / 142.5 % readings against the LED
absolute maximum, and the 0.4229 / 0.3677 / 0.3539 / 0.3125 V spread bounds — is a **datasheet worst case,
bench-unverified**, not a guaranteed value. The conclusions do not change; the confidence label does.

Note the phrase to avoid is "guaranteed", **not** "mirror-derived": these sources are manufacturer-primary,
not mirrors. Doc wording corrected accordingly in `architecture/board-l.mdx` and `architecture/decisions.mdx`.

### Correction 2 — the guard-band narrative was self-inconsistent; the operative bound is 0.3677 V

Decision 3's *Result* section says the locked 0.30 V limit "sits inside the tightest computed bound
(0.3125 V) and 18 % inside the ±1 % bound, leaving 54–68 mV of guard band". Those clauses do not describe the
same bound: 0.3125 V leaves 12.5 mV, not 54–68 mV. The 54 mV and 68 mV figures come from the ±1.25 % and
±1 % rows respectively. Step 4 of the measurement protocol then assesses the ≤10 mV instrument budget against
"the 54 mV guard band", a third choice again.

The fitted ballast is **FOJAN FRC2512F33R0TS** (`line-c2934070`), whose `F` suffix is **±1 %** — confirmed in
`src-c2934070-spec`'s evidence extract ("FRC2512F33R0TS decodes 2512, +/-1%, 33 ohm"). The ±1 % row is
therefore the operative bound for the part actually on the BOM:

| Row from the Result table | Bound | Guard vs the adopted 0.30 V | Status |
|---|---|---|---|
| ideal (identical resistors) | 0.4229 V | 122.9 mV | not physical |
| **±1 % initial tolerance — the fitted part** | **0.3677 V** | **67.7 mV** | **operative** |
| ±1.25 % (initial + realistic differential TCR) | 0.3539 V | 53.9 mV | sensitivity case |
| ±2 % (initial + worst-case differential TCR over 60 °C) | 0.3125 V | 12.5 mV | sensitivity case |

**Corrected narrative:** the adopted 0.30 V limit sits 18.4 % inside the operative ±1 % bound of 0.3677 V,
leaving **≈68 mV of guard band**. The 0.3539 V and 0.3125 V rows are differential-TCR sensitivity cases, not
the bound the fitted part imposes; the 0.3125 V figure in particular rests on the worst-case differential TCR
over a 60 °C excursion — the row's own stated condition — and should not be cited as "the tightest computed
bound" in a way that implies it governs.

**Protocol step 4 restated:** the ≤10 mV differential instrument-uncertainty budget is assessed against the
≈68 mV guard, which it consumes 14.8 % of (and 3.3 % of the 0.30 V limit itself). Both readings are
comfortable. Even against the pathological ±2 % sensitivity case the 10 mV budget fits inside the 12.5 mV
guard, though with no margin to spare — which is a reason to hold the ≤10 mV requirement, not to relax it.

---

## Decision summary

| # | Domain | Outcome | Key number |
|---|---|---|---|
| 1 | Encoder | **No change.** Primary source unavailable (HTTP 403, part-specific); EC11L absent from the current catalog. #32 stays open with a lifecycle note. | — |
| 2 | NTC | **R26 10 kΩ → 100 kΩ**, existing line C25803. As-built exceeded the operating maximum by 68 % at 25 °C; 33 kΩ rejected (asymptote 101.9 µA > 100 µA). | 33.6 µA worst case = 33.6 % of the 0.1 mA limit; thresholds 104 / 69 counts |
| 3 | LED | **Acceptance bound 0.30 V** string-total Vf spread + measurement protocol. Ballast unchanged. Follow-up issue raised for the residual driver-side headroom. | 88.19 mA peak at the limit (98.0 % of 90 mA); 80.18 mA (89.1 %) even at zero spread |
| 4 | CTRL | **Annotation only.** "100 % duty = 100 % of I_NOM" becomes nominal-only. | Guaranteed floor 2.4978 V ⇒ 99.90 % of I_NOM |
