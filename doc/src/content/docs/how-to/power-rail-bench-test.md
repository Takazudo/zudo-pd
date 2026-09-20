---
title: Power Rail Bench Test Procedure
sidebar_position: 104
description: Pre-power inspection, staged power-up, load regulation, thermal, ripple and transient tests for the +12V, +5V and -12V linear regulator outputs.
---

<Note title="Historical board procedure">

This procedure describes the previous hardware and may name retired parts, nets,
pin assignments or export assumptions. Use the [current architecture](/docs/architecture/),
[prototype bring-up procedure](/docs/how-to/renewal-bring-up/) and
[current manufacturing workflow](/docs/how-to/jlcpcb-package/) for renewed boards.

</Note>

Bench procedure for validating the Board B linear regulator stage once a board is
assembled: U6 (+12V, L7812CD2T-TR), U7 (+5V, L7805ABD2T-TR) and U8 (-12V, CJ7912).

Run [Regulator Assembly, Soldering, and Inspection](./regulator-assembly-and-inspection.md)
first. Everything below assumes that checklist has passed.

<Note>
This page covers the regulator stage only. For the full board bring-up sequence
including the USB-PD negotiation, see the
[bring-up test procedure](../inbox/v3-bringup-test-procedure.md).
</Note>

## 1. Pre-power inspection

Before applying any power:

1. **Capacitor polarity**

   - Check C24 and C25 (the -12V chain electrolytics) with a DMM in diode mode.
   - The positive terminal must sit at GND potential; the negative terminal goes to
     the negative rail. This is reversed relative to C20/C21 on the +12V chain.

2. **Visual inspection**

   - No solder bridges
   - Good solder coverage on every tab
   - Correct IC orientation, especially U8 (pin 1 = GND)
   - All components present

3. **Resistance checks** - with the board unpowered, confirm no short from any of
   +13.5V, +12V, +7.5V, +5V, -13.5V or -12V to GND.

## 2. Staged power-up

Bring each rail up gradually rather than switching the supply on at the target
voltage.

1. Start below the regulation threshold - for the -12V chain, around -10V in.
2. Increase to the design input in steps: +13.5V (U6), +7.5V (U7), -13.5V (U8).
3. Watch for smoke or smell at every step.
4. Feel for a package heating faster than the load explains - that is thermal
   runaway, and it means stop.

## 3. No-load output check

| Position | Input  | Expected output          | Source                     |
| -------- | ------ | ------------------------ | -------------------------- |
| U6       | +13.5V | 11.4V - 12.6V            | `fact-l7812cd2t-vout-band` |
| U7       | +7.5V  | 4.8V - 5.2V              | `fact-l7805abd2t-vout-band`|
| U8       | -13.5V | -11.4V to -12.6V         | `fact-cj7912-vi-guarantee-band` |

Also measure the quiescent current at no load. The CJ7912 specifies 3 mA maximum at
25 °C (`fact-cj7912-iq-max`); a reading well above that points at a fault, not at
normal quiescent draw.

<Warning title="U8 is running outside its guaranteed input band">
`fact-cj7912-vi-guarantee-band` records that the CJ7912 output band is guaranteed
only for an input between -14.5V and -27V. The design feeds it **-13.5V**, which is
1.0V short of that, and only 0.4V above the 1.1V typical dropout at 1A. So a -12V
reading that drifts under load is a **headroom** result, not necessarily a bad part.
Record the actual DC-DC output voltage alongside every -12V measurement, and treat
`fact-cj7912-rail-headroom` (verdict NEEDS BENCH) as the thing this test is
answering.
</Warning>

## 4. Load regulation

For each rail, connect a variable load and sweep it.

**+12V (U6)** - sweep 0 to 1.2A:

| Load  | Expect                          |
| ----- | ------------------------------- |
| 0 mA  | within the 11.4V - 12.6V band   |
| 600 mA| within the band                 |
| 1.2 A | within the band                 |

**+5V (U7)** - sweep 0 to 0.5A:

| Load   | Expect                        |
| ------ | ----------------------------- |
| 0 mA   | within the 4.8V - 5.2V band   |
| 250 mA | within the band               |
| 500 mA | within the band               |

Verify the total drop from no-load to full-load stays under 50 mV.

**-12V (U8)** - sweep 0 to 0.8A:

| Load   | Expect                            |
| ------ | --------------------------------- |
| 0 mA   | within the -11.4V to -12.6V band  |
| 400 mA | within the band                   |
| 800 mA | within the band                   |

Verify the variation from no-load to full-load stays under 120 mV.

Record the input voltage at every point. A rail that sags at high current when its
input has also sagged is a DC-DC stage problem, not an LDO problem.

## 5. Thermal

<Warning title="Do not test against an assumed junction temperature">
Older project pages quoted expected case temperatures ("should be about 69 °C",
"should be about 73 °C") derived from thermal resistances that do not match the
recorded datasheet facts. Those predictions are wrong and are not carried forward.
Measure the case temperature, convert it to a junction estimate, and compare that
against the junction limit - do not compare it against a predicted number.
</Warning>

Procedure, per position:

1. Apply the rated load - 1.2A on +12V, 0.5A on +5V, 0.8A on -12V - for 30 minutes.
2. Measure the case temperature with a thermal camera or a thermocouple on the tab.
3. Record the ambient temperature at the same time.
4. Convert to a junction estimate: `Tj ≈ Tcase + P_diss × thetaJC`.
5. Compare against the junction limit.

| Position | P_diss | thetaJC                          | Tj estimate     | Tcase limit for Tj ≤ 125 °C |
| -------- | ------ | -------------------------------- | --------------- | --------------------------- |
| U6       | 1.80 W | 3 °C/W (`fact-l7812cd2t-rthjc`)  | Tcase + 5.4 °C  | 119.6 °C                    |
| U7       | 1.25 W | 3 °C/W (`fact-l7805abd2t-rthjc`) | Tcase + 3.8 °C  | 121.2 °C                    |
| U8       | 1.20 W | **not published**                | not derivable   | see below                   |

`fact-cj7912-rthja` is the only thermal-resistance figure the CJ7912 datasheet
publishes - **there is no junction-to-case value**, so no case-to-junction conversion
is available for U8. Treat the measured case temperature as the raw datum, keep it
well clear of the 125 °C junction limit, and record it as the bench evidence that
`fact-cj7912-tj-rise-full-load` (verdict NEEDS BENCH) is waiting on.

Also record the measured case temperature and ambient for U6 and U7. Together with
the dissipation they give the **effective thetaJA of the actual board**, which is the
number the [thermal budget](./linear-regulator-layout.md#thermal-budget) needs and
which the datasheet does not supply for either part.

Finally: confirm thermal shutdown does not trigger during the 30-minute soak.

## 6. Ripple and noise

1. Set the oscilloscope to AC coupling with the 20 MHz bandwidth limit on.
2. Use a short ground spring or a coax probe - a long ground lead manufactures
   ripple that is not there.
3. Measure each output against GND at its rated load.
4. Target: under 5 mVp-p, with under 1 mVp-p as the design goal for the two-stage
   DC-DC plus LDO architecture.
5. Watch for oscillation or instability rather than just ripple amplitude.

<Note>
On the -12V rail, `fact-cj7912-esr-window-not-specified` records that the CJ7912
datasheet gives no output-capacitor ESR bounds, minimum capacitance, or stability
window at all. Stability of U8 with the C19/C25 output network therefore cannot be
predicted from the datasheet - this measurement is the only evidence that exists.
</Note>

## 7. Transient response

For each rail, drive a step with an electronic load and watch the output:

| Rail | Step        | Dip limit | Recovery |
| ---- | ----------- | --------- | -------- |
| +12V | 0 to 1.2A   | 250 mV    | 100 µs   |
| +5V  | 0 to 0.5A   | 250 mV    | 100 µs   |
| -12V | 0 to 0.8A   | 200 mV    | 100 µs   |

Check for ringing or overshoot on the recovery edge, not just the dip depth.

The +5V and -12V limits are carried over from the per-part procedures on the legacy
component pages. No separate figure was ever recorded for +12V, so that row applies
the same criterion as +5V; tighten it if the downstream load turns out to care.

## 8. Rail matching

For a bipolar analog supply, the two 12V rails should be symmetric:

- Measure +12V and -12V simultaneously at the same load.
- Compute the imbalance: the difference between the magnitudes should be under 0.5V.
- If it is not, adjust the upstream DC-DC feedback divider rather than the LDO.

## Recording results

Every measurement here feeds a fact carrying a **NEEDS BENCH** verdict:
`fact-cj7912-rail-headroom`, `fact-cj7912-tj-rise-full-load`,
`fact-cj7912-stability-project-network`, `fact-l7812cd2t-headroom`,
`fact-l7805abd2t-headroom`, `fact-lm2596-thermal`. Log the measured value, the load,
the input voltage and the ambient temperature for each, so the results can be folded
back into the component records rather than staying in a notebook.

## Related

- [Regulator Assembly, Soldering, and Inspection](./regulator-assembly-and-inspection.md)
- [Linear Regulator PCB Layout and Thermal Design](./linear-regulator-layout.md)
- [DC-DC Converter Stage Design (LM2596S-ADJ)](./dcdc-converter-design.md)
