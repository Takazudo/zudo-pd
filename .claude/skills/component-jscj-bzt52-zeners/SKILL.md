---
name: component-jscj-bzt52-zeners
description: Resolve exact JSCJ BZT52C11 (LCSC C14941) and BZT52C18 (LCSC C43490) zener limits and their Board P r3 / B20 placements. Use whenever JSCJ BZT52C11, BZT52C18, C14941, C43490, Board P D8, D9, D11, D12, D13, B20 D4, DZ1, DZ2, DZ3, their thermal screen, footprint or substitution is relevant.
---

# Exact component records

Run the central validator, read every local JSON record, and cite fact/source IDs with
conditions and locators. A BZT52C11 or BZT52C18 from another vendor is a different part:
Diodes BZT52C11-7-F C92321 (Board A D8) and BZT52C18-7-F C192739 (P15 D9) keep their own owners.

This bundle owns inventory lines `line-c14941` (JSCJ BZT52C11, C14941) and `line-c43490`
(JSCJ BZT52C18, C43490) on the manufacturer-neutral land `SOD-123_Pad0.90x0.95mm_P3.15mm`. They were adopted
on 2026-11-22 JST by the reviewed sourcing substitution (#326): C14941 at Board P r3 D8, D13 and
B20 D4, DZ1, DZ2, DZ3; C43490 at Board P r3 D9, D11, D12 only.

The source is the JSCJ BZT52C2V4-BZT52C43 SOD-123 document Rev. 2.1. Its 500 mW / 250 C/W
rating is a 1 in2 / 2 oz FR-4 test-board condition. The per-ref DC thermal screen is a paper bound,
not a measured temperature; the `clamp-application` domain stays open until the bench.

## Human component reference

Human projection of this bundle: [rec-c14941](/docs/components/records/c14941/) and
[rec-c43490](/docs/components/records/c43490/).
See also the [component catalog](/docs/components/catalog/) and [cross-component
rules](/docs/components/integration/).
These pages are generated from this bundle's JSON files and add nothing to them.
