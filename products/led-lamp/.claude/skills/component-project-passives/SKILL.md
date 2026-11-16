---
name: component-project-passives
description: Resolve the exact Samsung, Yageo, and UNI-ROYAL passive lines used by this project. Use whenever one of the listed MPNs/LCSC IDs, its capacitor or resistor limits, its Board P/Board L placement, bias/derating, reset, CCDB, CTRL, NTC, brightness ADC, or discharge network is relevant.
---

# Exact project passives

Run the central validator and read every local JSON record before using these records. Route an exact MPN or LCSC ID directly to its record; do not use a nearby value, generic 0603/0805 part, or the excluded `CL21A226MAQNNNE` / `C45783`.

## Evidence use

`sources.json` retains the manufacturer product pages/specifications and immutable hashes. `facts.json` separates primary ratings, project topology, and calculations. Cite exact fact and source IDs, with their units, locators, and conditions. Use `interactions.json` for the current generated-netlist assertions; these are audit observations, not authorization to change the design.

The Samsung page curves and Yageo simulation material are typical design-reference data, not guaranteed minima or ripple limits. Evaluate effective capacitance at the installed DC bias, AC ripple, temperature, aging, layout, and load with the exact curve/measurement conditions; do not claim a simulated result as a guarantee. Where an exact curve point, pulse energy, or installed condition is unavailable, preserve `UNSOURCED`/`NEEDS BENCH`.

## Passive limits

For MLCCs, apply nominal/tolerance, rated voltage, dielectric temperature range, termination/package, and the source-qualified DC-bias/ripple caveat. For UNI-ROYAL resistors, apply the decoded value/tolerance, package power, TCR, maximum continuous and overload voltage, temperature derating, and short-time-overload conditions. At ambient over 70 C, derate the family power curve; never exceed the lower of `sqrt(P*R)` and the family maximum continuous voltage.

Treat `0603WAF0000T5E` as a jumper, not a normal resistance: use its less-than-50-milliohm condition and 1 A rated / 2 A overload current conditions, and do not infer an RCWV or pulse-energy capability from the regular-resistor formula.

## Audit boundaries

The current generator connects C35 between Q1 gate and VBUS_IN, R12 as the VBEN-to-Q1-gate divider leg, R13 to DISCH, R14 to VBUS_VS_DISCH, fitted R19/R20 as CCDB bridges, and DNP R17/R18 as external-Rd options. It places R21 as the reset pull-down, Board L R20/R21/C21 on CTRL, Board L R26/RT1/C24 on NTC_SENSE, and R27 with R22/C22 in the absolute-brightness ADC path. These are fact-ID-linked observations only. Verify active-device requirements and reset polarity with their owning skills; do not infer them from passive values.

## Human component reference

Human projection of this bundle: [rec-c13585](/docs/components/records/c13585/), [rec-c14663](/docs/components/records/c14663/), [rec-c15849](/docs/components/records/c15849/), [rec-c25803](/docs/components/records/c25803/), [rec-c22807](/docs/components/records/c22807/), [rec-c23179](/docs/components/records/c23179/), [rec-c23162](/docs/components/records/c23162/), [rec-c21189](/docs/components/records/c21189/), [rec-c17414](/docs/components/records/c17414/), [rec-c4216](/docs/components/records/c4216/), [rec-c22775](/docs/components/records/c22775/). Those pages are generated from the JSON files here and add nothing to them — where the two disagree, this bundle is correct. See also the [component catalog](/docs/components/catalog/) and the [cross-component rules](/docs/components/integration/).
