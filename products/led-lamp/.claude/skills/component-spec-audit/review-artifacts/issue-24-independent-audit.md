# Issue 24 independent audit — Board L control-domain component skills

Audit target: `base/component-spec-skills` at `497ea37e61ecdfea1d2106aabce85f8723d2ee2e`
Scope: STM32/header, ALPS encoder, Murata NTC, Honglitronic LED/FOJAN ballast
Mode: read-only independent review; no repository files were edited

## Findings

### P1 — XFCN sources marked AVAILABLE no longer reproduce, leaving false primary PASS claims (forwarded)

In `.claude/skills/component-stm32g031f8p6/sources.json`:

- `src-c492404-page` points to `https://www.xfconn.com/product/pz254v-11-05p.html`; it returns HTTP 404, not the retained hash.
- `src-c492404-drawing` points to `https://www.xfconn.com/uploadfile/product/2024/06/12/PZ254V-11-XX.pdf`; it also returns HTTP 404.

Nevertheless `fact-c492404-manufacturer`, `fact-c492404-rating`, and `fact-c492404-mechanical` remain `PASS - primary-source confirmed`, and `cov-c492404-spec` is `COVERED`.

The stable official drawing is [XFCN PZ254V-11-XX](https://www.xfconn.com/uploads/soft/20240711/4-240G11122102R.pdf), 138,866 bytes, SHA-256 `e2966566f91532f87d0cb87317238d17d1e883ea6846ef4a0d6b6a83468cd9c9`. It supports XFCN/family identity, XX=05 mechanics, 3 A, 20 mΩ maximum, and -40 to 105 C, but not the existing `250 VAC/DC` claim. The current exact product page at `https://www.xfconn.com/index.php?a=index&aid=1738&c=View&m=home` does state 250 V AC/DC, but its response bytes change per request because of generated form tokens, so it is not an exact reproducible byte lock.

Action: rebind supported facts to the stable drawing, split the mixed rating fact, and keep the 250 V claim `UNSOURCED` (and its domain open) until a stable exact manufacturer source is locked.

### P1 — STM32 pin-map data erases PA11/PA12 remap semantics (forwarded)

In `.claude/skills/component-stm32g031f8p6/pin-map.json`, `pinmap-c529334` describes physical pins 16 and 17 as `PA11/PA9` and `PA12/PA10`, both with function `shared GPIO bond`. `fact-c529334-pin-bonds` repeats that notation under the condition “slash-separated labels share one physical package pin.”

The local KiCad symbol and the ST datasheet use `PA11[PA9]` and `PA12[PA10]`. The brackets matter: PA11/PA12 are software-remappable to PA9/PA10 through SYSCFG, unlike genuinely slash-separated internally bonded GPIOs. See the official [STM32G031 pin-assignment table](https://www.st.com/resource/en/datasheet/stm32g031g8.pdf).

Action: preserve bracket notation, describe these as remappable pads rather than bonded ports, and retain the SYSCFG remap requirement. Pins 16/17 are currently NC, but the component guidance is still materially wrong.

### P1 — FOJAN project topology names the wrong refdes range (forwarded)

In `.claude/skills/component-honglitronic-hl-am-2835h421w-s1-08-hr3/`:

- `fact-c2934070-topology` says “R1 through R8”.
- `src-c2934070-generator.evidence_extract` says the same.

The locked generator creates `R{29+n}`, so the eight ballast placements are `R30` through `R37`; the central inventory and Board L architecture document also use R30–R37.

Action: correct both the fact and retained generator extract to R30–R37. The raw generator URL itself is valid; the error is in the human-authored evidence record.

### P1 — ALPS deterministic BLOCKER depends on an UNSOURCED premise (forwarded)

`fact-c2991196-label-conflict` and `int-c2991196-label` use `BLOCKER - deterministic spec violation` because the generator says “15-detent” while `fact-c2991196-detents` says 30 detents / 15 pulses. The latter fact is explicitly `UNSOURCED` from `MANUFACTURER_MIRROR`, and the conflict fact declares no dependency on it.

The discrepancy is plausible and the mirrored manufacturer document is exact, but the bundle's trust vocabulary does not support calling a conclusion deterministic while its decisive premise remains untrusted. The generator text is also display metadata rather than an electrical implementation.

Action: downgrade the fact/interaction to `UNSOURCED` or a documentation discrepancy until primary evidence is locked, and encode the premise dependency if the schema is extended to support non-calculated logical dependencies.

### P1 — Four `AVAILABLE` document locks use URLs that now return HTML, not the retained PDFs (forwarded)

The retained bytes were recoverable, so these are URL-reproducibility defects rather than lost evidence:

| Source ID | Current URL result | Stable replacement / primary upgrade |
|---|---|---|
| `src-c2991196-spec` | Mouser returns HTML/403 rather than SHA `3358e123...` | [stable LCSC-hosted PDF](https://datasheet.lcsc.com/datasheet/pdf/e0a93036a66b5d2cacdda7d8f30bdea7.pdf?productCode=C2991196), same SHA; remains `MANUFACTURER_MIRROR` |
| `src-c13564-catalog` | `www.lcsc.com` redirects to HTML rather than SHA `64c596ad...` | `https://datasheet.lcsc.com/lcsc_datasheet_1809202230_Murata-Electronics-NCP18XH103F03RB_C13564.pdf`, same SHA |
| `src-c210315-spec` | old LCSC path redirects to HTML rather than SHA `51888793...` | [official Honglitronic PDF](https://www.honglitronic.com/upload/file/2025-04/col24/1745911741682.pdf), same SHA; upgrade to `MANUFACTURER_PRIMARY` |
| `src-c2934070-spec` | `www.lcsc.com` redirects to HTML rather than SHA `56042d12...` | `https://datasheet.lcsc.com/lcsc_datasheet_2404261607_FOJAN-FRC2512F33R0TS_C2934070.pdf`, same SHA |

Action: replace the stale authoritative URLs (or mark unavailable). For Honglitronic, the identical official bytes allow supported LED facts to become primary-source PASS after review.

### P1 — `COVERED` is being used for domains whose claims are entirely untrusted (forwarded)

These entries close their domains while their reasons admit the governing facts are `UNSOURCED` or the sources are unavailable:

- STM: `cov-c529334-pins`
- ALPS: `cov-c2991196-spec`
- Murata: `cov-c13564-context`
- Honglitronic: `cov-c210315-spec`
- FOJAN: `cov-c2934070-context`
- XFCN: `cov-c492404-spec` additionally relies on the stale false-PASS sources above

The validator checks only the enum and one-for-one `OPEN`/manifest mapping; it does not enforce trust closure for a `COVERED` domain. That makes the status misleading for the core goal of ensuring component specifications “for sure.”

Action: make domains `OPEN` until their exact claims are supported, then close only the primary-supported subset. Murata, Honglitronic, and FOJAN now have primary-source recovery paths; ALPS and STM still require honest open domains for unavailable-primary material.

### P1 — C210315's 3000 K orderable identity is not represented as evidence (forwarded)

The official Honglitronic specification covers one base MPN across multiple CCT rows (2700 K through 6500 K), and its label section carries `TC` separately. It supports the conditional 3000 K-bin flux values, but does not by itself establish that every `HL-AM-2835H421W-S1-08-HR3` is the 3000 K orderable.

The skill prose says “Exact 3000 K output,” the generator value says 3000 K, and inventory function says 3000 K. The current LCSC page identifies `C210315` as `HL-AM-2835H421W-S1-08-HR3(2800-3100K)` / 3000 K, but no record-local `DISTRIBUTOR_IDENTITY` source/fact captures that binding; the page's full HTML bytes are also dynamic.

Action: lock a stable exact C210315 identity artifact and add a distributor-identity fact, or keep installed CCT/orderability explicitly open and phrase the optical facts as conditional on the 3000 K bin.

### P2 — FOJAN's 200 V field is a package ceiling, not the exact 33 Ω part's working voltage (forwarded)

`fact-c2934070-voltage` currently reads “200 V maximum working”. The FOJAN rule is the lower of the package cap and `sqrt(P × R)`. For 1 W and 33 Ω, the exact rated continuous working voltage is `sqrt(33) = 5.7446 V`, not 200 V.

Action: call 200 V the 2512 package ceiling, retain overload/dielectric test limits separately, and add an exact calculated RCWV fact depending on trusted resistance and power facts. The illustrative 60 mA branch drop is about 1.98 V, so the present nominal branch remains below 5.7446 V.

### P2 — Murata missing-source fact uses `NEEDS BENCH` where the contract calls for `UNSOURCED` (forwarded)

`fact-c13564-curve-caveat` is tied to `src-c13564-current` (`SOURCE UNAVAILABLE`) but says `NEEDS BENCH` for the missing guaranteed R-T table. A bench test cannot establish a manufacturer-guaranteed table; the central workflow says unavailable authoritative evidence remains `UNSOURCED`.

Action: split the missing vendor-spec fact (`UNSOURCED`) from installed self-heating, placement coupling, and thermal-lag interactions (`NEEDS BENCH`).

The official [Murata exact-part list](https://www.murata.com/-/media/webrenewal/tool/library/common-pdf/static-model/component-list-ntc-2508.ashx?cvid=20250930011345000000&la=ja-jp), 393,694 bytes, SHA-256 `bf915019e6c5a744147b12f166194c53459a4b1e7826476ddc921d31d7e1f55f`, supports exact identity, NRND, 10 kΩ ±1%, B25/50 3380 K ±1%, B25/85 typical 3434 K, 0.1 mA maximum measurement current, 0603, and consumer use. It does not close the full R-T/self-heating/time-constant domains.

### P2 — ALPS prose asserts a lifecycle state that its own fact leaves unconfirmed (forwarded)

`.claude/skills/component-alps-ec11l1525g01/SKILL.md` calls the device “the exact retired ALPS EC11L1525G01”, while `fact-c2991196-lifecycle` says retired/discontinued is not confirmed from a current manufacturer page and remains `UNSOURCED`.

Action: remove “retired” from routing prose until exact current manufacturer evidence is locked, or add a correctly scoped lifecycle source.

### P2 — STM `sha256` fields are extraction hashes, not URL-document byte hashes (forwarded)

`src-c529334-ds`, `src-c529334-rm`, and `src-c529334-es` explicitly say their hashes lock a normalized reader extraction because official PDF bytes could not be retained. Those digests therefore cannot reproduce the documents named by `authoritative_url`, even though the schema field is simply `sha256`.

The facts correctly remain `UNSOURCED`, so this does not create a false PASS. It does prevent an exact source-byte audit.

Action: use real official PDF-byte hashes when reproducibly retrievable. If that remains impossible, a later contract revision should distinguish source-byte hash from extract hash (`hash_scope` or an unavailable sentinel) rather than overloading one field.

## Source recovery notes

- Board L generator: the commit-pinned raw URL returned 6,989 bytes and exactly matched SHA-256 `2139379c80c064ef4c9b69938643722661c4b90d9b9b28cc683921b9a1578d95` for all four bundles.
- Honglitronic: official PDF bytes exactly match the retained mirror hash and support polarity, conditional optical/electrical rows, absolute maxima, and process limits. Exact C210315 CCT binding remains separate.
- FOJAN: the manufacturer currently links [FJ-JS-3001 V2.0](http://www.fojan.cn/Private/Files/20260117/6390425653118283306794915.pdf), 1,612,617 bytes, SHA-256 `3129c2e0fcc114676646ce1435f7854974f999765dc5a8b9ea51ed275725e6f9`. It supports exact ordering decode, 2512/1 W ratings, the `sqrt(P×R)` rule, -55 to 155 C, and ±100 ppm/°C at 33 Ω. The retained V3 mirror is newer, so keep both and promote only claims confirmed by primary bytes.
- ALPS: exact manufacturer-authored bytes are recoverable only from a distributor mirror in this audit; keep component facts `UNSOURCED` under the frozen contract.
- STM: direct curl retrieval remained non-reproducible/time-out prone; keeping these primary sources unavailable is conservative.

## Checks with no finding

- `python3 .claude/skills/component-spec-audit/scripts/validate.py` passed: 32 lines, offline mode.
- `python3 .claude/skills/component-spec-audit/scripts/test_validate.py` passed all 17 tests.
- `git diff --check 20f9f97..497ea37` was clean, and the audited worktree was clean.
- Apart from the STM bracket/remap semantics above, symbol-pin to footprint-pad numbering matched local symbols/footprints for all six records.
- Header `rec-c492404` and ballast `rec-c2934070` are first-class subordinate records with their own sources, facts, routing, coverage, interactions, and pin maps; no orphan ownership defect was found.
- Direct positive/negative routing fixtures passed.
- Privacy scan found no absolute user paths, other-project names, credentials, tokens, or secrets in the four bundles.

## Conclusion

The bundles are structurally complete and validator-clean, but they are not yet safe to treat as trust-closed. The merge should be held until the false source locks/PASS claims, two mapping defects, false blocker, coverage closure, and exact CCT identity gap are corrected. All findings above were forwarded to the integration owner during the audit.
