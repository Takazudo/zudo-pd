# Documentation migration verification (2026-11-05 JST)

Scope: documentation only, baseline main `dda9ccc9bfdead8884c354c478280baca641cec1`.
This receipt records repository/site verification, not hardware qualification.

## Baseline

- Frozen install passed with pinned pnpm 11.5.2, Node 24.19.0 (satisfies >=22.18), Python 3.12.14.
  Initial host pnpm 11.25.0 install was repeated with exact 11.5.2; no dependency/lockfile changes.
- `pnpm circuit:check` PASS: strict audit 128 lines, 16 candidates, 41 bundles;
  6 integration cases, 9 negative routes; SCOPE five input specs, 443 placements, 17 exclusions,
  pin-asset check performed. No SCOPE/SKIP output was suppressed.
- Full tracked text/reference scan and site source/heading/hash inventories captured before edits.
  Baseline corpus: 203 pages = 132 generated + 71 authored; 24 top-level manufacturing Markdown files.

## Final checks

- `pnpm b4push`: initial complete sequence PASS, outer guard `verdict=PASS exit=0 secs=208`.
  It retained strict evidence checks, 258 circuit tests, 14 compatibility tests, Python audit/fixture/regression gates,
  four-generator schematic regeneration, geometry/baseline/decision/NVM checks, host types, build, publication/strict
  links/fragments, and two-preparation generated idempotency. The final full run after review corrections also passed: `verdict=PASS exit=0 secs=212`.
- Existing local doc-history generation was skipped by its normal local default; CI generates it. The artifact scanner
  reports docs-to-agent not scanned without an explicit agent-skill target; raw skill publication remains disabled.
  No strict validation, schematic gate or required browser check was skipped.
- Python suites included 53 validator tests, 5 schematic regression tests and 18 courtyard regressions; all passed.
- `pnpm test:model-viewer:browser`: PASS, 48 responsive/theme cases, dialogs/interactions/focus/idle/SPA/fallback/no-JS;
  outer guard `verdict=PASS exit=0 secs=33`.
- `pnpm exec zudo-circuit-doc check-browser`: PASS, 24 responsive/theme cases, paired references/media-only dialogs
  and runtime behavior; outer guard `verdict=PASS exit=0 secs=25`.
- Browser runs used installed Chromium (`CHROME_BIN=/usr/bin/chromium`) and both guards. The portable bundled
  `scripts/claude-reference/scripts/playwright-guard.sh` was used because the native `$HOME/.claude/scripts` link
  is absent; no runtime installation or repository policy change was made.
- Full route/fragment comparison: PASS, 203/203 baseline routes and 5,127 native heading IDs retained in source and
  built HTML; 183 baseline page hashes unchanged, including all 132 generated pages and all four archived categories.
  Original Board P narrative is a verbatim substring of the split historical page. The two newly scoped legacy KiCad
  guides retain their complete original technical bodies. Only documentation and `doc/zfb.config.ts` changed.
- Independent read-only hardware-semantics and documentation-compatibility reviewers completed. All six technical
  wording/scope findings and three compatibility/count findings were addressed; both rechecks reported no blocker.
  Reviewers inherited the session settings; no distinct model/effort override was requested or claimed.
- Initial PR head `044f588` CI found four broken new current-state fragment targets (eight source/built occurrences).
  Simplified current-state headings and restored the old release-readiness h2 fixed these; local native/built
  compatibility checks now pass. No gate or baseline was weakened. Final-head CI is recorded on PR 227.

## Focused desktop and mobile navigation

Final interaction verification **PASS** at 1440 × 1000 and 375 × 1000 using Chromium and both machine guards
(`verdict=PASS exit=0 secs=30`). At each width, the home route reaches Project; all three stream links work from
Project; correct architecture/category sidebars and parent active navigation appear; both Decisions/Research landing
children and all five Archive children open; six representative edited/historical deep links resolve; authored current
procedure recommendations exclude obsolete KiCad workflows. Screenshots were visually inspected at both widths.
The parent group remains active for Research/Archive child categories, as the supported configuration defines. Historical pages remain in category sidebars and
framework previous/next pagers; this migration does not claim full visual separation. The authored current-procedure
list links only current procedures; historical links in shared chrome remain historical access.

The focused scratch harness was corrected for canonical trailing slashes, asynchronous page transitions, parent
active state for dropdown children and the authored article versus automatic pager. Early harness assertion failures
were not reported as product failures or passes. No new test framework or repository test policy was introduced.

## Evidence preserved

Hardware/spec/generator/NVM/decisions/component/publication/package/generated bytes are outside this change.
Archived categories and explicitly historical procedures retain their source bodies/URLs. Existing edited-page
headings are compatibility constraints; Board P lineage preserves the full previous source body separately.
Frozen P15 package historical full-verifier/151-checksum success is retained, without a current-HEAD replay claim.
