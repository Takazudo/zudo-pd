---
name: component-bzt52c20-7-f
description: Resolve exact Diodes Incorporated BZT52C20-7-F (LCSC C260890) zener limits and its Board P STUSB4500 local-clamp placements. Use whenever BZT52C20, C260890, Board P D10, the STUSB4500 local clamps, their pins, package, substitution, or bring-up behavior is relevant.
---

# Exact component record

Run the central validator, read every local JSON record, and cite fact/source IDs with
conditions and locators. Never replace exact-orderable evidence with memory or same-name
vendor data (a BZT52C20 from any other vendor is a different part).
Keep this owner aligned with its `manifest.json`, `sources.json`, `facts.json`,
`coverage.json`, `routing.json`, `interactions.json`, and `pin-map.json`; its
inventory line and direct-routing fixture.

This record owns inventory line `line-c260890` (BZT52C20-7-F, Diodes Incorporated, C260890,
SOD-123_L2.8-W1.8-LS3.7-RD), fitted on Board P at D10. Board P local clamp D10 on VBUS_VS_DISCH (U1.18; R14 + R28 2 x 1k from VBUS_P); cathode on the pin node, anode on GND.

The exact BZT52C20 row of DS18004 Rev. 38-2 gives VZ 18.8-21.2 V at IZT 5 mA and a
14.4-18.0 mV/C temperature coefficient. The pin bounds that use them are calculated,
not measured; the `local-clamp-application` domain stays open until the Board P bench.

## Human component reference

Human projection of this bundle: [rec-c260890](/docs/components/records/c260890/).
See also the [component catalog](/docs/components/catalog/) and [cross-component
rules](/docs/components/integration/).
These pages are generated from this bundle's JSON files and add nothing to them.
