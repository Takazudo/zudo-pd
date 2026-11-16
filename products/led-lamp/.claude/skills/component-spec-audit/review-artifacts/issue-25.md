# Issue 25 review

Scope: central component-spec validator/fixtures, circuit-spec integration skill, workflow, narrowly corrected family evidence, and the approved stale documentation lines.

## Findings-first self-review

- Applied: bounded the newly enabled exponent operator so a malicious calculated expression cannot request unbounded integer exponentiation.
- Applied: strengthened forward tests from short identity checks to realistic USB-PD/NVM, converter passive-change, and MCU/LED/NTC/thermal prompts. They now assert the trigger skill, unioned rule/record loading, subordinate records, exact source/fact bindings, conditions/locators, refusal verdicts, conflicting identifiers, wrong-vendor identity, superseded identity, and ambiguous aliases.
- Applied: the MCU/LED/thermal forward case now loads both the LED-stage and NTC/ADC rules, including the STM32 and Murata owners.
- Applied: destructive-risk golden facts now hash-lock their independent family-review logs plus the foreground integration review; the validator requires exact reviewer/pass parity and distinct foreground/independent reviewers. OPEN/UNSOURCED facts remain honestly non-confirmed.
- Applied: reconciled all P1/P2 findings from the independent control audit. XFCN working voltage remains unclaimed; STM document-byte locks use unavailable sentinels and PA11/PA12 bracket/remap semantics; ALPS remains mirror-only and non-deterministic; Hongli static CCT/orderability is now distributor-identity confirmed while incoming acceptance remains OPEN; FOJAN uses R30-R37 and exact calculated RCWV; Murata's missing guaranteed curve remains UNSOURCED.
- Applied: corrected the allowed stale documentation for exact capacitors, R12 value/topology, C35 connection, UMW manufacturer attribution, and FOJAN ballast package/refdes.
- Applied in final cross-check: removed stale `-9.6 V` gate-drive arithmetic, encoded conditioned R11/R12/C35/VBEN calculations and a transient bench refusal, corrected UMW RDS(on)/loss prose, and removed false J1/D5 input-chain PASS claims.
- Applied in final cross-check: routing now rejects unknown wrong-vendor qualifiers case-insensitively; critical reviews hash-lock value, unit, source/review extract, locator and conditions; every pin map is compared with the generator-selected KiCad symbol and footprint; rail/PD/converter rules include capacitor, downstream-startup and input-transient facts.
- Applied: recovered HRO primary TYPE-C-31-M-17 and High Diode primary SMAJ20A sources, retained stable C283540/C571370 distributor bindings, split their ratings into atomic conditioned facts, and made the HRO drawing refresh reproducible with its official product-page Referer. Primary rating evidence is now closed; numeric project mapping, incoming/as-built continuity, both-rail simulation, and real waveforms remain open.
- Applied: retained exact STUSB4500 Rev 8/UM2650 mirror bytes, added atomic VDD/CC/VBUS-pin absolute limits, and recomputed conditioned D5-to-STUSB, Q1 VDS, Q1 steady VGS/margin, and R11/R12/C35 time-constant results from raw facts. Mirror-only trust and actual waveforms remain open.
- Applied: split Honglitronic Vf/current/power/reverse-voltage/junction/solder limits into atomic unit-bearing manufacturer facts; the distributor binding is now separately confirmed and received reel/label/CCT acceptance remains OPEN.
- Safety blocker updated: https://github.com/Takazudo/zudo-led-lamp/issues/34 now records the recovered primary sources and keeps the no-PD gate for project mapping, incoming/as-built inspection, both-board simulation, programmed state, and bench waveforms.
- Evidence follow-up created: https://github.com/Takazudo/zudo-led-lamp/issues/35 now has its static C210315-to-3000 K binding closed in this audit; incoming reel/label/bin and photometric verification remain the recoverable follow-up without being misclassified as a destructive electrical blocker.
- No further actionable findings after the final routing, trust-closure, pin-lock, critical-review, privacy, duplicate-key JSON, workflow, diff, and scope review.
- Applied after final audit: committed all four normalized review artifacts and made the validator recompute their byte hashes; missing paths and arbitrary hashes now fail closed.
- Applied after final audit: committed three hash-locked observed Claude Code policy-response artifacts. Deterministic fixtures prove routing/discovery; explicit-skill, tools-disabled frozen-packet runs prove rendered conditions, verdicts and refusal without claiming independent ID discovery.
- Applied after final audit: downgraded generator prose to a `MIXED` generated-netlist stage and added a mutation proving free text cannot promote it to `CONFIRMED` without structured exported-net evidence.
- Applied after final audit: required the zero SHA sentinel for every `SOURCE UNAVAILABLE` source and added a strictly structured distributor-identity-only lane that cannot support electrical/thermal claims, calculations, PASS or BLOCKER.
- Applied after final audit: confirmed C283540, C571370 and C210315 static orderable bindings through distributor identity evidence. C210315 live HTML hashes varied across retries, so its retained bytes remain locked but deterministic selective refresh is explicitly disabled; incoming reel/label/CCT acceptance remains OPEN.
- Applied after final audit: online refresh now uses a process-unique temporary directory; a nested concurrent-refresh regression test prevents one validator process from deleting another process's target directory.
- Applied after final independent audit: the allowlisted Board P prose no longer treats 32.4 V as installed-waveform proof, and Board P plus its ratings matrix now distinguish manufacturer-primary, manufacturer-mirror, and catalog authority in their introductory claims. The out-of-allowlist LED-driver research correction is isolated in follow-up #36 rather than expanding issue #25's ownership.

## Verification

- Offline validator: PASS, exact 32-line/13-owner parity.
- Validator unit suite: PASS, 32 tests under `-W error::ResourceWarning`.
- Integration forward suite: PASS, 3 realistic cases and 7 negative routes.
- Observed Claude policy suite: PASS, 3 prompt/response hash locks with exact loaded skills, sources, facts, conditions, calculations, verdicts and refusals; gardening, empty-evidence, missing-skill and fake-hash mutations fail.
- Selective online refresh: PASS for `src-type-c-c283540`, `src-type-c-primary-page`, `src-type-c-primary-drawing`, `src-high-diode-c571370`, and `src-high-diode-primary`, with browser-like/per-source headers and exact SHA-256 matches. Earlier AL8860 generator/primary refresh evidence remains locked.
- Skill Creator quick validation: PASS for `component-spec-audit` and `circuit-spec-integration`.
- JSON parse, duplicate-key scan, Python compile, workflow YAML parse, `git diff --check`, scope scan, and privacy/path scan: PASS.
- Documentation `pnpm install --frozen-lockfile && pnpm b4push`: PASS; type-check and 36-page production build succeeded.
- Visual checks: not applicable; no UI, schematic, PCB, or rendered layout artifact changed.

## Remaining risks

- Mirror-only and unavailable-primary component evidence remains OPEN/UNSOURCED by design, including STUSB trust closure despite reproducibly retained manufacturer-authored archive bytes.
- PCB/BOM/CPL, as-built, programmed/NVM, firmware threshold, and bench stages remain OPEN; generator connectivity is not promoted to those states.
- Forward fixtures mechanically validate realistic prompts, routing, selected rules/evidence, calculations, and refusal policy; they do not constitute an independently sampled live model response.
- Generator-authored topology remains `MIXED` until CI can bind structured exported KiCad net data; no free-text generator fact is treated as exported-netlist confirmation.

Self-review: foreground complete; findings: applied
