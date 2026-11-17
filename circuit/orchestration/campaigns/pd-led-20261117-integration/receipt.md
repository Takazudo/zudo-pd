# PD/LED controlled integration checkpoint

This isolated branch combines the accepted C1 baseline with the C2 import and
reviewed C3/C4 development lineage. It is **not** the C3 canonical evidence
adoption, the C5 unified public site, or permission to merge or publish.

## Exact inputs and ownership

- Destination main at preflight: `ea0a4a80e6d7268bb3df1e80c57408d672909244`.
- C1 reviewed baseline: `3759009c2db574bc2835139e0e951b1eb4d6445f`.
- C4k reviewed workspace/history candidate: `c1f5275eeeb7539df1046b6b3d4ef6cb8ca5568b`.
- The normal two-parent merge `e0be0bee` adds exactly eleven C1 campaign files;
  every staged blob matched the C1 head before commit. The C2–C4 candidate
  files and their source history came from the unchanged C4k parent.
- PD20 PR #307 remains open at
  `9312dc627df2de22d1ac44a3a05fbcb207665b3e` and is not in this branch.

The C1 `baseline.json` and TSV maps describe the pinned pre-import source
revisions. They are retained as historical migration inputs, not regenerated
from the later candidate head. The imported LED files remain under
`products/led-lamp/`, and the original LED repository remains available.

The C1 merge exposed a document-history edge case: `git log -m` included that
merge as an LED edit relative to its C1 parent even though the imported LED
file was unchanged from the first parent. The local history package patch now
filters such post-import, first-parent-identical merges from both Compare
entries and the rendered latest-update metadata. A focused regression binds
this exact merge and LED file. A second regression covers a same-named PD/LED
path where `--follow` misses the import commit despite an imported blob; the
patch restores that boundary without admitting unrelated PD history. The lock
changed only by the patch hash.

## Gates before C3 and C5 adoption

The accepted C3 translation work is source-bound feasibility evidence. It has
not changed the canonical PD inventory or owner bundles. C3a identifies four
overlapping line identities that cannot be collapsed by matching IDs alone:
STUSB4500QTR maker text, AO3401A maker identity, SMAJ20A's different footprint,
and PESD24VS1UB's order suffix and fitted conditions. The remaining LED lines,
placement-level DNP mapping, CAD pad/pin/model identity and calculated-rule
expressions need an independently reviewed active-corpus decision. Preserve
both original evidence sets until that decision; do not repin frozen receipts.

C1 inventories 97 old LED routes: 34 authored routes are provisional, 39
generated component routes must come from a single future catalog, and 24
raw-resource routes are held from automatic publication. Its asset map records
27 overlapping public paths, including 15 different-byte collisions. C5 needs
an exact route/fragment/redirect and per-asset publication selection before
moving authored pages into the unified public site. Keep PD's restricted
selection, `agentResources: false`, and the old LED site operational in the
meantime. A six-category header or copied LED pages alone would not satisfy C5.

The next serialized step is an owner-reviewed C3 identity/CAD/DNP and
publication disposition, followed by application of the source-locked ID map
to a single active corpus. C5 can then map the approved LED pages and assets,
verify old links and browser behavior, and run required CI on the exact final
integration head. Any PR may trigger the configured preview deployment; an
authorized main update may trigger production deployment. Neither is initiated
by this branch checkpoint. Hardware, private-source, #307 and physical holds
remain unchanged.
