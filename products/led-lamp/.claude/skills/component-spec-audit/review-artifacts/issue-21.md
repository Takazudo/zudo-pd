# Issue 21 foreground self-review

Initial implementation commit: `25bda400bf990bb81ca8cc9efa1ce31e28c5a102`

Final source-lock correction commit: `297fb2ae7cb83f9a42a04d0dcb87660466e2c314`

## Scope

- Added five project-local component skills owning exactly seven inventory records.
- Touched only the five issue-owned skill directories.
- Included full independent artifacts for DNP subordinate records PESD24VS1UB,115 and 0603WAF5101T5E.

## Findings applied

1. Split the JST XH catalog lock into page-specific rating and B6B header sources, then rebound identity and dimension facts to physical PDF page index 4 / printed page 5.
2. Expanded the JST connectivity assertion and pin maps to state both Board P JOUT1 and Board L J2 pin-by-pin mappings instead of referring vaguely to corresponding nets.
3. Corrected local negative routing fixtures so same-name wrong-vendor queries use foreign LCSC identities and exercise the resolver's intended negative path.
4. Corrected the blocking source-lock review: installed verified official PDF hashes for UMW AO3401A and Nexperia PESD24VS1UB; marked the four ST sources without obtainable byte files `SOURCE UNAVAILABLE`; downgraded every dependent controller primary PASS to `UNVERIFIED`/`UNSOURCED`; and changed the controller netlist interaction from PASS to `UNSOURCED`.

## Verification

- `python3 .claude/skills/component-spec-audit/scripts/validate.py` - PASS, 32 lines, offline.
- `python3 -m unittest discover -s .claude/skills/component-spec-audit/scripts -p 'test_*.py'` - PASS, 17 tests.
- Every owned JSON file parsed with `python3 -m json.tool`.
- All five `SKILL.md` files passed `@takazudo/mdx-formatter`; all JSON passed Prettier.
- `git diff --check` and staged scope/privacy checks passed.
- JST eXH PDF SHA-256 verified as `1128a1bdb747cf3da211ed85e11c542f2d310652d8188a69b2dc0e8c40115ef8`.
- Rendered and visually inspected JST printed pages 1 and 5: ratings, six-circuit B6B-XH-A row, A/B dimensions, square-post size, pin-1 view, and `(LF)(SN)` label note were legible and consistent with retained facts.
- UMW AO3401A PDF SHA-256 verified as `fd1ac814d5a5f489f565fb8abf63812335c561fb11d24d4b4f752381070c8139`; rendered and inspected pages 1, 2, and 4 for exact UMW identity, G/S/D pinout, absolute ratings, electrical test conditions, and SOA/thermal curves.
- Nexperia PESD24VS1UB PDF SHA-256 verified as `846d25f725135288af86dcdb604e34568070c0e48156701a5efc66ae91658e06`; rendered and inspected pages 2, 4, and 7 for pin polarity, ordering/package identity, standoff/breakdown/leakage/capacitance/clamp conditions, pulse derating, and package outline.
- Explicit audit confirmed no `AVAILABLE` source in the five owned bundles retains an all-zero SHA-256.
- Temporary downloads and renders were removed from ignored `tmp/pdfs/` before commit.

## Remaining risks intentionally preserved

- TYPE-C-31-M-17 and High Diode SMAJ20A exact primary identity/electrical/mechanical facts remain `UNSOURCED` with matching open coverage.
- The exact 0603WAF5101T5E primary specification remains unavailable; its DNP project role and external-Rd interaction remain explicit.
- Board P's factory NVM dump, normalized project 40-byte image, full readback/reset/power-cycle proof, negotiated PDO behavior, and NVM endurance/write budget remain open or `NEEDS BENCH` rather than inferred.
- ST DS12499 Rev 8, UM2650 Rev 3, UM2398 Rev 1, and DB3902 Rev 2 retain exact official URLs/revisions/locators but remain `SOURCE UNAVAILABLE` because no byte file could be obtained through bounded CLI or the available browser runtime; their controller claims remain `UNSOURCED` until a real byte lock can be reviewed.
- The JST mating housing, contacts, wire, crimp process, and completed harness remain an unselected open domain.
- Application thermal, surge, CC signal-integrity, load-switch inrush, connector orientation, and as-built fit-state checks remain staged bench work.

Self-review: foreground complete; findings: applied
