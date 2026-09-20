---
title: Linear Regulator PCB Layout and Thermal Design
sidebar_position: 102
description: Footprint, pad, copper-pour, thermal-via and capacitor-placement guidance for the U6/U7/U8 linear regulators, with the thermal budget recomputed from the recorded datasheet facts.
---

<Note title="Historical board procedure">

This procedure describes the previous hardware and may name retired parts, nets,
pin assignments or export assumptions. Use the [current architecture](/docs/architecture/),
[prototype bring-up procedure](/docs/how-to/renewal-bring-up/) and
[current manufacturing workflow](/docs/how-to/jlcpcb-package/) for renewed boards.

</Note>

Layout input for the three final-stage linear regulators on **Board B**:

| Ref | Part            | LCSC   | Package    | Rail             |
| --- | --------------- | ------ | ---------- | ---------------- |
| U6  | L7812CD2T-TR    | C13456 | TO-263-2 (D2PAK) | +13.5V to +12V |
| U7  | L7805ABD2T-TR   | C86206 | TO-263-2 (D2PAK) | +7.5V to +5V   |
| U8  | CJ7912          | C94173 | TO-252-2L (DPAK)  | -13.5V to -12V |

<Note>
Board B PCB layout has not started. Everything here is design input for that work.
Reference designators and nets come from `scripts/schgen/board_b_spec.py`.
</Note>

## Terminal functions

Read this before drawing any pour. The tab is the single biggest layout trap on this
stage, and it is **not** the same net on all three parts.

| Ref | Package   | Tab is...                    | Other terminals                       | Recorded fact              |
| --- | --------- | ---------------------------- | ------------------------------------- | -------------------------- |
| U6  | TO-263-2  | **GND** (`U6.4`)             | pad 1 = INPUT, pad 3 = OUTPUT         | `fact-l7812cd2t-pinout`    |
| U7  | TO-263-2  | **GND** (`U7.2`)             | pad 1 = INPUT, pad 3 = OUTPUT         | `fact-l7805abd2t-pinout`   |
| U8  | TO-252-2L | **INPUT, at -13.5V** (`U8.2`)| pin 1 = GND, pin 3 = OUTPUT           | `fact-cj7912-pinout`       |

<Danger title="The D2PAK tab is GND, not the output">
DS0422 Figure 2 gives the D2PAK terminal functions as **tab = GND**, upper lead =
OUTPUT, middle lead position cut, lower lead = INPUT. Older project pages drew the
U6/U7 tab as the output and told you to build the output copper pour under it. That
is wrong: the large tab pour on U6 and U7 is a **ground** pour, and the Board B net
table confirms it (`U6.4` and `U7.2` are both on `GND`). Building the +12V or +5V
rail under the tab shorts that rail to ground.
</Danger>

<Danger title="The CJ7912 tab is the -13.5V input">
`fact-cj7912-pinout` records TO-252-2L as pin 1 = GND, pin 2 = IN **at the tab
position**, pin 3 = OUT. The Board B net table matches: `U8.2` sits on
`/DC-DC Conversion/-13.5V OUT`. So the U8 tab pour is a live -13.5V island - not
ground, and not the -12V output. It needs clearance to every neighbouring pour.
</Danger>

## TO-263-2 (D2PAK) footprint - U6 and U7

```
         Top View (PCB Pad Layout)

    ┌──────────────────────────────┐
    │                              │
    │    Large Copper Pour         │  ← TAB = GND
    │    (6cm² recommended)        │     thermal + electrical
    │                              │
    │         Thermal Vias         │
    │         (6-10 vias)          │
    │                              │
    └──────────────────────────────┘

         PAD1 ■        PAD3 ■
        (INPUT)       (OUTPUT)

    Pin spacing: 2.54mm (0.1")
    Pin pad: 1.5mm x 2.0mm
    Tab pad: 10mm x 10mm (minimum)
            15mm x 15mm (recommended)
```

Recommended pad dimensions:

| Pad             | Width     | Length    | Purpose                            |
| --------------- | --------- | --------- | ---------------------------------- |
| Pad 1 (INPUT)   | 1.5 mm    | 2.0 mm    | Input lead                         |
| Pad 3 (OUTPUT)  | 2.0 mm    | 3.0 mm    | Output lead, carries rail current  |
| Tab (GND)       | 10-15 mm  | 10-15 mm  | Thermal path and ground connection |

The project footprints already in the library are
`zudo-pd:TO-263-2_L10.0-W9.1-P5.08-LS15.2-TL` (U6) and
`zudo-pd:TO-263-2_L10.0-W9.2-P5.08-LS15.3-TL-CW` (U7).

## TO-252-2L (DPAK) footprint - U8

The CJ7912 datasheet package outline is recorded in `fact-cj7912-package-outline`:
body 6.5-6.7 mm x 6.0-6.2 mm, suggested pad layout tab 5.80 x 5.85 mm, lead span
4.57 mm. The datasheet marks its own pad layout **"for reference purposes only"**.
The project footprint is `zudo-pd:TO-252-3_L6.5-W5.8-P4.58-BL`.

Because the U8 tab carries -13.5V rather than ground, the tab pour is a floating
island. Keep at least 2 mm of clearance between it and the ground pour, and more from
any positive rail.

## Layout recommendations

1. **Component placement**

   - Orient each IC with the tab facing the interior of the PCB, away from the edge.
   - Maximize copper area under and around the tab.
   - Keep the input and output capacitors on the same side as the regulator.

2. **Copper pours**

   - U6/U7: build a large ground pour (6 cm² minimum for U6, 5 cm² for U7) under and
     around the tab, tied into the main ground plane.
   - U8: build the -13.5V island under the tab, isolated from ground.
   - Bottom layer: additional copper reached through thermal vias.
   - Inner layers on a 4-layer board: further ground and power planes.

3. **Thermal vias**

   - 6-10 vias of 0.3 mm diameter under each tab, on roughly a 2 mm grid.
   - Connect to the matching net on the bottom layer - ground for U6/U7, the -13.5V
     island for U8.
   - Do **not** use thermal-relief spokes on these vias; a direct connection is the
     whole point.

4. **Trace widths**

   - U6 input (+13.5V) and output (+12V): 1 mm minimum for 1.2A.
   - U7 input (+7.5V) and output (+5V): 0.5 mm minimum for 0.5A; 1 mm on the output
     side keeps the drop negligible.
   - U8 input (-13.5V) and output (-12V): 1 mm minimum for 0.8A.
   - Ground: maximum available pour area.
   - High-current paths: 2 mm, or a pour.

5. **Capacitor placement** - the actual Board B pairs:

   | Position   | Input capacitors                        | Output capacitors                        |
   | ---------- | --------------------------------------- | ---------------------------------------- |
   | U6 (+12V)  | C14, C20 (470 µF 35V) on `+13.5V OUT`   | C17 (100 nF), C21 (470 µF 35V) on `Net-(U6-OUT)` |
   | U7 (+5V)   | C15 (470 nF), C22 (470 µF 10V) on `+7.5V OUT` | C18 (100 nF), C23 (470 µF 10V) on `Net-(U7-OUT)` |
   | U8 (-12V)  | C16 (470 nF), C24 (470 µF 35V) on `-13.5V OUT` | C19 (100 nF), C25 (470 µF 35V) on `Net-(U8-OUT)` |

   Placement distances: the ceramic within 5 mm of the input pad or output pad it
   serves, the bulk electrolytic within 10 mm. Note the asymmetry in the current
   spec - the U6 input pair is two electrolytics with no input ceramic, unlike the
   470 nF that U7 and U8 each carry, so there is nothing to place close on that one
   position.

   `fact-l7812cd2t-cap-input` calls for 0.33 µF or larger directly across the input
   terminals with the shortest possible leads; `fact-l7812cd2t-cap-output` records
   that the L78 topology does **not** need an output capacitor for stability, so the
   output capacitors here are transient-response parts, not stability parts. For the
   CJ7912, `fact-cj7912-esr-window-not-specified` records that the Rev 2.0 datasheet
   states no output-capacitor ESR bounds, minimum capacitance, or stability window at
   all - so U8 output stability with this network is a bench question, not a
   datasheet question.

## Thermal via pattern

```
    Thermal via pattern under a TO-263-2 tab:

    ┌─────────────────────────┐
    │  ●    ●    ●    ●    ●  │
    │                         │
    │  ●    ●    ●    ●    ●  │  ← 0.3mm vias
    │                         │     2mm spacing
    │  ●    ●    ●    ●    ●  │
    │                         │
    └─────────────────────────┘

    Minimum: 6 vias
    Recommended: 10 vias
    Aggressive: 15 vias
```

```
    Thermal via pattern under the TO-252-2L tab:

    ┌─────────────────────────┐
    │                         │
    │  ●    ●    ●    ●    ●  │
    │                         │  ← 0.3mm vias
    │  ●    ●    ●    ●    ●  │     2.5mm spacing
    │                         │
    └─────────────────────────┘

    Minimum: 6 vias
    Recommended: 8 vias
    Aggressive: 10 vias
```

## Thermal budget

<Warning title="Two of the three positions fail the free-air budget">
The numbers below are recomputed from the recorded datasheet facts, not from the
optimistic 35-40 °C/W figures the legacy component pages carried. At the recorded
thermal resistances, **U6 and U8 exceed their 125 °C junction limit at 25 °C
ambient in free air.** Copper area is therefore not an optimization on this board -
it is the thing that makes the design work.
</Warning>

Dissipation is the series-pass product, headroom x rated current:

| Position | Headroom | Rated current | P_diss  |
| -------- | -------- | ------------- | ------- |
| U6       | 1.5V     | 1.2A          | 1.80 W  |
| U7       | 2.5V     | 0.5A          | 1.25 W  |
| U8       | 1.5V     | 0.8A          | 1.20 W  |

Applying the recorded junction-to-ambient figures at 25 °C ambient:

| Position | thetaJA (recorded)                  | Rise    | Tj at 25 °C | Tj limit                              | Verdict            |
| -------- | ----------------------------------- | ------- | ----------- | ------------------------------------- | ------------------ |
| U6       | 62.5 °C/W (`fact-l7812cd2t-rthja`)  | 112.5 °C| **137.5 °C**| 125 °C (`fact-l7812cd2t-tj-op-range`) | **over by 12.5 °C**|
| U7       | 62.5 °C/W (`fact-l7805abd2t-rthja`) | 78.1 °C | 103.1 °C    | 125 °C (`fact-l7805abd2t-tj-op-range`)| 21.9 °C margin     |
| U8       | 100 °C/W (`fact-cj7912-rthja`)      | 120 °C  | **145 °C**  | 125 °C (`fact-cj7912-tj-operating-range`) | **over by 20 °C** |

The U8 row is already recorded as a fact in its own right -
`fact-cj7912-tj-rise-full-load`, verdict **NEEDS BENCH**.

Two caveats that decide how much weight these numbers carry:

- The conditions on `fact-l7812cd2t-rthja` and `fact-l7805abd2t-rthja` state that
  DS0422 gives **no board, copper-area, or FR4 mounting condition** for the 62.5 °C/W
  figure. It is a free-air-style bound, not a prediction for a board with a real
  copper pour.
- `fact-cj7912-rthja` is the **only** thermal-resistance figure the CJ7912 datasheet
  publishes - there is no junction-to-case value and no mounting condition either.

So the honest reading is: the datasheet numbers do not clear the junction limit, and
the effective thermal resistance on the actual Board B copper has to be established
by the layout thermal budget and then confirmed by bench measurement.

**Design targets.** To land at Tj = 110 °C with 25 °C ambient, the layout has to
achieve:

| Position | Required effective thetaJA | Versus the recorded figure |
| -------- | -------------------------- | -------------------------- |
| U6       | 47.2 °C/W                  | must beat 62.5 °C/W        |
| U7       | 68.0 °C/W                  | already met by 62.5 °C/W   |
| U8       | 70.8 °C/W                  | must beat 100 °C/W         |

If the copper pour cannot get there, the alternatives are to lower the headroom
(retune the upstream DC-DC setpoint), de-rate the rail current, or add a heatsink.
That is a design decision for the Board B layout wave, and it should be recorded, not
assumed away.

## +5V rail distribution

The +5V rail in a modular synthesizer feeds two quite different kinds of load.

**Digital circuits** (microcontrollers, logic ICs):

- Switching loads with transient current demand
- Decoupling: a 100 nF ceramic at every IC
- Distribution: star topology from the main filter capacitor

**Analog circuits** (op-amps, comparators):

- Steady loads, noise-sensitive
- Decoupling: 100 nF ceramic plus 10 µF electrolytic per section
- Isolation: an RC filter (10 Ω plus 100 µF) if needed

### Low-noise operation

1. **Additional output filtering** - a 10 Ω resistor plus a 100 µF capacitor forms
   an extra pole near 160 Hz and knocks down high-frequency noise.
2. **Separate analog and digital grounds** - split the +5V distribution into analog
   and digital sections and join the grounds at a single star point, so digital
   switching noise does not couple into the analog side.
3. **Shielding** - route +5V traces away from high-frequency signals, use the ground
   plane as a shield, and keep sensitive analog circuitry away from digital sections.

## Related

- [DC-DC Converter Stage Design (LM2596S-ADJ)](./dcdc-converter-design.md) - the stage upstream
- [Regulator Assembly, Soldering, and Inspection](./regulator-assembly-and-inspection.md)
- [Power Rail Bench Test Procedure](./power-rail-bench-test.md)
- L7812CD2T, L7805ABD2T and CJ7912 are retired selections. Their owner evidence
  remains in the repository; use the [renewed power stage](../architecture/power-stage-options.md)
  for current regulator records.
