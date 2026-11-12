<!-- Owner decision 2026-11-11 on this check: T2 on +5 V REJECTED by construction (RG2P / Q4 body-diode mechanism); T2 on -12 V admitted for evaluation under d1-t2-criteria.md. The general bound below is a constraint on any future +5 V / +12 V gate-hold scheme. -->
# T2 (peak-hold anti-windup clamp) paper check: fails on +5 V by construction, holds on −12 V; stopped before pre-registration

This is a DC and small-signal check of the deck topology, using the baseline waveforms of run 43109786353. Nothing
was built, pre-registered or run.

## +5 V fails: any gate held near the edge pumps the output through RG2P and Q4's body diode
**The current path.**
- In the +5 V gate network, RG2 (10 kΩ) runs from P5_DRV to P5_G and RG2P (100 kΩ) from P5_G to P5_CS.
- With the pair off, P5_CS has no path except the body diodes. Q3's diode (to P5_SH, 5 V) is reversed. Q4's
  diode runs from source P5_CS to drain P5_OUT, so it conducts as soon as P5_CS rises a diode above the output.
- So a gate held at internal Vgs drives Vgs / 100 kΩ through RG2P and Q4's body diode into the +5 V output.
  The pair's channel does not need to conduct.

**The baseline already shows it.** As DRV falls back from its 2.622 V enable peak, P5_CS rises to 0.468 V at
81.5 ms, a diode above the 52 mV output. Only when DRV reaches its rail does this stop. It contributes to the
floor overshoot: 52 mV against the 28 mV target.

**What T2 would do.**
- The clamp's purpose is to idle the gate about 0.8–0.9 V below each part's own 5 mA onset. That is Vgs
  ≈ 1.5 V at the model corner, 0.83 V at the low corner and 2.0 V at the high corner.
- Injected current: 8–20 µA into the output, against the 1.6 µA the 33.2 kΩ feedback divider drains at 52 mV.
- The output therefore rises by about (I − 1.6 µA)/120 µF ≈ 0.05–0.15 V/s: 4–11 mV over the 75 ms reset window.
  It settles toward about 0.2–0.45 V over seconds.
- That is an output pedestal, and its size depends on the threshold. It fails "cannot create an output
  pedestal" at every corner, and rule 6 by orders of magnitude.

**The no-pedestal limit, and why it applies beyond T2.**
- Avoiding the pedestal needs Vgs / 100 kΩ ≤ 1.6 µA, so an idle Vgs of 0.16 V or less. That leaves almost the
  whole dead zone.
- The same mechanism applies to any scheme that holds the +5 V gate up at no load, including C1. For example,
  C1's g20 rest Vgs of 0.44 V would inject 4.4 µA.
- +12 V has the same structure (RG1P, and Q2's body diode into P12_OUT).

## −12 V passes on paper
**Current path.** RG3P's current enters M12_CS. From there it goes to M12_SH through Q5's body diode (source M12_CS,
drain M12_SH, forward-biased). Q6's diode (M12_CS to M12_OUT) stays reversed, by about
12 V. So no gate-network current reaches the output.

**Idle point.** The clamp holds DRV at about the held peak minus 0.86 V (−9.48 V peak in the baseline, so about
−10.3 V). That is internal Vgs ≈ 2.34 − 0.78 ≈ 1.56 V at the model corner. Every corner idles about 0.9 V below
its own onset, because the loop finds each edge.

**Channel current at idle.** The same device model's curve, from the +5 V ramp (about 210 mV per decade between
1 µA at 1.665 V and 1 mA at 2.292 V), gives about 0.2–0.4 µA. That is below the output drain at −97 mV: about
0.97 µA through RMA1 100 kΩ, plus 0.1 µA through 750 kΩ. This is an inference: the −12 V supply current cannot
resolve below about 100 µA because the op-amp supplies vary.

**No pedestal, and threshold-independent.** No pedestal at any corner, because the corners are emulated by a
gate-referenced offset and the subthreshold slope is the same device.

**Small signal.**
- The clamp is a difference stage (k = 10) feeding the inverting input through a diode and R_C = 1 MΩ.
- Loop: L(s) = (k/R_C)(10 kΩ + 1/(s·10 nF)), crossing over near 160 Hz. The high-frequency term
  (k·10 kΩ/R_C = 0.1) stays below unity, giving about 90° phase margin, far below the OPAx187 bandwidth.
- Steady clamp error: about 1 µA × R_C / k ≈ 0.1 V.

**Stale high: not possible.**
- The hold is reset while EN_N is high, including the 19 ms re-enable and first power-up. At first power-up
  nothing has been held, so the clamp stays off until the peak charges it.
- The clamp acts only while RAMP_RST holds RAMP and EN is asserted. It is open during tracking, so later high
  driver levels are never used.
- Droop (C_H 100 nF C0G, R_B 10 MΩ, τ ≈ 1 s) only lowers the clamp level, which is the safe direction (less
  drive): 7 % over 75 ms, at most 10 % over 108 ms.

**Quick re-enable caveat.** After a 19–20 ms off, RAMP_RST has charged only to about 1.7 V, so the reset window
is about 24 ms. The loop peaked about 26 ms after enable in the baseline, so RAMP may release before the edge
is found. The clamp then never engages and the rail behaves as the baseline. That is no benefit, but no harm.

**Release step.**
- Removing the about 1 µA clamp current through the 10 kΩ zero steps DRV by about 10 mV, roughly 9 mV at the
  gate. The pair is off, so there is no output step.
- A real BSS138's charge injection (a few pC into the 10 nF integrator) is unmodelled and is about mV-level.

## Options for the owner
1. **Evaluate T2 on −12 V only, with the four enable-edge corners.**
   - On +5 V, record the RG2P and Q4 body-diode mechanism as the reason no gate-hold scheme can idle near the
     edge at no load.
   - This leaves the +5 V D1 failure without a threshold-independent candidate.
2. **Add a +5 V gate-network change to the candidate set.** RG2P from 100 kΩ to 10 MΩ would cut the injection
   to Vgs/10 MΩ, about 0.2 µA. That is a design change to the turn-off path: it relies on Q11 and DZ2 for
   off-state hold, and its unpowered behaviour is unverified. It would need its own analysis before any
   admission.
3. **Fall back to C3 (slower gate path) for +5 V.** It is not threshold-independent.

I recommend option 1 now, run with the corners. Option 2 should be analysed on paper first.
