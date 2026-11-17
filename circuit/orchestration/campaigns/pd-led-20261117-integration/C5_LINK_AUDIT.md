# C5 authored-link preflight

Run `python3 circuit/orchestration/campaigns/pd-led-20261117-integration/c5_link_audit.py`
from the repository root to verify [the saved result](c5-link-audit.json) against
the current authored LED bytes and the accepted C1 route/asset maps. The script
is read-only by default; `--write` regenerates the JSON for a reviewed source
change. Its SHA-256 locks cover both maps and all 34 current authored MDX files.
It also requires the current 97 MD/MDX document paths to match the C1 map
exactly, so a newly added or removed page cannot silently escape review.

The audit finds 136 old `/docs/` links: 76 target other authored LED pages and
60 target generated LED component pages that require the single C3 catalog.
It also resolves 80 relative MDX links to authored pages and records three
local fragment links for later rendered-page checking. No relative link in
this source snapshot targets a generated or raw-resource page.
Twelve asset references occur on two authored pages; all have C1 publication
holds, though none shares a public path with an existing PD asset. Three old
route paths already exist in PD (`/docs/architecture/`,
`/docs/architecture/board-p/`, `/docs/research/`), so a blanket redirect on
the PD host would be wrong. Twenty-five authored pages have no detected held
route or asset dependency, but still require content, fragment, history and
publication review before any move.

The preflight now checks the **bytes** of all 11 distinct referenced LED assets
against the SHA-256 values in C1 `asset-map.tsv`. For the enclosure viewer it
also checks the five relative HTML dependencies and all 33 mesh paths named by
the manifest (38 distinct dependencies), including their source-map hashes.
A missing or modified asset fails before the private page copies are accepted.
This is a local source/closure check, not permission to copy assets into PD's
public tree.

Authored-page links are inventoried lexically, excluding fenced code. The
enclosure viewer's source HTML and manifest are parsed for dependencies. This
check does not validate page meaning, authorize a redirect or approve any new
public asset. Keep the old LED host working while cutover is reviewed.

## Decision options for the next serialized step

| Concern | Recommended safe direction | Decision still required |
| --- | --- | --- |
| Reused IDs and part names | Keep product-scoped LED identities distinct until owner evidence proves equivalence | Approve the four conflicting lines, remaining LED records, arithmetic references and exact catalog mapping |
| CAD and DNP | Keep LED CAD roots separate and translate historical line DNP only to declared placements | Review pads, pins, models, assembled fit and the SMAJ20A footprint before a shared package or preview |
| Authored pages | Review the 25 pages without detected held dependencies first; retain old-host links until destination routes exist | Approve page status/history text and all old route/fragment mappings |
| Generated pages and assets | Keep 39 generated snapshots, 24 raw-resource pages and all twelve referenced asset links out of automatic PD publication | Approve each active component selection and each asset/redirect under PD policy |

The source-bound C3 proposals and this audit are inputs to those decisions;
neither is canonical adoption or permission to deploy.
