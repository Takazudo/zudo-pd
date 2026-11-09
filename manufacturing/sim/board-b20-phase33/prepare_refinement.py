"""Prepare fresh nom/adv 2 us decks without changing circuit or solver tolerances."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def transform(text, name):
    if name not in ('nom','adv') or text.count('.tran 2u 250m 0 5u')!=1 or text.count('.endc')!=1:
        raise ValueError('expected one reviewed 250 ms/5 us transient and control block')
    for line in ('CL12 p12_out cl12 180u','RCL12 cl12 0 50m','CL5 p5_out cl5 120u','RCL5 cl5 0 50m','CLN 0 cln 180u','RCLN cln m12_out 50m'):
        if line not in text: raise ValueError('OSC capacitor/ESR topology differs')
    return text.replace('.tran 2u 250m 0 5u','.tran 2u 250m 0 2u').replace('.endc',f'wrdata {name}-osc-cap.txt v(cl12) v(cl5) v(cln)\n.endc')


def prepare(source, output):
    decks={name:transform((source/'accepted-suite'/f'{name}.cir').read_text(),name) for name in ('nom','adv')}
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
    output.mkdir(parents=True,exist_ok=False)
    shutil.copytree(source/'lib',output/'lib');(output/'tracking').mkdir()
    shutil.copyfile(source/'tracking/.spiceinit',output/'tracking/.spiceinit')
    receipt={'scope':['nom','adv'],'baseline_revision':revision,'changes':['maximum transient step 5us to 2us','output-only supplemental capacitor ESR node voltages'],'cases':{},'physical_acceptance':'NOT ESTABLISHED'}
    for name,text in decks.items():
        path=output/'tracking'/f'{name}.cir';path.write_text(text)
        receipt['cases'][name]={'original':{ext:sha(source/'accepted-suite'/f'{name}.{ext}') for ext in ('cir','dat','log')},'derived_deck_sha256':sha(path)}
    receipt['inputs']={str(p.relative_to(output)):sha(p) for p in sorted(output.rglob('*')) if p.is_file()}
    (output/'preparation-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args();prepare(args.source,args.output)
