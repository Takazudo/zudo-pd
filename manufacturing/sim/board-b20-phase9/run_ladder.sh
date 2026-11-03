#!/bin/bash
# usage: run_ladder.sh <dir> <case...>; tries solver variants until one completes; records the one used
P="$(cd "$(dirname "$0")" && pwd)"  # decks run from <case dir>; ../lib must hold the vendor models listed in manufacturing/board-b-20v-switcher-direct-draft.md section 5
IMG=kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec
d=$1; shift
cd $P/$d
for k in "$@"; do
  cp $k.cir $k.base
  ok=0
  for v in "s/ 0 5u\( uic\)\{0,1\}$/ 0 5u\1/" "s/ 0 5u\( uic\)\{0,1\}$/ 0 2u\1/" "s/ 0 5u\( uic\)\{0,1\}$/ 0 10u\1/" "s/ 0 5u\( uic\)\{0,1\}$/ 0 20u\1/" "s/method=gear/method=trap/" "s/rshunt=1e10/rshunt=1e9/" "s/^RCV1 .*/&\nCCV1 m12_cs 0 100p/"; do
    sed "$v" $k.base > $k.cir
    timeout 1200 flock /tmp/kicad-native.lock docker run --rm --user 0 -v $P:/w -w /w/$d --entrypoint ngspice $IMG -b $k.cir > $k.log 2>&1
    e=$?
    if [ $e = 0 ]; then echo "$k OK variant=[$v]"; ok=1; break; fi
  done
  [ $ok = 0 ] && echo "$k FAILED all variants"
  rm -f $k.base
done
