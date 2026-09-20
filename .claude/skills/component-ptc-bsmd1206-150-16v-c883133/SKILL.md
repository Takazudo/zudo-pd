---
name: component-ptc-bsmd1206-150-16v-c883133
description: Resolve exact BHFUSE BSMD1206-150-16V (LCSC C883133) PPTC resettable-fuse limits and application constraints. Use whenever BSMD1206-150-16V, C883133, BHFUSE, or the board-b PTC3 -12V output overcurrent-protection function is relevant.
---

# Exact component record

Run the central validator, read every local JSON record, and cite fact/source IDs with
conditions and locators. Preserve `SOURCE UNAVAILABLE` and `UNSOURCED`; never replace
exact-orderable evidence with memory or same-name vendor data. Keep this owner aligned
with its `manifest.json`, `sources.json`, `facts.json`, `coverage.json`,
`routing.json`, `interactions.json`, and `pin-map.json`; its inventory line, direct-routing
fixture, real-pin lock, and any applicable cross-component forward test.

This record owns inventory line `line-c883133` (BSMD1206-150-16V, BHFUSE, C883133,
F1206), placed at board-b refdes PTC3. `line_id` is set and `candidate_id` is null.
PTC3 is the overcurrent-protection PPTC on the final -12V output, downstream of U8
(CJ7912 -12V LDO); its nominal continuous rail voltage magnitude is 12V and its rail
current budget is 0.8A.

BHFUSE's own BSMD1206 series datasheet structurally mirrors RUILON's SMD1210 series
document (same table shape: Ihold/Itrip/Vmax/Imax/Pd typ/time-to-trip/Rmin/R1max,
followed by a thermal derating chart and an environmental specifications table) but is
a wholly independent manufacturer document for a different part family; no data is
borrowed between the two. This bundle's PPTC-physics framing (hold/trip distinction,
ambient derating, one-hour hold wording, resistance-after-trip, cycling degradation)
follows the same structural pattern used in the read-only
`component-bhfuse-bsmd1206-075-30v` exemplar from the sibling zudo-led-lamp project
(a different exact part, BSMD1206-075-30V at 0.75A/30V, not this project's
BSMD1206-150-16V) — no facts or values were carried over from that exemplar.

Both Ihold (1.50A vs the 0.8A rail budget) and Vmax (16V vs the 12V nominal rail)
carry positive margins, though the voltage margin (4V, 33% headroom) is the tightest
of board-b's three PTCs and does not by itself account for switching-rail ripple or
transients.

## Human component reference

Human projection of this bundle: [rec-ptc-bsmd1206-150-16v-c883133](/docs/components/records/ptc-bsmd1206-150-16v-c883133/).
See also the [component catalog](/docs/components/catalog/) and [cross-component
rules](/docs/components/integration/).
These pages are generated from this bundle's JSON files and add nothing to them.

## Model placement review

The exact C883133 catalog model was freshly downloaded and compared byte-for-byte on2026-09-20. Use offset(0,0,0), rotation(0,0,0), scale1. Its existing centered node and mesh were correct and remain unchanged. Both opaque terminal ends register over the footprint lands. The STEP companion remains aligned with the WRL. The nominal mesh is an illustration, not a manufacturer maximum-tolerance package or physical-fit certificate. See the model-review source/facts and local JSON proof.
