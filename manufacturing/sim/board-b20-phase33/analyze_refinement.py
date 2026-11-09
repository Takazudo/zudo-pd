"""Audit two original-only 2 us startup refinements, including separate OSC ESR probes.

This is a convergence comparison, not a physical result or interface acceptance.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
from analysis_inputs import load, adjacent_slope_screen, window
from run_ladder import IMAGE


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def require(x, message):
    if not x: raise ValueError(message)


def supplemental(path, rows):
    data=[]
    for line in path.read_text().splitlines():
        if not line.strip(): continue
        r=list(map(float,line.split()))
        require(len(r)==6 and all(map(math.isfinite,r)), 'supplemental output must contain six finite columns')
        require(r[0]==r[2]==r[4], 'supplemental times disagree')
        data.append((r[0],r[1],r[3],r[5]))
    require(len(data)==len(rows), 'supplemental row count differs from main waveform')
    require(all(abs(a[0]-b[0])<1e-12 for a,b in zip(data,rows)), 'supplemental and main time coordinates differ')
    return data


def analyze(root):
    preparation=json.loads((root/'preparation-receipt.json').read_text())
    result={}
    for name in ('nom','adv'):
        matches=[]
        for path in root.glob('ladder-*/receipt.json'):
            r=json.loads(path.read_text())
            if r.get('requested_cases')==[name]: matches.append((path,r))
        require(len(matches)==1, f'{name}: require exactly one retained refinement run (failed attempts must be separately dispositioned)')
        rp,receipt=matches[0]; case=receipt['cases'][name]
        require(receipt['image']==IMAGE and receipt['platform']=='linux/amd64', 'unexpected solver image/platform')
        for relative,digest in receipt['input_sha256'].items():
            require(sha(rp.parent/'inputs'/relative)==digest, 'runner input snapshot changed')
        for relative,digest in preparation['inputs'].items():
            require(sha(root/relative)==digest, 'prepared input changed')
            if relative.startswith('lib/'):
                require(receipt['input_sha256'][relative]==digest, 'executed library differs from prepared input')
        require(receipt['input_sha256']['.spiceinit']==preparation['inputs']['tracking/.spiceinit'], 'executed settings differ')
        require(receipt['status']==case['status']=='COMPLETE' and receipt['variant_policy']=='original-only', f'{name}: incomplete or solver variants changed')
        require(len(case['attempts'])==1 and case['selected_variant']==0, f'{name}: unexpected attempt selection')
        attempt=case['attempts'][0]
        require(attempt['returncode']==0 and attempt['variant']=='original', f'{name}: solver failed')
        work=rp.parent/name/'0/tracking'; deck=work/(name+'.cir'); main=work/(name+'.dat'); probe=work/(name+'-osc-cap.txt')
        require(sha(deck)==preparation['cases'][name]['derived_deck_sha256']==attempt['deck_sha256'], f'{name}: deck changed')
        for suffix,key in [('.dat','waveform_sha256'),('.log','log_sha256')]: require(sha(work/(name+suffix))==attempt[key], f'{name}: output changed')
        text=deck.read_text()
        for line in ('CL12 p12_out cl12 180u','RCL12 cl12 0 50m','CL5 p5_out cl5 120u','RCL5 cl5 0 50m','CLN 0 cln 180u','RCLN cln m12_out 50m','.tran 2u 250m 0 2u'):
            require(line in text, f'{name}: topology/step no longer matches probe interpretation')
        rows=load(main); side=supplemental(probe,rows); on=window(rows,.04,.2345,name)
        caps=[(r[0],p[1]/.05,p[2]/.05,(p[3]-r[3])/.05) for r,p in zip(rows,side) if .04<=r[0]<.2345]
        screens={}
        for label,index,sign,normal,exception in [('+12',1,1,1.23,None),('+5',2,1,.51,(.45,.95,.114)),('-12',3,-1,1.22,(.75,1.47,.265))]:
            screen=adjacent_slope_screen(on,index,sign,normal,True,exception)
            screen['maximum_osc_capacitor_charging_current_a']=max(x[index] for x in caps)
            if exception:
                region=[c[index] for r,c in zip(on,caps) if 0<=sign*r[index]<=exception[0]]
                screen['exception']['capacitive_current_evidence']='Separate ESR-node voltages from the same solver run; resistor branch current, not source current'
                screen['exception']['maximum_current_in_voltage_region_a']=max(region)
                screen['exception']['current_ceiling_exceeded_in_saved_samples']=max(region)>exception[2]
            screens[label]=screen
        result[name]={'runner_source_revision':receipt['source_revision'],'runner_source_dirty':receipt['source_dirty'],'runner_sha256':receipt['runner_sha256'],'solver_image':receipt['image'],'solver_platform':receipt['platform'],'solver_version_output':receipt['solver_version_output'],'input_sha256':receipt['input_sha256'],'runner_receipt_sha256':sha(rp),'deck_sha256':sha(deck),'main_waveform_sha256':sha(main),'supplemental_waveform_sha256':sha(probe),'supplemental_path':str(probe),'samples':len(rows),'rails':screens}
    return {'scope':'nom and adv only; maximum step 5 us to 2 us; original solver settings','electrical_acceptance':'NOT ESTABLISHED','preparation':preparation,'preparation_receipt_sha256':sha(root/'preparation-receipt.json'),'analysis_sha256':sha(Path(__file__)),'current_interpretation':{'+12':'v(cl12)/0.05 ohm','+5':'v(cl5)/0.05 ohm','-12':'(v(cln)-v(m12_out))/0.05 ohm'},'limits':['Saved adjacent samples are not a continuous-time bound.','Small solver-scale excess requires convergence/model disposition, not a physical violation claim.','No source-current substitution, excess-current budget, or waiver is adopted.'],'cases':result}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('root',type=Path);parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    args.output.write_text(json.dumps(analyze(args.root),indent=2)+'\n')
