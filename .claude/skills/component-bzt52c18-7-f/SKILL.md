---
name: component-bzt52c18-7-f
description: Resolve exact Diodes Incorporated BZT52C18-7-F (LCSC C192739) zener limits, its P15 D9 placement and its former Board P r3 STUSB4500 local-clamp role. Use whenever Diodes BZT52C18-7-F, C192739, P15 D9, or the history of Board P D9, D11, D12 is relevant.
---

# Exact component record

Run the central validator, read every local JSON record, and cite fact/source IDs with
conditions and locators. Never replace exact-orderable evidence with memory or same-name
vendor data (a BZT52C18 from any other vendor is a different part).
Keep this owner aligned with its `manifest.json`, `sources.json`, `facts.json`,
`coverage.json`, `routing.json`, `interactions.json`, and `pin-map.json`; its
inventory line and direct-routing fixture.

This record owns inventory line `line-c192739` (BZT52C18-7-F, Diodes Incorporated, C192739,
SOD-123_L2.8-W1.8-LS3.7-RD), fitted at P15 D9. Board P r3 D9, D11 and D12 used this part until the
2026-11-22 JST sourcing adoption (#326); they are now JSCJ BZT52C18 C43490, owned by
`component-jscj-bzt52-zeners`. Their former role (D9 on VDD_LOC, D11 on VBEN_PIN, D12 on DISCH) is
kept in `fact-c192739-board-p-role` as history.

The exact BZT52C18 row of DS18004 Rev. 38-2 gives VZ 16.8-19.1 V at IZT 5 mA and a
12.4-16.0 mV/C temperature coefficient. The pin bounds that use them are calculated,
not measured; the `local-clamp-application` domain stays open until a bench measurement.

## Human component reference

Human projection of this bundle: [rec-c192739](/docs/components/records/c192739/).
See also the [component catalog](/docs/components/catalog/) and [cross-component
rules](/docs/components/integration/).
These pages are generated from this bundle's JSON files and add nothing to them.
