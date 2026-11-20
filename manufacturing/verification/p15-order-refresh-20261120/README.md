# P15 order refresh, 2026-11-20

Desk evidence for the [P15 order handoff](../../p15-order-handoff.md), campaign
[#318](https://github.com/Takazudo/zudo-pd/issues/318) / [#319](https://github.com/Takazudo/zudo-pd/issues/319).
Nothing was ordered, uploaded, quoted, programmed or energized.

| File | What it records |
| --- | --- |
| `upload-file-hashes.txt`, `sha256sum-c.txt` | The four `board-p15/` files and the NVM image match; the fixed package checks 150 of 151 (the local-only assembled STEP is absent, so full historical replay is NOT RUN) |
| `verify-shared-reference.txt`, `adoption-ancestry-github-compare.json` | All 7 shared-reference artifacts match; the adoption-ancestry FAIL is a shallow-clone artifact, confirmed through the GitHub compare API |
| `verify-p15-subset.json`, `scripts/verify-p15-subset.py` | Board-p15-only, non-replay subset of the `verify-jlcpcb.py` checks: PASS |
| `placement-checklist.md`, `polarized-pads-head-pcb.json`, `scripts/pads.py` | BOM/CPL lines and every polarized part with pad nets; D5 and D9 cathodes on the smaller-X pad |
| `parts-availability-2026-11-20.json`, `scripts/fetch-parts.py` | Read-only JLC and LCSC lookups of all 14 exact codes, 09:57Z |
| `catalog-estimate-2026-11-20.json`, `fee-pages-fetch.log`, `scripts/estimate.py` | Catalog estimate of parts and assembly; PCB fabrication and shipping UNAVAILABLE without the quote tool. Not a supplier quote |

Raw supplier page captures were kept out of the repository; the JSON keeps the values read. The scripts write to
`$P15_EVIDENCE_DIR` (default `tmp/p15-order-refresh`).
