---
name: component-jst-b6b-xh-a
description: Audit the exact JST B6B-XH-A(LF)(SN) C144397 six-circuit XH header at Board A J4 and its historical A-to-B cable contract. Use for pin order, orientation, footprint, ratings, current-derating math, housing, contacts, wire, harness, bring-up, or substitution.
---

# JST B6B-XH-A(LF)(SN) bundle

Run the central offline validator, then read all seven local JSON artifacts. This bundle
owns the single standalone record `rec-jst-b6b-xh-a` for inventory line `line-c144397`
(currently board-a `J4`). The former board-b `J5` placement belongs to the historical
#90 A-to-B cable contract; current Board B uses a different stacking header for
Board P. Keep the board header distinct from the mating housing, crimp contact, wire,
and completed cable assembly. No complete harness has been selected; do not invent one
from the XH family catalog.

The retained official JST XH catalog supports the identity, pitch, current, voltage,
temperature and dimension facts. The source URLs, retrieval metadata and PDF hashes
remain in `sources.json`. Project signal assignments come from
`doc/src/content/docs/inbox/board-split-decision.md`, Decision set (b): pins 1-2 +15V,
3 ATT, 4 PDOK and 5-6 GND. That historical cable contract used the same assignment
at Board A J4 and the former Board B JST J5.

The historical current calculation applies a project-assumed 80% continuous derating
to two 3 A contacts: 4.8 A derated capacity against a 3.0 A PD-contract cap, or 1.6x
derated / 2.0x nameplate arithmetic margin. This does not qualify an actual harness
or the renewed stacking connector. Preserve the existing fact IDs and numeric values;
keep their historical scope and bench conditions explicit.

Use the official JST XH catalog for the 2.50 mm six-circuit top-entry header identity,
dimensions, and series-level ratings. Use `pin-map.json` for Board A J4 and the
historical JST cable assignment, not to identify current Board B J5. Before using
that cable interface, verify both header pin-1 orientations, end-to-end mapping,
duplicate power/ground conductors, contact retention, wire current suitability and
absence of swaps or shorts. A polarized housing does not prove correct wiring.

## Human component reference

The [generated component record](/docs/components/records/jst-b6b-xh-a/) projects
this bundle. Edit the evidence and regenerate rather than hand-editing that page.
See the [historical board-split decision](/docs/inbox/board-split-decision/) for the
old cable contract and the [current board interface](/docs/architecture/board-contract/)
for the renewed Board P / Board B assembly.
