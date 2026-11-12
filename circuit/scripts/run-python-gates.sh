#!/usr/bin/env bash
# Offline project Python gates. The CI "validate" job and the local b4push both
# run this one script, so a gate cannot exist in one and be missing from the other.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

step() { printf '\n== %s\n' "$*"; }

step "Frozen component contract (strict)"
python3 .claude/skills/component-spec-audit/scripts/validate.py --strict
step "Validator and fixture tests"
python3 -m unittest discover -s .claude/skills/component-spec-audit/scripts -p 'test_*.py'
step "Cross-component routing and refusals (strict)"
python3 .claude/skills/circuit-spec-integration/scripts/check_forward_tests.py --strict
step "Baseline checker self-test"
python3 scripts/schgen/check_baseline.py --self-test
step "Schematic generator smoke test"
bash scripts/schgen/run_smoke_test.sh
step "Schematic verifier regression tests"
python3 -m unittest discover -s scripts/schgen -p 'test_*.py'

step "Regen idempotency: boards A, B, P and P15"
# Compare boards/ before and after regeneration, so uncommitted local edits elsewhere in boards/ do not
# mask or fake drift; CI starts from a clean checkout, so there this equals a diff against HEAD.
snapshot_boards() {
  git ls-files -z --cached --others --exclude-standard -- boards/ | sort -z | xargs -0 -r sha256sum
}
before="$(snapshot_boards)"
dirty_before="$(git status --porcelain --untracked-files=all -- boards/)"
python3 scripts/schgen/gen_schematic.py board_a_spec
python3 scripts/schgen/gen_schematic.py board_b_spec
python3 scripts/schgen/gen_schematic.py board_p_spec
python3 scripts/schgen/gen_schematic.py board_p15_spec
after="$(snapshot_boards)"
if [[ "$before" != "$after" ]]; then
  echo "FAIL: regeneration changed files under boards/:" >&2
  diff <(printf '%s\n' "$before") <(printf '%s\n' "$after") >&2 || true
  exit 1
fi
if [[ -n "$dirty_before" ]]; then
  printf 'NOTE: boards/ had uncommitted changes before regeneration; idempotency was checked against them:\n%s\n' "$dirty_before"
fi

step "Label geometry: boards A, B, P and P15"
python3 scripts/schgen/verify_geometry.py scripts/schgen/board_a_spec.py boards/board-a/board-a.kicad_sch
python3 scripts/schgen/verify_geometry.py scripts/schgen/board_b_spec.py boards/board-b/board-b.kicad_sch
python3 scripts/schgen/verify_geometry.py scripts/schgen/board_p_spec.py boards/board-p/board-p.kicad_sch
python3 scripts/schgen/verify_geometry.py scripts/schgen/board_p15_spec.py boards/board-p15/board-p15.kicad_sch

step "Connectivity-baseline drift: boards A, B, P and P15"
python3 scripts/schgen/check_baseline.py scripts/schgen/board_a_spec.py scripts/schgen/baselines/board-a.json --allow scripts/schgen/baselines/board-a-allowed-deltas.json
python3 scripts/schgen/check_baseline.py scripts/schgen/board_b_spec.py scripts/schgen/baselines/board-b.json --allow scripts/schgen/baselines/board-b-allow.json
python3 scripts/schgen/check_baseline.py scripts/schgen/board_p_spec.py scripts/schgen/baselines/board-p.json --allow scripts/schgen/baselines/board-p-allow.json
python3 scripts/schgen/check_baseline.py scripts/schgen/board_p15_spec.py scripts/schgen/baselines/board-p.json --allow scripts/schgen/baselines/board-p15-allow.json

step "Decision lock (decisions.json)"
python3 scripts/schgen/check_decisions.py
step "P15 NVM image rebuild check"
python3 scripts/pcb/board-p15/nvm-image.py --check
step "Shared P15 r1 source identity (byte identity only; needs full Git history)"
python3 scripts/pcb/board-p15/verify-shared-reference.py --worktree
python3 -m unittest discover -s scripts/pcb/board-p15 -p 'test_*.py'
step "Board P r3 20 V NVM intent rebuild check"
python3 scripts/pcb/board-p/nvm-intent-20v.py --check
step "Board P r3 Q1 closure screen: cited inputs, reproduction and tamper controls (typical data; not acceptance)"
python3 -m unittest discover -s scripts/pcb/board-p -p 'test_*.py'

step "PD15 supply-capability screen reproduces power-budget.json and its committed report is fresh"
python3 -m unittest discover -s scripts/pcb -p 'test_supply_capability.py'
step "Board P r3 draft native-evidence coverage and freshness negative controls (host-only)"
python3 scripts/pcb/board-p-r3-draft/test-correction-contract.py

step "B20 desk load cases bound to the PD20 contract; reports fresh"
python3 -m unittest discover -s scripts/pcb/board-b20 -p 'test_*.py'

step "B20 phase33 analysis input and threshold regressions (synthetic; not simulation qualification)"
python3 -m unittest discover -s manufacturing/sim/board-b20-phase33 -p 'test_*.py'

step "Courtyards enclose every pad"
python3 footprints/scripts/gen_courtyards.py --check
step "Courtyard geometry and library synchronization regressions"
python3 -m unittest discover -s footprints/scripts -p 'test_gen_courtyards.py'
step "Bare-copper footprints carry CPL/BOM exclusion attrs"
python3 footprints/scripts/check_bare_copper_attrs.py

printf '\nPASS: project Python gates\n'
