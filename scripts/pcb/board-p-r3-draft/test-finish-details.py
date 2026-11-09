"""Pinned-native regression: deterministic/idempotent finish, unchanged project settings and wrong-net rejection."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import pcbnew

source=Path(sys.argv[1]).resolve()
owner=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='r3-artwork-test-') as temporary:
    stage=Path(temporary)
    for name in ['a','b','again','bad']:
        project=source.with_suffix('.kicad_pro')
        if project.exists():shutil.copyfile(project,stage/(name+'.kicad_pro'))
    def finish(first,last):
        projects={path: path.read_bytes() if path.exists() else None
                  for path in [first.with_suffix('.kicad_pro'),last.with_suffix('.kicad_pro')]}
        result=subprocess.run([sys.executable,str(owner/'finish_details.py'),str(first),str(last)],capture_output=True,text=True)
        for path,before in projects.items():
            after=path.read_bytes() if path.exists() else None
            if after!=before:raise ValueError('Artwork save changed project sidecar: '+str(path))
        return result
    a,b,again=(stage/(name+'.kicad_pcb') for name in ['a','b','again'])
    for first,last in [(source,a),(source,b),(a,again)]:
        result=finish(first,last)
        if result.returncode:raise ValueError(result.stdout+result.stderr)
    if a.read_bytes()!=b.read_bytes() or a.read_bytes()!=again.read_bytes():raise ValueError('Artwork replay is not byte-identical/idempotent')
    proof=json.loads(a.with_suffix('.proposal.json').read_text())
    if not proof['unchanged_except_approved_artwork'] or len(proof['changed_items'])!=34:raise ValueError('Non-artwork proof failed')
    board=pcbnew.LoadBoard(str(source));j3=next(fp for fp in board.GetFootprints() if fp.GetReference()=='J3')
    pads={pad.GetNumber():pad for pad in j3.Pads()};pads['4'].SetNet(pads['5'].GetNet())
    bad=stage/'bad.kicad_pcb'
    if not pcbnew.SaveBoard(str(bad),board,True):raise RuntimeError('Negative fixture save failed')
    result=finish(bad,stage/'rejected.kicad_pcb')
    if result.returncode==0 or 'VBUS_IN' not in result.stderr:raise ValueError('Wrong J3.4 net was not explicitly rejected')
    # A polarity cue must never be accepted after D5 pin identity changes.
    board=pcbnew.LoadBoard(str(source));d5=next(fp for fp in board.GetFootprints() if fp.GetReference()=='D5')
    pads={pad.GetNumber():pad for pad in d5.Pads()};pads['1'].SetNet(pads['4'].GetNet())
    if not pcbnew.SaveBoard(str(bad),board,True):raise RuntimeError('Polarity negative fixture save failed')
    result=finish(bad,stage/'rejected.kicad_pcb')
    if result.returncode==0 or 'D5 pin identity changed' not in result.stderr:raise ValueError('Wrong D5.1 net was not explicitly rejected')
print('PASS: byte-identical twins, idempotent replay, artwork-only identity, unchanged source/output project sidecars, J3/D5 wrong-net negative controls')
