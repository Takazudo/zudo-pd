# Checks

What each project check establishes, and what it does not. Report a check's actual output, including its `SCOPE:`, `SKIP:` and `WARN:` lines; never summarize a skipped check as passed.

| Command | Establishes | Does not establish |
| --- | --- | --- |
| `pnpm circuit:check` | The evidence bundles, inventory, routing, integration rules and (when CAD is enabled) pin assets satisfy the v1 contract; the package's seeded self-test still detects known mutations | That any electrical claim is correct for the design, that a source was read correctly, or that declared placements match a schematic (see the `SCOPE:` line) |
| `pnpm circuit:generate` | Generated component pages and `circuit/generated/preflight.json` reflect the current evidence and selection | That the evidence is current with its remote sources |
| `pnpm check` | Validation passes, committed generated output matches a dry-run generation (drift and ownership conflicts), selected models and footprint previews match their inputs, the doc site type-checks | Anything about the built HTML |
| `pnpm build` then `pnpm check:site` | The built site references only files that exist, publishes nothing outside the selection and the assets allowlist, and has no broken links or anchors | Visual rendering or island behavior in a browser |
| `pnpm exec zudo-circuit-doc check-browser` | Islands hydrate and the built pages behave in system Chrome, for whichever representative pages it resolved | Anything about a representative it never resolved (reported `SKIP`), and anything at all when it exits `4` |
| `pnpm exec zudo-circuit-doc validate --online` | Retained non-volatile source hashes still match the bytes the URLs serve today | That the documents support the recorded claims; it never alters retained evidence |
| `pnpm previews:generate`, `pnpm exec zudo-circuit-doc footprints check` | Footprint SVG previews are rendered from, and match, the selected footprints | Dimensional correctness or pin correspondence; a preview is a rendering |
| `pnpm circuit:doctor` | Which required and optional tools are present | That any check passes |

### `check-browser` representative pages

`check-browser` resolves which pages to exercise in this order:

1. `--representatives <json>` on the command line.
2. `browserSmoke.representatives` in `circuit.config.ts`, used exactly as configured — even an explicit empty list.
3. Otherwise, up to 3 representatives **derived** from the preflight report: published record slugs, sorted, filtered to the ones whose generated page has a decodable component-references section (a reviewed PDF, a footprint and a WRL model), and, once the site is built, whose built output carries the matching marker and assets. A derived run prints `INFO: using derived representatives: ...`.

A declared-zero project (nothing published) is a `SKIP`, not a failure. If records are published but derivation finds none that qualifies, the command exits `4` rather than silently checking nothing — set `browserSmoke.representatives` in `circuit.config.ts` to name pages explicitly.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Pass |
| `1` | Check failed |
| `2` | Usage or configuration error |
| `4` | Not run: an optional tool (Docker, Chrome) is missing, or (`check-browser` only) records are published but none qualifies for a default representative and none was configured |

## What no check establishes

`COVERED` coverage, a clean validation and a green build are not hardware sign-off. Physical fit, assembled state, programmed state and bench behavior are established only by recorded observations (Workflow F in [WORKFLOW.md](../WORKFLOW.md)).
