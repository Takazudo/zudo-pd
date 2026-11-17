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

## Editorial integration and cutover choices

The 25 authored copies with no detected held record or asset dependency now
carry page-specific integrated-context notes. They point to current P15,
project status, release gates or repository setup as appropriate, while the
source-era body remains intact for traceability. In particular, the old
Cloudflare and scaffold installation instructions are labeled historical in
their navigation titles as well as in the page body. Historical Board P titles
also distinguish those pages from shared P15 and PD20 r3.
Every copied page links to its **exact original LED route**, so reviewers can
compare old and new text. The nine copies with held dependencies also state
their own generated-link and asset-link counts; the total remains 60 and 12.
`c5_editorial.py` is the source for these notes, and the build gate checks its
scope against the source-bound 25-page set.

The remaining cutover choices are concrete:

| Target | Safe current behavior | Later option and required evidence |
| --- | --- | --- |
| `/docs/architecture/`, `/docs/architecture/board-p/`, `/docs/research/` | Keep PD's existing routes and the LED old host; each private copy links to its exact original page. | Manage an LED-host redirect after approving the namespaced destinations. A blanket PD-host redirect would displace existing PD pages. |
| 60 links to historical generated LED records on seven pages | Keep exact old-host record links. | Approve source-bound C3 identity, document and active record selection per target, then replace each link and test fragments. |
| 12 references to 11 LED assets on two pages | Keep the old-host asset URLs and PD's current asset allowlist. | Review copyright, source, exact bytes and publication purpose per asset before copying selected files into namespaced PD paths. |
| 25 self-contained authored pages | Keep private with current-context notes and source-era body. | Editorially approve exact pages and currentness; a mechanically clean link graph alone does not authorize publication. |

The recommended immediate disposition is the safe current behavior in every
row. Any later cutover needs an entry-level decision and verification against
the final site head. This branch performs none of those public actions.

## Completion boundary

Before any public-site change, reviewers must settle component identity and
CAD/DNP mapping, regenerate one accepted active catalog, review current versus
historical LED statements, select every public asset and redirect, and verify
source-era history metadata on moved pages. In particular, the three legacy LED
routes that collide with PD cannot receive blanket redirects. The old LED
site stays operational until an approved cutover. A PR can trigger preview
deployment and main can trigger production deployment; neither is part of this
private branch candidate.
