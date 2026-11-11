# D1 reference extraction — 2026-11-11

**Diagnostic only. electrical_acceptance: NOT ESTABLISHED.** The recorded 2 us failures stay failures: +5 V 0.954850860 V/ms, −12 V 1.474778000 V/ms.

Run `43087070975` of `.github/workflows/phase33-d1-reference.yml` at `bdfc02a8bb0bccb53f899635dce01488553571ca`; artifact `13887047549` (zip sha256 `f80073b2400c788cbde533e45637639e31a6c5a456d52f0e5fb004d6ae00ed66`). Identity control: **REPRODUCED** (executed decks, primary and supplemental waveforms byte-identical to the 2026-11-09 refinement). Each executed deck differs from the refined deck by one output-only line:

- nom: `wrdata nom-ref.txt v(ramp) v(ramp_p12) v(ramp_p5) v(ramp_m12) v(clp12) v(clp5) v(clpm12)`
- adv: `wrdata adv-ref.txt v(ramp) v(ramp_p12) v(ramp_p5) v(ramp_m12) v(clp12) v(clp5) v(clpm12)`

Reference slopes are taken between adjacent 2 us bin averages (the refined maximum step) within ±100 us of each excursion and scaled by the deck tracking gain.

| Hypothesis | +5 V (nom) | −12 V (adv) |
| --- | --- | --- |
| Reference-side edge (D1-H6) | REFUTED | REFUTED |
| Clamp-diode release (D1-H6) | REFUTED | REFUTED |
| Recorded common RAMP too steep (D1-H1) | REFUTED | REFUTED |
| Adjacent-sample trigger is a solver-timestep artefact (D1-H7) | NOT APPLICABLE (the adjacent-sample rule did not fire) | SUPPORTED |
| Pre-bias overshoot (D1-H4) | UNRESOLVED (needs the paired variant run) | UNRESOLVED (needs the paired variant run) |

| Quantity | +5 V | −12 V |
| --- | ---: | ---: |
| Output slope at the failed segment (V/ms) | 0.954850860 | 1.474778000 |
| Scaled reference peak, 2 us bins (V/ms) | 0.1192 | 0.3557 |
| Scaled common RAMP peak, 2 us bins (V/ms) | 0.1192 | 0.3529 |
| Ideal tracking slope (V/ms) | 0.3137 | 0.7611 |
| Exception ceiling (V/ms) | 0.95 | 1.47 |
| Adjacent-sample scaled reference peak (V/ms) | 0.1192 | 3730.2284 |
| Clamp-diode voltage across window (V) | -4.850 to -4.843 | -4.893 to -4.041 |

The −12 V adjacent-sample peak is 0.977 mV over 2.11 ns at 138.211289 ms, inside a cluster of 21 samples (138.211270–138.211332 ms, minimum step 0.235 ns) where ramp_m12 rings 1.398 mV peak to peak with 18 sign reversals, as the XU16A clamp output reaches 4.962 V. On 2 us bins the reference stays within the ideal tracking band on both rails, so the reference side does not explain either excursion; the excursions lie downstream of the reference.

**Corrected attempt.** The in-job analysis used adjacent-sample slopes and classified the reference edge as REFUTED (+5 V), SUPPORTED (−12 V). Before adoption, the −12 V in-job result was first reported as a 0.85 V reference-side step. That was a misreading: the 0.85 V is the gradual rise of the XU16A clamp output (clpm12) across the window, and the reference jump is the millivolt-scale timestep ring described under timestep_artefact. The report was corrected and nothing was adopted from it.

No pre-bias variant, correction candidate, contract change or tolerance is adopted. `d1-reference-20261111.json` holds every hash and value.
