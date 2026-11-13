# Prototype order readiness — execution ledger

Checkpoint: 2026-11-10 JST, local Mac. Parent [#228](https://github.com/Takazudo/zudo-pd/issues/228).
This ledger separates source integration, local manufacturing inputs, supplier
review and physical qualification. It is not an order authorization or a measured
rating. The 14-case simulation reproduction is complete; native artwork corrections are independently reviewed, and fresh native pair verification for the refill-finalized B20 passed; manufacturing export and independent verification passed at `3f24a3abb43e0f24f5e0a12f739ba8ae6bbad03d`. The first export failed its strict B20 refill-geometry gate; a reviewed pinned two-refill finalizer now produces byte-stable output without relaxing that gate.

## Revision and integration register

| Work | Revision / state | Next action |
| --- | --- | --- |
| Existing bounded source/evidence integration | [#234](https://github.com/Takazudo/zudo-pd/pull/234) merged; main `44fd3ba810aad627fd461b90093a3482707b44da` | Preserve the separate hardware gates below |
| Runner, evidence and analysis improvements | [#239](https://github.com/Takazudo/zudo-pd/pull/239) merged; main `76f807f11d3b97a9625e8cc9dd6835e235bb99df` | Independent review, Mac build/browser and exact-head CI completed; retain hardware gates |
| P r3 native correction | [#236](https://github.com/Takazudo/zudo-pd/issues/236) | Canonical PCB `56cbe0ab48b3bd25b6bab4223e3826ef437e3b972474b15481c5b86b7e889348` adopted after fresh native acceptance and independent review; Native/pair/export acceptance complete in [PR #240](https://github.com/Takazudo/zudo-pd/pull/240); integration state is recorded there |
| B20 U6 decoupling / pair | [#237](https://github.com/Takazudo/zudo-pd/issues/237) | Canonical PCB `09cd97abf5f793d881ee30fc62c7a7b934b1c5973a37637b37c62d15224507ce` adopted after native acceptance and independent review; Native/pair/export acceptance complete in [PR #240](https://github.com/Takazudo/zudo-pd/pull/240); integration state is recorded there |
| Interface evidence | [#235](https://github.com/Takazudo/zudo-pd/issues/235), open | All 14 actual cases and strengthened analyses complete; retain the modeled limits and pre-order holds below |
| Per-stream disposition | [#238](https://github.com/Takazudo/zudo-pd/issues/238) | Local disposition and durable export receipts complete in PR #240; separate product holds remain below |

The simulation execution tree is fixed at
`fda0667df503aa7cdc8ec0d45920dd4c731dc56c`. Later analysis code is separately
identified; its tests are not circuit simulation. Native receipts must identify
their PCB and generator bytes as well as their execution revision.

Bounded issues #229 (including immutable LED consumer acceptance), #211 and #217
are closed after integration. #210 retains its narrow circuit-doc checker and
Mac lifecycle compatibility bridges; it is not closed as a patch-free migration.

## P15 local packet

**P15 local order packet ready; supplier placement preview and current quotation
pending.** Exactly **two assembled P15 r1** modules, LED first and then PD15;
zero new Board L and zero new Board B. Use only the P15 subdirectory in
`manufacturing/releases/corner-support-review/`, never current 20 V `board-p`.
The [handoff](p15-order-handoff.md) and [decision packet](p15-order-decision-packet.md)
own the supplier procedure and arrival-test links.

| Frozen file | SHA-256 |
| --- | --- |
| `board-p15/board-p15-gerbers.zip` | `e68a133e2a3fa610758ed0e183fb9c4e77e4a4bfff7a9a6bac5cd1ab7f8c14ae` |
| `board-p15/bom.csv` | `23d6e2902307ce3920c405abe3296600610bcd5b54f0cca67ee0a8291ecfd59f` |
| `board-p15/cpl.csv` | `a9116d1b9f1d7f092531173a7c8f4d49f4a4c282b9a88f449a89b0da3e030ce6` |
| `board-p15/excluded.csv` — review only, do not upload | `16d6146bd3ca6f3fbca8adbc4ddcddb176659dcd5d016a27a699b41467e9f616` |

All four actual file hashes matched during this execution. Shared source identity
also matches at integrated main `76f807f11d3b97a9625e8cc9dd6835e235bb99df`; all seven artifact
checks passed. The frozen source lock was 467/498 unchanged at that revision:
later repository changes are not a historical replay. DNP D6/D7/R17/R18 and the
bare-pad J2/J3 exclusions remain intact. The 2026-11-09 catalog snapshot has 52
exact-code lookups and no two-P15 stock-below-purchase flags. It is not a current
supplier quote; the older fee model and USD 39.94 estimate remain historical.

Owner supplier steps remain: upload the three P15 production files, request two
assembled modules, inspect every polarized placement, and obtain a current
quotation before ordering. In particular, D5 SMAJ16A/C74561's stripe must be on
VBUS_IN (smaller-X pad), and D9 BZT52C18/C192739's band on VDD_LOC (smaller-X pad).
Local CPL/model agreement does not establish supplier placement. Any preview
correction must preserve this frozen package.

The LED consumer's `boards/p15-r1-reference.json` was verified at LED commit
`49a6c316908f2668460d9707872e1641af41a855`: it pins the PD shared record at
`8af9e5569c2534c03ce132515d1ec11f4c3f83d3`, an ancestor of integrated PD main,
and retains the exact P15 PCB/NVM hashes. LED PR #150 is merged at `5726c8e`;
LED's old `boards/board-p/` remains historical. No physical LED acceptance is
inferred from that source reference, and no LED repository files were changed.

## Decision register — PD20 order holds and evidence residuals

| ID | Evidence / unresolved decision | Recommendation and next action |
| --- | --- | --- |
| D1 Startup exceptions | Actual 2 us refinements retain a modeled +5 V peak of 0.954850860 V/ms / 114.510041 mA and negative-rail magnitude peak of 1.474778000 V/ms / 265.259332 mA within the exception voltage regions; these exceed the adopted 0.95/114 mA and 1.47/265 mA ceilings. Small negative sample increments remain | Retain PRE-ORDER HOLD. Review model/convergence and a contract-preserving design correction before considering any explicitly agreed exception; no numerical tolerance or waiver is adopted. See [refinement evidence](sim/board-b20-phase33/startup-refinement.md). The completed OSC-bank and ceiling-corners diagnostics (runs 43221578569 and 43232694170) are audited as integrity-verified measurements that judge nothing ([audit](sim/board-b20-phase33/d1-diagnostic-audit-20261113.md)); most of their rows are matched-variant, and the pre-registered pinned cross-check was not formed. That gap was closed on 2026-11-13 by a separate cross-check run (43484213339, [record](sim/board-b20-phase33/d1-variant-cross-check-20261113.md)): on the identity pair the abstol variant is COMPARABLE (D1 peak slope/current within 0.001 %), so the abstol-labelled rows are readable but stay labelled; the rshunt step is NOT COMPARABLE (0.1–0.4 %, the size of the D1 exceedances), but a follow-up run (43486530273, [record](sim/board-b20-phase33/d1-adv-rshunt-free-20261113.md)) shows the −12 V failure is not an rshunt artefact: `adv` at rshunt 1e10 under abstol gives 1.474663 V/ms / 265.238 mA (−0.008 %). Owner chose the OSC contract route on 2026-11-14 JST and accepted OSC's conditional exception (four conditions, to be recorded by OSC as E21); no ceiling changes before OSC records it. Condition 3 (no overshoot of the tracking ramp) fails as worded on the identity waveforms: the step leads the ramp by up to 208 mV, monotonically; a rewording was sent to OSC ([OSC reply record](sim/board-b20-phase33/osc-reply-20261114.md)). OSC recorded E21 at zudo-osc-hole-field `512e1ec` (PR #337, open): the no-load in-region ceilings become charging-current limits of ≤ 350 mA on −12 V (\|V\| ≤ 0.75 V) and ≤ 180 mA on +5 V (≤ 0.45 V), with four conditions. In simulation the recorded peaks (265.259 / 114.510 mA) are within it, and conditions 1, 2 and 4 hold. Condition 3 holds if "ramp start" is the rail's own start (≤ 8.4 ms) and not if it is the reference's start (15.8–21.5 ms) ([E21 binding record](sim/board-b20-phase33/e21-binding-20261114.md)). The ceiling change takes effect only when #337 merges and that wording is settled. No result changed. The proposed 350 / 160 mA current-form exception is not adopted |
| D2 Loaded discharge and shutdown | Disconnect-before-discharge is the contract. Independent rail loads can reorder decay; phase33 behavioral re-entry models do not qualify the entire discharge implementation | Keep asymmetric discharge and shutdown/re-entry PRE-ORDER gates. OSC commits only to 0..maximum load per rail independently; with its recommended absent levels, passive uncoupled discharge fails R-VEE in 10 of 18 load corners (CALCULATED, [OSC reply record](sim/board-b20-phase33/osc-reply-20261114.md)), so a design change is needed. Tracked ramp-down before disconnection is only a proposal and needs owner choice and OSC amendment of disconnect-before-discharge |
| D3 Maximum delivered current | Trip-window arithmetic is not regulation or a fault-current overshoot bound | Establish the existing 2.1 / 2.0 / 0.5 A maximum including tolerance/let-through, or obtain explicit contract agreement. No excess-current charge/time budget is invented. OSC reads the maxima as instantaneous including let-through and asks for a peak, duration above maximum, I²t and detection-to-off envelope; switch-off timing is unsourced, so this needs a bench measurement or a series/regulating limit ([OSC reply record](sim/board-b20-phase33/osc-reply-20261114.md)) |
| D4 PD20 NVM | TDISPAR0V value/reset interaction, POWER_ONLY_ABOVE_5V map conflict and established-contract transitions remain unresolved | Recommend TDISPAR0V 15 for owner review only: 1.05 s minimum gives about 16% margin over 0.906 s, with 1.50 s maximum recovery window. Review reapplication timing. Obtain paired official GUI exports changing only the mapping setting, retain all 40 bytes/settings, then resolve intent before producing a binary |
| D5 Installed capacitor bounds | Exact Yageo C43 manufacturer simulation and Murata VIN historical mirror curve are retained; both are typical evidence, not guaranteed installed minima | Retain temperature/tolerance/aging/loop assumptions explicitly. Review adequate worst-case bounds or an owner-approved component/design change |
| D6 Shunt lot applicability — conservative residual, not an independent order hold | Primary RESI E16009 V9 documents the 10 mOhm 1 W → 2 W history; supplier lot revision is unknown. Calculated contractual power is about 0.044 / 0.040 W at the retained 1 W bound | Keep historical 1 W / 10 A working bound. Manufacturer +20 C reference is applied to the existing 5–45 C arithmetic interval. Unknown applicability of the higher rating alone does not demonstrate inadequacy; fault/pulse/let-through compliance remains separately open |
| D7 Discharge repetition | Exact UNI-ROYAL single-event overload evidence does not establish repetitive pulse endurance; +12 V is near the test-voltage ceiling | Obtain applicable repetitive evidence or approve a separately reviewed component/design change. T5 remains NOT RUN |
| D8 Thermal, land/paste and fabrication | Added P copper cannot establish installed thermal resistance. The shared Q1/Q3 lands/paste differ from manufacturer recommendations, without proving a deterministic open. Thermal via solder/stencil/process acceptance remains unresolved | Retain adopted exact components and 5 A contract. Review quantified land/paste adaptations and supplier via/stencil process before assembly; do not silently adopt filled-via costs or package changes. Preserve R5/R7, SMC B560C and EMI/thermal residuals |
| D9 Stack and enclosure assumptions | Nominal 11.1 mm plane spacing passes the CAD screen, but the separate 11.0 mm comparison intersects by 1.36449 mm³; 11.08 mm passes nominally. HC11 component-side-toward-flat-floor mounting has a known height conflict: P back plane extends at least 1.7 mm and terminal maximum 3.2 mm beyond the 11 mm floor | Resolve actual header seating/tolerance and intended enclosure/support orientation before treating the assembled stack as mechanically ready. A 16 mm support is only a candidate, not an adopted substitution. The diameter-6 mm collar screen is a PROJECT assumption, not supplier support geometry. Keep these stack/enclosure limits separate from the settled two-module P15 prototype purchase |
| D10 Board P r3 Q1 closure slew, inrush and SOA (correction adopted 2026-11-12; verification open) | History: on 2026-11-11 Samsung typical DC-bias data for the fitted 0603 X5R C36 CL10A105KB8NNNC C15849 (25 °C, 1 kHz, small-signal, not guaranteed) gave 0.136–0.183 µF at the start of the 20 V closure, below the adopted 0.4–1.1 µF PA range in `dec-p-20v-q1-soft-start`; the CALCULATED typical screen gave 19–31 V/ms, 3.6–7.6 A into 186–250 µF against U2 I(OL) 4.185 A minimum, and Q1 SOA ratios of 0.54–0.86. Owner decision `dec-p-20v-c36-x7r-1206` (2026-11-12 JST, campaign manager under Takazudo's delegation) adopts option A: C36 = Samsung CL31B105KBHNNNE, LCSC C1848 (1206 X7R 1 µF ±10 % 50 V; public LCSC catalogue lists it as a JLCPCB Basic part). Before adoption, `scripts/pcb/board-p/q1-closure.py` ran all 8 corners (20/21 V, 1.5/3.5 V plateau, C nominal/−10 %) against both banks: C36 0.776–0.904 µF at start, peak slew 3.88–5.34 V/ms (inside the adopted range), peak inrush at most 1.336 A (below 4.185 A), minimum peak-rectangular Q1 SOA ratio 1.67 (stop limit 1.2). Schematic, inventory, BOM projection and evidence are updated. **Native rebuild 2026-11-12** (Actions run 43107657333, pinned KiCad 10.0.6 image, twin rebuild byte-identical): the 1206 courtyard at the old C36 placement left 0.02 mm to R13, below the 0.10 mm placement gap, so C36 moved by the minimum grid shift to (6.25, 32.75) mm on B.Cu, as the manager approved. No other footprint moved. DRC with schematic parity: 0 errors, 0 unconnected items and 95 warnings (the same set as before); the only parity items are the board-only MH1–MH3. `verify-corrections.py` passes with C36 as the only footprint identity change; the R1 connected B.Cu GND under U2 is now 595.369 mm² (was 598.263 mm²). The STEP-datum proof passes on the new bytes | Retain PRE-ORDER HOLD. Correction adopted, verification open: it rests on typical 25 °C small-signal data and a graph-read SOA at VGS 10 V / 25 °C; no guaranteed C(V) minimum, linear-mode SOA or elevated-temperature data is sourced. The pair assembly preview and a fresh development export passed on the selected Mac (`manufacturing/verification/pd20-native-d10-merged-20261113/`, nominal CAD only). Remaining: bench T3 (slew, inrush, Q1 temperature). See [#231](https://github.com/Takazudo/zudo-pd/issues/231) |
| D11 B20 servo settle before enable (correction adopted 2026-11-12) | **Owner decision 2026-11-12 JST** (campaign manager, under Takazudo's delegation; `dec-b20-rdy-timing` in `scripts/schgen/decisions.json`): RRDY1/RRDY2 are 2 × 150k C22807, replacing 2 × 100k C25803. CRDY, the Q37 thresholds and the 5 × settle screen are unchanged. Selection rule: the smallest standard value, preferring inventory parts, whose short corner beats 5 × settle by ≥ 5 %. The short corner uses high P5_SUP, the 0.5 V PA threshold, R −1 %, C −10 %, X5R TCC −15 % and TYPICAL DC bias. 300k gives **0.23466 s against 0.1919 s (1.2228 ×)**; 250k, the other inventory pair, gives 1.019 ×. The long corner is 1.392 s, and nothing has an upper bound on it: the canonical interface sets no maximum detect-to-enable delay, POR ends ≤ 0.0464 s, the min-off hold ≤ 0.121 s, and no phase33 input models the RDY RC. The PCB Value/LCSC fields and the hash-bound desk reports were refreshed by the pinned-KiCad field-sync job (run 43103587589: only the RRDY1/RRDY2 fields changed, fills identical), and the STEP-datum proof was re-run (PASS, 45 pairs). History: on 2026-11-11, `timing()` moved to sourced corners and the 200k network failed at 0.18405 s (nominal 0.21407 s). That was a failed project screen, not proof of malfunction | Correction adopted, verification open. The 5 × factor stays a PROJECT screen and the DC-bias data is typical. RDY-node leakage of Q36/Q37 is UNSOURCED, and a higher R raises sensitivity to it. Nothing is measured. The pair assembly preview and the development export passed on the selected Mac (`manufacturing/verification/pd20-native-d11-20261113/`, nominal CAD only). See [#235](https://github.com/Takazudo/zudo-pd/issues/235) |
| D12 B20 OV/UV comparator input-diode loading and disabled back-feed (correction adopted 2026-11-12; PCB inserted 2026-11-13) | **Owner decision 2026-11-12** (campaign manager, under Takazudo's delegation; `dec-b20-comparator-input-series-r` in `scripts/schgen/decisions.json`): one 100k 0402 C25741 (0402WGF1003TCE: ±1 %, 1/16 W, 50 V working) in series with each of the four U6/U7 divider-side inputs (RS12O/RS12U/RS5O/RS5U, annotated R77–R80); U8 (−12) is left unresistored and a true comparator is not pursued. The package moved from 0603 C25803 to 0402 C25741 the same day: a placement search found only two 0603 sites near U6/U7 that clear existing courtyards and other-net copper, while 0402 sites exist 2–3.5 mm from all four pins; the parts dissipate microwatts with well under 1 V across them, and the short *_IN stubs keep the 3 pF stray assumption (amended 2026-11-13: the routed UV5_IN bound is 3.43 pF; see the reconciliation below the table). Value, tolerance and TCR are unchanged, so the CALCULATED results below stand. These are the first 0402 parts on any project board. The absent / discharge levels are taken to apply to a disabled, unloaded terminal. SBOS807E §7.3.7 gives back-to-back differential input diodes and names an input series resistor as the remedy; the diode VF is UNSOURCED (PA 0.4–0.7 V). CALCULATED by `calculate-board-b20-draft.py` `comparator_input_diodes()`, no external load after the discharge hold-up: before the fix +12 0.915–1.162 V and +5 1.467–1.78 V (OPEN); fitted +12 0.124–0.253 V, +5 0.158–0.307 V and −12 0.204–0.357 V, below the 0.5 / 0.6 / 0.6 V levels. A uniform 100k including U8 had lifted −12 to 0.302–0.601 V, bounded only by the unsourced Q55 body-diode drop, which reached the 0.6 V stop limit; U8's diodes therefore keep clamping the REF-referenced −12 dividers, and a spec walk shows No resistor path from U8's inputs reaches the +12/+5 terminals, P5_SUP or M12_PRE without passing through REF25 or GND (FET, diode and op-amp paths not walked). IB on the −40..125 °C rows (5 nA U6/U7, 7.5 nA U8) × (divider Thevenin + R_S) keeps all six windows inside their limits (tightest OV −12 high 0.197 %, OV +12 high 0.224 %, with the full-range REF5025 budget); `windows()` itself omits IB. The IB rows are specified at VCM = VS/2; U8's inputs sit near GND, about 4.6 V from its supply midpoint, so the U8 row is applied outside its stated condition. Added input RC ≤ 1.802 µs (UV+12) on typical input capacitance plus, per channel, the larger of the 3 pF stray PA and the CALCULATED routed upper bound; UV5_IN's routed 2.48–3.43 pF gives UV+5 1.435 µs (1.39 µs at 3 pF). REF25 diode loading falls from 0.93 to 0.17 mA (disabled load 2.077 mA, step on enable 0.153 mA). Open evidence gaps, not blockers: no OV response budget exists in the project; no retained BSS138 body-diode VF row (DS30144 Fig. 9 is a typical curve starting at 1 mA); the OPA2187 differential-diode VF. The REF5025 load-regulation budget now uses the −40..125 °C row at the 3.0 mA PA (150 ppm, [#282](https://github.com/Takazudo/zudo-pd/pull/282)), which covers the 96 ppm at the enabled load | Retain PRE-ORDER HOLD. R77–R80 were inserted natively on the selected Mac on 2026-11-13 (`manufacturing/verification/pd20-native-d12-insert-20261113/`): `verify-insert-parts.py` passes on the unfilled board with `--reach-mm 32`; DRC with schematic parity under the unchanged rules has 0 errors and 0 unconnected items. Routed `*_IN` stubs: OV12 1.65 mm, OV5 4.12 mm, UV12 6.18 mm (F.Cu 2.55 + In2 3.63), UV5 19.34 mm (F.Cu 2.43 + In2 16.91); CALCULATED stray 0.15–0.25, 0.37–0.62, 1.03–1.67 and 2.48–3.43 pF. Takazudo accepted the UV5 route over moving P5_SUP and GND copper. The refilled board fails the verifier's fill-vertex screen outside the edit region (out-of-region area change at most 1.6e-4 mm²); that is recorded as an open exception accepted by Takazudo, not waived. The pair assembly preview, STEP-datum proof and development export passed on the merged head (`manufacturing/verification/pd20-native-d12-merged-20261114/`, nominal CAD only). Nothing is measured. See [#279](https://github.com/Takazudo/zudo-pd/issues/279) |

D1–D3 diagnostics (2026-11-11, [#243](https://github.com/Takazudo/zudo-pd/issues/243)): the
[source-bound record](sim/board-b20-phase33/interface-diagnostics.md) refutes the designed
common-RAMP slope and maximum-step explanations for D1 (a start-order clamp-release edge stays
unresolved), shows slope and current exceedances are one constraint for the modeled C + ESR load,
finds zero-load D2 decay compliant only if "absent" is at most about 1.44 V with ideal simultaneous
disconnect, supports asymmetric-load decay reordering under stated assumptions, and refutes using
a trip threshold as the D3 delivered maximum. The holds above are unchanged; it names the exact
missing inputs.

**Reconciliation 2026-11-13 UTC (2026-11-14 JST, [#289](https://github.com/Takazudo/zudo-pd/issues/289)).**
Reconciliation only. No contract, threshold, component or physical state changed.

- **Native receipts.** The D10–D12 native passes are complete, and each receipt stays bound to its own execution head:
  - D11 at `1a4a954` (`pd20-native-d11-20261113/`, before the #262 merge `084580b`);
  - D10 at `0dbf462` (`pd20-native-d10-merged-20261113/`, the D10 branch head after merging main, before #264 `d63467b`);
  - D12 at `9435b2f` (`pd20-native-d12-merged-20261114/`, before #283 `e868593`).
  None was re-executed at `e868593`. Between `9435b2f` and `e868593` the only changes are that pass's receipts and
  assembly-preview outputs, the input-RC calculation, its test and documentation. The B20 PCB is still the insertion
  output `83e369f6…`.
- **Fitted count.** B20 now has **274 fitted** components and 88 BOM lines, from the D12 merged-head export at
  `9435b2f`. The projection `board_b20_components.py` has 278 entries, including R77–R80; less the four bare-pad
  exclusions (P1, TP3–TP5), that gives 274. The 270-fitted exports at `3f24a3a`, D10 and D11, and the older 269-component export, stay bound to
  their revisions.
- **D12 input capacitance.** The decision and its 0402 amendment expected short `*_IN` stubs to keep the 3 pF stray PA.
  - *Method.* The insertion receipt (`pd20-native-d12-insert-20261113/README.md`, Mac, 2026-11-13) instead CALCULATES
    routed upper bounds from project per-mm and per-via figures: F.Cu 0.09–0.15 pF/mm, In2 0.11–0.134 pF/mm and
    0.2–0.4 pF per via. These are not field-solver extractions or measurements.
  - *Result.* UV5_IN is 2.48–3.43 pF, above the PA. The receipt left the RC recomputation pending.
  - *Recomputation.* `adc4149` (merged in #283) takes, per U6/U7 channel, the larger of the PA and the routed bound.
    U8 had no new routing and keeps the PA. UV+5 becomes 1.435 µs (1.39 µs at 3 pF); the maximum stays 1.802 µs on UV+12.
  - *Applicability.* The figures apply to the inserted geometry on main. The DC thresholds and the IB screen do not
    depend on capacitance. No OV response budget exists, so the RC is reported, not judged.
  - *Records.* The historical decision and receipt text is preserved; `dec-b20-comparator-input-series-r` carries a
    dated observation.
- **D12 status.** The D12 mitigation is implemented. That does not establish electrical acceptance. The pre-order
  hold and the owner-accepted open fill-screen exception both remain.

## Capability and access register

| Capability | Actual state | Next action / boundary |
| --- | --- | --- |
| Mac Docker / pinned KiCad | Docker runs; exact digest `18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec` runs as `linux/amd64`; kicad-cli and pcbnew 10.0.6, wx/rendering verified | Use explicit matching wrappers and shared native/heavy locks. Installed native KiCad 10.0.0 is not acceptance tooling. Isolated official Mac 10.0.6 has verified hash/signature/notarization and ARM64 CLI/pcbnew/wx/render smoke; explicit wrappers isolate config/documents/cache. Final product use remains separately recorded |
| Numerical / mechanical tools | uv, numerical dependencies and CadQuery 2.6.1 / VTK 9.3.1 available | Run final datum and assembly checks on final PCB/model bytes |
| Historical frozen STEP | Required original 158591651-byte file, SHA-256 `b2d5d8da200c4f4e989e33d4190912054475fb17d601f2f76c0b347ab3508167`, not found. Existing same-path file differs; alternate Board B path absent | Historical full replay NOT RUN. Preserve existing files; do not generate a substitute or refresh frozen receipts. This does not invalidate the independent P15 upload-file/source checks |
| Official ST GUI | Acquired at `usb-c/STUSB4500` revision `55d1109e7ef0cffc2ffef2494095d23306594601`; Windows executable not run | Windows execution is outside this Mac task. Genuinely supplied exports can be inspected here; an export is not physical readback |
| GitHub | Read/write access works | Read back tracking writes and verify current-head checks/review before merges |
| Supplier / hardware | No supplier preview, quotation, order, programming or physical test performed | Remain owner actions |

## Verification register

| Evidence class | Checkpoint result | Outstanding obligation |
| --- | --- | --- |
| Software/evidence | Full guarded b4push PASS488s at `3f24a3a`; strict circuit checks pass; 30 phase33 regression tests and two shunt tests pass; independent actual refinement/C12 evidence audits pass integrity checks | Source #239 integrated after independent review, guarded Mac build/browser and exact-head CI; native follow-up checks remain separate |
| Startup simulation | Six actual startup cases complete at `fda0667`; strengthened 1.5 V predicate gives worst +5 V 0.6554 V while an analog magnitude is below 1.5 V | D1 and full model limitations prevent unconditional startup acceptance |
| Re-entry simulation | All eight actual re-entry cases complete. Effective-reenable windows satisfy the sampled slope and 1.5 V screens; whole off-interval sufficient-screen maxima are 0.8489 / 1.1837 V, not direct one-rail/8 V hazard proof | [Actual execution receipt](sim/board-b20-phase33/execution-20261110.md) retains all attempts/model/deck/log/wave hashes; installed asymmetric shutdown/discharge and let-through remain unqualified |
| P r3 layout | R1–R4 corrected through owned placement/router data; default full routing and byte-identical fresh-builder/fixed-route replays completed. Native errors/opens are zero; 11 thermal vias, connected copper and short regulator returns verified. Final probe/polarity artwork has deterministic finishing replay and individual dispositions for all 95 remaining warnings; only MH1–MH3 mechanical parity exceptions remain | Independent layout review and classified warning/process residuals remain separate from measured 5 A qualification |
| B20 layout | C35 bound to U6 with a 4.607 mm direct supply path and local ground returns. Final PCB `09cd97abf5f793d881ee30fc62c7a7b934b1c5973a37637b37c62d15224507ce` has 0 native DRC errors/unconnected/parity and four specifically reviewed J6/J7/J10/J11 library-artwork warnings. Full fresh-builder/fixed-route twins and the subsequent artwork-only finishing replay are separately recorded | Final native current/loop/thermal/mechanical/power reports bind B20 `09cd97ab…` and P `56cbe0ab…`; 45 B20/exporter tests pass, including stale-input and noncanonical-plane rejection |
| Final pair/manufacturing | Current-pair datum PASS for 45 model pairs, zero translations. Native ERC has zero errors; B20 zero warnings and P 27 specifically dispositioned imported-symbol typing warnings. Current-pair assembly PASS with 63 artifact hashes independently checked, 12195 cross-board pairs screened with zero unintended intersections, supplemental U2/U3 envelopes PASS and both native renders reviewed; First DEVELOPMENT REVIEW export failed the strict B20 refill-geometry gate; fresh finalized-pair datum/assembly and DEVELOPMENT REVIEW export plus independent verification now PASS at `3f24a3a` | Exact `board-p + board-b20-draft`, 274 fitted B20 at the D12 merged-head export (270 at `3f24a3a`), four layers, parity, mechanics, BOM/CPL/DNP/THT/rotation and independent export verification; export success is not electrical readiness |

Native schematic/tool evidence and individual ERC warning dispositions are retained in
[the dated native verification receipt](verification/pd20-native-20261110/README.md).
A zero-error result with Unspecified imported pin types is explicitly limited;
netlist/owner checks do not turn it into full electrical qualification.

## Revision-bound development package

Local package: `tmp/pd20-review-refill-3f24a3a-20261110`, exported from clean
`3f24a3abb43e0f24f5e0a12f739ba8ae6bbad03d`. Durable
[review receipt](verification/pd20-native-20261110/development-export-review.json),
manifest and independent result retain its identities. P r3: 44 fitted, 26 BOM
lines, 22 parts per side, two copper layers, four DNP and two bare-pad exclusions.
B20: 270 fitted on top, 87 BOM lines, four copper layers, zero DNP and four
bare-pad exclusions. Both Gerber/drill sets, outlines/origins, BOM/CPL identity,
sides/rotations, THT scope and schematic parity passed. All 145 manifest artifacts
and source hashes were independently checked; four Gerber and two native board
renders were inspected. The 320-second guarded export/independent-verifier run
passed. It is a **DEVELOPMENT REVIEW**, not an electrically ready order packet.
Later disposition-only documentation does not rewrite this package or its locks.

## Physical handoff — NOT RUN

P15: incoming inspection → isolated current-limited 5 V-only provisioning with
L/B disconnected → factory dump, write, readback and full power cycle → no-load
PD acceptance on a source also offering 20 V, verifying a 15 V contract and
VBUS_OUT off during the 5 V phase → accepted module to LED first → received S3
Board B identity/D1/usable-count inspection and PD15 qualification. Expected P15
image SHA-256 is
`76622e14862e53cf318b24eb662f7dc9f34d48134867cf954b30c195c26e8eeb`.

All PD20 T1–T8 sheets remain **NOT RUN**. These post-arrival tests do not replace
the explicitly pre-order interface gates above. PD15 target currents and PD20
continuous/transient/maximum demands remain acceptance demands, not measured
ratings. #228 stays open for its remaining PD, LED and physical acceptance scope.
#97 and #164 were retired as not planned on 2026-11-14 JST (2026-11-13 UTC); their human acceptance is mapped to #228 and these
procedures, and it is not waived.
