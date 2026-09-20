---
name: component-l7805abd2t-c86206
description: Resolve exact L7805ABD2T (LCSC C86206) +5 V precision linear regulator limits and application constraints. Use whenever L7805ABD2T, C86206, board-b U7, its dropout/headroom margin, pins, package, thermal data, substitution, bring-up, or bench behavior is relevant.
---

# Exact component record

Run the central validator, read every local JSON record, and cite fact/source IDs with
conditions and locators. Preserve `SOURCE UNAVAILABLE` and `UNSOURCED`; never replace
exact-orderable evidence with memory or same-name vendor data. Keep this owner aligned
with its `manifest.json`, `sources.json`, `facts.json`, `coverage.json`,
`routing.json`, `interactions.json`, and `pin-map.json`; its inventory line or
candidate entry, direct-routing fixture, real-pin lock, and any applicable
cross-component forward test.

This record owns inventory line `line-c86206` (board-b U7, fitted). It is the
AB-series precision 5 V type (2 percent, -40 to 125 degC): do not borrow facts from
the L7805C/L7805AC series or from other-vendor 7805 parts - they have different
guarantee bands and temperature ranges. The `dropout-operating-point` domain is OPEN
on purpose: the +7.5 V rail sits exactly at the lower edge of the guaranteed input
band and dropout has no guaranteed maximum, so the margin is bench-confirmed alongside
the L7812 bench gate, not from this bundle.

## Human component reference

This retired regulator remains a local historical candidate record. Its current
replacement is documented under [LT1963A](/docs/components/records/c107286/) or
[LT3015](/docs/components/records/c666307/). See the
[current catalog](/docs/components/catalog/) and
[integration rules](/docs/components/integration/).
