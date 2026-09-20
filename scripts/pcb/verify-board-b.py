#!/usr/bin/env python3
"""Check Board B against its schematic, socket pin contract and mating PD geometry."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import wx
_KICAD_APP = wx.App(False)
import pcbnew as p

from pcb_common import pcb_net_name
from board_b_layout import WIDTH, HEIGHT, pd_to_board_b

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/schgen'))
import board_b_spec as spec


def require(ok,message):
    if not ok:raise ValueError(message)


def xy(item):
    pos=item.GetPosition()
    return [p.ToMM(pos.x),p.ToMM(pos.y)]


def near(a,b):
    return len(a)==len(b) and all(abs(x-y)<.001 for x,y in zip(a,b))


def verify_pd_mating(fps):
    """Check the unchanged Board P interface through the declared face-to-face mirror mapping."""
    mechanical=json.loads((ROOT/'boards/board-p/mechanical.json').read_text())
    header=fps['J5']; j5={pad.GetNumber():pad for pad in header.Pads()}
    require(len(list(header.Pads()))==6 and set(j5)=={str(i) for i in range(1,7)},'J5 must have exactly six contacts')
    require(header.GetLayer()==p.F_Cu and abs(header.GetOrientationDegrees()%360-270)<.001,
            'J5 must be front-side, rotation270, facing the inverted Board P above Board B')
    require(pd_to_board_b((6.55,37.7))==(37.2,18.55) and pd_to_board_b((19.25,37.7))==(37.2,31.25),
            'PD transform must be P(x,y) -> B(y-0.5,x+12); in-plane rotation reverses the net order')
    contract=json.loads((ROOT/'boards/board-b/mechanical.json').read_text())['pd_stack']
    require(contract['point_transform']=='P(x,y) -> B(y-0.5,x+12)' and contract['nominal_board_p_top_z_mm']==11.1,
            'Unreviewed front-facing stack transform or spacing')
    netmap={'VBUS_OUT':'+15V INPUT','ATT':'ATT','PDOK':'PDOK','GND':'GND'}
    mating=[]
    for pin in mechanical['interface']['pads']:
        pad=j5[str(pin['pin'])]; target=pd_to_board_b(pin['center'])
        require(near(xy(pad),target),f'J5.{pin["pin"]}: mirrored PD mating pad mismatch')
        expected_net=pcb_net_name(netmap[pin['net']])
        require(pad.GetNetname()==expected_net,f'J5.{pin["pin"]}: end-to-end PD net mismatch')
        locked=next(v for v in contract['pads'] if v['pin']==pin['pin'])
        require(near(target,locked['center_mm']), 'Mechanical interface pin contract disagrees with source Board P')
        mating.append({'pin':pin['pin'],'board_p_center_mm':pin['center'],
                       'center_mm':xy(pad),'board_b_net':pad.GetNetname()})
    for i,hole in enumerate(mechanical['mounting_holes'],1):
        locked=next(v for v in contract['mounting_holes'] if v['ref']=='H'+str(i))
        require(near(pd_to_board_b(hole['center']),locked['center_mm']), 'Mechanical mount contract disagrees with source Board P')
        fp=fps['H'+str(i)];pads=list(fp.Pads());require(len(pads)==1,'Mount must have one hole')
        pad=pads[0]
        require(near(xy(pad),pd_to_board_b(hole['center'])) and pad.GetAttribute()==p.PAD_ATTRIB_NPTH
                and near([p.ToMM(pad.GetDrillSize().x),p.ToMM(pad.GetDrillSize().y)],[hole['drill']]*2),
                'Rotated PD mounting-hole mismatch')
    return mating


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pcb',nargs='?',type=Path,default=ROOT/'boards/board-b/board-b.kicad_pcb')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--project-dir',type=Path,help='Explicit model project directory for a temporary PCB')
    args=parser.parse_args()
    b=p.LoadBoard(str(args.pcb));fps={}
    for fp in b.GetFootprints():
        ref=fp.GetReference();require(ref not in fps,f'Duplicate reference {ref}');fps[ref]=fp
    expected={pin:pcb_net_name(net) for net,pins in spec.NETS.items() for pin in pins}
    seen=set()
    for ref,comp in spec.COMPONENTS.items():
        require(ref in fps,f'Missing {ref}')
        fp=fps[ref]
        require(fp.GetValue()==comp[1] and fp.GetFPIDAsString()==comp[3] and fp.IsDNP()==comp[4],f'{ref}: identity/population mismatch')
        require(fp.GetFieldText('LCSC')==comp[2],f'{ref}: LCSC mismatch')
        for pad in fp.Pads():
            key=ref+'.'+pad.GetNumber()
            if pad.GetAttribute()==p.PAD_ATTRIB_NPTH:continue
            if key in spec.NO_CONNECT:
                require(pad.GetNetCode()==0 or pad.GetNetname().startswith('unconnected-'),f'{key}: no-connect was connected')
            else:
                require(key in expected and pad.GetNetname()==expected[key],f'{key}: incorrect/missing net {pad.GetNetname()}')
                seen.add(key)
    require(seen==set(expected),'Not all schematic pins have matching PCB pads')
    stack=json.loads((ROOT/'boards/board-b/mechanical.json').read_text())['pd_stack']
    require(near(xy(fps['C5']),stack['c5_envelope']['center_mm']) and fps['C5'].GetLayer()==p.F_Cu
            and abs(fps['C5'].GetOrientationDegrees()%360-stack['c5_envelope']['orientation_deg'])<.001,
            'C5 must remain outside the front-facing PD stack at its reviewed placement')
    mating=verify_pd_mating(fps)
    socket_contract={1:'-12V rail',2:'-12V rail',**{n:'GND' for n in range(3,9)},9:'+12V rail',10:'+12V rail',11:'+5V rail',12:'+5V rail',13:'CV rail',14:'CV rail',15:'GATE rail',16:'GATE rail'}
    for ref in ('J10','J11'):
        fp=fps[ref];require(fp.GetLayer()==p.F_Cu and abs(fp.GetOrientationDegrees())<.001,f'{ref}: changed mating direction')
        require(abs(xy(fp)[1]+12.23-HEIGHT)<.001,f'{ref}: mating face not at straight board edge')
        pads={int(pad.GetNumber()):pad for pad in fp.Pads()}
        require(set(pads)==set(socket_contract),f'{ref}: missing/extra contacts')
        for num,net in socket_contract.items():require(pads[num].GetNetname()==net,f'{ref}.{num}: wrong Eurorack rail')
        require(pads[1].GetShape()==p.PAD_SHAPE_RECT,f'{ref}: no rectangular pin1 marker')
    result={'board':'board-b','size_mm':[WIDTH,HEIGHT],'component_count':len(spec.COMPONENTS),'schematic_pad_identity':'PASS','eurorack_pin_contract':'PASS','pd_mating_xy':'PASS','shared_mounting_holes':'PASS','mating_pads':mating,'physical_stack_and_cable_fit':'NOT MEASURED'}
    mechanics_spec=importlib.util.spec_from_file_location('compact_mechanics',ROOT/'scripts/pcb/verify-compact-mechanics.py')
    mechanics_module=importlib.util.module_from_spec(mechanics_spec)
    mechanics_spec.loader.exec_module(mechanics_module)
    mechanics=mechanics_module.verify_compact_mechanics(b,args.pcb,width=WIDTH,height=HEIGHT,project_dir=args.project_dir)
    require(mechanics['status']=='PASS','Compact mechanics failed: '+ '; '.join(mechanics['errors']))
    result['plain_rectangular_outline']='PASS'
    result['compact_mechanics']=mechanics
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
