<!-- Copied into the repository 2026-11-12 on owner decision (c). Option B is the candidate to evaluate, not adopted; no spec or schematic change. The +5 V pre-registration is held until the deck-stiffness item is resolved. -->

# +5 V option B (RG2P returned to GND) paper check: every part holds; off-state Vgs ≤ 0 V; one correction to my earlier note

Paper only, from `scripts/schgen/board_b20_spec.py`, the component owners and the baseline waveforms of run
43109786353. Nothing was built, pre-registered or dispatched.

**Sourced facts used:**
- **CSD18543Q3A** (`component-csd18543q3a`): VGS ±20 V abs max; IDSS 1 µA max at 48 V; VGS(th) 1.5 / 2.0 / 2.7 V at
  25 °C; RDS(on) 15.6 mΩ max at VGS 4.5 V. **Unsourced:** IGSS, Crss/Ciss, the transfer curve, and VGS(th) over
  temperature.
- **BZT52C11** (`component-bzt52c11-c92321`): VZ 10.4–11.6 V at 5 mA; IR 0.1 µA max at 8 V; VF 0.9 V at 10 mA.
- **OPA2187** (`component-board-b20-draft-candidates`): signal inputs (V−)−0.5 to (V+)+0.5 V abs max; output swing
  100 mV max at 10 kΩ (VS 8–36 V); VCM (V−)−0.1 to (V+)−2 V (4.5–8 V row); IQ 145 µA max per amplifier.

## Correction: DZ2 clamps negative Vgs at one forward drop, not at −11 V
- DZ2's cathode is on P5_G and its anode on P5_CS (`zener('DZ2', 'P5_G', 'P5_CS')`). It limits Vgs at +10.4–11.6 V.
- In the negative direction DZ2 is forward-biased, so Vgs ≥ −VF: at most −0.9 V at 10 mA, and less at µA.
- My earlier comparison said "DZ2 limits it at −11 V". That was wrong; the off state is still stronger, as below.
- The gate rating (±20 V) is never approached in either direction.

## Where P5_CS sits with the pair off, and the off-state Vgs
With RG2P to GND, P5_CS has no resistive DC path. Only the following can move it:
- **Up:** drain leakage of Q3 (from P5_SH) and Q4 (from P5_OUT), at most 1 µA each at 25 °C (IDSS row, 48 V).
- **Capped by the output body diode:** Q4's body diode, P5_CS ≤ P5_OUT + VF.
- **Capped by the input body diode:** Q3's body diode, P5_CS ≤ P5_SH + VF.
- **Capped by DZ2 forward:** P5_CS ≤ P5_G + VF.
- **Nothing pulls P5_CS below its leakage equilibrium**, apart from DZ2's reverse leakage (≤ 0.1 µA at 8 V) toward
  the gate. So P5_CS ≥ about min(P5_G, 0 V) once leakage has settled.

| Case | P5_G | P5_CS bound | Off-state Vgs | Today (RG2P to P5_CS) |
| --- | --- | --- | --- | --- |
| Driver unpowered (VIN absent) | 0 V: RG2P to GND; the unpowered OPA2187 output is clamped near its rails | 0 to min(P5_SH, P5_OUT, P5_G) + VF | −0.9 V to 0 V | 0 V (RG2P ties G to CS) |
| Input present, output at 0 V, driver unpowered | 0 V | ≤ P5_OUT + VF, so ≤ 0.9 V; IDSS ≤ 1 µA flows to the output | −0.9 V to 0 V | 0 V |
| Output back-driven, input absent | 0 V | ≤ P5_SH + VF, so ≤ 0.9 V | −0.9 V to 0 V | 0 V |
| Slow VIN ramp below the OPA2187's 4.5 V minimum supply | Q11 holds G at GND if EN_N is valid; otherwise it is set by the undefined driver output | ≈ 0 V (both supplies still low) | **Same as today**: not bounded by B either way | Same exposure |

- **Against the threshold.** The worst off-state Vgs is 0 V. That leaves at least 1.5 V to the guaranteed minimum
  VGS(th) at 25 °C. **Over temperature this margin is unsourced**, because the owner holds no VGS(th) tempco.
- **The slow VIN ramp is not a B question.** Today and with B, the gate is held only by Q11, and only while EN_N is
  valid. That depends on the VIN / P5_SUP / EN_N start-up order. B neither improves nor worsens it.

## Turn-off and disconnect-before-discharge: unchanged
- **Turn-off.** Q11 (BSS138 on EN_N) pulls P5_G straight to GND; the deck models it as about 3.5 Ω. B only puts
  RG2P's 100 kΩ in parallel to GND, which changes the off-path conductance by 0.0035 %.
- **P5_CS discharge.** P5_CS discharges through DZ2 forward into Q11, as it does today, because Q11 already pulls
  the gate to GND.
- **Discharge order.** The discharge network and the AGND return are not touched, so the order is unchanged.
- Turn-off time is set by Q11 and the pair's gate charge, neither of which B touches. The gate charge is unsourced,
  but it is the same element either way.

## U13B drive and low-line headroom
**Gate drive needed at full load.** VGS 4.5 V is enough for the sourced 15.6 mΩ RDS(on) row, so full enhancement
needs at most:

| | DRV needed | Load on U13B |
| --- | --- | --- |
| B: G = 0.909·DRV | (5.15 + 4.5) / 0.909 = 10.6 V | 10.6 V / 110 kΩ = 96 µA, to GND |
| Today: Vgs = 0.909·(DRV − out) | 5.15 + 4.5 / 0.909 = 10.1 V | (10.1 − 5.15) / 110 kΩ = 45 µA |

- **Headroom.** U13B swings to within 100 mV of VIN at 10 kΩ (1 mA, VS 8–36 V row). At VIN_MIN 19.0 V that is
  18.9 V, leaving **8.3 V of headroom**. 96 µA is far inside the 10 kΩ swing condition.
- **Supply cost.** The extra ~50 µA comes from VIN, upstream of every shunt, so it is not sensed and the low-side
  margins are unchanged.
- **DZ2 at a saturated driver.** If DRV saturates high with the output near 0 V, DZ2 clamps Vgs at 10.4–11.6 V.
  The zener current is limited by RG2 to about 0.6 mA, the same order as today. That is within the gate rating
  and the zener's 370 mW.

## Loop recheck with the GND-referenced divider
- **In conduction (source follower, P5_CS ≈ P5_OUT).**
  - Today: Vgs = 0.909·(DRV − out), so dout/dDRV ≈ 1.
  - With B: Vgs = 0.909·DRV − out, so dout/dDRV ≈ 0.909.
  - The plant gain falls by 0.8 dB. The follower pole (gm against the output capacitance) is unchanged.
  - The +5 V tracking loop is the U13B integrator (CT5 10 nF) through the 1/3.32 divider. Its crossover therefore
    falls by about 9 % and its phase is essentially unchanged.
  - The existing c12 record covers the converter inner loop, not this loop, so no retained margin moves.
  - **The B-only case in a +5 V dispatch measures this directly** (tracking, slope screen, overshoot).
- **At the enable edge (subthreshold).** Vgs = G − P5_CS with P5_CS ≈ P5_OUT ≈ 4–52 mV, so the loop finds the same
  edge. RG2P's 0.55 µC enable-window injection into P5_CS goes to GND instead, a floor change of at most −4.6 mV.

## T2 on +5 V with B: passes on paper at all three corners
**The +5 V realization differs from −12 V in one structural point: the clamp needs a negative rail.**
- With the clamp active, U13B is linear and TRK5 ≈ RAMP_P5 ≈ 0 V.
- The clamp must sink about 1.0 µA from TRK5: out/23.2 kΩ (2.24 µA at 52 mV) minus RT5O's 1.21 µA.
- Its output must therefore reach about −0.9 V (diode drop plus I_C·R_C), below GND.
- **So the clamp OPA2187 runs from VIN / M12_PRE.** The span is 31–33 V, inside the 40 V abs max and the VS 8–36 V row.
- **Input headroom at the high end.** With DRV at 18.9 V, the difference stage's + input sits at about
  0.83·DRV + 0.17·V_R ≈ 16.1 V. That is below VIN − 2 V = 17 V at VIN_MIN. The margin is small but inside, and
  the clamp is saturated inactive there.
- **The hold.** It captures DRV through a diode, holds on C_H to GND, and resets to GND while EN_N is high. The
  buffer input at 0 V is mid-range on a VIN / M12_PRE supply, better than −12 V, where it sits at V−.
- V_R = REF25 and k = 4.99 give the same offset as −12 V: Δ ≈ (2.5 + 0.36 + 0.5) / 4.99 ≈ 0.68 V. Together with
  the capture drop, the floor is about 1.0 V below the held peak.
- **If M12_PRE is absent while VIN is present,** the clamp cannot go below about 0 V and stays inactive. That is
  baseline behaviour, a fail-safe direction.

**Idle point and pedestal at each corner.**
- With the pair subthreshold, the Q3 channel current flows into P5_CS. Q4 passes it (channel at near-zero Vds, or
  its body diode), so P5_CS ≈ P5_OUT and Vgs ≈ G − P5_OUT. The idle point is therefore referenced to the output,
  not to a floating node.
- **Idle internal Vgs** ≈ enable peak (2.31 V at the model corner) − 0.91 × 1.0 V ≈ 1.40 V. The same offset applies
  at the −0.66 V and +0.54 V corners, because the hold captures each part's own edge.
- **Channel current into the output** is about 0.05 µA (210 mV per decade from 1 µA at 1.665 V; an inference).
- **Output drain** is ≥ 1.5 µA: 2.24 µA through RT5A while TRK5 is held at 0 V, and 1.56 µA if wound.
- So the injection is about 4 % of the drain at every corner, against the pre-registered bound of 0.5×. **No
  pedestal.**
- **The general bound now applies only through the channel.** Under B, no gate-network current reaches the output
  at any Vgs.

**Small signal.**
- +5 V has no 10 kΩ zero: CT5 runs straight from DRV to TRK5. The loop L = (k/R_C)/(s·CT5) is a pure integrator
  with crossover k/(R_C·CT5) = 1000 rad/s (160 Hz) and a phase margin near 90°.
- The difference stage's closed-loop bandwidth (about 92 kHz) and the diode's ~24 kΩ small-signal resistance
  (+5 % on R_C) do not move that.
- **Release.** Without the zero there is no instantaneous step. DRV continues from the clamp floor at the integrator
  rate.

**Stale high and first power-up.** Both are the same as −12 V: the hold is reset while EN_N is high, captures only
in the early reset window, and the clamp floor sits below the held edge.

## Where this leaves +5 V
**Every part of the check holds. Nothing failed, so this does not stop here.**

**Held (owner decision 2026-11-12)** because it runs on the same deck and would likely lose its corners to the same aborts ([deck stiffness](d1-deck-stiffness-20261112.md)). When admitted, it will include:
- the corners;
- an inert control (B plus T2, clamp returned to GND);
- a **B-only case** (net change, no clamp), so the effects of B and T2 are separable.

**RG2P does not explain the 52 versus 28 mV floor** (at most 4.6 mV, 19 %; [options note](d1-p5-gate-hold-options-20261111.md)). Recorded here per owner decision; the floor is left as it is. +12 V stays report-only.
