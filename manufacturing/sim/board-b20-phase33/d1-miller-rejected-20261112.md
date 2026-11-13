# Miller capacitor on the −12 V pass pair: REJECTED (owner decision 2026-11-12)

This was a paper check only. No SPICE deck was built or run, and no verdict changes. electrical_acceptance stays
NOT ESTABLISHED.

## Candidate
- **The part.** A capacitor C_M from Q6 drain (M12_OUT) to the pair gate (M12_G), meant to cap the no-load catch-up
  step's dV/dt independently of the FET threshold.
- **Withdrawn sizing.** The proportionality note gave 1.7 µF (RG3 10k) or 0.17 µF (RG3 100k). That assumed
  rail-to-rail gate drive and is withdrawn. The recorded step is set by the FET's transconductance: Vgs climbs
  0.54 V on a net gate drive near zero, while U9B's integrator ramps M12_DRV at 0.8–1.1 V/ms.

## The figures come from a reduced-order model fitted to the recorded step
`miller-paper/reduced_m12_loop.py` integrates three parts:
- U9B's PI, taken as ideal;
- the gate node (RG3, RG3P, a lumped Cg, C_M);
- the 180 µF output.

The FET's Id(Vgs) curve, ramp_m12 and m12_cs are taken from run 43187732133, deck adv. With C_M = 0 the model
reproduces the recorded step: 1.447–1.520 V/ms, against 1.4748.

| C_M (Cg 1–3 nF, ±5 %) | Peak below 0.75 V (limit 1.47) | Peak above 0.75 V (limit 1.22) |
| --- | --- | --- |
| 1–22 nF | Worse than the baseline | — |
| 47 nF | 1.43–1.47 V/ms | 1.43–1.47 V/ms, fails |
| 100 nF | 1.28–1.31 V/ms | 1.30–1.33 V/ms, fails |
| 220 nF | 1.06–1.10 V/ms | 1.12–1.15 V/ms |
| 330 nF | 0.95–0.98 V/ms | 1.03–1.05 V/ms |
| 470 nF | 0.86–0.89 V/ms | 0.96–0.98 V/ms |

## Rejected for five reasons
- **Phase margin about 9° at the useful sizes.** The plant becomes 1/(s·RG3·C_M). With U9B's PI it is a double
  integrator, with its zero at 1.6 kHz and crossover near 160 Hz. So the loop would need recompensating.
- **The capacitor cannot be bounded.**
  - The bias across C_M reverses: −12.3 V at enable, about −8.3 V at the step, +3.3 V running.
  - The largest sourced C0G is 10 nF, so 220–470 nF means X7R.
  - No X7R DC-bias curve is retained, and dV/dt scales as 1/C_M.
- **It depends on the start-order clamps.** The 1.1–1.7 ms −12 V lag would put +12 at 0.67–0.82 V on the recorded
  trajectory, against the 0.5 V limit, unless U15/U16 hold +12's ramp.
- **It does nothing on +5 V.** Q3 is a source follower (p5_cs tracks the output), and the +5 V step is U13B's
  integrator ramp.
- **FET spread is uncovered.** The CSD18543Q3A owner bundle retains no VGS(th), transfer-curve or Crss rows.

No recompensated loop study is planned. The full paper is in the project files
(`d1/miller-capacitor-paper-20261112.md`).
