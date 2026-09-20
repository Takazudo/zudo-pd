---
name: component-ptc-msmd110-33v-c70119
description: Resolve exact TECHFUSE mSMD110-33V (LCSC C70119) PPTC resettable-fuse limits and application constraints. Use whenever mSMD110-33V, C70119, TECHFUSE, Sea&Land Electronic Corp, or the board-b PTC2 +5V output overcurrent-protection function is relevant.
---

# Exact component record

Run the central validator, read every local JSON record, and cite fact/source IDs with
conditions and locators. Preserve `SOURCE UNAVAILABLE` and `UNSOURCED`; never replace
exact-orderable evidence with memory or same-name vendor data. Keep this owner aligned
with its `manifest.json`, `sources.json`, `facts.json`, `coverage.json`,
`routing.json`, `interactions.json`, and `pin-map.json`; its inventory line, direct-routing
fixture, real-pin lock, and any applicable cross-component forward test.

This record owns inventory line `line-c70119` (mSMD110-33V, TECHFUSE, C70119, F1812),
placed at board-b refdes PTC2. `line_id` is set and `candidate_id` is null. PTC2 is the
overcurrent-protection PPTC on the final +5V output, downstream of U7 (L7805ABD2T +5V
LDO); its nominal continuous rail voltage is +5V and its rail current budget is 0.5A.

The primary datasheet (Sea&Land Electronic Corp, brand Techfuse, document QR0429, REV
DATE 2021-4-30) is a single-page specification sheet: it carries the full electrical
performance table (Vmax, Imax, Ihold, Itrip, Pd typ, time-to-trip, Rimin, R1max) but,
unlike the RUILON and BHFUSE datasheets for PTC1/PTC3, has no ambient-temperature
derating chart or environmental/aging test table. That gap is recorded as an OPEN
coverage domain rather than assumed away.

Both Ihold (1.10A vs the 0.5A rail budget) and Vmax (33.0V vs the 5V nominal rail) carry
large, healthy positive margins here — unlike PTC1's board-b sibling, this part passes
its rail-application check outright.

## Human component reference

Human projection of this bundle: [rec-ptc-msmd110-33v-c70119](/docs/components/records/ptc-msmd110-33v-c70119/).
See also the [component catalog](/docs/components/catalog/) and [cross-component
rules](/docs/components/integration/).
These pages are generated from this bundle's JSON files and add nothing to them.

## Model placement review

The exact C70119 catalog model was freshly downloaded and compared byte-for-byte on2026-09-20. Use offset(0,0,0), rotation(0,0,0), scale1. The former footprint node displaced the visible body far from its pads; only that node was corrected. Both opaque terminal ends register over the footprint lands. The STEP companion remains aligned with the WRL. The nominal mesh is an illustration, not a manufacturer maximum-tolerance package or physical-fit certificate. See the model-review source/facts and local JSON proof.
