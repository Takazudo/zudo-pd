#!/bin/bash
# usage: run_ladder.sh <dir> <case...>; tries solver variants in order until one completes; records the one used.
# Decks run from <dir>; ../lib must hold the vendor models listed in manufacturing/board-b-20v-switcher-direct-draft.md
# section 5, and <dir>/.spiceinit must set `ngbehavior=psa` and `num_threads=1`. ngspice runs without the KiCad lock, one CPU.
P="$(cd "$(dirname "$0")" && pwd)"
IMG=kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec
d=$1; shift
cd "$P/$d"
for k in "$@"; do
  cp "$k.cir" "$k.base"
  ok=0
  for v in "s/^xx//" "s/rshunt=1e10/rshunt=1e9/" "s/ 0 5u$/ 0 2u/" "s/abstol=1e-9/abstol=1e-8/" "s/reltol=1e-3/reltol=3e-3/" "s/method=trap/method=gear/" "s/method=trap/method=gear/;s/rshunt=1e10/rshunt=1e9/"; do
    sed "$v" "$k.base" > "$k.cir"
    timeout 3000 docker run --rm --cpus 1 --user 0 -v "$P":/w -w "/w/$d" --entrypoint ngspice $IMG -b "$k.cir" > "$k.log" 2>&1
    if [ $? = 0 ] && ! grep -q "aborted" "$k.log"; then echo "$k OK variant=[$v]"; ok=1; break; fi
  done
  [ $ok = 0 ] && echo "$k FAILED all variants"
  cp "$k.base" "$k.cir"; rm -f "$k.base"
done
