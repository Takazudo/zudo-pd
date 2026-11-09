# Phase33 actual interface reproduction — 2026-11-10 JST

**All 14 requested cases completed with actual waveforms. Electrical order acceptance remains NOT ESTABLISHED.** The [machine receipt](execution-20261110.json) contains every case's source/deck/model/settings/log/waveform hashes, failed attempts, selected solver command and both strengthened analysis outputs. Raw waveforms, vendor models and logs remain local and ignored in `zudo-pd-simulation/tmp/phase33-execution/`; they are not replaced by analysis unit tests.

## Execution identity

The clean execution tree was fixed at `fda0667df503aa7cdc8ec0d45920dd4c731dc56c`. Analysis ran against the separately hashed current analyzers based on main `76f807f11d3b97a9625e8cc9dd6835e235bb99df`. The selected host was the Mac; ngspice 44.2 executed in the required `linux/amd64` image `kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`, one CPU and one solver thread, under the heavy guard. `.spiceinit` sets `ngbehavior=psa` and `num_threads=1`. The decks retain `numdgt=15`, a 5 us maximum step and the recorded per-case solver options/variant changes. Selected variants are evidence, not interchangeable solver runs.

| Case | Selected variant | Actual samples | End (ms) |
| --- | --- | ---: | ---: |
| nom | original | 52139 | 250 |
| adv | rshunt | 53332 | 250 |
| rev | rshunt | 53579 | 250 |
| nomR | original | 51523 | 250 |
| advR | original | 51509 | 250 |
| revR | rshunt | 52750 | 250 |
| reR6 | abstol | 66186 | 320 |
| reR10 | rshunt | 68002 | 320 |
| reR14 | rshunt | 68129 | 320 |
| reR20 | rshunt | 68059 | 320 |
| reB6 | rshunt | 89220 | 420 |
| reB10 | rshunt | 89192 | 420 |
| reB14 | rshunt | 89190 | 420 |
| reB20 | rshunt | 89285 | 420 |

The aggregate audit rejects incomplete/missing cases, stale source or runner bytes, changed deck transformations, altered retained **and executed** library/settings copies, changed logs/waveforms, incomplete time coverage, and mismatched aggregate copies. It reran `analyze_tracking.py` and `analyze_reentry.py` on the complete actual waveform directory. Independent review separately checked the executed model/settings copies and representative worst samples. A successful integrity/analysis process is not a circuit acceptance verdict.

## Exact model recovery

The four TI archives match the historical section-5 hashes; full URLs and hashes are in `model_recovery` in the receipt. These 14 tracking/re-entry runs use OPAx187 SBOMAB6 and CSD18543Q3A SLPM286. TPS54560 average/transient archives were recovered separately; they are not used by these stiff-source tracking decks.

- OPAx187 library is unchanged: `a1a17afb119ffc7dbcceff289ca43af137b794f447b0e190b56a289d6cfe8f4f`.
- Original CSD18543Q3A library: `fa4ef72177bc7691b956ef047985e6fc0a490ae1e12d41295c787e6e51dba170`.
- Syntax-only ngspice copy: `fe12b71b021aa03d0fd6718e1de1d7cf013147e00161bb8853565f3dbff2c9b8`. Exactly five `.PARAM name value` assignments use `name=value`; all other bytes are preserved.

No substitute vendor model is presented as exact-part evidence. The behavioral enable/interlock, level shifters and 35-ohm gate pull-down approximations remain limitations. Reset paths use their separately recorded 3.5-ohm approximations; disable edges take 1 ms. These are authored model assumptions, not measured switching behavior.

## Startup and re-entry results

All six startup cases use the current **1.5 V** analysis threshold, not the historical 1.45 V threshold. The worst +5 V value while either analog magnitude is below 1.5 V is 0.6554 V. Band-entry skew is 0.730–0.810 ms (a PROPOSED criterion); the 1.845–3.920 ms ramp-start skew is a CALCULATED fastest-slope proxy, distinct from the direct voltage-form checks.

Adjacent-sample analysis still finds the nominal no-load +5 V and adverse no-load negative-rail slope exceedances. The separate [2 us refinement](startup-refinement.md) measures 0.954850860 V/ms / 114.510041 mA and 1.474778000 V/ms / 265.259332 mA within the respective low-voltage regions. These exceed the adopted exceptions; no tolerance, excess-current budget or wider exception is adopted. This remains a **PRE-ORDER HOLD**, not a measured physical violation.

`reR*` interrupts the modeled ramp at 150 ms; `reB*` disables established modeled outputs at 200 ms. The upstream ideal sources remain present. Requests occur 6/10/14/20 ms later, while the modeled interlock delays effective re-enable as shown. Every case reaches the discharged modeled state before re-enable; this does not validate the installed discharge implementation.

| Case | Effective re-enable after disable (ms) | Band-entry skew (ms) | +5 V max after re-enable, analog min <1.5 V | +5 V max over off/re-entry, analog min <1.5 V |
| --- | ---: | ---: | ---: | ---: |
| reB10 | 19.147 | 0.730 | 0.6553 | 1.1837 |
| reB14 | 19.164 | 0.730 | 0.6553 | 1.1837 |
| reB20 | 21.179 | 0.735 | 0.6554 | 1.1837 |
| reB6 | 19.137 | 0.730 | 0.6553 | 1.1837 |
| reR10 | 19.147 | 0.735 | 0.6551 | 0.8475 |
| reR14 | 19.164 | 0.730 | 0.6552 | 0.8475 |
| reR20 | 21.179 | 0.735 | 0.6551 | 0.8475 |
| reR6 | 19.137 | 0.735 | 0.6554 | 0.8489 |

All eight effective-reenable windows have zero adjacent-sample slope-bound exceedances and satisfy the sampled +5 V/1.5 V screen. Small negative sample increments remain, so no strict monotonicity PASS is claimed without numerical/model disposition. The modeled loads are fixed resistors 6.0 / 6.316 / 12.625 ohms (+12 / −12 / +5), with 180 / 180 / 120 uF and 50 mOhm assumed ESR. They are not a complete independent/asymmetric load envelope or a 20 ms constant-current qualification.

The whole off/re-entry maxima exceed 0.8 V under the sufficient 1.5 V screen. This must not be mislabeled as proof of the contract's one-rail-absent/other-at-least-8-V hazard. The [independent raw samples](independent-sample-review-20261110.json) show reR6 at 151.864253 ms: +12=1.498028 V, +5=0.848868 V, −12=−1.666823 V; and reB20 at 203.171090 ms: +12=1.498927 V, +5=1.183699 V, −12=−1.806534 V. The other analog rail is below 8 V in both. The conservative conjunction of one analog below 1.5 V, the other at least 8 V and +5 above 0.8 V has zero saved samples in those two complete representative intervals. This is a bounded diagnostic, not proof over untested loads or continuous time.

## Remaining pre-order work

The canonical [OSC interface](https://github.com/Takazudo/zudo-osc-hole-field/blob/433c88b27b2e49284fe1a717b47ba4226c829dd3/design/architecture-278/integration/power-contract/pd-interface-20v.md) keeps CONTRACT, CALCULATED and PROPOSED rows distinct. Its 1.5 V definition is sufficient; the band-entry/discharged-state proposals and direct component-limit voltage forms are not silently converted into a single PASS/FAIL rule.

A final read-only refresh found OSC main at `d00638cbfbf204bdeaabb95bca5206f7b6dd7511`; the canonical contract file is byte-identical to the requested `433c88b27b2e49284fe1a717b47ba4226c829dd3` version (SHA-256 `8702890d4d13c4ba3fbd129dca98ccabf12b006aee7e99230e81ed4dad09556a`). See [refresh receipt](upstream-contract-20261110.json). No OSC files or proposed terms were changed.

The actual installed shutdown implementation still needs a contract-preserving model and evidence for independently asymmetric loads, detection/disconnection timing, active discharge and maximum delivered current including overshoot. The contract requires **disconnect before discharge**; tracked ramp-down before disconnection remains an unadopted proposal. A limiter trip window or a recorded ideal-source current cannot establish let-through compliance. These decks omit the complete installed limiter/window-monitor/PD shutdown dynamics.

Completion closes the missing-waveform reproduction work only. Refined startup exceptions, strict monotonicity/model limitations, shutdown/discharge and let-through remain pre-order issues under #235/#231/#238. NVM and thermal/component/process residuals are separately recorded in the [readiness ledger](../../prototype-order-readiness.md). All physical T1–T8 sheets remain NOT RUN; these pre-order obligations are not reassigned to post-arrival testing.
