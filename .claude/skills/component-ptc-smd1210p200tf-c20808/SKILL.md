---
name: component-ptc-smd1210p200tf-c20808
description: Resolve exact RUILON SMD1210-family PPTC evidence for the board-b PTC1 slot - the fitted SMD1210P150TF/16 (LCSC C7529589, 16V decision-g pick) and the removed SMD1210P200TF (C20808, 6V Vmax BLOCKER). Use whenever SMD1210P150TF/16, C7529589, SMD1210P200TF, C20808, RUILON, or the board-b PTC1 +12V output overcurrent-protection function is relevant.
---

# Exact component record

Run the central validator, read every local JSON record, and cite fact/source IDs with
conditions and locators. Preserve `SOURCE UNAVAILABLE` and `UNSOURCED`; never replace
exact-orderable evidence with memory or same-name vendor data. Keep this owner aligned
with its `manifest.json`, `sources.json`, `facts.json`, `coverage.json`,
`routing.json`, `interactions.json`, and `pin-map.json`; its inventory line, direct-routing
fixture, real-pin lock, and any applicable cross-component forward test.

This record owns inventory line `line-c20808` (SMD1210P200TF, RUILON, C20808, F1210),
placed at board-b refdes PTC1. `line_id` is set and `candidate_id` is null. PTC1 is the
overcurrent-protection PPTC on the final +12V output, downstream of U6 (L7812CD2T +12V
LDO); its nominal continuous rail voltage is +12V and its rail current budget is 1.2A.

**Known project data gap, now resolved from the RUILON primary datasheet (SMD1210
Series, `SP-PTC-007`, Version A4/2026-03-11):** the manufacturer's own Performance
Specification table lists the exact orderable `SMD1210P200TF` (no voltage suffix) at
`Vmax = 6 VDC`. LCSC's own C20808 listing independently confirms the same rating
("Polymeric PTC Resettable Fuse 6V 2A Surface Mount 1210"). **This is a deterministic
spec violation, not merely a data gap**: the part's 6V maximum voltage rating is less
than the +12V nominal rail it protects. See `fact-ptc1-vmax-margin`
(`BLOCKER - deterministic spec violation`, margin = -6V) and `int-ptc1-12v-rail-protection`.
The RUILON SMD1210 family does offer higher-voltage-suffixed variants of adjacent
current ratings (e.g. `SMD1210P150TF/16`, `SMD1210P110TF/16`) but the exact orderable
placed here, `SMD1210P200TF`, has no such suffix in the manufacturer's table and is
rated 6V only. Design remediation (part substitution) is out of this bundle's scope;
this record's job is to make the violation explicit and evidenced.

## Human component reference

Human projection of this bundle: [rec-ptc-smd1210p200tf-c20808](/docs/components/records/ptc-smd1210p200tf-c20808/).
See also the [component catalog](/docs/components/catalog/) and [cross-component
rules](/docs/components/integration/).
These pages are generated from this bundle's JSON files and add nothing to them.

## Model placement review

The exact C7529589 catalog model was freshly downloaded and compared byte-for-byte on2026-09-20. Use offset(0,0,0), rotation(0,0,0), scale1. The former footprint node displaced the visible body far from its pads; only that node was corrected. Both opaque terminal ends register over the footprint lands. The STEP companion remains aligned with the WRL. The nominal mesh is an illustration, not a manufacturer maximum-tolerance package or physical-fit certificate. See the model-review source/facts and local JSON proof.
