---
title: Regulator Assembly, Soldering, and Inspection
sidebar_position: 103
description: Assembly-critical warnings, soldering profiles, inspection points and a pre-power checklist for the Board B linear regulator stage - including the negative-rail capacitor polarity trap.
---

<Note title="Historical board procedure">

This procedure describes the previous hardware and may name retired parts, nets,
pin assignments or export assumptions. Use the [current architecture](/docs/architecture/),
[prototype bring-up procedure](/docs/how-to/renewal-bring-up/) and
[current manufacturing workflow](/docs/how-to/jlcpcb-package/) for renewed boards.

</Note>

Assembly procedure for the Board B linear regulator stage: U6 (L7812CD2T-TR, C13456),
U7 (L7805ABD2T-TR, C86206) and U8 (CJ7912, C94173), plus their surrounding
capacitors.

Two of the traps below have destroyed hardware in other people's projects and will
destroy it here. Read them before touching a soldering iron.

## Trap 1: CJ7912 pin 1 is GND, not INPUT

<Danger title="Pin 1 = GND, not INPUT">
Negative regulators do **not** share the 78xx pin order. On the CJ7912 in TO-252-2L:

- **Pin 1 = GND (common)**
- **Pin 2 = INPUT (-13.5V), at the tab position**
- **Pin 3 = OUTPUT (-12V)**

This is recorded as `fact-cj7912-pinout`, primary-source confirmed against the
datasheet package figure and typical-application figure, and it matches the Board B
baseline (`U8.1` on `GND`, `U8.2` on `/DC-DC Conversion/-13.5V OUT`, `U8.3` on
`Net-(U8-OUT)`) with no remapping.

Assuming pin 1 is the input - the reflex if you have only ever wired 78xx positives -
gets you wrong connections and no output.
</Danger>

Prevention:

- Label the pins explicitly on the schematic: write "Pin 1 = GND", not just "Pin 1".
- Keep a reference-designator-to-pin table next to the symbol.
- Use a distinct schematic symbol for negative regulators so the eye does not
  auto-complete the 78xx layout.

Note that the tab is the pin 2 position, so the U8 tab is at **-13.5V**, not at
ground and not at the -12V output. See
[Linear Regulator PCB Layout and Thermal Design](./linear-regulator-layout.md#terminal-functions).

## Trap 2: negative-rail electrolytic polarity is reversed

<Danger title="On the -12V chain, the capacitor's positive terminal goes to GND">
For the capacitors on the negative rail, ground is the **more positive** node. So:

- **Positive terminal to GROUND (0V)**
- **Negative terminal to the negative voltage**

This is the opposite of every capacitor on the +12V and +5V chains.
</Danger>

```
Correct polarity for the negative rail:

C24 (input, 470µF 35V):
         ┌─────────┐
  GND ───┤+       -├─── -13.5V
         └─────────┘

C25 (output, 470µF 35V):
         ┌─────────┐
  GND ───┤+       -├─── -12V
         └─────────┘
```

Installing one of these backwards causes immediate capacitor failure, possibly a
burst electrolytic, regulator damage, and board contamination.

Prevention:

1. Put clear polarity markings on the silkscreen, and make the negative-rail parts
   visually distinct from the positive-rail parts.
2. Carry an assembly note in the BOM for C24 and C25.
3. Check polarity with a DMM before applying power.

The ceramics on the same nets - C16 (470 nF, input) and C19 (100 nF, output) - are
non-polarized, so they carry no orientation risk. The distances still matter: keep
the ceramic within 5 mm of the pin it decouples and the electrolytic within 10 mm.

## Trap 3: TVS3 orientation on the -12V rail

TVS3 (SMAJ15A, unidirectional) sits on the -12V output. Its orientation is locked by
`dec-tvs3-orientation-lock` in `scripts/schgen/decisions.json`:

- **Cathode to GND (0V)**
- **Anode to the -12V rail**

Fit it the other way round and the part is forward-biased at -12V - a dead short
through one diode drop across the rail.

<Warning title="Older project pages state the opposite">
The legacy CJ7912 component page tells you to wire the negative-rail TVS with the
cathode to the negative voltage and the anode to GND. That contradicts the locked
decision and is not carried forward here. The locked orientation above is the one to
build. The Board B net table agrees: it places `TVS3.1` on `GND` and `TVS3.2` on the
`-12V rail`, annotated in the spec module as the locked cathode-to-GND orientation.
On the physical part, `fact-smaj15a-polarity` records that the colour band marks the
cathode end.
</Warning>

## Soldering

### Reflow (recommended for production)

- Peak temperature: 260 °C maximum
- Time above 220 °C: 60-90 seconds
- Solder paste: SAC305 or a comparable lead-free alloy
- Stencil thickness: 0.125 mm (5 mil)

### Hand soldering

- Iron temperature: 350 °C maximum
- **U8 (CJ7912)**: solder pin 1 (GND) first as a mechanical reference, then pin 2
  (INPUT), then the tab.
- **U6, U7 (D2PAK)**: solder the two leads first, then the tab.
- Apply solder to the tab from the component side.
- Get real thermal contact between the tab and its pad - the tab is the entire heat
  path on these packages, and a partly-wetted tab turns a working thermal budget into
  a failing one.

## Inspection

After assembly, check:

1. **Electrolytic capacitor polarity** - critical on the negative rail; verify the
   positive terminal is at GND for C24 and C25.
2. **Pin solder joints** - smooth fillet, no bridges.
3. **Tab solder joint** - full coverage, no visible voids.
4. **Component alignment** - centred on the pads.
5. **No cold joints** - a good joint is shiny and smooth.
6. **Thermal via filling** - solder should wick into the vias.

## Pre-power checklist

- [ ] C24 polarity: positive terminal to GND, negative terminal to -13.5V
- [ ] C25 polarity: positive terminal to GND, negative terminal to -12V
- [ ] C20, C21 polarity: positive terminal to the positive rail (the normal case)
- [ ] U8 orientation: pin 1 to GND, pin 2 (tab) to -13.5V, pin 3 to the -12V output
- [ ] TVS3 orientation: cathode to GND, anode to -12V
- [ ] Visual inspection complete
- [ ] Continuity test: GND to U8 pin 1
- [ ] Resistance test: no short between -12V and GND
- [ ] Resistance test: no short between -13.5V and GND
- [ ] Resistance test: no short between +12V and GND, or +5V and GND

## Common mistakes

### Reversed electrolytic capacitors

**Problem**: installing a negative-rail electrolytic (C24 or C25) with the polarity
that would be correct on a positive rail.
**Consequence**: capacitor failure or rupture, regulator damage.
**Prevention**: large silkscreen warnings, DMM check before power-up, and the
checklist above.

### Confusing positive and negative regulator pinouts

**Problem**: assuming pin 1 is the INPUT because that is how the 78xx positives are
laid out.
**Consequence**: wrong connections, no output.
**Prevention**: see [Trap 1](#trap-1-cj7912-pin-1-is-gnd-not-input).

### Insufficient dropout voltage

**Problem**: feeding the regulator an input that is not far enough from the output -
for example -12V in for a -12V out.
**Consequence**: no regulation; the output simply follows the input.
**Prevention**: the magnitude of VIN must exceed the magnitude of VOUT by the
dropout voltage plus margin. `fact-cj7912-vi-guarantee-band` records that the CJ7912
output band is only guaranteed for an input between -14.5V and -27V, and the design
runs it at **-13.5V** - already outside the guaranteed band, which is why
`fact-cj7912-rail-headroom` carries a **NEEDS BENCH** verdict. Confirm the DC-DC
setpoint on the bench and treat a marginal -12V as a headroom problem before
suspecting the regulator.

### Shared copper pour between rails

**Problem**: letting the -12V copper touch the +12V copper.
**Consequence**: a direct short between rails, catastrophic.
**Prevention**: a separate pour per rail, at least 2 mm of clearance between pours at
different potentials, and a DRC run to prove it. The U8 tab island at -13.5V is the
easiest one to get wrong, because it looks like a ground pour and is not.

## Related

- [Linear Regulator PCB Layout and Thermal Design](./linear-regulator-layout.md)
- [Power Rail Bench Test Procedure](./power-rail-bench-test.md)
- [Board B - synth power conversion](../overview/board-b-synth-power.md)
