#!/bin/bash
# full rebuild from plan.json: apply, then prune by KiCad dangling reports until none
set -e -o pipefail
cd /home/user/zudo-pd
tmp/d2/kpy.sh tmp/d2/apply.py tmp/d2v/before.kicad_pcb tmp/d2/work.kicad_pcb tmp/d2/plan.json 2>&1 | grep -v Debug | grep -v "^$" | tail -3
rm -f tmp/d2/prune-log.json
for i in $(seq 1 45); do
  tmp/d2/drc.sh tmp/d2/work.kicad_pcb > /dev/null 2>&1
  n=$(python3 -c "import json;r=json.load(open('tmp/d2s/drc.json'));print(sum(1 for v in r['violations'] if v['type'] in ('track_dangling','via_dangling') and not any('[GND]' in i['description'] for i in v['items'])))")
  echo "pass $i dangling $n"
  [ "$n" = "0" ] && break
  tmp/d2/kpy.sh tmp/d2/prune_step.py tmp/d2/work.kicad_pcb tmp/d2/work.kicad_pcb tmp/d2s/drc.json tmp/d2/prune-log.json 2>&1 | grep -E "dangling|Error|Trace" 
done
cp tmp/d2/work.kicad_pcb tmp/d2/after-unfilled.kicad_pcb
tmp/d2/drc.sh tmp/d2/after-unfilled.kicad_pcb | tail -14
# repair pass for links broken by removed junction pads
for k in 1 2; do
  u=$(python3 -c "import json;print(len(json.load(open('tmp/d2s/drc.json'))['unconnected_items']))")
  [ "$u" = "0" ] && break
  tmp/d2/kpy.sh tmp/d2/dump.py tmp/d2/after-unfilled.kicad_pcb tmp/d2/work-geom.json >/dev/null 2>&1
  uv run -q --python 3.12 --with shapely --with numpy --with scipy python tmp/d2/repair.py
  tmp/d2/kpy.sh tmp/d2/addroutes.py tmp/d2/after-unfilled.kicad_pcb tmp/d2/after-unfilled.kicad_pcb tmp/d2/repair-items.json 2>&1 | grep added
  python3 -c "import json;a=json.load(open('tmp/d2/repair-items.json'));b=json.load(open('tmp/d2/repair-all.json')) if __import__('os').path.exists('tmp/d2/repair-all.json') else [];json.dump(b+a,open('tmp/d2/repair-all.json','w'))"
  tmp/d2/drc.sh tmp/d2/after-unfilled.kicad_pcb | tail -10
done
