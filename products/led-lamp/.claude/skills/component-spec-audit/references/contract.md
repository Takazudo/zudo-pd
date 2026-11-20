# Frozen component-spec contract (version 1)

The central inventory is generated-spec identity truth; an owner record is evidence truth. One inventory line represents one nonblank LCSC/orderable identity and may have many placements. Bare-copper pogo and test pads remain explicit exclusions.

Every standalone or subordinate record uses the same files and schema. Subordinates receive their own record, source, fact, interaction, routing, coverage, and pin-map IDs; parentage changes organization, never rigor.

A subordinate's `parent_record_id` resolves to a standalone record in the same bundle. Each record lists exactly all and only its assigned source, fact, and interaction IDs, has direct positive/negative routing plus coverage and pin-map data, and owns no unexplained orphan data. Each open domain is a named entry matched one-for-one by `OPEN` coverage with an explicit reason.

Every coverage entry also carries a machine-readable `blocking_fact_ids` array. For an `OPEN` entry it names the exact same-record facts whose non-PASS verdicts keep the domain open; each member must carry a verdict of `UNSOURCED` or `NEEDS BENCH`, or cite a `SOURCE UNAVAILABLE` source. The converse is enforced too: whenever any fact listed in `fact_ids` meets that same blocking test, `blocking_fact_ids` must name at least one of them. It may be empty only when no listed fact addresses the domain in that sense — a `NOT APPLICABLE` fact never blocks, so an `OPEN` entry whose only evidence is `NOT APPLICABLE` correctly keeps the array empty. Independently, a reason whose text claims evidence is unavailable, lower-authority, or `UNSOURCED` must cite those facts through `blocking_fact_ids` rather than leave the claim unverifiable.

## Evidence retention

A source lock records document title/number, revision/date, primary and optional alternate authoritative URLs, retrieval date, authority class, SHA-256, physical PDF page index, printed label, and exact section/table/figure/row locator. Retain a normalized, minimal evidence extract beside the locator so a reviewer can audit a critical claim without redistributing a PDF. An inaccessible source is `SOURCE UNAVAILABLE`; its SHA-256 is always the all-zero sentinel. Its extract may remain for audit history but cannot promote a new claim or invite a memory-based fallback.

Fact classes are `ABSOLUTE_MAXIMUM`, `RECOMMENDED_OPERATION`, `GUARANTEED_ELECTRICAL`, `TYPICAL_CURVE`, `TRANSIENT`, `PROTECTION_STANDOFF`, `PROTECTION_BREAKDOWN`, `PROTECTION_CLAMP`, `THERMAL_SOA`, and `PROJECT_STATE`. Provenance is `PRIMARY-SPEC`, narrowly scoped `DISTRIBUTOR-IDENTITY`, `REFERENCE-DESIGN`, `CALCULATED`, `PROJECT-CHOICE`, `BENCH-OBSERVED`, or `UNVERIFIED`. Every quantitative fact carries an explicit unit and conditions; textual facts use unit `NONE`. Calculated facts list raw fact IDs and an evaluable arithmetic expression. Cycles are invalid.

Only these verdicts are valid: `PASS - primary-source confirmed`, `CONFIRMED - distributor identity only`, `BLOCKER - deterministic spec violation`, `NEEDS BENCH`, `UNSOURCED`, and `NOT APPLICABLE`. Distributor identity confirmation is valid only for an `AVAILABLE` `DISTRIBUTOR_IDENTITY` source and a `PROJECT_STATE` identity fact; it cannot support electrical/thermal limits, calculations, primary PASS, or deterministic BLOCKER.

`PRIMARY-SPEC` may receive a PASS only from an `AVAILABLE` `MANUFACTURER_PRIMARY` source. A calculated PASS is trusted only when every raw leaf in its dependency closure is such a primary-source PASS. Its expression names exactly the transformed fact IDs in `depends_on`; undeclared, unused, self, missing, or cyclic dependencies fail.

Unknown identity, source, open harness/mechanical domains, unavailable URLs, and unexplained coverage gaps stay explicit. Generic-family, distributor, or same-name cross-vendor data never silently stands in for the exact orderable.
