<!-- Copied into the repository 2026-11-12 on owner decision (c): the +5 V B pre-registration is held; this paper work and the RG2P/floor finding are recorded now. Paper only; nothing built or dispatched for +5 V. -->

# +5 V D1 options on paper: return the gate pull-down to GND (recommended); RG2P alone explains at most 4.6 mV of the 24 mV floor excess

Paper only, from the deck topology and the baseline waveforms of run 43109786353 (nom). Nothing was built,
pre-registered or dispatched for +5 V.

## The 52 mV floor is mostly channel conduction at the enable peak, not RG2P leakage
- The 28 mV target is RT5O's 1.214 µA (from M12_PRE through 10 MΩ) × RT5A 23.2 kΩ = 28.2 mV.
- The output rises 47.6 mV over 40–115 ms, which is 5.71 µC on 120 µF.
- Of that charge:
  - **The channel supplies 5.26 µC.** It is the integral of the P5 supply current, which peaks at 1.26 mA
    over 60–80 ms as the loop finds the edge.
  - **RG2P carries 0.55 µC into P5_CS in total**, about 21 µA while DRV is at its 2.6 V peak and falling to 0 by
    90 ms. Not all of it reaches the output.
- So RG2P can account for **at most 4.6 mV** (19 %) of the 24 mV excess. Removing it would move the floor to about
  47 mV, not 28 mV.
- **Not worth a standalone change.** It comes free with option B.

## Comparison

| | A. Raise RG2P to ≥ 2.5 MΩ (10 MΩ) | B. Return the gate pull-down to GND (RG2P from P5_G to GND, 100 kΩ) | C. Slower gate path (C3) |
| --- | --- | --- | --- |
| Body-diode injection at an idle gate hold | Vgs / R: about 0.2 µA at 2.0 V (high corner), against the 1.6 µA drain | **None.** The current returns to GND, not through Q4's body diode | Unchanged (8–20 µA if a hold is added) |
| Allows a +5 V T2 (gate held near the edge) | Yes, with margin about 4× at the high corner | **Yes, with no injection term at any corner** | No; C3 is not a hold scheme |
| Turn-off time and disconnect-before-discharge | Unchanged: Q11 pulls P5_G to GND through about 3.5 Ω; RG2P has no role while it is on | **Unchanged** for the same reason. The extra pull-down is also to GND, so it adds to the off path | Slower turn-on only if the RC is on the drive side; must be checked against the order |
| Off state with the driver unpowered or high-Z | **Weaker.** Only 10 MΩ holds Vgs; gate leakage and slow P5_SUP or output ramps through Crss can lift the gate up to DZ2 (11 V). Needs CSD18543Q3A Crss, Ciss and IGSS from the owner bundle (#259 pending) | **Stronger.** The gate is held at GND, so Vgs = −V(P5_CS) ≤ 0. DZ2 is forward-biased in that direction and limits Vgs to −VF, at most −0.9 V (corrected 2026-11-11; this said −11 V) | Unchanged |
| Effect on the loop | Gate divider 0.909 → 0.999 (+10 % loop gain); compensation record needs a recheck | Divider stays 0.909, but it is referenced to GND instead of P5_CS: Vgs = 0.909·DRV − V(P5_CS). Driver headroom at full output: DRV ≈ 1.1 × (5.1 + Vgs) ≈ 8–9 V on the 20 V VIN rail. The compensation record needs a recheck | Lower bandwidth by design |
| Static cost | None | About 50–90 µA from U13B (VIN) at full output; none sensed by the shunt | None |
| Threshold independence | Only as part of a T2 | Only as part of a T2 | **No**: it trades slope for delay at every corner |
| Floor | About −4.5 mV | About −4.5 mV (the RG2P share goes to GND) | None |
| Fixes D1 on its own | No | No | Possibly (unevaluated), at the threshold-dependent cost |
| Parts and schematic | One value | One net change (RG2P's second pin from P5_CS to GND) | Added RC, new values |

The same structure exists on +12 V (RG1P and Q2's body diode into P12_OUT). B applies there too if a +12 V hold is
ever needed. +12 V passes its screen today, so nothing is proposed for it.

## Recommendation: B, followed by a +5 V T2 pre-registration
- **B removes the obstacle without weakening the off state.** It makes the off state stronger, not weaker, and
  changes one net and no values. It leaves the disable path (Q11), DZ2, the discharge order and the AGND return as
  they are.
- **A works on paper**, but it moves the off-state hold of an output disconnect onto a 10 MΩ resistor. Its
  unpowered and slow-ramp behaviour depends on Crss and leakage figures we do not yet hold.
- **C stays the fallback.** It is threshold-dependent.

**B alone does not fix D1.** It only makes a +5 V T2 possible. That T2 would mirror the −12 V candidate on U13B
(VIN/GND): the capture and clamp sinking from TRK5, with V_R and k re-derived for a 0 V lower rail. It would be
pre-registered and run the same way, with B's net change in the deck.

**B's own checks before any adoption:**
- the loop recheck (c12 compensation) with the GND-referenced divider;
- driver headroom at low-line VIN;
- the D11/PCB sequencing, since it is a net change on the B20 schematic.

Not dispatched; waiting for the owner's decision.
