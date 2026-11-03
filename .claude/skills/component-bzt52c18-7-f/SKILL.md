---
name: component-bzt52c18-7-f
description: Resolve exact Diodes Incorporated BZT52C18-7-F (LCSC C192739) zener limits and its Board P STUSB4500 local-clamp placements. Use whenever BZT52C18, C192739, Board P D9, D11, D12, the STUSB4500 local clamps, their pins, package, substitution, or bring-up behavior is relevant.
---

# Exact component record

Run the central validator, read every local JSON record, and cite fact/source IDs with
conditions and locators. Never replace exact-orderable evidence with memory or same-name
vendor data (a BZT52C18 from any other vendor is a different part).
Keep this owner aligned with its `manifest.json`, `sources.json`, `facts.json`,
`coverage.json`, `routing.json`, `interactions.json`, and `pin-map.json`; its
inventory line and direct-routing fixture.

This record owns inventory line `line-c192739` (BZT52C18-7-F, Diodes Incorporated, C192739,
SOD-123_L2.8-W1.8-LS3.7-RD), fitted on Board P at D9, D11, D12. Board P local clamps: D9 on VDD_LOC (U1.24 VDD; R29 1k + R30 470R from VBUS_P), D11 on VBEN_PIN (U1.16 behind the Q6 cascode), D12 on DISCH (U1.9; R13 4.7k from VBUS_OUT); cathode on the pin node, anode on GND.

The exact BZT52C18 row of DS18004 Rev. 38-2 gives VZ 16.8-19.1 V at IZT 5 mA and a
12.4-16.0 mV/C temperature coefficient. The pin bounds that use them are calculated,
not measured; the `local-clamp-application` domain stays open until the Board P bench.

## Human component reference

Human projection of this bundle: [rec-c192739](/docs/components/records/c192739/).
See also the [component catalog](/docs/components/catalog/) and [cross-component
rules](/docs/components/integration/).
These pages are generated from this bundle's JSON files and add nothing to them.
