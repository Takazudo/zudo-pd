"""Finalize B20 in isolated projects with two fresh pinned-Docker refills.

Run under the machine heavy guard. This CLI acquires the native fcntl lock;
do not wrap it in a second native lock. No canonical project is ever saved.
"""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from verify_staged_geometry import normalize
from sexp import atom, parse, tokenize

ROOT=Path(__file__).resolve().parents[3]
IMAGE='kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec'


def sha(data):return hashlib.sha256(data).hexdigest()
def tree(data):return parse(tokenize(data.decode()))
def require(ok,message):
    if not ok:raise ValueError(message)


def without_fill(node):
    if not isinstance(node,list):return node
    return [without_fill(item) for item in node if not (atom(node[0])=='zone' and isinstance(item,list) and atom(item[0])=='filled_polygon')]


def uuid_bindings(node,model_base):
    """Bind every unique UUID to its own non-fill node and nearest UUID parent."""
    result={}
    def visit(item,parent=None):
        if not isinstance(item,list):return
        ids=[atom(child[1]) for child in item[1:]
             if isinstance(child,list) and atom(child[0])=='uuid']
        require(len(ids)<=1,'Multiple UUIDs on one native item')
        owner=parent
        if ids:
            identity=ids[0]
            require(identity and identity not in result,'Duplicate or empty native item UUID')
            result[identity]=(parent,normalize(item,model_base))
            owner=identity
        for child in item[1:]:visit(child,owner)
    visit(without_fill(node))
    return result


def validate_geometry(before,first,second,model_base):
    require(first==second,'Second fresh-process refill is not byte-identical; candidate rejected')
    a,b=tree(before),tree(first)
    require(normalize(without_fill(a),model_base)==normalize(without_fill(b),model_base),
            'Refill changed non-fill manufacturing geometry; candidate rejected')
    identities=uuid_bindings(a,model_base)
    require(identities==uuid_bindings(b,model_base),'Refill changed native item identity associations')
    return len(identities)


def validate_drc(report):
    require(not report['unconnected_items'] and not report['schematic_parity'], 'Refill has open connections or parity findings')
    expected={'Footprint J6','Footprint J7','Footprint J10','Footprint J11'}
    findings=report['violations']
    require(len(findings)==4 and all(v['severity']=='warning' and v['type']=='lib_footprint_mismatch' for v in findings),
            'Unexpected native DRC findings')
    require({item['description'] for v in findings for item in v['items']}==expected,'Unreviewed library mismatch')


def run_refill(stage,number):
    print(f'Isolated finalization diagnostics: {stage}',flush=True)
    board=stage/'board-b20-draft.kicad_pcb';report=stage/f'drc-{number}.json'
    command=['docker','run','--rm','--platform','linux/amd64','--cpus','1','--user','0',
             '-v',f'{ROOT}:{ROOT}','-w',str(ROOT),'--entrypoint','/bin/bash',IMAGE,
             '-c','broadwayd :5 >/dev/null 2>&1 & sleep 1; GDK_BACKEND=broadway BROADWAY_DISPLAY=:5 exec kicad-cli "$@"',
             'kicad-cli','pcb','drc','--refill-zones','--save-board','--schematic-parity','--format','json','--severity-all',
             '-o',str(report),str(board)]
    process=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (stage/f'refill-{number}.log').write_text(process.stdout)
    require(process.returncode==0,f'Pinned refill {number} failed: {process.stdout}')
    result=json.loads(report.read_text());validate_drc(result)
    return board.read_bytes(),command


def finalize(source,output,project,receipt):
    source,output,project,receipt=map(Path,(source,output,project,receipt))
    before=source.read_bytes();project_bytes=project.read_bytes()
    output_before=output.read_bytes() if output.exists() else None
    sidecars={project.parent/name:(project.parent/name).read_bytes() for name in
              ('board-b20-draft.kicad_sch','fp-lib-table','sym-lib-table')}
    owners=[Path(__file__).resolve(),ROOT/'scripts/pcb/board-b20/verify_staged_geometry.py',ROOT/'scripts/schgen/sexp.py']
    owner_bytes={path:path.read_bytes() for path in owners}
    (ROOT/'tmp').mkdir(exist_ok=True)
    # Fixed depth matches canonical boards/<board>, preserving ${KIPRJMOD}/../../ models.
    stage=Path(tempfile.mkdtemp(prefix='b20-finalize-',dir=ROOT/'tmp'))
    print(f'Isolated finalization diagnostics: {stage}',flush=True)
    board=stage/'board-b20-draft.kicad_pcb';private_project=board.with_suffix('.kicad_pro')
    board.write_bytes(before)
    for path,data in sidecars.items():
        (stage/path.name).write_bytes(data)
    private_project.write_bytes(project_bytes)
    first,command1=run_refill(stage,1)
    (stage/'first-refill.kicad_pcb').write_bytes(first)
    private_project.write_bytes(project_bytes) # isolated copy only; exact authored rules for both passes
    second,command2=run_refill(stage,2)
    identity_count=validate_geometry(before,first,second,project.resolve().parent)
    require(source.read_bytes()==before,'Source changed during finalization')
    require(project.read_bytes()==project_bytes,'Authored project changed during finalization')
    for path,data in {**sidecars,**owner_bytes}.items():
        require(path.read_bytes()==data,f'Native context/checker changed during finalization: {path}')
    result={'scope':'Owned serialized reload/refill finalization; two fresh pinned Docker CLI processes, no heuristic rerouting.',
            'input_sha256':sha(before),'pcb_sha256':sha(second),'project_sha256':sha(project_bytes),
            'byte_identical_second_refill':True,'nonfill_geometry_unchanged':True,'native_ids_unchanged':True,'native_identity_count':identity_count,
            'image':IMAGE,'commands':[command1,command2],'diagnostics':str(stage.relative_to(ROOT)),
            'source_hashes':{str(path.relative_to(ROOT)):sha(data) for path,data in owner_bytes.items()},
            'native_context_hashes':{str(path):sha(data) for path,data in sidecars.items()},
            'drc':{'errors':0,'unconnected':0,'parity':0,'warnings':'J6/J7/J10/J11 reviewed silk-only library mismatches'},
            'limit':'Fill delta still requires independent review; no electrical, thermal, supplier or order acceptance.'}
    require((output.read_bytes() if output.exists() else None)==output_before,'Output changed during finalization')
    # Adoption occurs only after both actual native passes and unchanged-input checks.
    output.write_bytes(second)
    receipt.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--project',required=True,type=Path);parser.add_argument('--receipt',required=True,type=Path)
    args=parser.parse_args()
    with open('/tmp/kicad-native.lock','a') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
        finalize(args.source,args.output,args.project,args.receipt)


if __name__=='__main__':main()
