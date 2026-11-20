# C4d root LED component gate — isolated review candidate

- Parent: [#308](https://github.com/Takazudo/zudo-pd/issues/308). Moya remains
  sole manager and integrator. This branch starts at independently accepted
  C4c `56b93f286a1d881f0676be202db08a401c18dc5f`.
- Branch: `codex/c4d-led-component-gate-20261116-01`. Exclusive writes are
  new `.github/workflows/led-component-checks.yml` and this receipt.
- Historical LED workflow SHA256:
  `dfb3fb6ae891262b3b54d4c0a00292c74126fa010287dabe4cfc0557f1e3c927`.
  The historical LED sources, #307 and publication files are untouched.

The LED component workflow is nested under `products/led-lamp/.github` and
inactive after import. This root-discovered workflow preserves its offline
component validator, unit and forward tests, three schematic-regeneration
checks, power-switch check, and SWD-orientation check. Its P15 step invokes
the independently reviewed same-repository consumer/owner entry instead of
the historical `--local-only` shortcut, with full Git history checkout. It
also runs both retained verifier suites. The workflow is scoped to LED inputs
and its own file, triggers on PRs to `main` or `base/**` and on `main` pushes,
and has read-only repository permission. It has no deploy or hardware command.

The exact commands were run on a disposable clean worktree at the stated base
with two-CPU affinity and a 4 GiB per-process address-space limit. The
sampled process-group RSS peak was 181,904 KiB; that sample is not a hard
aggregate memory ceiling. Results:

- LED component validator: **PASS**, 35 lines, offline, no refreshed source.
- Validator unit suite: **38 PASS**. Forward suite: **5 integration cases and
  7 negative routes PASS**.
- Three imported schematic generators: **PASS**, no tracked or untracked
  board change. External power-switch and SWD numeric-orientation checks:
  **PASS**.
- Same-repository P15 consumer and owner identity at the original pinned
  revision and reviewed C2 revision: **PASS**. Consumer tests **10 PASS**;
  owner tests **17 PASS**. The worktree stayed clean.

The LED workflow remains a product-specific gate, not one canonical evidence
catalog or a replacement for PD's existing gates. Native KiCad/CAD, ARM target
checks, browser, full build, CI, PR, merge, deployment, programming and
physical checks were **NOT RUN** in this step. Independent exact-head review
is required before any integration. Identity/SMAJ, DNP, textual-prose,
private-resource, publication, #307 and hardware holds remain.
