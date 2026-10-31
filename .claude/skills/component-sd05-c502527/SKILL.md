---
name: component-sd05-c502527
description: Resolve exact evidence for the board-b TVS2 slot - the fitted Brightking SMAJ6.5A (LCSC C87267, decision-a pick), the removed MDD SD05 (C502527) with its +5V-rail 0% standoff-margin BLOCKER, and the SMF6.0A/SMAJ6.0A runner-up candidates. Use whenever SMAJ6.5A, C87267, SD05, C502527, board-b TVS2, or the +5V output overvoltage clamp is relevant.
---

# Exact component record

Run the central validator, read every local JSON record, and cite fact/source IDs with
conditions and locators. Preserve `SOURCE UNAVAILABLE` and `UNSOURCED`; never replace
exact-orderable evidence with memory or same-name vendor data (the MDD SD05 is not the
Semtech SD05, and each replacement candidate is its own exact orderable). Keep this
owner aligned with its `manifest.json`, `sources.json`, `facts.json`, `coverage.json`,
`routing.json`, `interactions.json`, and `pin-map.json`; its inventory line,
direct-routing fixture, and any applicable cross-component forward test.

Board B TVS2 is fitted with inventory line `line-c87267` (Brightking SMAJ6.5A, C87267,
D-FLAT_L4.3-W2.6-LS5.3-RD), owned here as `rec-cand-smaj6-5a-c87267` with `line_id` set.
Pin 1 is the cathode on the `+5V rail`; pin 2 is the anode on GND. The record keeps its
`cand-` id because locked decision evidence cites it. The MDD SD05 (C502527) is no longer
placed: `rec-sd05-c502527` is a candidate record (`line_id` null) retained for the
removal rationale below.

**BLOCKER:** the SD05 VRWM is 5.0 V, exactly the nominal +5 V rail — a deterministic
0 V / 0% standoff margin (`fact-sd05-plus5-margin`,
`fact-sd05-plus5-margin-percent`, `int-sd05-plus5-rail-blocker`). That margin
is why this bundle researched three TVS2 replacement candidates, registered in
`component-spec-audit/references/candidates.json`; wave-6 decision `dec-a-tvs2-replacement`
promoted SMAJ6.5A and kept the other two as runner-up candidate records:

- `cand-smf6-0a-c123790` — MDD SMF6.0A, SOD-123FL, VRWM 6 V, VC 10.3 V at 19.4 A
- `cand-smaj6-5a-c87267` — Brightking SMAJ6.5A (orderable SMAJ6.5A/TR13), SMA, VRWM 6.5 V, VC 11.2 V at 35.7 A
- `cand-smaj6-0a-c5353156` — FOSAN SMAJ6.0A, SMA, VRWM 6.0 V, VC 10.3 V at 38.8 A

Deterministic shortlist criteria: VRWM >= 6.0 V, low clamp at rated IPP,
hand-reworkable/JLCPCB-assemblable two-pad package, LCSC in stock at the dated
research retrieval. The wave-6 decision selected SMAJ6.5A; the selection is recorded in
`scripts/schgen/decisions.json`, not in this bundle.

## Human component reference

Human projection of this bundle: [rec-sd05-c502527](/docs/components/records/sd05-c502527/).
See also the [component catalog](/docs/components/catalog/) and [cross-component
rules](/docs/components/integration/).
These pages are generated from this bundle's JSON files and add nothing to them.
