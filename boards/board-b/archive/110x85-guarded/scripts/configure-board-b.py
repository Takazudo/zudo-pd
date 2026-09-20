#!/usr/bin/env python3
"""Restore explicit routing/manufacturing rules after pcbnew saves a generated board."""
import copy
import json
from pathlib import Path
import sys
from pcb_common import pcb_net_name

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/schgen'))
import board_b_spec as spec

path=ROOT/'boards/board-b/board-b.kicad_pro'
data=json.loads(path.read_text())
default=next(c for c in data['net_settings']['classes'] if c['name']=='Default')
default.update(clearance=.25,track_width=.25,via_diameter=1.2,via_drill=.6)
power=copy.deepcopy(default);power.update(name='Power',track_width=1.0,priority=1)
feed=copy.deepcopy(default);feed.update(name='PD feed',track_width=1.5,priority=0)
data['net_settings']['classes']=[default,power,feed]
signals={'ATT','PDOK','CV rail','GATE rail','U2_BST'}
for name in spec.NETS:
    if any(token in name for token in ('Feedback','ADJ','FB upper series','R7-','R8-','R9-')):
        signals.add(name)
data['net_settings']['netclass_patterns']=[{'netclass':('PD feed' if name=='+15V INPUT' else 'Power'),'pattern':pcb_net_name(name)}
                                           for name in spec.NETS if name not in signals]
rules=data.setdefault('board',{}).setdefault('design_settings',{}).setdefault('rules',{})
rules.update(min_clearance=.2,min_track_width=.2,min_via_diameter=.8,min_through_hole_diameter=.3,
             min_hole_to_hole=.25,min_copper_edge_clearance=.3,min_via_annular_width=.25)
path.write_text(json.dumps(data,indent=2)+'\n')
print('Board B: Default0.25mm, Power1.0mm, PDfeed1.5mm; explicit power-net assignments')
