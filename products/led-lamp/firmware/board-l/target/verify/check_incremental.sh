#!/usr/bin/env bash
# Prove the target Makefile never reuses stale objects: clean vs incremental, header
# edits (target and V72), the CTRL ceiling guard, and BOARD_DEFS profile switching.
# Runs on a scratch copy of firmware/board-l, so the checkout is never edited.
set -euo pipefail

here=$(cd "$(dirname "$0")/.." && pwd)
scratch=$(mktemp -d)
trap 'rm -rf -- "${scratch:?}"' EXIT
mkdir -p "$scratch/board-l"
cp -a "$here/../src" "$scratch/board-l/src"
mkdir -p "$scratch/board-l/target"
(cd "$here" && tar --exclude=./build -cf - .) | (cd "$scratch/board-l/target" && tar -xf -)
cd "$scratch/board-l/target"

fail() { echo "FAIL: $*"; exit 1; }
pass() { echo "PASS: $*"; }
elf_hash() { sha256sum build/board-l-skeleton.elf | cut -d' ' -f1; }
compiled() { grep -c -- ' -c ' "$1" || true; }
field() { python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1]))
for k in sys.argv[2].split("."): d=d[k]
print(d)' build/board-l-skeleton.receipt.json "$1"; }
mk() { make "$@" >"$scratch/log" 2>&1 || { cat "$scratch/log"; fail "make $* exited non-zero"; }; }

mk
total=$(compiled "$scratch/log")
h0=$(elf_hash)
[ "$total" -eq 17 ] || fail "clean build compiled $total objects, expected 17"
[ "$(field ctrl_ceiling.CTRL_FULL_CCR)" = 2407 ] || fail "default receipt ceiling is not 2407"
[ "$(field options.profile)" = default-rs1-200mohm ] || fail "default profile name"
[ "$(field status)" = "UNFLASHED BENCH CANDIDATE" ] || fail "receipt status"
pass "clean build: 17 objects, CTRL_FULL_CCR 2407, ELF $h0"

mk
[ "$(compiled "$scratch/log")" -eq 0 ] || fail "no-op rebuild compiled objects"
grep -q 'arm-none-eabi-gcc .* -o build/board-l-skeleton.elf' "$scratch/log" && fail "no-op rebuild relinked"
pass "no-op incremental build: nothing compiled or linked"

touch board_l_proposal.h
mk
n=$(compiled "$scratch/log")
users=$(grep -l 'board_l_proposal.h' build/*.d build/v72/*.d | wc -l)
[ "$n" -eq "$users" ] && [ "$n" -gt 0 ] || fail "touching board_l_proposal.h rebuilt $n, expected $users"
[ "$(elf_hash)" = "$h0" ] || fail "unchanged header content changed the ELF"
pass "target header touch: rebuilt exactly its $n dependents, ELF unchanged"

touch Makefile
mk
[ "$(compiled "$scratch/log")" -eq 17 ] || fail "Makefile change did not rebuild all 17 objects"
[ "$(elf_hash)" = "$h0" ] || fail "unchanged Makefile content changed the ELF"
pass "Makefile touch: all 17 rebuilt, ELF unchanged"

touch ../src/lamp_app.h
mk
n=$(compiled "$scratch/log")
[ "$n" -gt 0 ] || fail "touching V72 lamp_app.h rebuilt nothing"
pass "V72 header touch: rebuilt $n dependents"

sed -i 's/#define CTRL_FULL_CCR 2407u/#define CTRL_FULL_CCR 2406u/' board_l_proposal.h
if make >"$scratch/log" 2>&1; then fail "non-default ceiling built without ACCEPT_NONDEFAULT_CAP"; fi
grep -q 'CTRL_FULL_CCR 2406u != adopted 2407u' "$scratch/log" || fail "cap-check message"
pass "header ceiling change refused without ACCEPT_NONDEFAULT_CAP"
mk ACCEPT_NONDEFAULT_CAP=1
[ "$(compiled "$scratch/log")" -gt 0 ] || fail "header value change rebuilt nothing"
[ "$(elf_hash)" != "$h0" ] || fail "header value change left the ELF unchanged (stale)"
[ "$(field ctrl_ceiling.CTRL_FULL_CCR)" = 2406 ] || fail "receipt does not show the changed ceiling"
[ "$(field ctrl_ceiling.adopted_default)" = False ] || fail "receipt marks 2406 as default"
pass "header value change: rebuilt, new ELF, receipt shows non-default 2406"
sed -i 's/#define CTRL_FULL_CCR 2406u/#define CTRL_FULL_CCR 2407u/' board_l_proposal.h
mk
[ "$(elf_hash)" = "$h0" ] || fail "restoring the header did not restore the ELF"
pass "header restored: ELF back to $h0"

mk BOARD_DEFS=-DBOARD_L_PRODUCTION
n=$(compiled "$scratch/log")
[ "$n" -eq 17 ] || fail "BOARD_DEFS switch rebuilt $n objects, expected 17"
grep -q 'build configuration changed' "$scratch/log" || fail "config stamp not refreshed"
[ "$(elf_hash)" != "$h0" ] || fail "BOARD_L_PRODUCTION left the ELF unchanged"
[ "$(field options.profile)" = custom ] || fail "receipt profile for BOARD_DEFS"
[ "$(field options.BOARD_L_PRODUCTION)" = True ] || fail "receipt BOARD_L_PRODUCTION flag"
pass "BOARD_DEFS switch: all 17 rebuilt, new ELF, receipt profile custom"
mk BOARD_DEFS=-DBOARD_L_PRODUCTION
[ "$(compiled "$scratch/log")" -eq 0 ] || fail "repeat BOARD_DEFS build was not incremental"
mk
[ "$(compiled "$scratch/log")" -eq 17 ] || fail "switch back did not rebuild everything"
[ "$(elf_hash)" = "$h0" ] || fail "switch back did not restore the default ELF"
[ "$(field options.profile)" = default-rs1-200mohm ] || fail "receipt profile after switch back"
pass "switch back to default: all 17 rebuilt, ELF back to $h0"

if make BOARD_DEFS=-DCTRL_FULL_CCR=3200 >"$scratch/log" 2>&1; then
  fail "-DCTRL_FULL_CCR=3200 built without ACCEPT_NONDEFAULT_CAP"; fi
pass "-DCTRL_FULL_CCR=3200 refused without ACCEPT_NONDEFAULT_CAP"

incremental=$(elf_hash)
make clean >/dev/null
mk
[ "$(elf_hash)" = "$incremental" ] || fail "incremental ELF differs from clean rebuild"
pass "incremental result equals a clean rebuild ($incremental)"
echo "check-incremental: all checks passed"
