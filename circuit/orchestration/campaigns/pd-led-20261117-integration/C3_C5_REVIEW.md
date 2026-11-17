# C3/C5 private decision dossier

`c3_c5_decisions.py --write` generates [the decision review page](../../../../doc/src/content/docs/catalog/review.mdx)
and [the machine-readable bundle](c3-c5-candidates.json). Run it without a flag
to require exact replay. `test_c3_c5_decisions.py` checks that a changed source
lock or a newly active generated C3 route fails closed. The site and public
asset/redirect outputs are not changed by this dossier.

The script binds the accepted C1 route, asset and redirect maps, the accepted
C3 reconciliation and route-contract result, and the C5 authored-link audit
by SHA-256. It verifies the seven C3a source locks and replays C3e's pinned
route check against the current 393-source corpus. C3e's original result
predates the C4 history-package lock update: only the `pnpm-lock.yaml` hash
differs; the script requires all route semantics and inspected provider/code
hashes to match and records the current lock hash. It also checks both current
`_redirects` source files, all 34 private authored destinations, the absence
of 35 unadopted generated record destinations and raw-resource routes, and the
absence of the namespaced held assets from PD's public root.

Mechanically supportable candidates are kept separate from owner decisions:

- Four conflicting identity text lines remain distinct. Thirteen same-text
  overlaps remain unverified, and 18 LED-only lines remain candidates.
- Seven LED placement DNP flags are transcribed from four historical line
  flags only. Source BOM/CPL, CAD and assembled fit remain unproved.
- All 21 same-relative CAD paths retain separate PD and LED roots; 20 have
  different bytes. No pad/pin/model equivalence follows from the one equal
  project file.
- Thirty-four authored C1 destinations exist in the private site, while 35
  record-route translations remain ungenerated, four generated section routes
  need semantic mapping and 24 raw-resource routes remain withheld. Three old
  authored routes conflict with PD paths.
- Eleven distinct assets used by copied pages (12 links), 49 manual assets,
  51 generated previews and all 12 LED aliases remain on the old-host side of
  the publication gate. Six aliases have proposed record targets and six point
  to raw resources; none is activated in PD's `_redirects`.

The [review page](../../../../doc/src/content/docs/catalog/review.mdx) gives
the exact rows and decision options. It is a private candidate, not approval
of shared identities, CAD, fit, publication, preview, production or physical
work. Retain the old LED host and restricted PD selection until reviewed
decisions and a separately verified cutover.
