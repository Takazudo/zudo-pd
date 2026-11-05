# schgen — schematic generation from board spec modules

Generated board schematics are owned by executable Python specs. The pure-Python regeneration gate covers
A/B/P/P15. P15 is shared 15 V input, P is current 20 V r3, B is PD15 conversion and A is historical.
B20 has its own `board_b20_spec.py`; inventory uses `board_b20_components.py`, the fifth provider input.
Read [current source mapping](../../doc/src/content/docs/project/repository-map.md),
[hardware workflow](../../doc/src/content/docs/project/hardware-workflow.md) and `circuit.config.ts`.
Historical generator docstrings may use earlier “as-built” vocabulary; the PD-specific retired r2 was never built.
Do not change executable Python merely to reconcile documentation.

## Files

- `board_a_spec.py`, `board_b_spec.py`, `board_p_spec.py` (20 V r3 draft) and
  `board_p15_spec.py` (shared P15 15 V input derived from retired r2; deltas in
  `baselines/board-p15-allow.json` against `baselines/board-p.json`) — per-board `COMPONENTS` / `NETS` /
  `NO_CONNECT` tables. Edit these, never the generated `.kicad_sch` directly.
- `decisions.json` — the wave-6 decision lock for epic #86 (part swaps,
  provisions, dispositions the board specs must implement), with rationale and
  fact-ID evidence per decision. Machine-consumable source of truth; issue
  bodies #124/#125/#126 mirror it. Its `required_decision_keys` list declares
  which decision keys the validator requires.
- `check_decisions.py` — offline validator for `decisions.json`: schema shape,
  the data-declared required decision keys, and kind-aware resolution of every
  evidence ID against the component-bundle / integration-rule fact base. Run:
  `python3 scripts/schgen/check_decisions.py`.
- `baselines/` — locked connectivity baselines per board
  (`board-a.json` / `board-b.json`: net → `Ref.Pin` lists derived from the
  reviewed netlist) plus the allow-list files naming the intentional
  spec-vs-baseline deltas (`board-a-allowed-deltas.json` /
  `board-b-allow.json`).
- `check_baseline.py` — diffs a spec module's `NETS` against its locked
  baseline JSON, modulo the allow-list. Every declared allow-list delta is
  also verified to actually hold in the spec, so a stale entry surfaces as a
  mismatch instead of masking an incomplete implementation. Also has a
  fixture-driven `--self-test` (see `fixtures/check_baseline/`). Run:
  ```
  python3 scripts/schgen/check_baseline.py scripts/schgen/board_a_spec.py scripts/schgen/baselines/board-a.json --allow scripts/schgen/baselines/board-a-allowed-deltas.json
  python3 scripts/schgen/check_baseline.py scripts/schgen/board_b_spec.py scripts/schgen/baselines/board-b.json --allow scripts/schgen/baselines/board-b-allow.json
  python3 scripts/schgen/check_baseline.py --self-test
  ```
- `schgen_core.py` — shared generator: reads symbols from
  `symbols/zudo-pd.kicad_sym`, places components, and emits global labels for
  every net (no drawn wires) plus no-connect markers. Also home of the shared
  `load_spec_module()` loader (path or dotted module name) every CLI here
  uses, and the `SchgenError` the tools report as messages rather than
  tracebacks.
- `sexp.py` — tiny, dependency-free KiCad s-expression tokenizer/parser used
  by the generator, the verifiers, and the smoke test. No KiCad install
  required.
- `gen_schematic.py` — CLI entry point:
  `python3 scripts/schgen/gen_schematic.py <spec_module>` where
  `<spec_module>` is a path (`scripts/schgen/board_a_spec.py`) or a dotted
  module name (`board_a_spec`). `--help` works.
- `verify_geometry.py` — re-derives every pin endpoint from a generated
  `.kicad_sch` itself (embedded lib_symbols + instance placements) and checks
  that every global label sits on a pin endpoint, no coordinate mixes two
  nets (no implicit shorts), the label-derived net map equals the spec's
  `NETS`, and no-connect markers match `NO_CONNECT`. Pure Python, no KiCad.
  Run: `python3 scripts/schgen/verify_geometry.py <spec_module> <kicad_sch>`.
- `verify_netlist.py` — diffs a kicad-cli netlist export against a spec's
  `NETS`/`NO_CONNECT` tables and prints `PASS`/`FAIL`.
- `verify.sh` — wraps the kicad-cli export + `verify_netlist.py` call for one
  board. Local-only (see below); not run in CI.
- `test_spec_smoke.py` — minimal spec (3 real zudo-pd resistor symbols, 2
  nets, 2 no-connects) used only to smoke-test the generator itself. Not a
  real board.
- `run_smoke_test.sh` — regenerates `test_spec_smoke.py` into a throwaway
  temp dir (never touches the repo tree), asserts the emitted global net
  labels match the spec's `NETS`, runs the `verify_geometry.py` checks on the
  output, and proves the geometry check can fail via a corrupted-label
  negative control. Requires only stock `python3` — no pip installs, no
  KiCad.
- `fixtures/check_baseline/` — the fixture corpus behind
  `check_baseline.py --self-test`.

## Regen + verify workflow

1. Edit the spec module (the intended `board_a_spec.py`, `board_b_spec.py`, `board_p_spec.py` or `board_p15_spec.py`) — add/move a
   component, change a net, etc.
2. Regenerate the schematic:
   ```
   python3 scripts/schgen/gen_schematic.py board_a_spec   # or board_b_spec
   ```
   This rewrites `boards/<board>/<board>.kicad_sch` in place. No KiCad
   install needed — `gen_schematic.py` only depends on `sexp.py`.
3. Run the offline checks CI will run (baseline drift + geometry):
   ```
   python3 scripts/schgen/check_baseline.py scripts/schgen/board_a_spec.py scripts/schgen/baselines/board-a.json --allow scripts/schgen/baselines/board-a-allowed-deltas.json
   python3 scripts/schgen/verify_geometry.py scripts/schgen/board_a_spec.py boards/board-a/board-a.kicad_sch
   ```
4. Verify connectivity against a real netlist export (requires a local KiCad
   install with `kicad-cli` on `PATH`):
   ```
   scripts/schgen/verify.sh board-a   # or board-b
   ```
   This runs `kicad-cli sch export netlist --format kicadsexpr` on the
   regenerated `.kicad_sch`, then diffs the result against the spec's `NETS`
   and `NO_CONNECT` tables via `verify_netlist.py`, printing `PASS`/`FAIL`.
5. Open the regenerated schematic in KiCad's Eeschema at least once (ERC,
   visual sanity) before committing.
6. Commit the spec module and the regenerated `.kicad_sch` together — never
   one without the other.

## Smoke test (no board, no KiCad)

To sanity-check the generator itself — e.g. after touching `schgen_core.py`
or `sexp.py` — run:

```
bash scripts/schgen/run_smoke_test.sh
```

This generates `test_spec_smoke.py` into a temp directory, parses the result
back with `sexp.py`, asserts the emitted global labels equal the spec's
`NETS`, and runs the full geometry check (including its negative control). It
needs stock `python3` only.

## kicad-cli availability

`verify.sh` degrades gracefully when `kicad-cli` is not on `PATH`: it prints
a `SKIPPED` marker and exits `0` rather than failing. This is intentional —
netlist verification is a local-only check that needs a real KiCad install
(the CI runner has no KiCad). Install KiCad (kicad-cli ships with the desktop
app) to exercise the real path.

## What CI checks

`.github/workflows/component-spec-skills.yml` runs, for every PR touching
this toolchain (and pushes to `main`), using `circuit/scripts/run-python-gates.sh` as the canonical sequence:

- **Regen-idempotency** — regenerate A/B/P/P15 against the checked-out tree
  and fail on any diff under `boards/` (with `git add --intent-to-add` first,
  so a newly emitted untracked file also fails). Catches "spec and committed
  schematic drifted apart".
- **Label geometry** — `verify_geometry.py` on A/B/P/P15 committed schematics: labels
  on pin endpoints, no cross-net coordinate collisions, label net map equal
  to the spec, no-connects matching.
- **Baseline drift** — `check_baseline.py` per board against
  `baselines/*.json` with the allow-list files.
- **Tool self-tests** — `check_baseline.py --self-test` and
  `run_smoke_test.sh`.
- **Decision lock** — `check_decisions.py`.

What CI still cannot do is run `kicad-cli`; the netlist cross-check in
`verify.sh` stays a local, KiCad-installed step.
