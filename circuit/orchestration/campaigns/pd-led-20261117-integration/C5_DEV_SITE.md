# C5 private development site candidate

This isolated branch supplies a buildable six-category navigation and one
Components entry point for local review. It is not a public cutover or canonical
C3 adoption. The six header categories are Project, Shared P15, PD15, PD20,
LED Lamp and Components. Existing PD architecture, verification, research and
archive routes remain intact and reachable through the new landing pages and
internal links. `categoryMatch` values bind the new directories. The development
site name and every copied LED page describe the candidate status.

`c5_dev_site.py --write` creates 34 LED authored page copies from the accepted
C1 route map and a 35-line LED candidate table from the unchanged PD and LED
inventories, plus a unified comparison table with 129 PD and 35 LED rows.
`c5_dev_site.py` checks their exact bytes. It first runs
`c5_link_audit.py`, which binds both maps and all source authored pages and
requires the 97 current LED MD/MDX paths to match the C1 map. The new page
path set is also checked. The maintained LED source files and original Git
history remain under `products/led-lamp/`.

The copied text is explicitly historical. Its metadata description says it is
a development candidate so search results do not describe old decisions as
current. Authored-to-authored links use the C1 proposed paths. The 60 links to
generated LED routes and 12 references to LED assets continue to use the old
LED host. No LED raw resource, generated record, preview, asset or redirect is
copied into PD's publication selection. Two legacy citations that coincide with
PD denied-only alternate-source values link back to their original LED pages
in the candidate copy. The exact historical text and source URL remain at the
maintained source path; the PD publication canary allowance is not widened.

The single Components landing links to PD's unchanged generated catalog and
records, a product-scoped 164-line comparison, and a clearly unadopted LED
detail table. Its 17 shared line IDs are
not merged. Four text conflicts are explicit; the other 13 shared IDs still
need source, pin, CAD and use review. The 18 LED-only lines are proposals.
Historical line DNP flags do not assert assembled fit. PD's owner bundles,
inventory, candidates, CAD roots, selection, asset allowlist and matrix remain
unchanged.

The [private C3/C5 decision review](../../../../doc/src/content/docs/catalog/review.mdx)
joins the accepted identity, DNP and CAD reconciliation to the C1 route,
asset and redirect maps. Its machine-readable bundle is source-locked and
holds every unapproved route or asset from activation.

## Completion boundary

Before any public-site change, reviewers must settle component identity and
CAD/DNP mapping, regenerate one accepted active catalog, review current versus
historical LED statements, select every public asset and redirect, and verify
source-era history metadata on moved pages. In particular, the three legacy LED
routes that collide with PD cannot receive blanket redirects. The old LED
site stays operational until an approved cutover. A PR can trigger preview
deployment and main can trigger production deployment; neither is part of this
private branch candidate.
