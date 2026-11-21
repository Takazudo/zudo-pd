---
name: component-bzt52c11-c92321
description: Resolve exact Diodes Incorporated BZT52C11-7-F (LCSC C92321) zener limits and the board-a D8 Q1 gate-source clamp evidence. Use whenever BZT52C11, C92321, board-a D8, the Q1 20V-contract gate guard, its pins, package, substitution, or bring-up behavior is relevant.
---

# Exact component record

Run the central validator, read every local JSON record, and cite fact/source IDs with
conditions and locators. Preserve `SOURCE UNAVAILABLE` and `UNSOURCED`; never replace
exact-orderable evidence with memory or same-name vendor data (a BZT52C11 from any
other vendor is a different part, and BZT52C11-7-F is not BZT52C11-13-F packaging).
Keep this owner aligned with its `manifest.json`, `sources.json`, `facts.json`,
`coverage.json`, `routing.json`, `interactions.json`, and `pin-map.json`; its
inventory line, direct-routing fixture, and any applicable cross-component forward
test.

This record owns inventory line `line-c92321` (BZT52C11-7-F, Diodes Incorporated,
C92321, SOD-123_L2.8-W1.8-LS3.7-RD), placed fitted at board-a refdes D8: the
dec-e-q1-20v-gate-guard zener clamp across the Q1 gate-source (cathode/pin 1 on
VBUS_IN = Q1 source, anode/pin 2 on Net-(Q1-G)). `line_id` is set and
`candidate_id` is null.

Board P r3 D8/D13 and B20 D4/DZ1/DZ2/DZ3 used this part until the 2026-11-22 JST sourcing
adoption (#326); they are now JSCJ BZT52C11 C14941, owned by `component-jscj-bzt52-zeners`.
A JSCJ BZT52C11 is a different part from this Diodes record.

The exact BZT52C11 row of DS18004 Rev. 38-2 gives VZ 10.4-11.6 V at IZT 5 mA —
exactly the decision-locked window — with IR 0.1 uA guaranteed only at VR 8.0 V,
below the 9.62 V divider operating point at the 15 V contract. Sub-knee conduction
at the operating point (0.78 V of knee margin) and Q1 gate soft-start with the added
junction capacitance are the recorded NEEDS BENCH residuals; the
`gate-clamp-application` domain stays open until the Board A bring-up bench.

## Human component reference

Human projection of this bundle: [rec-bzt52c11-c92321](/docs/components/records/bzt52c11-c92321/).
See also the [component catalog](/docs/components/catalog/) and [cross-component
rules](/docs/components/integration/).
These pages are generated from this bundle's JSON files and add nothing to them.
